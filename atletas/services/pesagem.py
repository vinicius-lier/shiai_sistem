from typing import Optional, Tuple, Dict
from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone

from atletas.models import (
    Categoria,
    Inscricao,
    PesagemHistorico,
    OcorrenciaAtleta,
    AcademiaPontuacao,
    Chave,
    Luta,
    Classe,
)
from atletas.utils import validar_faixa_e_categoria_por_idade


def _normalize_classe_nome(nome: str) -> str:
    """
    Normaliza nome de classe para comparação/lookup em Categoria.
    Exemplos:
      - "sub 9" -> "SUB-9"
      - "veteranos" -> "VETERANOS"
      - "master", "sênior" -> "SÊNIOR"
    """
    if not nome:
        return ""
    up = nome.strip().upper().replace("SUB ", "SUB-")

    # remover sufixos tipo " - F" ou " - M"
    if " - " in up:
        up = up.split(" - ", 1)[0]
    if up in {"VETERANOS", "VETERANO", "VETS"}:
        return "VETERANOS"
    if up in {
        "MASTER",
        "MASTERS",
        "SÊNIOR",
        "SENIOR",
        "SENIOR / MASTER",
        "SÊNIOR / MASTER",
        "SENIOR/MASTER",
        "SÊNIOR/MASTER",
        "SENIORES",
    }:
        return "SÊNIOR"
    return up


def _buscar_classe_por_nome(nome: str):
    """
    Encontra Classe usando normalizacao flexivel (SUB 13 vs SUB-13).
    Retorna None se nao encontrar.
    """
    if not nome:
        return None
    nome_norm = _normalize_classe_nome(nome)
    # Tenta match direto primeiro
    classe = Classe.objects.filter(nome__iexact=nome).first()
    if classe:
        return classe
    # Match por normalizacao
    for classe_obj in Classe.objects.all():
        if _normalize_classe_nome(classe_obj.nome) == nome_norm:
            return classe_obj
    return None


def _tolerancia_por_classe(classe_nome: str) -> Decimal:
    """
    Retorna tolerância (kg) aplicada no limite máximo para a classe.
    Até Sub18: 0.2kg. Acima disso: 0.
    """
    if not classe_nome:
        return Decimal("0.0")
    nome = _normalize_classe_nome(classe_nome)
    sub_list = ['SUB-9', 'SUB-11', 'SUB-13', 'SUB-15', 'SUB-18']
    if nome in sub_list:
        return Decimal("0.2")  # 200 gramas
    return Decimal("0.0")


def calcular_categoria_por_peso(classe_nome: str, sexo: str, peso: Decimal) -> Optional[Categoria]:
    """
    Retorna a categoria que contém o peso informado para a classe e sexo.
    Se não encontrar exata, tenta a mais próxima acima ou abaixo.
    """
    if isinstance(peso, float):
        peso = Decimal(str(peso))
    elif isinstance(peso, (int,)):
        peso = Decimal(peso)
    elif not isinstance(peso, Decimal):
        peso = Decimal(str(peso))
    if not classe_nome or not sexo or peso is None:
        return None
    classe_obj = _buscar_classe_por_nome(classe_nome)
    if not classe_obj:
        return None

    qs = Categoria.objects.filter(
        classe=classe_obj,
        sexo=sexo
    ).order_by('limite_min')

    categoria = qs.filter(
        limite_min__lte=peso
    ).filter(
        models.Q(limite_max__gte=peso) | models.Q(limite_max__isnull=True)
    ).first()

    if categoria:
        return categoria

    acima = qs.filter(limite_min__gt=peso).order_by('limite_min').first()
    abaixo = qs.filter(limite_min__lte=peso).order_by('-limite_min').first()
    return acima or abaixo


def _limites_categoria(categoria: Optional[Categoria]) -> Tuple[Optional[Decimal], Optional[Decimal]]:
    if not categoria:
        return None, None
    limite_min = categoria.limite_min
    limite_max = categoria.limite_max if categoria.limite_max is not None else None
    return limite_min, limite_max


