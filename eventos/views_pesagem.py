from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q
from atletas.decorators import operacional_required
from atletas.models import Academia, Atleta, Categoria, AdminLog
from atletas.utils import categoria_por_peso
from .models import Evento, EventoAtleta


def sugerir_categoria(atleta, peso):
    """
    ✅ FUNÇÃO CORRIGIDA: Sugere categoria baseado no peso.
    Apenas da mesma classe.
    A categoria cujo limite contém o peso informado.
    """
    categorias = Categoria.objects.filter(
        classe=atleta.classe,
        sexo=atleta.sexo
    ).order_by('limite_min')
    
    for cat in categorias:
        limite_max_real = cat.limite_max if cat.limite_max < 999.0 else 999999.0
        if cat.limite_min <= peso <= limite_max_real:
            return cat
    
    return None


@operacional_required
def pesagem_evento(request, evento_id):
    """Tela de pesagem para um evento específico - usa APENAS inscritos (EventoAtleta)"""
    evento = get_object_or_404(Evento, id=evento_id)
    
    # ✅ BLOQUEIO: Verificar se pesagem está liberada
    bloqueado = not evento.pesagem_liberada
    
    # IMPORTANTE: Buscar APENAS atletas INSCRITOS no evento (EventoAtleta)
    # NÃO mostrar todos os atletas do sistema
    evento_atletas = evento.evento_atletas.all().select_related('atleta', 'academia', 'categoria', 'categoria_final', 'categoria_inicial').order_by('atleta__nome')
    
    # Filtros
    nome_filtro = request.GET.get('nome', '').strip()
    classe_filtro = request.GET.get('classe', '')
    status_filtro = request.GET.get('status', '')
    academia_filtro = request.GET.get('academia', '')
    
    if nome_filtro:
        evento_atletas = evento_atletas.filter(atleta__nome__icontains=nome_filtro)
    
    if classe_filtro:
        # Filtrar pela classe do EventoAtleta (congelada no evento) ou do Atleta
        evento_atletas = evento_atletas.filter(
            Q(classe=classe_filtro) | Q(atleta__classe=classe_filtro)
        )
    
    if status_filtro:
        evento_atletas = evento_atletas.filter(status_pesagem=status_filtro)
    
    if academia_filtro:
        try:
            evento_atletas = evento_atletas.filter(academia_id=int(academia_filtro))
        except (ValueError, TypeError):
            pass
    
    # Buscar opções para filtros
    classes = evento_atletas.values_list('atleta__classe', flat=True).distinct().order_by('atleta__classe')
    academias = Academia.objects.filter(id__in=evento_atletas.values_list('academia_id', flat=True)).distinct().order_by('nome')
    
    # Verificar se todos foram pesados
    pendentes = evento_atletas.filter(status_pesagem='PENDENTE').count()
    todos_pesados = pendentes == 0
    
    # Converter QuerySet para lista para usar .count no template
    evento_atletas_list = list(evento_atletas)
    
    context = {
        'evento': evento,
        'evento_atletas': evento_atletas_list,  # Lista para usar no template
        'classes': classes,
        'academias': academias,
        'nome_filtro': nome_filtro,
        'classe_filtro': classe_filtro,
        'status_filtro': status_filtro,
        'academia_filtro': academia_filtro,
        'pendentes': pendentes,
        'todos_pesados': todos_pesados,
        'bloqueado': bloqueado,  # ✅ NOVO: Flag para bloquear pesagem
    }
    
    return render(request, 'eventos/pesagem/pesagem_evento.html', context)


