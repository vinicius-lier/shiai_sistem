from decimal import Decimal, InvalidOperation
from datetime import date
from typing import Optional, Tuple

from django.db import transaction
from django.core.exceptions import ValidationError

from atletas.models import (
    Inscricao,
    Classe,
    Categoria,
)


# =========================
# Helpers de status
# =========================
STATUS_ATUAL = {
    "PENDENTE": "pendente",
    "INSCRITO": "inscrito",
    "APROVADO": "aprovado",
    "REMANEJADO": "remanejado",
    "DESCLASSIFICADO": "desclassificado",
}


def map_status_legado(status_legado: str) -> str:
    if not status_legado:
        return STATUS_ATUAL["PENDENTE"]
    s = status_legado.lower()
    if s == "pendente_pesagem":
        return STATUS_ATUAL["INSCRITO"]
    if s == "ok":
        return STATUS_ATUAL["APROVADO"]
    if s == "remanejado":
        return STATUS_ATUAL["REMANEJADO"]
    if s == "desclassificado":
        return STATUS_ATUAL["DESCLASSIFICADO"]
    if s in ("pendente", "confirmado"):
        return STATUS_ATUAL["INSCRITO"]
    if s == "aprovado":
        return STATUS_ATUAL["APROVADO"]
    if s == "reprovado":
        return STATUS_ATUAL["DESCLASSIFICADO"]
    return STATUS_ATUAL["PENDENTE"]


# =========================
# Classe / Idade (ano do evento)
# =========================
def _normalize_classe_nome(classe_nome: str) -> str:
    if not classe_nome:
        return ""
    return classe_nome.strip().upper().replace("SUB ", "SUB-")


def calcular_classe_por_idade(idade: Optional[int]) -> Optional[str]:
    if idade is None:
        return None
    if idade <= 6:
        return "FESTIVAL"
    if 7 <= idade <= 8:
        return "SUB-9"
    if idade == 9:
        return "SUB-10"
    if idade == 10:
        return "SUB-11"
    if 11 <= idade <= 12:
        return "SUB-13"
    if 13 <= idade <= 14:
        return "SUB-15"
    if 15 <= idade <= 17:
        return "SUB-18"
    if 18 <= idade <= 29:
        return "SÊNIOR"
    return "VETERANOS"


def validar_classe(classe_nome: str, idade: Optional[int]) -> bool:
    if not classe_nome:
        return False
    cls = _normalize_classe_nome(classe_nome)
    if idade is None:
        return True
    calc = _normalize_classe_nome(calcular_classe_por_idade(idade))
    if cls in ("MASTER", "MASTERS"):
        cls = "VETERANOS"
    if calc in ("SUB-18", "SUB-21", "SÊNIOR"):
        return cls in ("SUB-18", "SUB-21", "SÊNIOR")
    if calc == "VETERANOS":
        return cls in ("VETERANOS", "SÊNIOR")
    return cls == calc


def _ano_evento_from_campeonato(campeonato) -> int:
    if campeonato and getattr(campeonato, "data_competicao", None):
        return campeonato.data_competicao.year
    return date.today().year


def _ano_nascimento_atleta(atleta) -> Optional[int]:
    if atleta is None:
        return None
    if hasattr(atleta, "get_ano_nasc"):
        return atleta.get_ano_nasc()
    data_nascimento = getattr(atleta, "data_nascimento", None)
    if data_nascimento:
        return data_nascimento.year
    return getattr(atleta, "ano_nasc", None)


def _idade_evento(ano_nascimento: Optional[int], ano_evento: int) -> Optional[int]:
    if not ano_nascimento or not ano_evento:
        return None
    return int(ano_evento) - int(ano_nascimento)


def _get_classe_por_nome(classe_nome: Optional[str]) -> Optional[Classe]:
    if not classe_nome:
        return None
    nome = _normalize_classe_nome(classe_nome)
    classe = Classe.objects.filter(nome__iexact=nome).first()
    if classe:
        return classe
    if nome == "VETERANOS":
        classe = Classe.objects.filter(nome__iexact="MASTER").first()
        if classe:
            return classe
    alt = nome.replace("-", " ")
    return Classe.objects.filter(nome__iexact=alt).first()


