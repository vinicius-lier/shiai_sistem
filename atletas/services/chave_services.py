"""
Serviços para geração e gerenciamento de chaves de judô.
Implementa todos os formatos de chave solicitados.
"""
from decimal import Decimal
from django.db import transaction
from django.db.models import Q
from atletas.models import Chave, Luta, Atleta, Categoria
from eventos.models import Evento, EventoAtleta


def criar_luta(chave, **kwargs):
    """
    Helper para criar lutas sempre com evento vinculado.
    """
    if 'evento' not in kwargs:
        kwargs['evento'] = chave.evento
    return Luta.objects.create(chave=chave, **kwargs)


def validar_pesagem_completa(evento, categoria):
    """
    Valida se todos os atletas da categoria foram pesados.
    Retorna (True, None) se válido, (False, mensagem) se inválido.
    """
    from eventos.models import EventoAtleta
    
    # Buscar todos os EventoAtleta da categoria no evento
    evento_atletas = EventoAtleta.objects.filter(
        evento=evento,
        categoria_final__categoria_nome=categoria.categoria_nome,
        categoria_final__classe=categoria.classe,
        categoria_final__sexo=categoria.sexo
    ).select_related('atleta', 'categoria_final')
    
    # Verificar se todos têm peso_oficial, categoria_final e status OK
    pendentes = []
    for evento_atleta in evento_atletas:
        if not evento_atleta.peso_oficial:
            pendentes.append(f"{evento_atleta.atleta.nome} (sem peso oficial)")
        elif not evento_atleta.categoria_final:
            pendentes.append(f"{evento_atleta.atleta.nome} (sem categoria final)")
        elif evento_atleta.status_pesagem not in ['OK', 'REMANEJADO']:
            pendentes.append(f"{evento_atleta.atleta.nome} (status: {evento_atleta.status_pesagem})")
    
    if pendentes:
        return False, f"Os seguintes atletas ainda não foram pesados ou estão pendentes: {', '.join(pendentes[:5])}{'...' if len(pendentes) > 5 else ''}"
    
    return True, None


def obter_atletas_categoria(evento, categoria):
    """
    Retorna lista de EventoAtleta aptos para a categoria no evento.
    Filtra apenas atletas com peso_oficial e status OK/REMANEJADO.
    """
    evento_atletas = EventoAtleta.objects.filter(
        evento=evento,
        categoria_final__categoria_nome=categoria.categoria_nome,
        categoria_final__classe=categoria.classe,
        categoria_final__sexo=categoria.sexo,
        peso_oficial__isnull=False,
        status__in=['OK']
    ).select_related('atleta', 'categoria_final')
    
    # Converter para lista de Atleta para compatibilidade
    atletas = [ea.atleta for ea in evento_atletas if ea.atleta]
    return atletas


def determinar_tipo_chave_automatico(num_atletas):
    """
    Determina o tipo de chave automaticamente baseado no número de atletas.
    """
    if num_atletas == 2:
        return 'MELHOR_DE_3'
    elif num_atletas == 3:
        return 'SIMPLES_3'  # ✅ NOVO: Eliminatória simples com 3 atletas (stand-by)
    elif 3 < num_atletas <= 5:
        return 'RODIZIO'
    elif num_atletas >= 6:
        return 'ELIMINATORIA_REPESCAGEM'
    return None


@transaction.atomic
def gerar_chave_melhor_de_3(chave, atletas_list):
    """
    Gera chave Melhor de 3 para 2 atletas.
    O primeiro a vencer 2 lutas ganha.
    """
    if len(atletas_list) != 2:
        raise ValueError("Melhor de 3 requer exatamente 2 atletas")
    
    # Limpar lutas antigas
    chave.lutas.all().delete()
    
    atleta_a = atletas_list[0]
    atleta_b = atletas_list[1]
    
    # Criar 3 lutas (máximo necessário)
    lutas = []
    for i in range(3):
        luta = criar_luta(
            chave,
            atleta_a=atleta_a,
            atleta_b=atleta_b,
            round=1,
            tipo_luta='NORMAL'
        )
        lutas.append(luta)
    
    estrutura = {
        "tipo": "melhor_de_3",
        "atletas": 2,
        "lutas": [l.id for l in lutas],
        "vencedor": None,
        "vitorias_a": 0,
        "vitorias_b": 0
    }
    
    chave.estrutura = estrutura
    chave.tipo_chave = 'MELHOR_DE_3'
    chave.save()
    
    return chave