@operacional_required
@require_http_methods(["POST"])
def registrar_peso_evento(request, evento_id, evento_atleta_id):
    """
    Registra o peso de um atleta inscrito em um evento.
    IMPORTANTE: Atualiza apenas EventoAtleta, NÃO altera o modelo Atleta base.
    Retorna JSON com o resultado da análise.
    """
    evento = get_object_or_404(Evento, id=evento_id)
    
    # ✅ BLOQUEIO: Não permitir registrar peso após o evento
    if not evento.pesagem_liberada:
        return JsonResponse({"erro": "Pesagem encerrada. O evento já aconteceu."}, status=403)
    
    evento_atleta = get_object_or_404(EventoAtleta, id=evento_atleta_id, evento=evento)
    atleta = evento_atleta.atleta  # Referência ao atleta permanente
    
    # Aceitar tanto 'peso' quanto 'peso_oficial' para compatibilidade
    peso_str = request.POST.get('peso') or request.POST.get('peso_oficial')
    try:
        peso_oficial = float(peso_str)
    except (ValueError, TypeError):
        return JsonResponse({'erro': 'Peso inválido'}, status=400)
    
    # Usar classe do EventoAtleta se disponível, senão usar do Atleta permanente
    classe_atleta = evento_atleta.classe or atleta.classe
    
    # Buscar categoria atual do EventoAtleta (não do Atleta base)
    categoria_atual = evento_atleta.categoria_final or evento_atleta.categoria_inicial or evento_atleta.categoria
    if not categoria_atual and evento_atleta.categoria_ajustada:
        categoria_atual = Categoria.objects.filter(
            classe=classe_atleta,
            sexo=atleta.sexo,
            categoria_nome=evento_atleta.categoria_ajustada
        ).first()
    
    # ✅ CORRIGIDO: Usar função sugerir_categoria (apenas mesma classe, limite contém peso)
    # Criar atleta temporário com classe correta para a função
    atleta_temp = atleta
    if evento_atleta.classe:
        # Usar classe do evento se disponível
        atleta_temp.classe = evento_atleta.classe
    categoria_sugerida = sugerir_categoria(atleta_temp, peso_oficial)
    
    # SITUAÇÃO A: Categoria correta OU primeira pesagem (sem categoria atual)
    if not categoria_atual and categoria_sugerida:
        # Primeira pesagem - aceitar categoria sugerida
        with transaction.atomic():
            # Atualizar APENAS EventoAtleta (NÃO alterar Atleta base)
            evento_atleta.peso_oficial = peso_oficial
            evento_atleta.categoria_final = categoria_sugerida
            evento_atleta.categoria = categoria_sugerida  # Compatibilidade
            evento_atleta.categoria_ajustada = categoria_sugerida.categoria_nome  # Compatibilidade
            evento_atleta.status_pesagem = 'OK'  # Compatibilidade
            evento_atleta.status = 'OK'
            evento_atleta.save()
            
            # Criar log
            AdminLog.objects.create(
                tipo='PESAGEM',
                acao=f'Pesagem OK - {atleta.nome}',
                atleta=atleta,
                academia=atleta.academia,
                detalhes=f'Evento: {evento.nome} - Peso: {peso_oficial} kg - Categoria: {categoria_sugerida.categoria_nome}'
            )
        
        return JsonResponse({
            'sucesso': True,
            'status': 'OK',
            'mensagem': f'Peso registrado com sucesso! Categoria: {categoria_sugerida.categoria_nome}'
        })
    
    # SITUAÇÃO A2: Categoria atual igual à sugerida
    if categoria_atual and categoria_sugerida and categoria_atual.id == categoria_sugerida.id:
        with transaction.atomic():
            # Atualizar APENAS EventoAtleta
            evento_atleta.peso_oficial = peso_oficial
            evento_atleta.categoria_final = categoria_sugerida
            evento_atleta.categoria = categoria_sugerida  # Compatibilidade
            evento_atleta.categoria_ajustada = categoria_sugerida.categoria_nome  # Compatibilidade
            evento_atleta.status_pesagem = 'OK'  # Compatibilidade
            evento_atleta.status = 'OK'
            evento_atleta.save()
            
            # Criar log
            AdminLog.objects.create(
                tipo='PESAGEM',
                acao=f'Pesagem OK - {atleta.nome}',
                atleta=atleta,
                academia=atleta.academia,
                detalhes=f'Evento: {evento.nome} - Peso: {peso_oficial} kg - Categoria: {categoria_sugerida.categoria_nome}'
            )
        
        return JsonResponse({
            'sucesso': True,
            'status': 'OK',
            'mensagem': f'Peso registrado com sucesso! Categoria: {categoria_sugerida.categoria_nome}'
        })
    
    # SITUAÇÃO B: Categoria válida, porém diferente
    if categoria_sugerida:
        # Garantir que a categoria sugerida é da mesma classe
        if categoria_sugerida.classe != classe_atleta:
            categoria_sugerida = None
        else:
            # Calcular limites para exibição
            limite_atual_max = categoria_atual.limite_max if categoria_atual and categoria_atual.limite_max < 999.0 else None
            limite_atual_str = f"{categoria_atual.limite_min} a {limite_atual_max} kg" if limite_atual_max else f"{categoria_atual.limite_min} kg ou mais" if categoria_atual else "Não definida"
            
            limite_sugerido_max = categoria_sugerida.limite_max if categoria_sugerida.limite_max < 999.0 else None
            limite_sugerido_str = f"{categoria_sugerida.limite_min} a {limite_sugerido_max} kg" if limite_sugerido_max else f"{categoria_sugerida.limite_min} kg ou mais"
            
            return JsonResponse({
                'modal': 'ESCOLHA',
                'evento_atleta_id': evento_atleta.id,
                'inscricao_id': evento_atleta.id,  # Compatibilidade
                'atleta_nome': atleta.nome,
                'peso': peso_oficial,
                'categoria_atual': {
                    'nome': categoria_atual.categoria_nome if categoria_atual else 'Não definida',
                    'classe': categoria_atual.classe if categoria_atual else classe_atleta,
                    'limite': limite_atual_str,
                    'limite_min': categoria_atual.limite_min if categoria_atual else 0,
                    'limite_max': limite_atual_max if limite_atual_max else 999999.0,
                },
                'categoria_sugerida': {
                    'nome': categoria_sugerida.categoria_nome,
                    'classe': categoria_sugerida.classe,
                    'limite': limite_sugerido_str,
                    'limite_min': categoria_sugerida.limite_min,
                    'limite_max': limite_sugerido_max if limite_sugerido_max else 999999.0,
                }
            })
    
    # SITUAÇÃO C: Peso fora de todas as categorias
    return JsonResponse({
        'modal': 'DESC_ONLY',
        'evento_atleta_id': evento_atleta.id,
        'inscricao_id': evento_atleta.id,  # Compatibilidade
        'atleta_nome': atleta.nome,
        'peso': peso_oficial,
    })


