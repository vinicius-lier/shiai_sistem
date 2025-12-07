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
# Classe / Idade
# =========================
def calcular_classe_por_idade(idade: Optional[int]) -> Optional[str]:
    if idade is None:
        return None
    if idade <= 6:
        return "FESTIVAL"
    if 7 <= idade <= 8:
        return "SUB-9"
    if 9 <= idade <= 10:
        return "SUB-11"
    if 11 <= idade <= 12:
        return "SUB-13"
    if 13 <= idade <= 14:
        return "SUB-15"
    if 15 <= idade <= 17:
        return "SUB-18"
    if 18 <= idade <= 20:
        return "SUB-21"
    if 21 <= idade <= 29:
        return "SÊNIOR"
    return "VETERANOS"


def validar_classe(classe_nome: str, idade: Optional[int]) -> bool:
    if not classe_nome:
        return False
    cls = classe_nome.upper().strip()
    if idade is None:
        return True
    calc = calcular_classe_por_idade(idade)
    if calc == "SUB-18" and cls in ("SUB-18", "SUB-21", "SÊNIOR"):
        return True
    if calc == "SUB-21" and cls in ("SUB-21", "SÊNIOR"):
        return True
    if calc == "VETERANOS" and cls in ("VETERANOS", "SÊNIOR"):
        return True
    # Igual calculado
    return cls == calc


def _idade_atual(data_nascimento) -> Optional[int]:
    if not data_nascimento:
        return None
    hoje = date.today()
    return (
        hoje.year
        - data_nascimento.year
        - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))
    )


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
        # tenta por idade
        idade = _idade_atual(getattr(atleta, "data_nascimento", None))
        classe_nome = calcular_classe_por_idade(idade)
        classe = Classe.objects.filter(nome__iexact=classe_nome).first() if classe_nome else None
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