def validar_peso(inscricao: Inscricao, peso: float) -> Dict:
    """
    Não salva nada. Apenas valida peso contra categoria atual e sugere nova categoria.
    """
    if isinstance(peso, float):
        peso = Decimal(str(peso))
    elif isinstance(peso, (int,)):
        peso = Decimal(peso)
    elif not isinstance(peso, Decimal):
        try:
            peso = Decimal(str(peso))
        except Exception:
            return {
                'categoria_ok': False,
                'precisa_remanejamento': True,
                'status_pesagem': 'PESO_FORA',
                'mensagem': 'Peso inválido',
                'categoria_encontrada': None,
                'categoria_sugerida': None,
                'categoria_atual_nome': '',
            }
    categoria_nome_raw = (
        inscricao.categoria_real.categoria_nome if inscricao.categoria_real else
        inscricao.categoria_ajustada or inscricao.categoria_calculada or ''
    )
    if ' - ' in categoria_nome_raw:
        # Sempre pegar a última parte como nome da categoria
        categoria_nome = categoria_nome_raw.rsplit(' - ', 1)[-1].strip()
    else:
        categoria_nome = categoria_nome_raw
    classe_atleta_raw = inscricao.classe_real.nome if inscricao.classe_real else None
    classe_atleta = _normalize_classe_nome(classe_atleta_raw)

    categoria_encontrada = None
    categoria_sugerida = None
    categoria_ok = False
    precisa_remanejamento = False
    status_pesagem = 'APTO'
    mensagem = ''

    if categoria_nome and classe_atleta:
        # Preferir categoria_real se existir
        if inscricao.categoria_real:
            categoria_encontrada = inscricao.categoria_real
        else:
            categoria_encontrada = Categoria.objects.filter(
                categoria_nome=categoria_nome,
                classe__nome=classe_atleta,
                sexo=inscricao.atleta.sexo
            ).first()
            if not categoria_encontrada and classe_atleta_raw and classe_atleta_raw != classe_atleta:
                categoria_encontrada = Categoria.objects.filter(
                    categoria_nome=categoria_nome,
                    classe__nome=classe_atleta_raw,
                    sexo=inscricao.atleta.sexo
                ).first()
            if not categoria_encontrada:
                categoria_encontrada = Categoria.objects.filter(
                    categoria_nome=categoria_nome,
                    sexo=inscricao.atleta.sexo
                ).order_by('limite_min').first()

        if categoria_encontrada:
            tolerancia = _tolerancia_por_classe(classe_atleta)
            limite_max_real = None
            if categoria_encontrada.limite_max is not None and categoria_encontrada.limite_max < Decimal("999.0"):
                limite_max_real = categoria_encontrada.limite_max + tolerancia

            dentro_limite_superior = True
            if limite_max_real is not None:
                dentro_limite_superior = peso <= limite_max_real

            if categoria_encontrada.limite_min <= peso and dentro_limite_superior:
                categoria_ok = True
                mensagem = 'OK'
            elif limite_max_real is not None and peso > limite_max_real:
                categoria_ok = False
                precisa_remanejamento = True
                status_pesagem = 'PESO_FORA'
                mensagem = f'Peso {peso}kg acima do limite máximo ({limite_max_real}kg)'
                categoria_sugerida = calcular_categoria_por_peso(classe_atleta, inscricao.atleta.sexo, peso)
            else:
                categoria_ok = False
                precisa_remanejamento = True
                status_pesagem = 'PESO_FORA'
                mensagem = f'Peso {peso}kg abaixo do limite mínimo ({categoria_encontrada.limite_min}kg)'
                categoria_sugerida = calcular_categoria_por_peso(classe_atleta, inscricao.atleta.sexo, peso)
        else:
            # Sem categoria encontrada, forçar remanejamento/desclassificação
            categoria_ok = False
            precisa_remanejamento = True
            status_pesagem = 'PESO_FORA'
            mensagem = 'Categoria não encontrada para validar peso'
            categoria_sugerida = calcular_categoria_por_peso(classe_atleta, inscricao.atleta.sexo, peso)

    print("[AUDITORIA PESO] categoria_atual_raw=", categoria_nome_raw,
          "categoria_normalizada=", categoria_nome,
          "classe_raw=", classe_atleta_raw,
          "classe_norm=", classe_atleta,
          "tolerancia=", _tolerancia_por_classe(classe_atleta),
          "limite_min=", categoria_encontrada.limite_min if categoria_encontrada else None,
          "limite_max=", categoria_encontrada.limite_max if categoria_encontrada else None,
          "limite_max_real=", limite_max_real if 'limite_max_real' in locals() else None,
          "status_pesagem=", status_pesagem,
          "categoria_sugerida=", categoria_sugerida.categoria_nome if categoria_sugerida else None)

    return {
        'categoria_ok': categoria_ok,
        'precisa_remanejamento': precisa_remanejamento,
        'status_pesagem': status_pesagem,
        'mensagem': mensagem,
        'categoria_encontrada': categoria_encontrada,
        'categoria_sugerida': categoria_sugerida,
        'categoria_atual_nome': categoria_nome_raw or categoria_nome,
    }


