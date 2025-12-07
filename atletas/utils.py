from datetime import date
from decimal import Decimal
from django.db.models import Q
from .models import Atleta, Categoria, Chave, Luta, Academia, Campeonato, AcademiaPontuacao, Inscricao
import random


def calcular_classe(ano_nasc):
    """Calcula a classe do atleta baseado no ano de nascimento
    
    Regras:
    - Festival: até 6 anos
    - SUB 9: 7-8 anos
    - SUB 11: 9-10 anos
    - SUB 13: 11-12 anos
    - SUB 15: 13-14 anos
    - SUB 18: 15-17 anos
    - SUB 21: 18-20 anos
    - VETERANOS: 30 anos ou mais (ex: nascido em 1987 ou antes, considerando 2024)
    - SÊNIOR: 21-29 anos
    """
    hoje = date.today()
    idade = hoje.year - ano_nasc
    
    if idade <= 6:
        return "Festival"
    elif idade <= 8:
        return "SUB 9"
    elif idade <= 10:
        return "SUB 11"
    elif idade <= 12:
        return "SUB 13"
    elif idade <= 14:
        return "SUB 15"
    elif idade <= 17:
        return "SUB 18"
    elif idade <= 20:
        return "SUB 21"
    elif idade >= 30:
        return "VETERANOS"
    else:
        return "SÊNIOR"


def categorias_permitidas(classe_atleta, categorias_existentes=None):
    """Retorna as classes de categorias que um atleta pode escolher baseado na sua classe
    
    Regras de elegibilidade:
    - VETERANOS: podem escolher VETERANOS ou SÊNIOR
    - SUB 18: podem escolher SUB 18, SUB 21 (se existir) ou SÊNIOR
    - Demais classes: apenas sua própria classe
    
    Args:
        classe_atleta: Classe do atleta (ex: "VETERANOS", "SUB 18", "SÊNIOR")
        categorias_existentes: Lista opcional de classes que existem no evento (filtra resultados)
    
    Returns:
        Lista de classes permitidas para inscrição
    """
    # Normalizar nome da classe
    classe_normalizada = classe_atleta.upper().strip()
    
    # Regras especiais
    if classe_normalizada == "VETERANOS":
        classes_permitidas = ["VETERANOS", "SÊNIOR"]
    elif classe_normalizada == "SUB 18" or classe_normalizada == "SUB18":
        classes_permitidas = ["SUB 18", "SUB 21", "SÊNIOR"]
    else:
        # Regra padrão: apenas sua própria classe
        classes_permitidas = [classe_atleta]
    
    # Filtrar apenas classes que existem no evento (se fornecido)
    if categorias_existentes is not None:
        # Converter para lista se necessário
        if isinstance(categorias_existentes, str):
            categorias_existentes = [categorias_existentes]
        
        # Normalizar lista de classes existentes
        classes_existentes_normalizadas = [c.upper().strip() for c in categorias_existentes]
        
        # Filtrar classes permitidas que existem no evento
        classes_permitidas_filtradas = []
        for classe in classes_permitidas:
            if classe.upper().strip() in classes_existentes_normalizadas:
                classes_permitidas_filtradas.append(classe)
        
        return classes_permitidas_filtradas
    
    return classes_permitidas