# =========================
# Categoria / Peso
# =========================
def _normalize_decimal(peso) -> Optional[Decimal]:
    if peso is None:
        return None
    try:
        if isinstance(peso, Decimal):
            return peso
        return Decimal(str(peso))
    except (InvalidOperation, ValueError, TypeError):
        return None


def calcular_categoria_por_peso(classe: Classe, sexo: str, peso: Decimal) -> Optional[Categoria]:
    if not classe or not sexo or peso is None:
        return None
    qs = Categoria.objects.filter(
        classe=classe,
        sexo=sexo
    ).order_by('limite_min')
    cat = qs.filter(
        limite_min__lte=peso
    ).filter(
        limite_max__gte=peso
    ).first()
    if cat:
        return cat
    acima = qs.filter(limite_min__gt=peso).order_by('limite_min').first()
    abaixo = qs.filter(limite_min__lte=peso).order_by('-limite_min').first()
    return acima or abaixo


def validar_peso_oficial(peso) -> Optional[Decimal]:
    d = _normalize_decimal(peso)
    if d is None or d <= Decimal("0"):
        return None
    return d


# =========================
# Fluxo de inscrição/pesagem
# =========================
@transaction.atomic
def inscrever_atleta(atleta, campeonato, classe: Optional[Classe], categoria: Optional[Categoria], peso=None) -> Inscricao:
    """
    Cria inscrição com campos normalizados e status 'inscrito'.
    """
    if not atleta or not campeonato:
        raise ValidationError("Atleta e campeonato são obrigatórios.")

    # Peso opcional
    peso_real = validar_peso_oficial(peso)

    # Classe obrigatória (por FK)
    if not classe:
        # tenta por idade no ano do evento (sem considerar mês/dia)
        ano_evento = _ano_evento_from_campeonato(campeonato)
        idade = _idade_evento(_ano_nascimento_atleta(atleta), ano_evento)
        classe_nome = calcular_classe_por_idade(idade)
        classe = _get_classe_por_nome(classe_nome)
    if not classe:
        raise ValidationError("Classe não informada ou inválida.")

    # Categoria opcional, mas se não vier e houver peso, tentar calcular
    if not categoria and peso_real is not None:
        categoria = calcular_categoria_por_peso(classe, atleta.sexo, peso_real)

    # Evitar duplicidade mesma classe/categoria/campeonato
    dup = Inscricao.objects.filter(
        atleta=atleta,
        campeonato=campeonato,
        classe_real=classe,
        categoria_real=categoria
    ).first()
    if dup:
        return dup

    ins = Inscricao.objects.create(
        atleta=atleta,
        campeonato=campeonato,
        classe_real=classe,
        categoria_real=categoria,
        peso_real=peso_real,
        status_atual=STATUS_ATUAL["INSCRITO"],
        bloqueado_chave=True,
    )
    return ins


@transaction.atomic
def aprovar(inscricao: Inscricao, peso=None):
    peso_real = validar_peso_oficial(peso) or inscricao.peso_real
    inscricao.peso_real = peso_real
    inscricao.status_atual = STATUS_ATUAL["APROVADO"]
    inscricao.bloqueado_chave = False
    inscricao.remanejado = False
    inscricao.save(update_fields=["peso_real", "status_atual", "bloqueado_chave", "remanejado"])
    return inscricao


@transaction.atomic
def remanejar(inscricao: Inscricao, nova_categoria: Categoria, peso=None):
    if not nova_categoria:
        raise ValidationError("Categoria obrigatória para remanejamento.")
    peso_real = validar_peso_oficial(peso) or inscricao.peso_real
    inscricao.peso_real = peso_real
    inscricao.categoria_real = nova_categoria
    inscricao.status_atual = STATUS_ATUAL["REMANEJADO"]
    inscricao.remanejado = True
    inscricao.bloqueado_chave = False
    inscricao.save(update_fields=["peso_real", "categoria_real", "status_atual", "remanejado", "bloqueado_chave"])
    return inscricao


@transaction.atomic
def desclassificar(inscricao: Inscricao, motivo: str = ""):
    inscricao.status_atual = STATUS_ATUAL["DESCLASSIFICADO"]
    inscricao.bloqueado_chave = True
    inscricao.remanejado = False
    if motivo:
        inscricao.motivo_ajuste = motivo
    inscricao.save(update_fields=["status_atual", "bloqueado_chave", "remanejado", "motivo_ajuste"])
    return inscricao