def registrar_peso(inscricao: Inscricao, peso: Decimal, observacoes: str = "", usuario=None) -> Dict:
    """
    Fluxo central de registro de pesagem:
    - Se peso dentro do limite: salva e retorna sucesso.
    - Se fora do limite: não salva; retorna payload para decisão (remanejar/desclassificar).
    Importante: nenhuma escrita de histórico/ocorrência acontece aqui em caso de peso fora.
    """
    if isinstance(peso, float):
        peso = Decimal(str(peso))
    elif isinstance(peso, (int,)):
        peso = Decimal(peso)
    elif not isinstance(peso, Decimal):
        peso = Decimal(str(peso))

    faixa_ok, faixa_msg, categoria_etaria, grupo = validar_faixa_e_categoria_por_idade(inscricao.atleta)
    if not faixa_ok:
        desclassificar_por_faixa(
            inscricao,
            peso,
            motivo=faixa_msg,
            categoria_etaria=categoria_etaria,
            grupo_tecnico=grupo,
            observacoes=observacoes,
            usuario=usuario,
        )
        return {
            "categoria_ok": False,
            "desclassificado": True,
            "status_pesagem": "FAIXA_INVALIDA",
            "mensagem_validacao": faixa_msg,
            "resultado": "desclassificado",
            "motivo": "faixa_incompativel_idade",
        }

    validacao = validar_peso(inscricao, peso)
    categoria_encontrada = validacao.get("categoria_encontrada")
    categoria_sugerida = validacao.get("categoria_sugerida")

    if validacao["categoria_ok"]:
        registrar_peso_ok(
            inscricao,
            peso,
            categoria_final=categoria_encontrada,
            observacoes=observacoes,
            motivo_ajuste=validacao.get("mensagem"),
            usuario=usuario,
        )
        limite_min, limite_max = _limites_categoria(categoria_encontrada)
        return {
            "categoria_ok": True,
            "status_pesagem": validacao.get("status_pesagem"),
            "categoria_encontrada": categoria_encontrada.categoria_nome if categoria_encontrada else validacao.get("categoria_atual_nome"),
            "limite_min": limite_min,
            "limite_max": limite_max,
        }

    limite_atual_min, limite_atual_max = _limites_categoria(categoria_encontrada)
    limite_novo_min, limite_novo_max = _limites_categoria(categoria_sugerida)
    print("[AUDITORIA PESO] retorno_validacao",
          "categoria_ok=", validacao.get("categoria_ok"),
          "status=", validacao.get("status_pesagem"),
          "categoria_atual=", validacao.get("categoria_atual_nome"),
          "categoria_encontrada=", categoria_encontrada.categoria_nome if categoria_encontrada else None,
          "categoria_sugerida=", categoria_sugerida.categoria_nome if categoria_sugerida else None,
          "limite_atual=", (limite_atual_min, limite_atual_max),
          "limite_novo=", (limite_novo_min, limite_novo_max))
    return {
        "categoria_ok": False,
        "precisa_confirmacao": True,
        "status_pesagem": validacao.get("status_pesagem"),
        "mensagem_validacao": validacao.get("mensagem"),
        "categoria_atual": validacao.get("categoria_atual_nome"),
        "categoria_encontrada": categoria_encontrada.categoria_nome if categoria_encontrada else None,
        "limite_atual_min": limite_atual_min,
        "limite_atual_max": limite_atual_max,
        "categoria_nova": categoria_sugerida.categoria_nome if categoria_sugerida else None,
        "limite_novo_min": limite_novo_min,
        "limite_novo_max": limite_novo_max,
    }


def remover_de_chaves(campeonato, atleta):
    """
    Remove atleta de todas as chaves e lutas do campeonato.
    """
    chaves = Chave.objects.filter(campeonato=campeonato, atletas=atleta)
    for chave in chaves:
        chave.atletas.remove(atleta)
        # remover lutas onde o atleta participa
        Luta.objects.filter(chave=chave).filter(
            models.Q(atleta_a=atleta) | models.Q(atleta_b=atleta) | models.Q(vencedor=atleta)
        ).delete()
        chave.save()