@transaction.atomic
def gerar_chave_casada_3(chave, atletas_list):
    """
    Gera chave casada para 3 atletas: A x B → Perdedor x C → Final.
    """
    if len(atletas_list) != 3:
        raise ValueError("Chave casada 3 requer exatamente 3 atletas")
    
    # Limpar lutas antigas
    chave.lutas.all().delete()
    
    atleta_a = atletas_list[0]
    atleta_b = atletas_list[1]
    atleta_c = atletas_list[2]
    
    # Luta 1: A vs B
    luta1 = criar_luta(
        chave,
        atleta_a=atleta_a,
        atleta_b=atleta_b,
        round=1,
        tipo_luta='NORMAL'
    )
    
    # Luta 2: Perdedor de Luta 1 vs C (será preenchida quando Luta 1 terminar)
    luta2 = criar_luta(
        chave,
        atleta_a=atleta_c,
        atleta_b=None,  # Será preenchido com perdedor de Luta 1
        round=2,
        tipo_luta='NORMAL',
        proxima_luta=None
    )
    
    # Luta 3: Final (Vencedor Luta 1 vs Vencedor Luta 2)
    luta3 = criar_luta(
        chave,
        atleta_a=None,  # Será preenchido com vencedor de Luta 1
        atleta_b=None,  # Será preenchido com vencedor de Luta 2
        round=3,
        tipo_luta='FINAL',
        proxima_luta=None
    )
    
    # Vincular próximas lutas
    luta1.proxima_luta = luta2
    luta1.save()
    luta2.proxima_luta = luta3
    luta2.save()
    
    estrutura = {
        "tipo": "casada_3",
        "atletas": 3,
        "lutas": [luta1.id, luta2.id, luta3.id],
        "vencedor": None
    }
    
    chave.estrutura = estrutura
    chave.tipo_chave = 'CASADA_3'
    chave.save()
    
    return chave


@transaction.atomic
def gerar_rodizio(chave, atletas_list):
    """
    Gera chave de rodízio para 3 a 5 atletas.
    Todos lutam contra todos. Vence quem tiver mais vitórias.
    """
    num_atletas = len(atletas_list)
    if num_atletas < 3 or num_atletas > 5:
        raise ValueError("Rodízio requer entre 3 e 5 atletas")
    
    # Limpar lutas antigas
    chave.lutas.all().delete()
    
    # Criar todas as combinações possíveis (todos contra todos)
    lutas = []
    for i in range(num_atletas):
        for j in range(i + 1, num_atletas):
            luta = criar_luta(
                chave,
                atleta_a=atletas_list[i],
                atleta_b=atletas_list[j],
                round=1,
                tipo_luta='NORMAL'
            )
            lutas.append(luta)
    
    estrutura = {
        "tipo": "rodizio",
        "atletas": num_atletas,
        "lutas": [l.id for l in lutas],
        "vencedor": None,
        "pontuacao": {}  # Será preenchido ao finalizar
    }
    
    chave.estrutura = estrutura
    chave.tipo_chave = 'RODIZIO'
    chave.save()
    
    return chave


@transaction.atomic
def gerar_chave_simples_tres_atletas(chave, atletas_list):
    """
    ✅ NOVO: Gera chave eliminatória simples para exatamente 3 atletas.
    Luta 1: Atleta 1 vs Atleta 2
    Luta 2 (Final): Atleta 3 (stand-by) vs Vencedor da Luta 1
    """
    if len(atletas_list) != 3:
        raise ValueError("Esta função requer exatamente 3 atletas")
    
    # Limpar lutas antigas
    chave.lutas.all().delete()
    
    # Atleta 3 é stand-by
    atleta_standby = atletas_list[2]
    
    # Criar luta 1: Atleta 1 vs Atleta 2
    luta1 = criar_luta(
        chave,
        atleta_a=atletas_list[0],
        atleta_b=atletas_list[1],
        round=1,
        tipo_luta='NORMAL',
        concluida=False
    )
    
    # Criar luta 2 (Final): Atleta 3 (stand-by) vs Vencedor da Luta 1 (será preenchido)
    luta2 = criar_luta(
        chave,
        atleta_a=atleta_standby,  # Stand-by já definido
        atleta_b=None,  # Será preenchido quando luta1 for concluída
        round=2,
        tipo_luta='FINAL',
        concluida=False
    )
    
    # Vincular luta 1 à luta 2
    luta1.proxima_luta = luta2
    luta1.save()
    
    # Estrutura JSON para compatibilidade
    estrutura = {
        "tipo": "simples_3",
        "atletas": 3,
        "luta1_id": luta1.id,
        "luta2_id": luta2.id,
        "standby_id": atleta_standby.id,
        "rounds": {
            "1": [luta1.id],
            "2": [luta2.id]
        }
    }
    
    chave.estrutura = estrutura
    chave.tipo_chave = 'SIMPLES_3'
    chave.save()
    
    return chave


