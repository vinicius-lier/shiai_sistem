"""
Views para o módulo de ocorrências
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
import datetime
from .models import Ocorrencia, Campeonato, Academia, Atleta, Inscricao
from .academia_auth import operacional_required
from .utils_historico import registrar_historico


@operacional_required
def ocorrencias_lista(request):
    """Lista todas as ocorrências com filtros"""
    # Buscar campeonato ativo ou selecionado
    campeonato_id = request.GET.get('campeonato_id')
    if campeonato_id:
        campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    else:
        campeonato = Campeonato.objects.filter(ativo=True).first()
    
    # Filtros
    categoria_filtro = request.GET.get('categoria', '')
    status_filtro = request.GET.get('status', '')
    prioridade_filtro = request.GET.get('prioridade', '')
    busca = request.GET.get('busca', '')
    
    # Query base
    ocorrencias = Ocorrencia.objects.all()
    
    if campeonato:
        ocorrencias = ocorrencias.filter(campeonato=campeonato)
    
    if categoria_filtro:
        ocorrencias = ocorrencias.filter(categoria=categoria_filtro)
    
    if status_filtro:
        ocorrencias = ocorrencias.filter(status=status_filtro)
    
    if prioridade_filtro:
        ocorrencias = ocorrencias.filter(prioridade=prioridade_filtro)
    
    if busca:
        ocorrencias = ocorrencias.filter(
            Q(titulo__icontains=busca) |
            Q(descricao__icontains=busca) |
            Q(academia__nome__icontains=busca) |
            Q(atleta__nome__icontains=busca)
        )
    
    ocorrencias = ocorrencias.select_related(
        'campeonato', 'academia', 'atleta', 'registrado_por', 'responsavel_resolucao'
    ).order_by('-data_ocorrencia', '-data_registro')
    
    # Paginação
    paginator = Paginator(ocorrencias, 20)
    page = request.GET.get('page')
    ocorrencias_page = paginator.get_page(page)
    
    # Estatísticas
    total = ocorrencias.count()
    abertas = ocorrencias.filter(status='ABERTA').count()
    em_andamento = ocorrencias.filter(status='EM_ANDAMENTO').count()
    resolvidas = ocorrencias.filter(status='RESOLVIDA').count()
    
    campeonatos = Campeonato.objects.all().order_by('-data_competicao', '-data_inicio')
    
    context = {
        'ocorrencias': ocorrencias_page,
        'campeonatos': campeonatos,
        'campeonato_selecionado': campeonato,
        'categoria_filtro': categoria_filtro,
        'status_filtro': status_filtro,
        'prioridade_filtro': prioridade_filtro,
        'busca': busca,
        'total': total,
        'abertas': abertas,
        'em_andamento': em_andamento,
        'resolvidas': resolvidas,
        'CATEGORIA_CHOICES': Ocorrencia.CATEGORIA_CHOICES,
        'STATUS_CHOICES': Ocorrencia.STATUS_CHOICES,
        'PRIORIDADE_CHOICES': Ocorrencia.PRIORIDADE_CHOICES,
    }
    
    return render(request, 'atletas/administracao/ocorrencias_lista.html', context)


@operacional_required
def ocorrencias_criar(request):
    """Cria uma nova ocorrência"""
    # Buscar campeonato ativo ou selecionado
    campeonato_id = request.GET.get('campeonato_id') or request.POST.get('campeonato_id')
    if campeonato_id:
        campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    else:
        campeonato = Campeonato.objects.filter(ativo=True).first()
    
    if not campeonato:
        messages.warning(request, 'Selecione um evento primeiro.')
        return redirect('ocorrencias_lista')
    
    if request.method == 'POST':
        categoria = request.POST.get('categoria')
        titulo = request.POST.get('titulo', '').strip()
        descricao = request.POST.get('descricao', '').strip()
        prioridade = request.POST.get('prioridade', 'MEDIA')
        data_ocorrencia = request.POST.get('data_ocorrencia')
        academia_id = request.POST.get('academia_id')
        atleta_id = request.POST.get('atleta_id')
        inscricao_id = request.POST.get('inscricao_id')
        observacoes = request.POST.get('observacoes', '').strip()
        
        if not titulo or not descricao:
            messages.error(request, 'Título e descrição são obrigatórios.')
        else:
            # Converter data_ocorrencia
            try:
                if data_ocorrencia:
                    data_ocorrencia_obj = datetime.datetime.strptime(data_ocorrencia, '%Y-%m-%dT%H:%M')
                    # Tornar timezone-aware
                    data_ocorrencia_obj = timezone.make_aware(data_ocorrencia_obj)
                else:
                    data_ocorrencia_obj = timezone.now()
            except:
                data_ocorrencia_obj = timezone.now()
            
            ocorrencia = Ocorrencia.objects.create(
                categoria=categoria,
                titulo=titulo,
                descricao=descricao,
                prioridade=prioridade,
                campeonato=campeonato,
                academia_id=academia_id if academia_id else None,
                atleta_id=atleta_id if atleta_id else None,
                inscricao_id=inscricao_id if inscricao_id else None,
                registrado_por=request.user,
                data_ocorrencia=data_ocorrencia_obj,
                observacoes=observacoes,
            )
            
            # Registrar no histórico
            registrar_historico(
                tipo_acao='OUTRO',
                descricao=f'Ocorrência criada: {titulo} ({ocorrencia.get_categoria_display()})',
                usuario=request.user,
                campeonato=campeonato,
                academia=ocorrencia.academia,
                atleta=ocorrencia.atleta,
                request=request
            )
            
            messages.success(request, 'Ocorrência registrada com sucesso!')
            return redirect('ocorrencias_detalhe', ocorrencia_id=ocorrencia.id)
    
    # Buscar academias e atletas para o formulário
    academias = Academia.objects.filter(
        vinculos_campeonatos__campeonato=campeonato,
        vinculos_campeonatos__permitido=True
    ).distinct().order_by('nome')
    
    atletas = Atleta.objects.filter(
        inscricoes__campeonato=campeonato
    ).distinct().order_by('nome')
    
    campeonatos = Campeonato.objects.all().order_by('-data_competicao', '-data_inicio')
    
    context = {
        'campeonatos': campeonatos,
        'campeonato_selecionado': campeonato,
        'academias': academias,
        'atletas': atletas,
        'CATEGORIA_CHOICES': Ocorrencia.CATEGORIA_CHOICES,
        'PRIORIDADE_CHOICES': Ocorrencia.PRIORIDADE_CHOICES,
    }
    
    return render(request, 'atletas/administracao/ocorrencias_criar.html', context)


@operacional_required
def ocorrencias_detalhe(request, ocorrencia_id):
    """Detalhes de uma ocorrência"""
    ocorrencia = get_object_or_404(
        Ocorrencia.objects.select_related(
            'campeonato', 'academia', 'atleta', 'inscricao',
            'registrado_por', 'responsavel_resolucao'
        ),
        id=ocorrencia_id
    )
    
    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        if acao == 'atualizar_status':
            novo_status = request.POST.get('status')
            ocorrencia.status = novo_status
            if novo_status == 'EM_ANDAMENTO' and not ocorrencia.responsavel_resolucao:
                ocorrencia.responsavel_resolucao = request.user
            ocorrencia.save()
            
            registrar_historico(
                tipo_acao='OUTRO',
                descricao=f'Status da ocorrência alterado para: {ocorrencia.get_status_display()}',
                usuario=request.user,
                campeonato=ocorrencia.campeonato,
                request=request
            )
            
            messages.success(request, 'Status atualizado com sucesso!')
            
        elif acao == 'resolver':
            solucao = request.POST.get('solucao', '').strip()
            ocorrencia.marcar_como_resolvida(request.user, solucao)
            
            registrar_historico(
                tipo_acao='OUTRO',
                descricao=f'Ocorrência resolvida: {ocorrencia.titulo}',
                usuario=request.user,
                campeonato=ocorrencia.campeonato,
                request=request
            )
            
            messages.success(request, 'Ocorrência marcada como resolvida!')
            
        elif acao == 'atualizar':
            ocorrencia.titulo = request.POST.get('titulo', ocorrencia.titulo)
            ocorrencia.descricao = request.POST.get('descricao', ocorrencia.descricao)
            ocorrencia.observacoes = request.POST.get('observacoes', ocorrencia.observacoes)
            ocorrencia.prioridade = request.POST.get('prioridade', ocorrencia.prioridade)
            ocorrencia.save()
            
            registrar_historico(
                tipo_acao='OUTRO',
                descricao=f'Ocorrência atualizada: {ocorrencia.titulo}',
                usuario=request.user,
                campeonato=ocorrencia.campeonato,
                request=request
            )
            
            messages.success(request, 'Ocorrência atualizada com sucesso!')
        
        return redirect('ocorrencias_detalhe', ocorrencia_id=ocorrencia.id)
    
    context = {
        'ocorrencia': ocorrencia,
        'STATUS_CHOICES': Ocorrencia.STATUS_CHOICES,
        'PRIORIDADE_CHOICES': Ocorrencia.PRIORIDADE_CHOICES,
    }
    
    return render(request, 'atletas/administracao/ocorrencias_detalhe.html', context)


@operacional_required
def ocorrencias_historico(request):
    """Visualiza o histórico completo do sistema"""
    # Filtros
    tipo_acao_filtro = request.GET.get('tipo_acao', '')
    campeonato_id = request.GET.get('campeonato_id')
    usuario_id = request.GET.get('usuario_id')
    busca = request.GET.get('busca', '')
    
    from .models import HistoricoSistema
    
    historicos = HistoricoSistema.objects.all()
    
    if tipo_acao_filtro:
        historicos = historicos.filter(tipo_acao=tipo_acao_filtro)
    
    if campeonato_id:
        historicos = historicos.filter(campeonato_id=campeonato_id)
    
    if usuario_id:
        historicos = historicos.filter(usuario_id=usuario_id)
    
    if busca:
        historicos = historicos.filter(descricao__icontains=busca)
    
    historicos = historicos.select_related(
        'usuario', 'campeonato', 'academia', 'atleta'
    ).order_by('-data_hora')
    
    # Paginação
    paginator = Paginator(historicos, 50)
    page = request.GET.get('page')
    historicos_page = paginator.get_page(page)
    
    campeonatos = Campeonato.objects.all().order_by('-data_competicao', '-data_inicio')
    from django.contrib.auth.models import User
    usuarios = User.objects.filter(is_staff=True).order_by('username')
    
    context = {
        'historicos': historicos_page,
        'campeonatos': campeonatos,
        'usuarios': usuarios,
        'tipo_acao_filtro': tipo_acao_filtro,
        'campeonato_id': campeonato_id,
        'usuario_id': usuario_id,
        'busca': busca,
        'TIPO_ACAO_CHOICES': HistoricoSistema.TIPO_ACAO_CHOICES,
    }
    
    return render(request, 'atletas/administracao/ocorrencias_historico.html', context)