def registrar_peso_ok(inscricao: Inscricao, peso: Decimal, categoria_final: Optional[Categoria] = None, observacoes: str = '', motivo_ajuste: str = '', usuario=None):
    """
    Salva peso e histórico quando dentro do limite.
    """
    inscricao.peso = peso
    inscricao.data_pesagem = timezone.now()
    inscricao.peso_real = peso
    inscricao.status_inscricao = 'aprovado'
    inscricao.status_atual = 'aprovado'
    inscricao.bloqueado_chave = False
    inscricao.remanejado = False
    if categoria_final:
        inscricao.categoria_calculada = categoria_final.categoria_nome
        inscricao.categoria_ajustada = inscricao.categoria_ajustada or categoria_final.categoria_nome
        inscricao.categoria_real = categoria_final
        inscricao.classe_real = categoria_final.classe
    if motivo_ajuste:
        inscricao.motivo_ajuste = motivo_ajuste
    inscricao.save(update_fields=[
        'peso',
        'peso_real',
        'data_pesagem',
        'status_inscricao',
        'status_atual',
        'bloqueado_chave',
        'remanejado',
        'categoria_calculada',
        'categoria_ajustada',
        'categoria_real',
        'classe_real',
        'motivo_ajuste'
    ])

    PesagemHistorico.objects.create(
        inscricao=inscricao,
        campeonato=inscricao.campeonato,
        peso_registrado=peso,
        categoria_ajustada=inscricao.categoria_ajustada or inscricao.categoria_calculada or inscricao.categoria_escolhida,
        motivo_ajuste=motivo_ajuste or 'Peso dentro da categoria',
        observacoes=observacoes or '',
        pesado_por=usuario if usuario and usuario.is_authenticated else None
    )


@transaction.atomic
def confirmar_remanejamento(inscricao: Inscricao, peso: Decimal, acao: str, categoria_sugerida: Optional[Categoria], observacoes: str = '', usuario=None):
    """
    Executa a decisão do modal: remanejar ou desclassificar.
    - Se remanejar: recalcula categoria (usa sugerida se fornecida), debita 1 ponto, registra ocorrência e histórico, remove chaves antigas.
    - Se desclassificar: status desclassificado, ocorrência, remove chaves e bloqueia chaveamento.
    """
    inscricao.peso = peso
    inscricao.peso_real = peso
    inscricao.data_pesagem = timezone.now()

    # Nome/categoria legada para fallback em ocorrências
    categoria_nome_raw = (
        inscricao.categoria_real.categoria_nome if inscricao.categoria_real else
        inscricao.categoria_ajustada or inscricao.categoria_calculada or ''
    )

    if acao == 'remanejar':
        faixa_ok, faixa_msg, categoria_etaria, grupo = validar_faixa_e_categoria_por_idade(inscricao.atleta)
        if not faixa_ok:
            raise ValueError(faixa_msg)

        if not categoria_sugerida:
            raise ValueError("Categoria sugerida obrigatoria para remanejamento.")

        categoria_final = categoria_sugerida
        classe_final = categoria_final.classe.nome if categoria_final.classe else ""
        if categoria_etaria:
            classe_norm = _normalize_classe_nome(classe_final)
            categoria_norm = _normalize_classe_nome(categoria_etaria)
            if classe_norm and categoria_norm and classe_norm != categoria_norm:
                raise ValueError("Categoria sugerida incompativel com idade.")