@transaction.atomic
def gerar_eliminatoria_simples(chave, atletas_list):
    """
    Gera chave eliminatória simples (sem repescagem).
    """
    num_atletas = len(atletas_list)
    if num_atletas < 2:
        raise ValueError("Eliminatória simples requer pelo menos 2 atletas")
    
    # Limpar lutas antigas
    chave.lutas.all().delete()
    
    # Calcular tamanho da chave (potência de 2: 2, 4, 8, 16, 32)
    tamanho_chave = 2
    while tamanho_chave < num_atletas:
        tamanho_chave *= 2
    
    # Preencher com BYEs se necessário
    atletas_com_bye = list(atletas_list) + [None] * (tamanho_chave - num_atletas)
    
    estrutura = {
        "tipo": "eliminatoria_simples",
        "atletas": num_atletas,
        "tamanho_chave": tamanho_chave,
        "rounds": {}
    }
    
    # Criar lutas round por round
    lutas_anteriores = []
    round_num = 1
    num_lutas_round = tamanho_chave // 2
    
    while num_lutas_round >= 1:
        lutas_round = []
        
        for i in range(num_lutas_round):
            if round_num == 1:
                # Primeiro round: usar lista de atletas
                idx_a = i * 2
                idx_b = i * 2 + 1
                atleta_a = atletas_com_bye[idx_a] if idx_a < len(atletas_list) else None
                atleta_b = atletas_com_bye[idx_b] if idx_b < len(atletas_list) else None
            else:
                # Rounds seguintes: atletas serão preenchidos quando lutas anteriores terminarem
                atleta_a = None
                atleta_b = None
            
            tipo_luta = 'FINAL' if num_lutas_round == 1 else 'NORMAL'
            
            luta = criar_luta(
                chave,
                atleta_a=atleta_a,
                atleta_b=atleta_b,
                round=round_num,
                tipo_luta=tipo_luta
            )
            
            # Vincular com lutas anteriores
            if round_num > 1 and lutas_anteriores:
                # Cada luta deste round recebe vencedores de 2 lutas do round anterior
                idx_luta_anterior = i * 2
                if idx_luta_anterior < len(lutas_anteriores):
                    lutas_anteriores[idx_luta_anterior].proxima_luta = luta
                    lutas_anteriores[idx_luta_anterior].save()
                if idx_luta_anterior + 1 < len(lutas_anteriores):
                    lutas_anteriores[idx_luta_anterior + 1].proxima_luta = luta
                    lutas_anteriores[idx_luta_anterior + 1].save()
            
            lutas_round.append(luta)
        
        estrutura["rounds"][round_num] = [l.id for l in lutas_round]
        lutas_anteriores = lutas_round
        round_num += 1
        num_lutas_round //= 2
    
    chave.estrutura = estrutura
    chave.tipo_chave = 'ELIMINATORIA_SIMPLES'
    chave.save()
    
    return chave