@operacional_required
@require_http_methods(["POST"])
def confirmar_acao_pesagem(request, evento_id, evento_atleta_id):
    """
    Confirma a ação escolhida pelo operador (remanejar ou desclassificar)
    IMPORTANTE: Atualiza apenas EventoAtleta, NÃO altera o modelo Atleta base.
    """
    evento = get_object_or_404(Evento, id=evento_id)
    
    # ✅ BLOQUEIO: Não permitir remanejar/desclassificar após o evento
    if not evento.pesagem_liberada:
        return JsonResponse({"erro": "Pesagem encerrada. O evento já aconteceu."}, status=403)
    
    evento_atleta = get_object_or_404(EventoAtleta, id=evento_atleta_id, evento=evento)
    atleta = evento_atleta.atleta  # Referência ao atleta permanente
    academia = evento_atleta.academia
    
    acao = request.POST.get('acao')
    # Aceitar tanto 'peso' quanto 'peso_oficial' para compatibilidade
    peso_str = request.POST.get('peso') or request.POST.get('peso_oficial')
    peso_oficial = float(peso_str)
    
    with transaction.atomic():
        # Atualizar APENAS EventoAtleta
        evento_atleta.peso_oficial = peso_oficial
        
        if acao == 'remanejar':
            categoria_nova_nome = request.POST.get('categoria_nova')
            # Usar classe do EventoAtleta se disponível
            classe_atleta = evento_atleta.classe or atleta.classe
            categoria_nova = get_object_or_404(
                Categoria,
                classe=classe_atleta,
                sexo=atleta.sexo,
                categoria_nome=categoria_nova_nome
            )
            
            # Buscar categoria atual para o log
            categoria_atual_nome = evento_atleta.categoria_ajustada if evento_atleta.categoria_ajustada else (evento_atleta.categoria.categoria_nome if evento_atleta.categoria else 'Não definida')
            
            # Atualizar APENAS EventoAtleta (NÃO alterar Atleta base)
            evento_atleta.categoria_final = categoria_nova
            evento_atleta.categoria = categoria_nova  # Compatibilidade
            evento_atleta.categoria_ajustada = categoria_nova.categoria_nome  # Compatibilidade
            evento_atleta.status_pesagem = 'REMANEJADO'  # Compatibilidade
            evento_atleta.status = 'OK'  # Status OK após remanejamento
            evento_atleta.remanejado = True
            evento_atleta.save()
            
            # Aplicar penalidade na academia
            try:
                penalidade = evento.parametros_config.penalidade_remanejamento if hasattr(evento, 'parametros_config') else 1
            except EventoParametro.DoesNotExist:
                penalidade = 1  # Valor padrão
            
            academia.pontos = max(0, academia.pontos - penalidade)
            academia.save()
            
            # Criar log
            AdminLog.objects.create(
                tipo='REMANEJAMENTO',
                acao=f'Remanejamento - {atleta.nome}',
                atleta=atleta,
                academia=academia,
                detalhes=f'Evento: {evento.nome} - De {categoria_atual_nome} para {categoria_nova.categoria_nome}. Peso: {peso_oficial} kg. Penalidade: -{penalidade} ponto(s).'
            )
            
            return JsonResponse({
                'sucesso': True,
                'status': 'REMANEJADO',
                'mensagem': f'Atleta remanejado para {categoria_nova.categoria_nome}. Academia perdeu {penalidade} ponto(s).'
            })
        
        elif acao == 'desclassificar':
            # Desclassificar - atualizar APENAS EventoAtleta
            evento_atleta.status_pesagem = 'DESC'  # Compatibilidade
            evento_atleta.status = 'ELIMINADO_PESO'
            evento_atleta.desclassificado = True  # Compatibilidade
            evento_atleta.save()
            
            # Criar log
            AdminLog.objects.create(
                tipo='DESCLASSIFICACAO',
                acao=f'Desclassificação - {atleta.nome}',
                atleta=atleta,
                academia=academia,
                detalhes=f'Evento: {evento.nome} - Peso fora do limite: {peso_oficial} kg. Motivo: Peso fora do limite permitido.'
            )
            
            return JsonResponse({
                'sucesso': True,
                'status': 'DESC',
                'mensagem': 'Atleta desclassificado por peso.'
            })
        
        else:
            return JsonResponse({'erro': 'Ação inválida'}, status=400)


@operacional_required
@require_http_methods(["POST"])
def encerrar_pesagem(request, evento_id):
    """Encerra a pesagem do evento"""
    evento = get_object_or_404(Evento, id=evento_id)
    
    # Verificar se todos foram pesados
    pendentes = evento.evento_atletas.filter(status_pesagem='PENDENTE').count()
    
    if pendentes > 0:
        return JsonResponse({
            'erro': True,
            'mensagem': f'Ainda há {pendentes} atleta(s) pendente(s) de pesagem.'
        }, status=400)
    
    evento.pesagem_encerrada = True
    evento.save()
    
    return JsonResponse({
        'sucesso': True,
        'mensagem': 'Pesagem encerrada com sucesso!'
    })