# Atualizar campos novos
        inscricao.categoria_ajustada = categoria_final.categoria_nome
        inscricao.categoria_calculada = categoria_final.categoria_nome
        inscricao.categoria_real = categoria_final
        inscricao.classe_real = categoria_final.classe or inscricao.classe_real
        inscricao.status_inscricao = 'aprovado'
        inscricao.status_atual = 'remanejado'
        inscricao.remanejado = True
        inscricao.bloqueado_chave = False
        inscricao.motivo_ajuste = inscricao.motivo_ajuste or 'Remanejamento confirmado via pesagem'
        inscricao.save(update_fields=[
            'categoria_ajustada',
            'categoria_calculada',
            'categoria_real',
            'status_inscricao',
            'status_atual',
            'remanejado',
            'bloqueado_chave',
            'motivo_ajuste',
            'peso',
            'peso_real',
            'data_pesagem'
        ])

        PesagemHistorico.objects.create(
            inscricao=inscricao,
            campeonato=inscricao.campeonato,
            peso_registrado=peso,
            categoria_ajustada=categoria_final.categoria_nome,
            motivo_ajuste='Peso fora do limite - remanejamento automático',
            observacoes=observacoes or '',
            pesado_por=usuario if usuario and usuario.is_authenticated else None
        )

        OcorrenciaAtleta.objects.create(
            atleta=inscricao.atleta,
            campeonato=inscricao.campeonato,
            tipo='REMANEJAMENTO',
            motivo='REMANEJAMENTO AUTOMÁTICO',
            detalhes_json={
                'peso_registrado': peso,
                'categoria_antiga': (inscricao.categoria_real.categoria_nome if inscricao.categoria_real else categoria_nome_raw),
                'categoria_nova': categoria_final.categoria_nome
            }
        )

        pontuacao, _ = AcademiaPontuacao.objects.get_or_create(
            campeonato=inscricao.campeonato,
            academia=inscricao.atleta.academia,
            defaults={'pontos_totais': 0}
        )
        pontuacao.remanejamento = pontuacao.remanejamento + 1
        pontuacao.pontos_totais = pontuacao.pontos_totais - 1
        pontuacao.save()

        # Remover atleta de chaves antigas para reprocessar chaveamento
        remover_de_chaves(inscricao.campeonato, inscricao.atleta)
        return 'remanejado', categoria_final

    elif acao == 'desclassificar':
        inscricao.status_inscricao = 'desclassificado'
        inscricao.status_atual = 'desclassificado'
        inscricao.remanejado = False
        inscricao.bloqueado_chave = True
        inscricao.motivo_ajuste = 'Desclassificado por peso fora da categoria - exige nova inscrição'
        inscricao.save(update_fields=[
            'status_inscricao',
            'status_atual',
            'remanejado',
            'bloqueado_chave',
            'motivo_ajuste',
            'peso',
            'peso_real',
            'data_pesagem'
        ])

        PesagemHistorico.objects.create(
            inscricao=inscricao,
            campeonato=inscricao.campeonato,
            peso_registrado=peso,
            categoria_ajustada=inscricao.categoria_ajustada or (inscricao.categoria_real.categoria_nome if inscricao.categoria_real else ''),
            motivo_ajuste='Desclassificado por peso fora do limite',
            observacoes=observacoes or '',
            pesado_por=usuario if usuario and usuario.is_authenticated else None
        )

        OcorrenciaAtleta.objects.create(
            atleta=inscricao.atleta,
            campeonato=inscricao.campeonato,
            tipo='DESCLASSIFICACAO',
            motivo='DESCLASSIFICACAO',
            detalhes_json={
                'peso_registrado': peso,
                'categoria_original': (inscricao.categoria_real.categoria_nome if inscricao.categoria_real else '')
            }
        )

        remover_de_chaves(inscricao.campeonato, inscricao.atleta)
        return 'desclassificado', None

    else:
        raise ValueError("Ação inválida. Use 'remanejar' ou 'desclassificar'.")


def desclassificar_por_faixa(inscricao: Inscricao, peso: Decimal, motivo: str, categoria_etaria: Optional[str], grupo_tecnico: Optional[str], observacoes: str = '', usuario=None):
    inscricao.peso = peso
    inscricao.peso_real = peso
    inscricao.data_pesagem = timezone.now()
    inscricao.status_inscricao = 'desclassificado'
    inscricao.status_atual = 'desclassificado'
    inscricao.remanejado = False
    inscricao.bloqueado_chave = True
    inscricao.motivo_ajuste = motivo
    inscricao.save(update_fields=[
        'status_inscricao',
        'status_atual',
        'remanejado',
        'bloqueado_chave',
        'motivo_ajuste',
        'peso',
        'peso_real',
        'data_pesagem'
    ])

    PesagemHistorico.objects.create(
        inscricao=inscricao,
        campeonato=inscricao.campeonato,
        peso_registrado=peso,
        categoria_ajustada=inscricao.categoria_ajustada or (inscricao.categoria_real.categoria_nome if inscricao.categoria_real else ''),
        motivo_ajuste=motivo,
        observacoes=observacoes or '',
        pesado_por=usuario if usuario and usuario.is_authenticated else None
    )

    OcorrenciaAtleta.objects.create(
        atleta=inscricao.atleta,
        campeonato=inscricao.campeonato,
        tipo='DESCLASSIFICACAO',
        motivo='FAIXA_IDADE',
        detalhes_json={
            'peso_registrado': peso,
            'faixa': inscricao.atleta.faixa,
            'categoria_etaria': categoria_etaria,
            'grupo_tecnico': grupo_tecnico,
        }
    )

    remover_de_chaves(inscricao.campeonato, inscricao.atleta)