def validar_elegibilidade_categoria(classe_atleta, categoria_desejada, categorias_existentes=None):
    """Valida se um atleta pode se inscrever em uma categoria específica
    
    Args:
        classe_atleta: Classe do atleta (ex: "VETERANOS", "SUB 18")
        categoria_desejada: Classe da categoria desejada (ex: "SÊNIOR")
        categorias_existentes: Lista opcional de classes existentes no evento
    
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    classes_permitidas = categorias_permitidas(classe_atleta, categorias_existentes)
    
    # Normalizar categoria desejada
    categoria_desejada_normalizada = categoria_desejada.upper().strip()
    
    # Verificar se a categoria desejada está na lista permitida
    classes_permitidas_normalizadas = [c.upper().strip() for c in classes_permitidas]
    
    if categoria_desejada_normalizada in classes_permitidas_normalizadas:
        return True, None
    
    # Montar mensagem de erro
    classes_str = ", ".join(classes_permitidas)
    mensagem = f"A classe {classe_atleta} só pode se inscrever nas categorias: {classes_str}."
    
    return False, mensagem


def get_categorias_disponiveis(classe, sexo, classe_atleta=None):
    """Retorna as categorias disponíveis para uma classe e sexo, respeitando elegibilidade
    
    Args:
        classe: Classe da categoria (ex: "SÊNIOR", "VETERANOS")
        sexo: Sexo do atleta ("M" ou "F")
        classe_atleta: Classe do atleta (opcional, para validar elegibilidade)
    
    Returns:
        QuerySet de categorias filtradas
    """
    # Se classe_atleta for fornecida, validar elegibilidade
    if classe_atleta:
        classes_permitidas = categorias_permitidas(classe_atleta)
        # Normalizar nomes para comparação
        classes_permitidas_normalizadas = [c.upper().strip() for c in classes_permitidas]
        classe_normalizada = classe.upper().strip()
        
        # Se a classe não está nas permitidas, retornar queryset vazio
        if classe_normalizada not in classes_permitidas_normalizadas:
            return Categoria.objects.none()
    
    return Categoria.objects.filter(classe=classe, sexo=sexo).order_by('limite_min')


def get_categorias_elegiveis(classe_atleta, sexo):
    """Retorna todas as categorias elegíveis para um atleta baseado na sua classe
    
    Esta função retorna categorias de TODAS as classes que o atleta pode escolher
    baseado nas regras de elegibilidade.
    
    Args:
        classe_atleta: Classe do atleta (ex: "VETERANOS", "SUB 18")
        sexo: Sexo do atleta ("M" ou "F")
    
    Returns:
        QuerySet de categorias elegíveis
    """
    # Obter classes permitidas para esta classe de atleta
    classes_permitidas = categorias_permitidas(classe_atleta)
    
    # Buscar todas as categorias dessas classes para o sexo do atleta
    # Obter classes que realmente existem no banco
    classes_existentes = list(Categoria.objects.filter(
        sexo=sexo
    ).values_list('classe', flat=True).distinct())
    
    # Normalizar para comparação
    classes_permitidas_normalizadas = [c.upper().strip() for c in classes_permitidas]
    classes_existentes_normalizadas = [c.upper().strip() for c in classes_existentes]
    
    # Filtrar apenas classes permitidas que existem no banco
    classes_finais = []
    for classe_permitida in classes_permitidas:
        classe_permitida_normalizada = classe_permitida.upper().strip()
        if classe_permitida_normalizada in classes_existentes_normalizadas:
            # Encontrar a classe exata no banco (para manter capitalização correta)
            for classe_existente in classes_existentes:
                if classe_existente.upper().strip() == classe_permitida_normalizada:
                    classes_finais.append(classe_existente)
                    break
    
    # Retornar categorias dessas classes
    if not classes_finais:
        return Categoria.objects.none()
    
    return Categoria.objects.filter(classe__in=classes_finais, sexo=sexo).order_by('classe', 'limite_min')


def ajustar_categoria_por_peso(atleta, peso_oficial):
    """Ajusta a categoria do atleta baseado no peso oficial, respeitando elegibilidade
    
    IMPORTANTE: Ao ajustar categoria, só considera categorias elegíveis para a classe do atleta.
    """
    categoria_atual = Categoria.objects.filter(
        classe=atleta.classe,
        sexo=atleta.sexo,
        categoria_nome=atleta.categoria_nome
    ).first()
    
    if not categoria_atual:
        # Tentar buscar pela categoria_ajustada se existir
        if atleta.categoria_ajustada:
            categoria_atual = Categoria.objects.filter(
                categoria_nome=atleta.categoria_ajustada,
                sexo=atleta.sexo
            ).first()
        
        if not categoria_atual:
            return None, "Categoria não encontrada"
    
    # Obter classes elegíveis para o atleta
    classes_elegiveis = categorias_permitidas(atleta.classe)
    classes_elegiveis_normalizadas = [c.upper().strip() for c in classes_elegiveis]
    
    # Verifica se peso está dentro dos limites (limite_max pode ser 999.0 para categorias "acima de")
    limite_max_real = categoria_atual.limite_max if categoria_atual.limite_max < 999.0 else 999999.0
    
    if categoria_atual.limite_min <= peso_oficial <= limite_max_real:
        # Verificar se a categoria atual é elegível
        if categoria_atual.classe.upper().strip() not in classes_elegiveis_normalizadas:
            # Categoria atual não é elegível, precisa ajustar
            atleta.motivo_ajuste = f"Categoria atual ({categoria_atual.classe}) não é elegível para atleta de classe {atleta.classe}"
            # Buscar categoria elegível que contenha o peso
            categorias_elegiveis = get_categorias_elegiveis(atleta.classe, atleta.sexo)
            categoria_correta = categorias_elegiveis.filter(
                limite_min__lte=peso_oficial
            )
            categorias_normais = categoria_correta.filter(limite_max__lt=999.0)
            categoria_que_contem = categorias_normais.filter(limite_max__gte=peso_oficial).order_by('limite_min').first()
            if categoria_que_contem:
                return categoria_que_contem, "Categoria ajustada para elegível"
            # Tentar categoria "acima de"
            categoria_acima = categoria_correta.filter(limite_max__gte=999.0).order_by('-limite_min').first()
            if categoria_acima and peso_oficial >= categoria_acima.limite_min:
                return categoria_acima, "Categoria ajustada para elegível"
            return None, "Não há categoria elegível que contenha este peso"
        # Peso OK, manter categoria
        return categoria_atual, "OK"
    
    # Peso acima do limite máximo - usar apenas categorias elegíveis
    limite_max_real = categoria_atual.limite_max if categoria_atual.limite_max < 999.0 else 999999.0
    
    if peso_oficial > limite_max_real:
        # Buscar próxima categoria superior apenas entre categorias elegíveis
        categorias_elegiveis = get_categorias_elegiveis(atleta.classe, atleta.sexo)
        
        categoria_superior = categorias_elegiveis.filter(
            limite_min__gt=limite_max_real
        ).exclude(limite_max__gte=999.0).order_by('limite_min').first()
        
        if not categoria_superior:
            # Tentar categoria "acima de" se existir (apenas se elegível)
            categoria_superior = categorias_elegiveis.filter(
                limite_min__lte=peso_oficial,
                limite_max__gte=999.0
            ).order_by('-limite_min').first()
        
        if categoria_superior:
            # Verificar se é elegível
            if categoria_superior.classe.upper().strip() in classes_elegiveis_normalizadas:
                # Existe categoria superior elegível, ajustar
                atleta.categoria_ajustada = categoria_superior.categoria_nome
                atleta.motivo_ajuste = f"Peso {peso_oficial}kg acima do limite máximo ({limite_max_real}kg)"
                return categoria_superior, "Ajustado para categoria superior"
        
        # Não existe categoria superior elegível, eliminar
        atleta.status = "Eliminado Peso"
        atleta.motivo_ajuste = f"Peso {peso_oficial}kg acima da última categoria elegível disponível"
        return None, "Eliminado - Peso acima da última categoria elegível"
    
    # Peso abaixo do limite mínimo - buscar categoria correta que contenha o peso
    if peso_oficial < categoria_atual.limite_min:
        # Buscar categoria que contenha o peso do atleta
        limite_max_real = categoria_atual.limite_max if categoria_atual.limite_max < 999.0 else 999999.0
        
        # Primeiro tentar encontrar categoria que contenha o peso exato
        categoria_correta = Categoria.objects.filter(
            classe=atleta.classe,
            sexo=atleta.sexo,
            limite_min__lte=peso_oficial
        ).exclude(
            categoria_nome=categoria_atual.categoria_nome  # Excluir a categoria atual
        )
        
        # Filtrar categorias normais (com limite_max < 999.0)
        categorias_normais = categoria_correta.filter(limite_max__lt=999.0)
        
        if categorias_normais.exists():
            # Buscar categoria que contenha o peso (limite_min <= peso <= limite_max)
            categoria_que_contem = categorias_normais.filter(limite_max__gte=peso_oficial).order_by('limite_min').first()
            if categoria_que_contem:
                atleta.motivo_ajuste = f"Peso {peso_oficial}kg abaixo do limite mínimo da categoria atual ({categoria_atual.limite_min}kg). Categoria correta: {categoria_que_contem.categoria_nome}"
                return categoria_que_contem, "Pode rebaixar para categoria inferior"
            
            # Se não encontrou categoria que contenha, buscar a categoria com limite_max mais próximo e menor que o peso
            categoria_inferior = categorias_normais.filter(limite_max__lt=peso_oficial).order_by('-limite_max').first()
            if categoria_inferior:
                atleta.motivo_ajuste = f"Peso {peso_oficial}kg abaixo do limite mínimo ({categoria_atual.limite_min}kg) - Pode rebaixar"
                return categoria_inferior, "Pode rebaixar para categoria inferior"
        
        # Verificar categoria "acima de" (Super Pesado)
        categoria_acima = categoria_correta.filter(limite_max__gte=999.0).order_by('-limite_min').first()
        if categoria_acima and categoria_acima.limite_min <= peso_oficial:
            atleta.motivo_ajuste = f"Peso {peso_oficial}kg abaixo do limite mínimo ({categoria_atual.limite_min}kg). Categoria correta: {categoria_acima.categoria_nome}"
            return categoria_acima, "Pode rebaixar para categoria inferior"
        
        # Não encontrou categoria apropriada
        atleta.status = "Eliminado Peso"
        atleta.motivo_ajuste = f"Peso {peso_oficial}kg abaixo da primeira categoria disponível"
        return None, "Eliminado - Peso abaixo da primeira categoria"
    
    return categoria_atual, "OK"


def gerar_chave(categoria_nome, classe, sexo, modelo_chave=None, campeonato=None):
    """Gera a chave para uma categoria usando inscrições do campeonato
    
    Args:
        categoria_nome: Nome da categoria
        classe: Classe da categoria
        sexo: Sexo ('M' ou 'F')
        modelo_chave: Modelo de chave escolhido manualmente (None = automático)
            Valores possíveis: 'vazia', 'campeao_automatico', 'melhor_de_3', 'triangular',
            'olimpica_4', 'olimpica_8', 'olimpica_16', 'olimpica_32'
        campeonato: Campeonato ativo (obrigatório)
    
    Returns:
        Chave criada ou atualizada
    """
    import logging
    logger = logging.getLogger(__name__)
    
    from .models import Inscricao
    
    print(f"\n{'='*80}")
    print(f"🔍 AUDITORIA: Iniciando geração de chave")
    print(f"{'='*80}")
    print(f"📋 Parâmetros recebidos:")
    print(f"   - Categoria: {categoria_nome}")
    print(f"   - Classe: {classe}")
    print(f"   - Sexo: {sexo}")
    print(f"   - Modelo: {modelo_chave}")
    print(f"   - Campeonato: {campeonato}")
    
    if not campeonato:
        print(f"❌ ERRO: Campeonato não fornecido")
        raise ValueError("Campeonato é obrigatório para gerar chaves")
    
    # Buscar inscrições aprovadas/remanejadas do campeonato COM PESO REAL CONFIRMADO e categoria/classe reais
    print(f"\n🔍 Buscando inscrições...")
    from django.db.models import Q

    base_qs = Inscricao.objects.filter(
        campeonato=campeonato,
        classe_real__nome=classe,
        atleta__sexo=sexo
    ).exclude(classe_real__nome__iexact='Festival').select_related(
        'atleta', 'atleta__academia', 'classe_real', 'categoria_real'
    )

    total_inscritos = base_qs.count()
    bloqueados = base_qs.filter(bloqueado_chave=True).count()
    sem_categoria = base_qs.filter(categoria_real__isnull=True).count()
    sem_peso = base_qs.filter(Q(peso_real__isnull=True) | Q(peso_real=0)).count()

    inscricoes = base_qs.filter(
        status_inscricao__in=['aprovado', 'remanejado'],
        bloqueado_chave=False,
        categoria_real__isnull=False,
        peso_real__gt=Decimal('0.0')
    )
    
    inscricoes_count = inscricoes.count()
    print(f"   📊 Totais para {classe}/{sexo}/{categoria_nome}:")
    print(f"      - Inscritos (classe/sexo): {total_inscritos}")
    print(f"      - Bloqueados: {bloqueados}")
    print(f"      - Sem categoria_real: {sem_categoria}")
    print(f"      - Sem peso_real: {sem_peso}")
    print(f"      - Aptos (status_inscricao aprovado/remanejado, desbloqueados, peso_real>0, categoria_real ok): {inscricoes_count}")
    
    if inscricoes_count == 0:
        print(f"   ⚠️  Nenhuma inscrição encontrada com os critérios:")
        print(f"      - Campeonato: {campeonato.id} ({campeonato.nome})")
        print(f"      - Classe: {classe}")
        print(f"      - Sexo: {sexo}")
        print(f"      - Categoria: {categoria_nome}")
        print(f"      - Status: aprovado")
        print(f"      - Peso: não nulo e != 0")
    
    # Extrair lista de atletas das inscrições
    atletas_list = [inscricao.atleta for inscricao in inscricoes]
    num_atletas = len(atletas_list)
    print(f"   ✅ {num_atletas} atletas extraídos")
    
    if num_atletas > 0:
        print(f"   📝 Atletas:")
        for idx, atleta in enumerate(atletas_list, 1):
            print(f"      {idx}. {atleta.nome} (ID: {atleta.id}, Academia: {atleta.academia.nome})")
    else:
        aviso = (
            f"Nenhuma inscrição elegível para gerar chave "
            f"({classe} / {sexo} / {categoria_nome}) no campeonato {campeonato.id}."
        )
        print(f"   ⚠️  {aviso}")
        # Não gerar/atualizar chave vazia
        raise ValueError(aviso)
    
    # Criar ou atualizar chave vinculada ao campeonato
    print(f"\n🔍 Criando/atualizando chave no banco...")
    chave, created = Chave.objects.get_or_create(
        campeonato=campeonato,
        classe=classe,
        sexo=sexo,
        categoria=categoria_nome,
        defaults={'estrutura': {}}
    )
    
    print(f"   {'✅ Chave criada' if created else '🔄 Chave existente encontrada'} (ID: {chave.id})")
    
    # Garantir que o campeonato está definido (caso a chave já existisse)
    if not chave.campeonato:
        chave.campeonato = campeonato
        chave.save()
        print(f"   ✅ Campeonato vinculado à chave")
    
    # Limpar lutas antigas e atletas
    print(f"\n🧹 Limpando dados antigos...")
    lutas_antigas_count = chave.lutas.count()
    atletas_antigos_count = chave.atletas.count()
    print(f"   - Lutas antigas: {lutas_antigas_count}")
    print(f"   - Atletas antigos: {atletas_antigos_count}")
    
    chave.lutas.all().delete()
    chave.atletas.clear()
    print(f"   ✅ Dados antigos removidos")
    
    # Vincular novos atletas
    if atletas_list:
        chave.atletas.set(atletas_list)
        print(f"   ✅ {len(atletas_list)} atletas vinculados à chave")
    else:
        print(f"   ⚠️  Nenhum atleta para vincular")
    
    # Se modelo escolhido manualmente, usar ele
    if modelo_chave and modelo_chave != 'automatico':
        print(f"\n🎯 Gerando chave com modelo manual: {modelo_chave}")
        estrutura = gerar_chave_escolhida(chave, atletas_list, modelo_chave)
    else:
        # Comportamento automático baseado no número de atletas
        print(f"\n🎯 Gerando chave automática para {num_atletas} atleta(s)")
        estrutura = gerar_chave_automatica(chave, atletas_list)
    
    print(f"   ✅ Estrutura gerada: tipo={estrutura.get('tipo')}, atletas={estrutura.get('atletas', 0)}")
    
    # Verificar se lutas foram criadas
    lutas_criadas_count = chave.lutas.count()
    print(f"   ✅ Lutas criadas no banco: {lutas_criadas_count}")
    
    if lutas_criadas_count == 0 and num_atletas > 0:
        print(f"   ⚠️  ATENÇÃO: Nenhuma luta foi criada, mas há {num_atletas} atleta(s)!")
        print(f"   ⚠️  Tipo de estrutura: {estrutura.get('tipo')}")
        if 'lutas' in estrutura:
            print(f"   ⚠️  IDs de lutas na estrutura: {estrutura.get('lutas', [])}")
    
    chave.estrutura = estrutura
    chave.save()
    print(f"   ✅ Chave salva no banco")
    
    print(f"\n{'='*80}")
    print(f"✅ Geração de chave concluída (ID: {chave.id})")
    print(f"{'='*80}\n")
    
    return chave


def agrupar_atletas_por_academia(atletas_list):
    """Agrupa atletas por academia e retorna lista embaralhada evitando mesma academia na primeira rodada
    
    Returns:
        Lista de atletas organizada para que atletas da mesma academia não se enfrentem na 1ª rodada
    """
    # Agrupar por academia
    por_academia = {}
    for atleta in atletas_list:
        academia_id = atleta.academia.id
        if academia_id not in por_academia:
            por_academia[academia_id] = []
        por_academia[academia_id].append(atleta)
    
    # Se todas as academias têm apenas 1 atleta, retornar embaralhado
    if all(len(atletas) == 1 for atletas in por_academia.values()):
        resultado = list(atletas_list)
        random.shuffle(resultado)
        return resultado
    
    # Distribuir atletas de forma que academias diferentes fiquem em lados opostos da chave
    academias_list = list(por_academia.keys())
    random.shuffle(academias_list)
    
    # Dividir em duas metades
    metade = len(atletas_list) // 2
    primeira_metade = []
    segunda_metade = []
    
    for academia_id in academias_list:
        atletas_academia = por_academia[academia_id].copy()
        random.shuffle(atletas_academia)
        
        # Distribuir alternadamente
        while atletas_academia:
            if len(primeira_metade) < metade:
                primeira_metade.append(atletas_academia.pop(0))
            elif len(segunda_metade) < metade:
                segunda_metade.append(atletas_academia.pop(0))
            else:
                if len(primeira_metade) <= len(segunda_metade):
                    primeira_metade.append(atletas_academia.pop(0))
                else:
                    segunda_metade.append(atletas_academia.pop(0))
    
    # Intercalar para evitar confrontos na primeira rodada
    resultado = []
    max_len = max(len(primeira_metade), len(segunda_metade))
    for i in range(max_len):
        if i < len(primeira_metade):
            resultado.append(primeira_metade[i])
        if i < len(segunda_metade):
            resultado.append(segunda_metade[i])
    
    return resultado


def gerar_melhor_de_3(chave, atletas_list):
    """Gera chave tipo Melhor de 3"""
    print(f"   🔧 gerar_melhor_de_3: {len(atletas_list)} atleta(s)")
    
    if len(atletas_list) < 2:
        print(f"   ❌ ERRO: Melhor de 3 requer pelo menos 2 atletas")
        return {"tipo": "vazia", "atletas": len(atletas_list)}
    
    estrutura = {
        "tipo": "melhor_de_3",
        "atletas": len(atletas_list),
        "lutas": [],
        "lutas_detalhes": {}
    }
    
    # Criar 3 lutas
    print(f"   🔧 Criando 3 lutas entre {atletas_list[0].nome} e {atletas_list[1].nome}")
    for i in range(3):
        try:
            luta = Luta.objects.create(
                chave=chave,
                atleta_a=atletas_list[0],
                atleta_b=atletas_list[1],
                round=1,
                proxima_luta=None
            )
            estrutura["lutas"].append(luta.id)
            print(f"      ✅ Luta {i+1} criada (ID: {luta.id})")
        except Exception as e:
            print(f"      ❌ ERRO ao criar luta {i+1}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"   ✅ Melhor de 3 gerado: {len(estrutura['lutas'])} lutas criadas")
    return estrutura


def gerar_round_robin(chave, atletas_list):
    """Gera chave tipo Round Robin (todos contra todos - Rodízio)"""
    num_atletas = len(atletas_list)
    print(f"   🔧 gerar_round_robin: {num_atletas} atleta(s)")
    
    estrutura = {
        "tipo": "round_robin",
        "atletas": num_atletas,
        "lutas": [],
        "rounds": {1: []}
    }
    
    # Gerar todas as combinações possíveis (todos contra todos)
    lutas_ids = []
    total_combinacoes = (num_atletas * (num_atletas - 1)) // 2
    print(f"   🔧 Criando {total_combinacoes} combinações de lutas")
    
    for i in range(num_atletas):
        for j in range(i + 1, num_atletas):
            try:
                luta = Luta.objects.create(
                    chave=chave,
                    atleta_a=atletas_list[i],
                    atleta_b=atletas_list[j],
                    round=1,
                    proxima_luta=None
                )
                lutas_ids.append(luta.id)
                print(f"      ✅ Luta criada: {atletas_list[i].nome} vs {atletas_list[j].nome} (ID: {luta.id})")
            except Exception as e:
                print(f"      ❌ ERRO ao criar luta {atletas_list[i].nome} vs {atletas_list[j].nome}: {str(e)}")
                import traceback
                traceback.print_exc()
    
    estrutura["lutas"] = lutas_ids
    estrutura["rounds"][1] = lutas_ids
    
    print(f"   ✅ Round Robin gerado: {len(lutas_ids)} lutas criadas")
    return estrutura


def gerar_eliminatoria_repescagem(chave, atletas_list, tamanho_chave=8):
    """Gera chave eliminatória com repescagem (modelo CBJ correto)
    
    SISTEMA DE REPESCAGEM CORRETO:
    1. Chave Principal: Vencedores seguem normalmente
    2. Chave de Repescagem: Perdedores vão para chave separada
    3. Luta de 3º lugar: Vencedor da repescagem vs Perdedor da semifinal principal
    
    Estrutura:
    - Round 1: Todas as lutas iniciais
    - Chave Principal: Vencedores do Round 1 seguem (rounds 2, 3, etc.)
    - Chave Repescagem: Perdedores do Round 1 vão para repescagem (rounds 100+, 200+, etc.)
    - Luta 3º lugar: Round 999 (vencedor repescagem vs perdedor semifinal)
    
    Atletas da mesma academia não se enfrentam na primeira rodada.
    """
    num_atletas = len(atletas_list)
    print(f"   🔧 gerar_eliminatoria_repescagem: {num_atletas} atleta(s), tamanho_chave={tamanho_chave}")
    
    # Organizar atletas para evitar mesma academia na 1ª rodada
    atletas_organizados = agrupar_atletas_por_academia(atletas_list)
    print(f"   🔧 Atletas organizados: {len(atletas_organizados)}")
    
    # Preencher com BYEs se necessário
    atletas_com_bye = atletas_organizados + [None] * (tamanho_chave - num_atletas)
    print(f"   🔧 Atletas com BYEs: {len(atletas_com_bye)} (BYEs: {tamanho_chave - num_atletas})")
    
    estrutura = {
        "tipo": "eliminatoria_repescagem",
        "atletas": num_atletas,
        "tamanho_chave": tamanho_chave,
        "rounds": {},  # Rounds da chave principal (1, 2, 3...)
        "repescagem": {
            "rounds": {},  # Rounds da repescagem (100, 101, 102...)
            "luta_3_lugar": None  # ID da luta de 3º lugar (round 999)
        }
    }
    
    # ========== ROUND 1: TODAS AS LUTAS INICIAIS ==========
    round_num = 1
    lutas_round1 = []
    num_lutas_round1 = tamanho_chave // 2
    print(f"   🔧 Criando {num_lutas_round1} lutas do Round {round_num} (inicial)")
    
    for i in range(0, tamanho_chave, 2):
        atleta_a = atletas_com_bye[i] if i < len(atletas_organizados) else None
        atleta_b = atletas_com_bye[i + 1] if i + 1 < len(atletas_organizados) else None
        
        try:
            # Criar luta mesmo que um dos atletas seja None (BYE)
            luta = Luta.objects.create(
                chave=chave,
                atleta_a=atleta_a,
                atleta_b=atleta_b,
                round=round_num,
                proxima_luta=None
            )
            lutas_round1.append(luta.id)
            nome_a = atleta_a.nome if atleta_a else "BYE"
            nome_b = atleta_b.nome if atleta_b else "BYE"
            print(f"      ✅ Luta Round {round_num} criada: {nome_a} vs {nome_b} (ID: {luta.id})")
        except Exception as e:
            print(f"      ❌ ERRO ao criar luta Round {round_num}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    estrutura["rounds"][round_num] = lutas_round1
    print(f"   ✅ Round {round_num} criado: {len(lutas_round1)} lutas")
    
    # ========== CHAVE PRINCIPAL: VENCEDORES SEGUEM ==========
    lutas_anteriores = lutas_round1
    round_num_principal = 2
    
    while len(lutas_anteriores) > 1:
        num_lutas = len(lutas_anteriores) // 2
        lutas_novo_round = []
        print(f"   🔧 Criando Round {round_num_principal} (Principal): {num_lutas} lutas")
        
        for i in range(num_lutas):
            try:
                luta = Luta.objects.create(
                    chave=chave,
                    atleta_a=None,  # Será preenchido quando vencedor do round anterior for definido
                    atleta_b=None,
                    round=round_num_principal,
                    proxima_luta=None
                )
                lutas_novo_round.append(luta.id)
                print(f"      ✅ Luta Round {round_num_principal} criada (ID: {luta.id})")
            except Exception as e:
                print(f"      ❌ ERRO ao criar luta Round {round_num_principal}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Vincular lutas da chave principal
        for idx, luta_ant_id in enumerate(lutas_anteriores):
            try:
                luta_ant = Luta.objects.get(id=luta_ant_id)
                proxima_luta_idx = idx // 2
                if proxima_luta_idx < len(lutas_novo_round):
                    luta_ant.proxima_luta = lutas_novo_round[proxima_luta_idx]
                    luta_ant.save()
            except Luta.DoesNotExist:
                print(f"      ⚠️  Luta anterior {luta_ant_id} não encontrada para vincular")
        
        estrutura["rounds"][round_num_principal] = lutas_novo_round
        print(f"   ✅ Round {round_num_principal} (Principal) criado: {len(lutas_novo_round)} lutas")
        lutas_anteriores = lutas_novo_round
        round_num_principal += 1
    
    # ========== CHAVE DE REPESCAGEM: PERDEDORES DO ROUND 1 ==========
    # A repescagem será criada dinamicamente quando as lutas do Round 1 forem finalizadas
    # Mas precisamos criar a estrutura básica agora
    
    # Identificar quantos perdedores teremos (número de lutas do Round 1)
    num_perdedores_round1 = len([l for l in lutas_round1 if True])  # Todos os perdedores do Round 1
    
    # Criar estrutura de repescagem (será preenchida quando as lutas forem finalizadas)
    # Round 100 = primeira rodada da repescagem (perdedores do Round 1)
    # Round 101 = segunda rodada da repescagem
    # etc.
    
    repescagem_round = 100
    num_lutas_repescagem = num_lutas_round1 // 2  # Metade dos perdedores vão para próxima rodada
    
    if num_lutas_repescagem > 0:
        print(f"   🔧 Criando estrutura de repescagem (Round {repescagem_round})")
        lutas_repescagem_round1 = []
        
        for i in range(num_lutas_repescagem):
            try:
                luta = Luta.objects.create(
                    chave=chave,
                    atleta_a=None,  # Será preenchido com perdedor do Round 1
                    atleta_b=None,  # Será preenchido com perdedor do Round 1
                    round=repescagem_round,
                    proxima_luta=None
                )
                lutas_repescagem_round1.append(luta.id)
                print(f"      ✅ Luta Repescagem Round {repescagem_round} criada (ID: {luta.id})")
            except Exception as e:
                print(f"      ❌ ERRO ao criar luta de repescagem: {str(e)}")
                import traceback
                traceback.print_exc()
        
        estrutura["repescagem"]["rounds"][repescagem_round] = lutas_repescagem_round1
        
        # Criar rounds seguintes da repescagem se necessário
        lutas_rep_anteriores = lutas_repescagem_round1
        repescagem_round += 1
        
        while len(lutas_rep_anteriores) > 1:
            num_lutas_rep = len(lutas_rep_anteriores) // 2
            lutas_rep_novo_round = []
            
            for i in range(num_lutas_rep):
                try:
                    luta = Luta.objects.create(
                        chave=chave,
                        atleta_a=None,
                        atleta_b=None,
                        round=repescagem_round,
                        proxima_luta=None
                    )
                    lutas_rep_novo_round.append(luta.id)
                except Exception as e:
                    print(f"      ❌ ERRO ao criar luta de repescagem Round {repescagem_round}: {str(e)}")
            
            # Vincular lutas da repescagem
            for idx, luta_ant_id in enumerate(lutas_rep_anteriores):
                try:
                    luta_ant = Luta.objects.get(id=luta_ant_id)
                    proxima_luta_idx = idx // 2
                    if proxima_luta_idx < len(lutas_rep_novo_round):
                        luta_ant.proxima_luta = lutas_rep_novo_round[proxima_luta_idx]
                        luta_ant.save()
                except Luta.DoesNotExist:
                    pass
            
            estrutura["repescagem"]["rounds"][repescagem_round] = lutas_rep_novo_round
            lutas_rep_anteriores = lutas_rep_novo_round
            repescagem_round += 1
    
    # ========== LUTA DE 3º LUGAR ==========
    # Vencedor da repescagem vs Perdedor da semifinal da chave principal
    print(f"   🔧 Criando luta de 3º lugar (Round 999)")
    try:
        luta_3_lugar = Luta.objects.create(
            chave=chave,
            atleta_a=None,  # Será preenchido com vencedor da repescagem
            atleta_b=None,  # Será preenchido com perdedor da semifinal principal
            round=999,  # Round especial para 3º lugar
            proxima_luta=None
        )
        estrutura["repescagem"]["luta_3_lugar"] = luta_3_lugar.id
        estrutura["rounds"][999] = [luta_3_lugar.id]  # Incluir no rounds para facilitar busca
        print(f"      ✅ Luta de 3º lugar criada (ID: {luta_3_lugar.id})")
    except Exception as e:
        print(f"      ❌ ERRO ao criar luta de 3º lugar: {str(e)}")
        import traceback
        traceback.print_exc()
    
    total_lutas = sum(len(lutas) for lutas in estrutura["rounds"].values())
    total_lutas_rep = sum(len(lutas) for lutas in estrutura["repescagem"]["rounds"].values())
    print(f"   ✅ Eliminatória com repescagem gerada:")
    print(f"      - Chave Principal: {total_lutas - 1} lutas (sem contar 3º lugar)")
    print(f"      - Chave Repescagem: {total_lutas_rep} lutas")
    print(f"      - Luta 3º lugar: 1 luta")
    print(f"      - Total: {total_lutas + total_lutas_rep} lutas")
    
    return estrutura


def gerar_eliminatoria_simples(chave, atletas_list, tamanho_chave=8):
    """Gera chave eliminatória simples (sem repescagem)
    
    Atletas da mesma academia não se enfrentam na primeira rodada.
    """
    num_atletas = len(atletas_list)
    
    # Organizar atletas para evitar mesma academia na 1ª rodada
    atletas_organizados = agrupar_atletas_por_academia(atletas_list)
    
    # Preencher com BYEs se necessário
    atletas_com_bye = atletas_organizados + [None] * (tamanho_chave - num_atletas)
    
    estrutura = {
        "tipo": "eliminatoria_simples",
        "atletas": num_atletas,
        "tamanho_chave": tamanho_chave,
        "rounds": {}
    }
    
    # Criar lutas do primeiro round
    round_num = 1
    lutas_round = []
    
    for i in range(0, tamanho_chave, 2):
        atleta_a = atletas_com_bye[i] if i < len(atletas_organizados) else None
        atleta_b = atletas_com_bye[i + 1] if i + 1 < len(atletas_organizados) else None
        
        luta = Luta.objects.create(
            chave=chave,
            atleta_a=atleta_a,
            atleta_b=atleta_b,
            round=round_num,
            proxima_luta=None
        )
        lutas_round.append(luta.id)
    
    estrutura["rounds"][round_num] = lutas_round
    
    # Criar lutas dos rounds seguintes e vincular
    lutas_anteriores = lutas_round
    while len(lutas_anteriores) > 1:
        round_num += 1
        num_lutas = len(lutas_anteriores) // 2
        lutas_novo_round = []
        
        for i in range(num_lutas):
            luta = Luta.objects.create(
                chave=chave,
                atleta_a=None,
                atleta_b=None,
                round=round_num,
                proxima_luta=None
            )
            lutas_novo_round.append(luta.id)
        
        # Vincular lutas
        for idx, luta_ant_id in enumerate(lutas_anteriores):
            try:
                luta_ant = Luta.objects.get(id=luta_ant_id)
                proxima_luta_idx = idx // 2
                if proxima_luta_idx < len(lutas_novo_round):
                    luta_ant.proxima_luta = lutas_novo_round[proxima_luta_idx]
                    luta_ant.save()
            except Luta.DoesNotExist:
                pass
        
        estrutura["rounds"][round_num] = lutas_novo_round
        lutas_anteriores = lutas_novo_round
    
    return estrutura


def gerar_chave_automatica(chave, atletas_list):
    """Gera chave automaticamente baseado no número de atletas (NOVA LÓGICA AUTOMÁTICA)
    
    Nova lógica:
    - 1 atleta → WO / Campeão direto
    - 2 atletas → Melhor de 3
    - 3-5 atletas → Rodízio (Round Robin)
    - 6-7 atletas → Eliminatória com Repescagem (CBJ) usando layout de 8 posições com stand-by
    - 8 atletas → Eliminatória com Repescagem (CBJ completa)
    """
    num_atletas = len(atletas_list)
    estrutura = {}
    
    if num_atletas == 0:
        estrutura = {"tipo": "vazia", "atletas": 0}
    elif num_atletas == 1:
        # 1 atleta = campeão automático (WO)
        estrutura = {
            "tipo": "campeao_automatico",
            "atletas": 1,
            "vencedor": atletas_list[0].id
        }
    elif num_atletas == 2:
        # 2 atletas = melhor de 3
        estrutura = gerar_melhor_de_3(chave, atletas_list)
    elif 3 <= num_atletas <= 5:
        # 3-5 atletas = Round Robin (Rodízio)
        estrutura = gerar_round_robin(chave, atletas_list)
    elif 6 <= num_atletas <= 7:
        # 6-7 atletas = Eliminatória com Repescagem (CBJ) - layout 8 posições
        estrutura = gerar_eliminatoria_repescagem(chave, atletas_list, tamanho_chave=8)
    elif num_atletas == 8:
        # 8 atletas = Eliminatória com Repescagem (CBJ completa)
        estrutura = gerar_eliminatoria_repescagem(chave, atletas_list, tamanho_chave=8)
    else:
        # 9+ atletas = Chave olímpica com repescagem
        if num_atletas <= 16:
            estrutura = gerar_eliminatoria_repescagem(chave, atletas_list, tamanho_chave=16)
        else:
            estrutura = gerar_eliminatoria_repescagem(chave, atletas_list, tamanho_chave=32)
    
    return estrutura


def gerar_chave_escolhida(chave, atletas_list, modelo_chave):
    """Gera chave conforme modelo escolhido manualmente pelo oficial"""
    num_atletas = len(atletas_list)
    
    if modelo_chave == 'vazia':
        return {"tipo": "vazia", "atletas": num_atletas}
    
    elif modelo_chave == 'campeao_automatico':
        if num_atletas == 0:
            return {"tipo": "vazia", "atletas": 0}
        elif num_atletas == 1:
            return {
                "tipo": "campeao_automatico",
                "atletas": 1,
                "vencedor": atletas_list[0].id
            }
        else:
            # Mais de 1 atleta, pegar o primeiro como campeão
            return {
                "tipo": "campeao_automatico",
                "atletas": num_atletas,
                "vencedor": atletas_list[0].id
            }
    
    elif modelo_chave == 'melhor_de_3':
        if num_atletas == 0:
            return {"tipo": "vazia", "atletas": 0}
        elif num_atletas == 1:
            # Apenas 1 atleta, criar campeão automático
            return {
                "tipo": "campeao_automatico",
                "atletas": 1,
                "vencedor": atletas_list[0].id
            }
        else:
            # Pegar os 2 primeiros atletas
            atletas_para_luta = atletas_list[:2]
            estrutura = {
                "tipo": "melhor_de_3",
                "atletas": len(atletas_para_luta),
                "lutas": [],
                "lutas_detalhes": {}
            }
            # Criar 3 lutas
            for i in range(3):
                luta = Luta.objects.create(
                    chave=chave,
                    atleta_a=atletas_para_luta[0],
                    atleta_b=atletas_para_luta[1],
                    round=1,
                    proxima_luta=None
                )
                estrutura["lutas"].append(luta.id)
            return estrutura
    
    elif modelo_chave == 'triangular':
        if num_atletas == 0:
            return {"tipo": "vazia", "atletas": 0}
        elif num_atletas == 1:
            return {
                "tipo": "campeao_automatico",
                "atletas": 1,
                "vencedor": atletas_list[0].id
            }
        elif num_atletas == 2:
            # Apenas 2 atletas, criar melhor de 3
            estrutura = {
                "tipo": "melhor_de_3",
                "atletas": 2,
                "lutas": [],
                "lutas_detalhes": {}
            }
            for i in range(3):
                luta = Luta.objects.create(
                    chave=chave,
                    atleta_a=atletas_list[0],
                    atleta_b=atletas_list[1],
                    round=1,
                    proxima_luta=None
                )
                estrutura["lutas"].append(luta.id)
            return estrutura
        else:
            # Pegar os 3 primeiros atletas
            atletas_para_luta = atletas_list[:3]
            estrutura = {
                "tipo": "triangular",
                "atletas": len(atletas_para_luta),
                "lutas": [],
                "lutas_detalhes": {}
            }
            # Triangular: 3 lutas (A vs B, A vs C, B vs C)
            luta1 = Luta.objects.create(
                chave=chave,
                atleta_a=atletas_para_luta[0],
                atleta_b=atletas_para_luta[1],
                round=1,
                proxima_luta=None
            )
            luta2 = Luta.objects.create(
                chave=chave,
                atleta_a=atletas_para_luta[0],
                atleta_b=atletas_para_luta[2],
                round=1,
                proxima_luta=None
            )
            luta3 = Luta.objects.create(
                chave=chave,
                atleta_a=atletas_para_luta[1],
                atleta_b=atletas_para_luta[2],
                round=1,
                proxima_luta=None
            )
            estrutura["lutas"].extend([luta1.id, luta2.id, luta3.id])
            return estrutura
    
    elif modelo_chave == 'round_robin':
        # Round Robin (todos contra todos)
        return gerar_round_robin(chave, atletas_list)
    
    elif modelo_chave == 'eliminatoria_simples':
        # Eliminatória simples (sem repescagem)
        num_atletas = len(atletas_list)
        # Determinar tamanho da chave
        if num_atletas <= 4:
            tamanho_chave = 4
        elif num_atletas <= 8:
            tamanho_chave = 8
        elif num_atletas <= 16:
            tamanho_chave = 16
        else:
            tamanho_chave = 32
        return gerar_eliminatoria_simples(chave, atletas_list, tamanho_chave)
    
    elif modelo_chave == 'eliminatoria_repescagem':
        # Eliminatória com repescagem (modelo CBJ)
        num_atletas = len(atletas_list)
        # Determinar tamanho da chave
        if num_atletas <= 4:
            tamanho_chave = 4
        elif num_atletas <= 8:
            tamanho_chave = 8
        elif num_atletas <= 16:
            tamanho_chave = 16
        else:
            tamanho_chave = 32
        return gerar_eliminatoria_repescagem(chave, atletas_list, tamanho_chave)
    
    elif modelo_chave in ['olimpica_4', 'olimpica_8', 'olimpica_16', 'olimpica_32']:
        # Extrair tamanho do modelo
        tamanho_chave = int(modelo_chave.split('_')[1])
        return gerar_chave_olimpica_manual(chave, atletas_list, tamanho_chave)
    
    else:
        # Modelo desconhecido, usar comportamento automático
        return gerar_chave_automatica(chave, atletas_list)


def gerar_chave_olimpica(chave, atletas_list):
    """Gera uma chave olímpica (eliminatória) - comportamento automático"""
    num_atletas = len(atletas_list)
    
    # Calcular próximo tamanho de chave (4, 8, 16...)
    if num_atletas <= 4:
        tamanho_chave = 4
    elif num_atletas <= 8:
        tamanho_chave = 8
    elif num_atletas <= 16:
        tamanho_chave = 16
    else:
        tamanho_chave = 32
    
    return gerar_chave_olimpica_manual(chave, atletas_list, tamanho_chave)


def gerar_chave_olimpica_manual(chave, atletas_list, tamanho_chave):
    """Gera uma chave olímpica (eliminatória) com tamanho especificado
    
    Atletas da mesma academia não se enfrentam na primeira rodada.
    """
    num_atletas = len(atletas_list)
    
    # Organizar atletas para evitar mesma academia na 1ª rodada
    atletas_organizados = agrupar_atletas_por_academia(atletas_list)
    
    # Preencher com BYEs se necessário
    atletas_com_bye = atletas_organizados + [None] * (tamanho_chave - num_atletas)
    
    estrutura = {
        "tipo": "chave_olimpica",
        "atletas": num_atletas,
        "tamanho_chave": tamanho_chave,
        "rounds": {}
    }
    
    # Criar lutas do primeiro round
    round_num = 1
    lutas_round = []
    num_lutas = tamanho_chave // 2
    
    for i in range(0, tamanho_chave, 2):
        atleta_a = atletas_com_bye[i] if i < len(atletas_organizados) else None
        atleta_b = atletas_com_bye[i + 1] if i + 1 < len(atletas_organizados) else None
        
        # Se um dos atletas existe, criar luta
        if atleta_a or atleta_b:
            luta = Luta.objects.create(
                chave=chave,
                atleta_a=atleta_a,
                atleta_b=atleta_b,
                round=round_num,
                proxima_luta=None  # Será definido depois
            )
            lutas_round.append(luta.id)
    
    estrutura["rounds"][round_num] = lutas_round
    
    # Criar lutas dos rounds seguintes e vincular
    lutas_anteriores = lutas_round
    while len(lutas_anteriores) > 1:
        round_num += 1
        num_lutas = len(lutas_anteriores) // 2
        lutas_novo_round = []
        
        for i in range(num_lutas):
            luta = Luta.objects.create(
                chave=chave,
                atleta_a=None,  # Será preenchido quando a luta anterior terminar
                atleta_b=None,
                round=round_num,
                proxima_luta=None  # Será definido depois
            )
            lutas_novo_round.append(luta.id)
        
        # Vincular lutas do round anterior às do novo round
        for idx, luta_ant_id in enumerate(lutas_anteriores):
            try:
                luta_ant = Luta.objects.get(id=luta_ant_id)
                proxima_luta_idx = idx // 2
                if proxima_luta_idx < len(lutas_novo_round):
                    luta_ant.proxima_luta = lutas_novo_round[proxima_luta_idx]
                    luta_ant.save()
            except Luta.DoesNotExist:
                pass
        
        estrutura["rounds"][round_num] = lutas_novo_round
        lutas_anteriores = lutas_novo_round
    
    return estrutura


def atualizar_proxima_luta(luta):
    """Atualiza a próxima luta quando uma luta é concluída
    Também atualiza lutas de repescagem quando aplicável.
    """
    if not luta.vencedor or not luta.concluida:
        return
    
    # Atualizar próxima luta normal
    if luta.proxima_luta:
        try:
            proxima = Luta.objects.get(id=luta.proxima_luta, chave=luta.chave)
            
            # Determinar qual posição preencher (A ou B)
            if proxima.atleta_a is None:
                proxima.atleta_a = luta.vencedor
            elif proxima.atleta_b is None:
                proxima.atleta_b = luta.vencedor
            
            proxima.save()
        except Luta.DoesNotExist:
            pass
    
    # Atualizar repescagem se a chave tiver repescagem (SISTEMA CORRETO)
    estrutura = luta.chave.estrutura or {}
    if estrutura.get("tipo") == "eliminatoria_repescagem":
        repescagem = estrutura.get("repescagem", {})
        rounds_dict = estrutura.get("rounds", {})
        rounds_keys = [int(k) for k in rounds_dict.keys() if str(k).isdigit() and int(k) < 100]
        
        # Identificar perdedor
        perdedor = None
        if luta.atleta_a == luta.vencedor:
            perdedor = luta.atleta_b
        elif luta.atleta_b == luta.vencedor:
            perdedor = luta.atleta_a
        
        # ROUND 1: Perdedores vão para repescagem (Round 100)
        if luta.round == 1 and perdedor:
            repescagem_rounds = repescagem.get("rounds", {})
            if 100 in repescagem_rounds:
                lutas_repescagem_round1 = repescagem_rounds[100]
                # Encontrar próxima luta vazia na repescagem
                for luta_rep_id in lutas_repescagem_round1:
                    try:
                        luta_rep = Luta.objects.get(id=luta_rep_id, chave=luta.chave)
                        if luta_rep.atleta_a is None:
                            luta_rep.atleta_a = perdedor
                            luta_rep.save()
                            break
                        elif luta_rep.atleta_b is None:
                            luta_rep.atleta_b = perdedor
                            luta_rep.save()
                            break
                    except Luta.DoesNotExist:
                        continue
        
        # SEMIFINAL PRINCIPAL: Perdedor vai para luta de 3º lugar
        if rounds_keys:
            ultimo_round_principal = max(rounds_keys)
            if luta.round == ultimo_round_principal - 1:  # Semifinal da chave principal
                if perdedor and repescagem.get("luta_3_lugar"):
                    try:
                        luta_3_lugar = Luta.objects.get(id=repescagem["luta_3_lugar"], chave=luta.chave)
                        # Perdedor da semifinal vai para posição B da luta de 3º lugar
                        if luta_3_lugar.atleta_b is None:
                            luta_3_lugar.atleta_b = perdedor
                            luta_3_lugar.save()
                    except Luta.DoesNotExist:
                        pass
        
        # FINAL DA REPESCAGEM: Vencedor vai para luta de 3º lugar
        repescagem_rounds = repescagem.get("rounds", {})
        if repescagem_rounds:
            rounds_rep_keys = sorted([int(k) for k in repescagem_rounds.keys()])
            if rounds_rep_keys:
                ultimo_round_rep = max(rounds_rep_keys)
                # Verificar se esta é a última luta da repescagem
                lutas_ultimo_round_rep = repescagem_rounds[ultimo_round_rep]
                if len(lutas_ultimo_round_rep) == 1 and luta.round == ultimo_round_rep:
                    # Esta é a final da repescagem, vencedor vai para 3º lugar
                    if luta.vencedor and repescagem.get("luta_3_lugar"):
                        try:
                            luta_3_lugar = Luta.objects.get(id=repescagem["luta_3_lugar"], chave=luta.chave)
                            # Vencedor da repescagem vai para posição A da luta de 3º lugar
                            if luta_3_lugar.atleta_a is None:
                                luta_3_lugar.atleta_a = luta.vencedor
                                luta_3_lugar.save()
                        except Luta.DoesNotExist:
                            pass


def calcular_pontuacao_academias(campeonato_id=None):
    """Calcula e atualiza a pontuação de todas as academias para um campeonato"""
    # Obter ou criar campeonato padrão/ativo
    if campeonato_id:
        campeonato = Campeonato.objects.filter(id=campeonato_id).first()
    else:
        campeonato = Campeonato.objects.filter(ativo=True).first()
    if not campeonato:
        campeonato = Campeonato.objects.create(nome="Campeonato Padrão", ativo=True)
    
    # Limpar pontuações anteriores deste campeonato
    AcademiaPontuacao.objects.filter(campeonato=campeonato).delete()
    
    # Mapa de pontuações por academia
    pontos_academias = {}
    
    def get_registro(academia):
        if academia.id not in pontos_academias:
            pontos_academias[academia.id] = {
                'academia': academia,
                'ouro': 0,
                'prata': 0,
                'bronze': 0,
                'quarto': 0,
                'quinto': 0,
                'festival': 0,
                'remanejamento': 0,
            }
        return pontos_academias[academia.id]
    
    # 1. Pontos de Festival (através de inscrições)
    inscricoes_festival = Inscricao.objects.filter(
        campeonato=campeonato,
        classe_escolhida='Festival',
        status_inscricao='aprovado'
    ).select_related('atleta', 'atleta__academia')
    
    for inscricao in inscricoes_festival:
        reg = get_registro(inscricao.atleta.academia)
        reg['festival'] += 1
    
    # 2. Pontos por colocações nas chaves
    # Filtrar chaves do campeonato (se o modelo tiver campo campeonato)
    if hasattr(Chave, 'campeonato'):
        chaves = Chave.objects.filter(campeonato=campeonato)
    else:
        # Se não tiver campo campeonato, buscar todas (compatibilidade)
        chaves = Chave.objects.all()
    for chave in chaves:
        # Sempre usar get_resultados_chave:
        # - Conta resultados reais de lutas já decididas
        # - Inclui WOs e casos de campeão automático
        resultados = get_resultados_chave(chave)
        if not resultados:
            continue
        
        # Salvar classificação no JSON da chave
        classificacao = []
        for idx, atleta_id in enumerate(resultados, 1):
            if not atleta_id:
                continue
            classificacao.append({
                "atleta_id": atleta_id,
                "colocacao": idx,
            })
        estrutura = chave.estrutura or {}
        estrutura["classificacao"] = classificacao
        chave.estrutura = estrutura
        chave.save()
        
        # Aplicar contagem por colocação
        for idx, atleta_id in enumerate(resultados, 1):
            if not atleta_id:
                continue
            try:
                atleta = Atleta.objects.get(id=atleta_id)
            except Atleta.DoesNotExist:
                continue

            reg = get_registro(atleta.academia)

            # Pontuação por colocação:
            # 1º = ouro, 2º = prata, 3º = bronze, 4º = quarto, 5º = quinto
            if idx == 1:
                reg['ouro'] += 1
            elif idx == 2:
                reg['prata'] += 1
            elif idx == 3:
                reg['bronze'] += 1
            elif idx == 4:
                reg['quarto'] += 1
            elif idx == 5:
                reg['quinto'] += 1
    
    # 3. Remanejamentos (-1 ponto por atleta remanejado)
    inscricoes_remanejadas = Inscricao.objects.filter(
        campeonato=campeonato,
        remanejado=True,
        status_inscricao='aprovado'
    ).select_related('atleta', 'atleta__academia')
    
    for inscricao in inscricoes_remanejadas:
        reg = get_registro(inscricao.atleta.academia)
        reg['remanejamento'] += 1
    
    # 4. Calcular pontos totais e salvar registros
    Academia.objects.all().update(pontos=0)
    for data in pontos_academias.values():
        academia = data['academia']
        ouro = data['ouro']
        prata = data['prata']
        bronze = data['bronze']
        quarto = data['quarto']
        quinto = data['quinto']
        festival = data['festival']
        remanejamento = data['remanejamento']
        
        # Regras informadas:
        # Ouro = 10, Prata = 7, Bronze = 5, 4º = 3, 5º = 1, Festival = 1
        pontos_totais = (
            ouro * 10 +
            prata * 7 +
            bronze * 5 +
            quarto * 3 +
            quinto * 1 +
            festival * 1 +
            remanejamento * (-1)
        )
        
        AcademiaPontuacao.objects.create(
            campeonato=campeonato,
            academia=academia,
            ouro=ouro,
            prata=prata,
            bronze=bronze,
            quarto=quarto,
            quinto=quinto,
            festival=festival,
            remanejamento=remanejamento,
            pontos_totais=pontos_totais,
        )
        
        academia.pontos = pontos_totais
        academia.save()


def registrar_remanejamento(inscricao_id):
    """Registra remanejamento de um atleta (inscrição) e aplica -1 ponto automaticamente"""
    try:
        atleta = Atleta.objects.get(id=inscricao_id)
    except Atleta.DoesNotExist:
        return
    
    atleta.remanejado = True
    atleta.save()
    
    # Reprocessar pontuações
    calcular_pontuacao_academias()


def get_resultados_chave(chave):
    """Retorna os resultados finais de uma chave (1º, 2º, 3º, 3º)"""
    estrutura = chave.estrutura
    
    # Lutas casadas / chave manual não contam medalhas
    if estrutura.get("tipo") in ["lutas_casadas"]:
        return []
    
    if estrutura.get("tipo") == "vazia":
        return []
    
    if estrutura.get("tipo") == "campeao_automatico":
        return [estrutura.get("vencedor")]
    
    # Melhor de 3
    if estrutura.get("tipo") == "melhor_de_3":
        lutas = Luta.objects.filter(chave=chave, round=1).order_by('id')
        if len(lutas) > 0:
            # Contar vitórias (excluindo YUKO que não é vitória)
            vitorias = {}
            for luta in lutas:
                if luta.vencedor and luta.concluida and luta.tipo_vitoria != "YUKO":
                    vencedor_id = luta.vencedor.id
                    vitorias[vencedor_id] = vitorias.get(vencedor_id, 0) + 1
            
            # Verificar se algum atleta atingiu 2 vitórias
            atletas_ids = set()
            for luta in lutas:
                if luta.atleta_a:
                    atletas_ids.add(luta.atleta_a.id)
                if luta.atleta_b:
                    atletas_ids.add(luta.atleta_b.id)
            
            vencedor_id = None
            for atleta_id, num_vitorias in vitorias.items():
                if num_vitorias >= 2:
                    vencedor_id = atleta_id
                    break
            
            if vencedor_id:
                perdedor_id = None
                for atleta_id in atletas_ids:
                    if atleta_id != vencedor_id:
                        perdedor_id = atleta_id
                        break
                if perdedor_id:
                    return [vencedor_id, perdedor_id]
        return []
    
    # Triangular
    if estrutura.get("tipo") == "triangular":
        lutas = Luta.objects.filter(chave=chave, round=1).order_by('id')
        if len(lutas) == 3:
            # Verificar se todas as lutas foram concluídas
            todas_concluidas = all(luta.concluida and luta.vencedor for luta in lutas)
            if not todas_concluidas:
                # Ainda há lutas pendentes
                return []
            
            # Contar vitórias
            vitorias = {}
            for luta in lutas:
                if luta.vencedor:
                    vencedor_id = luta.vencedor.id
                    vitorias[vencedor_id] = vitorias.get(vencedor_id, 0) + 1
            
            # Verificar se todos os atletas têm vitórias registradas
            atletas_ids = set()
            for luta in lutas:
                if luta.atleta_a:
                    atletas_ids.add(luta.atleta_a.id)
                if luta.atleta_b:
                    atletas_ids.add(luta.atleta_b.id)
            
            # Se algum atleta não tem vitória registrada, ainda não está completo
            if len(vitorias) < len(atletas_ids):
                return []
            
            # Calcular pontos técnicos por atleta
            pontos_por_atleta = {}
            ippons_por_atleta = {}
            wazaris_por_atleta = {}
            yukos_por_atleta = {}
            
            for atleta_id in atletas_ids:
                pontos_por_atleta[atleta_id] = 0
                ippons_por_atleta[atleta_id] = 0
                wazaris_por_atleta[atleta_id] = 0
                yukos_por_atleta[atleta_id] = 0
                
                for luta in lutas:
                    if luta.vencedor and luta.vencedor.id == atleta_id:
                        pontos_por_atleta[atleta_id] += luta.pontos_vencedor
                        ippons_por_atleta[atleta_id] += luta.ippon_count
                        wazaris_por_atleta[atleta_id] += luta.wazari_count
                        yukos_por_atleta[atleta_id] += luta.yuko_count
            
            # Verificar empates
            # Agrupar atletas por pontos totais
            grupos_por_pontos = {}
            for atleta_id in atletas_ids:
                pontos_total = pontos_por_atleta[atleta_id]
                if pontos_total not in grupos_por_pontos:
                    grupos_por_pontos[pontos_total] = []
                grupos_por_pontos[pontos_total].append(atleta_id)
            
            # Ordenar por pontos (maior para menor)
            ordenados_por_pontos = sorted(pontos_por_atleta.items(), key=lambda x: x[1], reverse=True)
            
            # Se há desempate manual salvo, usar ele
            if 'desempate' in estrutura:
                desempate = estrutura['desempate']
                resultados = []
                
                for pontos_total, atletas_grupo in sorted(grupos_por_pontos.items(), reverse=True):
                    if len(atletas_grupo) == 1:
                        resultados.append(atletas_grupo[0])
                    else:
                        if pontos_total in desempate:
                            resultados.extend(desempate[pontos_total])
                        else:
                            resultados.extend(atletas_grupo)
                
                return resultados[:3]
            
            # Verificar se há empate
            precisa_desempate = any(len(grupo) > 1 for grupo in grupos_por_pontos.values())
            
            if precisa_desempate:
                # Aplicar critérios de desempate
                resultados = []
                
                for pontos_total, atletas_grupo in sorted(grupos_por_pontos.items(), reverse=True):
                    if len(atletas_grupo) == 1:
                        resultados.append(atletas_grupo[0])
                    else:
                        # Desempate: 1) Vitórias, 2) Confronto direto, 3) Ippons, 4) Wazaris, 5) Yukos
                        desempatados = []
                        
                        # 1. Ordenar por número de vitórias (excluindo YUKO)
                        vitorias_grupo = {}
                        for atleta_id in atletas_grupo:
                            vitorias_grupo[atleta_id] = sum(1 for luta in lutas 
                                                          if luta.vencedor and luta.vencedor.id == atleta_id 
                                                          and luta.tipo_vitoria != "YUKO")
                        
                        ordenados_vitorias = sorted(vitorias_grupo.items(), key=lambda x: x[1], reverse=True)
                        
                        # Se ainda empatado, usar confronto direto
                        grupos_vitorias = {}
                        for atleta_id, num_vit in ordenados_vitorias:
                            if num_vit not in grupos_vitorias:
                                grupos_vitorias[num_vit] = []
                            grupos_vitorias[num_vit].append(atleta_id)
                        
                        for num_vit, atletas_vit in sorted(grupos_vitorias.items(), reverse=True):
                            if len(atletas_vit) == 1:
                                desempatados.append(atletas_vit[0])
                            else:
                                # Confronto direto
                                confrontos = []
                                for atleta_id in atletas_vit:
                                    ganhou_de = False
                                    for luta in lutas:
                                        if (luta.vencedor and luta.vencedor.id == atleta_id and
                                            ((luta.atleta_a and luta.atleta_a.id != atleta_id and luta.atleta_a.id in atletas_vit) or
                                             (luta.atleta_b and luta.atleta_b.id != atleta_id and luta.atleta_b.id in atletas_vit))):
                                            ganhou_de = True
                                            break
                                    
                                    confrontos.append((atleta_id, ganhou_de))
                                
                                confrontos.sort(key=lambda x: (not x[1], x[0]))
                                
                                # Se ainda empatado, ordenar por ippons, wazaris, yukos
                                if len([x for x in confrontos if x[1]]) > 1 or len([x for x in confrontos if not x[1]]) > 1:
                                    confrontos.sort(key=lambda x: (
                                        ippons_por_atleta[x[0]],
                                        wazaris_por_atleta[x[0]],
                                        yukos_por_atleta[x[0]]
                                    ), reverse=True)
                                
                                desempatados.extend([x[0] for x in confrontos])
                        
                        resultados.extend(desempatados)
                
                return resultados[:3]
            
            # Sem empates, retornar ordenados por pontos
            return [atleta_id for atleta_id, _ in ordenados_por_pontos[:3]]
        return []
    
    # Round Robin (todos contra todos)
    if estrutura.get("tipo") == "round_robin":
        lutas = Luta.objects.filter(chave=chave, round=1).order_by('id')
        if len(lutas) == 0:
            return []
        
        # Verificar se todas as lutas foram concluídas
        todas_concluidas = all(luta.concluida and luta.vencedor for luta in lutas)
        if not todas_concluidas:
            return []
        
        # Coletar todos os atletas
        atletas_ids = set()
        for luta in lutas:
            if luta.atleta_a:
                atletas_ids.add(luta.atleta_a.id)
            if luta.atleta_b:
                atletas_ids.add(luta.atleta_b.id)
        
        # Contar vitórias
        vitorias = {}
        pontos_por_atleta = {}
        ippons_por_atleta = {}
        wazaris_por_atleta = {}
        yukos_por_atleta = {}
        
        for atleta_id in atletas_ids:
            vitorias[atleta_id] = 0
            pontos_por_atleta[atleta_id] = 0
            ippons_por_atleta[atleta_id] = 0
            wazaris_por_atleta[atleta_id] = 0
            yukos_por_atleta[atleta_id] = 0
        
        for luta in lutas:
            if luta.vencedor and luta.tipo_vitoria != "YUKO":
                vencedor_id = luta.vencedor.id
                vitorias[vencedor_id] = vitorias.get(vencedor_id, 0) + 1
                pontos_por_atleta[vencedor_id] += luta.pontos_vencedor or 0
                ippons_por_atleta[vencedor_id] += luta.ippon_count or 0
                wazaris_por_atleta[vencedor_id] += luta.wazari_count or 0
                yukos_por_atleta[vencedor_id] += luta.yuko_count or 0
        
        # Ordenar por: 1) Vitórias, 2) Pontos, 3) Ippons, 4) Wazaris, 5) Yukos
        resultados = sorted(atletas_ids, key=lambda x: (
            vitorias.get(x, 0),
            pontos_por_atleta.get(x, 0),
            ippons_por_atleta.get(x, 0),
            wazaris_por_atleta.get(x, 0),
            yukos_por_atleta.get(x, 0)
        ), reverse=True)
        
        return resultados[:5]  # Retornar até 5 colocados
    
    # Eliminatória com Repescagem (CBJ)
    if estrutura.get("tipo") == "eliminatoria_repescagem":
        rounds_dict = estrutura.get("rounds", {})
        if not rounds_dict:
            return []
        
        # Converter chaves para inteiros
        rounds_keys = [int(k) for k in rounds_dict.keys() if str(k).isdigit() and int(k) < 999]
        
        if not rounds_keys:
            return []
        
        ultimo_round = max(rounds_keys)
        
        # Buscar final
        lutas_final = Luta.objects.filter(chave=chave, round=ultimo_round)
        if len(lutas_final) == 0 or not lutas_final.first().vencedor:
            return []
        
        luta_final = lutas_final.first()
        primeiro = luta_final.vencedor.id
        
        # 2º lugar (perdedor da final)
        segundo = None
        if luta_final.atleta_a == luta_final.vencedor:
            segundo = luta_final.atleta_b.id if luta_final.atleta_b else None
        else:
            segundo = luta_final.atleta_a.id if luta_final.atleta_a else None
        
        # 3º lugar (vencedor da luta de 3º lugar)
        terceiro = None
        repescagem = estrutura.get("repescagem", {})
        if repescagem.get("luta_3_lugar"):
            luta_3_lugar = Luta.objects.filter(id=repescagem["luta_3_lugar"]).first()
            if luta_3_lugar and luta_3_lugar.vencedor:
                terceiro = luta_3_lugar.vencedor.id
        
        resultados = [primeiro, segundo]
        if terceiro:
            resultados.append(terceiro)
        
        return resultados
    
    # Eliminatória Simples (sem repescagem)
    if estrutura.get("tipo") == "eliminatoria_simples":
        rounds_dict = estrutura.get("rounds", {})
        if not rounds_dict:
            return []
        
        rounds_keys = [int(k) for k in rounds_dict.keys() if str(k).isdigit()]
        if not rounds_keys:
            return []
        
        ultimo_round = max(rounds_keys)
        lutas_final = Luta.objects.filter(chave=chave, round=ultimo_round)
        
        if len(lutas_final) == 0 or not lutas_final.first().vencedor:
            return []
        
        luta_final = lutas_final.first()
        primeiro = luta_final.vencedor.id
        
        segundo = None
        if luta_final.atleta_a == luta_final.vencedor:
            segundo = luta_final.atleta_b.id if luta_final.atleta_b else None
        else:
            segundo = luta_final.atleta_a.id if luta_final.atleta_a else None
        
        return [primeiro, segundo] if segundo else [primeiro]
    
    # Chave Olímpica e outros tipos de eliminatória
    # Buscar a última luta (final)
    rounds_dict = estrutura.get("rounds", {})
    if not rounds_dict:
        return []
    
    # Converter chaves para inteiros se necessário
    rounds_keys = [int(k) for k in rounds_dict.keys() if str(k).isdigit()]
    
    if not rounds_keys:
        # Chave não finalizada
        return []
    
    ultimo_round = max(rounds_keys)
    
    if ultimo_round == 0:
        # Chave não finalizada
        return []
    
    lutas_final = Luta.objects.filter(
        chave=chave,
        round=ultimo_round
    )
    
    if len(lutas_final) == 0:
        return []
    
    luta_final = lutas_final.first()
    
    if not luta_final.vencedor:
        return []
    
    # 1º lugar
    primeiro = luta_final.vencedor.id
    
    # 2º lugar (perdedor da final)
    segundo = None
    if luta_final.atleta_a == luta_final.vencedor:
        segundo = luta_final.atleta_b.id if luta_final.atleta_b else None
    else:
        segundo = luta_final.atleta_a.id if luta_final.atleta_a else None
    
    # 3º lugares (perdedores das semifinais que não foram para a final)
    terceiros = []
    if ultimo_round > 1:
        semi_round = ultimo_round - 1
        semi_finais = Luta.objects.filter(chave=chave, round=semi_round)
        
        for semi in semi_finais:
            if semi.vencedor and semi.vencedor.id != primeiro and semi.vencedor.id != segundo:
                if semi.vencedor.id not in terceiros:
                    terceiros.append(semi.vencedor.id)
            else:
                # Perdedor da semifinal
                perdedor = None
                if semi.atleta_a and semi.atleta_a.id != (semi.vencedor.id if semi.vencedor else None):
                    perdedor = semi.atleta_a.id
                elif semi.atleta_b and semi.atleta_b.id != (semi.vencedor.id if semi.vencedor else None):
                    perdedor = semi.atleta_b.id
                
                if perdedor and perdedor not in terceiros:
                    terceiros.append(perdedor)
    
    resultados = [primeiro, segundo] + terceiros[:2]  # Máximo 2 terceiros
    return resultados