@transaction.atomic
def gerar_eliminatoria_com_repescagem(chave, atletas_list):
    """
    Gera chave eliminatória com repescagem (modelo CBJ).
    Perdedores da semifinal disputam bronze.
    """
    num_atletas = len(atletas_list)
    if num_atletas < 4:
        raise ValueError("Eliminatória com repescagem requer pelo menos 4 atletas")
    
    # Limpar lutas antigas
    chave.lutas.all().delete()
    
    # Calcular tamanho da chave
    tamanho_chave = 2
    while tamanho_chave < num_atletas:
        tamanho_chave *= 2
    
    # Preencher com BYEs
    atletas_com_bye = list(atletas_list) + [None] * (tamanho_chave - num_atletas)
    
    estrutura = {
        "tipo": "eliminatoria_repescagem",
        "atletas": num_atletas,
        "tamanho_chave": tamanho_chave,
        "rounds": {},
        "repescagem": {}
    }
    
    # FASE PRINCIPAL (eliminatória)
    lutas_por_round = {}
    round_num = 1
    num_lutas_round = tamanho_chave // 2
    
    while num_lutas_round >= 1:
        lutas_round = []
        
        for i in range(num_lutas_round):
            if round_num == 1:
                idx_a = i * 2
                idx_b = i * 2 + 1
                atleta_a = atletas_com_bye[idx_a] if idx_a < len(atletas_list) else None
                atleta_b = atletas_com_bye[idx_b] if idx_b < len(atletas_list) else None
            else:
                atleta_a = None
                atleta_b = None
            
            tipo_luta = 'FINAL' if num_lutas_round == 1 else ('NORMAL' if num_lutas_round > 2 else 'NORMAL')
            
            luta = criar_luta(
                chave,
                atleta_a=atleta_a,
                atleta_b=atleta_b,
                round=round_num,
                tipo_luta=tipo_luta
            )
            
            # Vincular com lutas anteriores
            if round_num > 1 and i * 2 < len(lutas_por_round.get(round_num - 1, [])):
                lutas_ant = lutas_por_round[round_num - 1]
                if i * 2 < len(lutas_ant):
                    lutas_ant[i * 2].proxima_luta = luta
                    lutas_ant[i * 2].save()
                if i * 2 + 1 < len(lutas_ant):
                    lutas_ant[i * 2 + 1].proxima_luta = luta
                    lutas_ant[i * 2 + 1].save()
            
            lutas_round.append(luta)
        
        lutas_por_round[round_num] = lutas_round
        estrutura["rounds"][round_num] = [l.id for l in lutas_round]
        
        # Se chegou na semifinal (2 lutas), criar estrutura de repescagem
        if num_lutas_round == 2:
            # Criar luta de bronze (perdedores das semifinais)
            luta_bronze = criar_luta(
                chave,
                atleta_a=None,  # Perdedor da primeira semifinal
                atleta_b=None,  # Perdedor da segunda semifinal
                round=round_num + 1,
                tipo_luta='BRONZE'
            )
            
            # Vincular perdedores das semifinais para a luta de bronze
            for luta_semi in lutas_round:
                luta_semi.proxima_luta_repescagem = luta_bronze
                luta_semi.save()
            
            estrutura["repescagem"]["bronze"] = luta_bronze.id
        
        round_num += 1
        num_lutas_round //= 2
    
    chave.estrutura = estrutura
    chave.tipo_chave = 'ELIMINATORIA_REPESCAGEM'
    chave.save()
    
    return chave


@transaction.atomic
def gerar_chave_olimpica(chave, atletas_list):
    """
    Gera chave olímpica (IJF) - similar à eliminatória com repescagem,
    mas com estrutura específica da IJF.
    """
    # Similar à eliminatória com repescagem, mas com regras específicas IJF
    return gerar_eliminatoria_com_repescagem(chave, atletas_list)


@transaction.atomic
def gerar_chave_liga(chave, atletas_list):
    """
    Gera chave Liga: rodízio inicial + semifinais + final.
    """
    num_atletas = len(atletas_list)
    if num_atletas < 4:
        raise ValueError("Chave Liga requer pelo menos 4 atletas")
    
    # Limpar lutas antigas
    chave.lutas.all().delete()
    
    # FASE 1: Rodízio (dividir em grupos se necessário)
    # Simplificado: todos contra todos se <= 6, senão dividir em 2 grupos
    if num_atletas <= 6:
        # Rodízio simples
        lutas_rodizio = []
        for i in range(num_atletas):
            for j in range(i + 1, num_atletas):
                luta = Luta.objects.create(
                    chave=chave,
                    atleta_a=atletas_list[i],
                    atleta_b=atletas_list[j],
                    round=1,
                    tipo_luta='NORMAL'
                )
                lutas_rodizio.append(luta)
    else:
        # Dividir em 2 grupos (simplificado)
        meio = num_atletas // 2
        grupo_a = atletas_list[:meio]
        grupo_b = atletas_list[meio:]
        
        lutas_rodizio = []
        # Rodízio grupo A
        for i in range(len(grupo_a)):
            for j in range(i + 1, len(grupo_a)):
                luta = Luta.objects.create(
                    chave=chave,
                    atleta_a=grupo_a[i],
                    atleta_b=grupo_a[j],  # ✅ CORRIGIDO: grupo_a[i] vs grupo_a[j]
                    round=1,
                    tipo_luta='NORMAL'
                )
                lutas_rodizio.append(luta)
        
        # Rodízio grupo B
        for i in range(len(grupo_b)):
            for j in range(i + 1, len(grupo_b)):
                luta = Luta.objects.create(
                    chave=chave,
                    atleta_a=grupo_b[i],
                    atleta_b=grupo_b[j],
                    round=1,
                    tipo_luta='NORMAL'
                )
                lutas_rodizio.append(luta)
    
    # FASE 2: Semifinais (top 4 do rodízio - será preenchido após rodízio)
    semi1 = criar_luta(
        chave,
        atleta_a=None,
        atleta_b=None,
        round=2,
        tipo_luta='NORMAL'
    )
    
    semi2 = criar_luta(
        chave,
        atleta_a=None,
        atleta_b=None,
        round=2,
        tipo_luta='NORMAL'
    )
    
    # FASE 3: Final
    final = criar_luta(
        chave,
        atleta_a=None,
        atleta_b=None,
        round=3,
        tipo_luta='FINAL'
    )
    
    semi1.proxima_luta = final
    semi2.proxima_luta = final
    semi1.save()
    semi2.save()
    
    estrutura = {
        "tipo": "liga",
        "atletas": num_atletas,
        "rodizio": [l.id for l in lutas_rodizio],
        "semifinais": [semi1.id, semi2.id],
        "final": final.id,
        "vencedor": None
    }
    
    chave.estrutura = estrutura
    chave.tipo_chave = 'LIGA'
    chave.save()
    
    return chave


@transaction.atomic
def gerar_chave_por_grupos(chave, atletas_list):
    """
    Gera chave em grupos (pools).
    Divide atletas em grupos, faz rodízio em cada grupo, depois mata-mata.
    """
    num_atletas = len(atletas_list)
    if num_atletas < 4:
        raise ValueError("Chave por grupos requer pelo menos 4 atletas")
    
    # Limpar lutas antigas
    chave.lutas.all().delete()
    
    # Determinar número de grupos (idealmente 2 grupos de 3-4 atletas)
    if num_atletas <= 6:
        num_grupos = 2
    elif num_atletas <= 8:
        num_grupos = 2
    else:
        num_grupos = 3
    
    atletas_por_grupo = num_atletas // num_grupos
    resto = num_atletas % num_grupos
    
    grupos = []
    idx = 0
    for g in range(num_grupos):
        tamanho_grupo = atletas_por_grupo + (1 if g < resto else 0)
        grupos.append(atletas_list[idx:idx + tamanho_grupo])
        idx += tamanho_grupo
    
    estrutura = {
        "tipo": "grupos",
        "atletas": num_atletas,
        "num_grupos": num_grupos,
        "grupos": {},
        "fase_final": {}
    }
    
    # Criar rodízio em cada grupo
    lutas_grupos = []
    for grupo_idx, grupo in enumerate(grupos):
        lutas_grupo = []
        for i in range(len(grupo)):
            for j in range(i + 1, len(grupo)):
                luta = Luta.objects.create(
                    chave=chave,
                    atleta_a=grupo[i],
                    atleta_b=grupo[j],
                    round=1,
                    tipo_luta='NORMAL'
                )
                lutas_grupo.append(luta)
        
        estrutura["grupos"][grupo_idx + 1] = {
            "atletas": [a.id for a in grupo],
            "lutas": [l.id for l in lutas_grupo]
        }
        lutas_grupos.extend(lutas_grupo)
    
    # Fase final (mata-mata entre vencedores dos grupos)
    # Será criada após rodízio (simplificado: criar estrutura vazia)
    estrutura["fase_final"] = {
        "semifinais": [],
        "final": None
    }
    
    chave.estrutura = estrutura
    chave.tipo_chave = 'GRUPOS'
    chave.save()
    
    return chave

