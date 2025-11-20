from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from atletas.decorators import operacional_required, academia_required
from atletas.models import Academia, Atleta
from .models import Evento, EventoParametro, EventoAtleta
from .models import calcular_classe_por_idade
from datetime import date


# ========== PAINEL OPERACIONAL ==========

@operacional_required
def lista_eventos(request):
    """Lista todos os eventos"""
    eventos = Evento.objects.all().order_by('-data_evento')
    return render(request, 'eventos/operacional/lista_eventos.html', {
        'eventos': eventos
    })


@operacional_required
def criar_evento(request):
    """Cria um novo evento"""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao', '')
        local = request.POST.get('local')
        data_evento = request.POST.get('data_evento')
        data_limite_inscricao = request.POST.get('data_limite_inscricao')
        parametros_baseado_em_id = request.POST.get('parametros_baseado_em')
        ativo = request.POST.get('ativo') == 'on'
        
        valor_federado = request.POST.get('valor_federado', '0.00')
        valor_nao_federado = request.POST.get('valor_nao_federado', '0.00')
        
        evento = Evento.objects.create(
            nome=nome,
            descricao=descricao,
            local=local,
            data_evento=data_evento,
            data_limite_inscricao=data_limite_inscricao,
            ativo=ativo,
            valor_federado=valor_federado,
            valor_nao_federado=valor_nao_federado
        )
        
        # Se foi selecionado um evento base, copiar parâmetros
        if parametros_baseado_em_id:
            evento_base = Evento.objects.get(id=parametros_baseado_em_id)
            evento.parametros_baseado_em = evento_base
            evento.save()
            EventoParametro.copiar_de_evento(evento_base, evento)
        
        messages.success(request, f'Evento "{nome}" criado com sucesso!')
        return redirect('eventos:configurar_evento', evento_id=evento.id)
    
    eventos_anteriores = Evento.objects.all().order_by('-data_evento')
    return render(request, 'eventos/operacional/criar_evento.html', {
        'eventos_anteriores': eventos_anteriores
    })


@operacional_required
def editar_evento(request, evento_id):
    """Edita um evento existente"""
    evento = get_object_or_404(Evento, id=evento_id)
    
    # ✅ BLOQUEIO: Não permitir editar evento após a data
    if evento.is_expired:
        messages.error(request, "Este evento já foi realizado e só pode ser visualizado.")
        return redirect('eventos:lista_eventos')
    
    if request.method == 'POST':
        evento.nome = request.POST.get('nome')
        evento.descricao = request.POST.get('descricao', '')
        evento.local = request.POST.get('local')
        evento.data_evento = request.POST.get('data_evento')
        evento.data_limite_inscricao = request.POST.get('data_limite_inscricao')
        evento.ativo = request.POST.get('ativo') == 'on'
        evento.valor_federado = request.POST.get('valor_federado', '0.00')
        evento.valor_nao_federado = request.POST.get('valor_nao_federado', '0.00')
        evento.save()
        
        messages.success(request, f'Evento "{evento.nome}" atualizado com sucesso!')
        return redirect('lista_eventos')
    
    # ✅ BLOQUEIO: Verificar se evento está expirado (para mostrar banner)
    evento_expirado = evento.is_expired
    
    return render(request, 'eventos/operacional/editar_evento.html', {
        'evento': evento,
        'evento_expirado': evento_expirado  # ✅ NOVO
    })


@operacional_required
def configurar_evento(request, evento_id):
    """Configura parâmetros de um evento"""
    evento = get_object_or_404(Evento, id=evento_id)
    
    # ✅ BLOQUEIO: Não permitir configurar evento após a data
    if evento.is_expired:
        messages.error(request, "Este evento já foi realizado e só pode ser visualizado.")
        return redirect('eventos:lista_eventos')
    
    if request.method == 'POST':
        parametros, created = EventoParametro.objects.get_or_create(evento=evento)
        
        parametros.idade_min = int(request.POST.get('idade_min', 0))
        parametros.idade_max = int(request.POST.get('idade_max', 99))
        parametros.usar_pesagem = request.POST.get('usar_pesagem') == 'on'
        parametros.usar_chaves_automaticas = request.POST.get('usar_chaves_automaticas') == 'on'
        parametros.permitir_festival = request.POST.get('permitir_festival') == 'on'
        parametros.pontuacao_primeiro = int(request.POST.get('pontuacao_primeiro', 10))
        parametros.pontuacao_segundo = int(request.POST.get('pontuacao_segundo', 7))
        parametros.pontuacao_terceiro = int(request.POST.get('pontuacao_terceiro', 5))
        parametros.penalidade_remanejamento = int(request.POST.get('penalidade_remanejamento', 1))
        parametros.save()
        
        messages.success(request, 'Parâmetros do evento atualizados com sucesso!')
        return redirect('eventos:configurar_evento', evento_id=evento.id)
    
    parametros = getattr(evento, 'parametros', None)
    # ✅ BLOQUEIO: Verificar se evento está expirado (para mostrar banner)
    evento_expirado = evento.is_expired
    
    return render(request, 'eventos/operacional/configurar_evento.html', {
        'evento': evento,
        'parametros': parametros,
        'evento_expirado': evento_expirado  # ✅ NOVO
    })


@operacional_required
def ver_inscritos(request, evento_id):
    """Visualiza atletas inscritos em um evento"""
    evento = get_object_or_404(Evento, id=evento_id)
    evento_atletas = evento.evento_atletas.all().select_related('atleta', 'academia', 'categoria_final', 'categoria_inicial').order_by('atleta__nome')
    
    # ✅ BLOQUEIO: Verificar se evento está expirado
    evento_expirado = evento.is_expired
    bloqueado = evento_expirado
    
    return render(request, 'eventos/operacional/ver_inscritos.html', {
        'evento': evento,
        'evento_atletas': evento_atletas,
        'evento_expirado': evento_expirado,
        'bloqueado': bloqueado  # ✅ NOVO
    })


# ========== PAINEL DO PROFESSOR (ACADEMIA) ==========

@login_required
def eventos_disponiveis(request):
    """Lista eventos disponíveis para inscrição (academia ou operacional)"""
    hoje = date.today()
    eventos = Evento.objects.filter(
        ativo=True,
        status='INSCRICOES',  # Apenas eventos com inscrições abertas
        data_limite_inscricao__gte=hoje
    ).order_by('data_evento')
    
    # ✅ NOVO: Filtrar eventos expirados (não mostrar para inscrição)
    eventos = [e for e in eventos if not e.is_expired]
    
    is_operacional = hasattr(request.user, 'profile') and request.user.profile.tipo_usuario in ['operacional', 'admin']
    
    return render(request, 'eventos/academia/eventos_disponiveis.html', {
        'eventos': eventos,
        'is_operacional': is_operacional,
    })


@login_required
def inscrever_atletas(request, evento_id):
    """Tela para inscrever atletas (academia ou operacional)"""
    evento = get_object_or_404(Evento, id=evento_id)
    
    # Verificar tipo de usuário e definir filtros
    is_academia = hasattr(request.user, 'profile') and request.user.profile.tipo_usuario == 'academia'
    is_operacional = hasattr(request.user, 'profile') and request.user.profile.tipo_usuario in ['operacional', 'admin']
    
    if not (is_academia or is_operacional):
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('index')
    
    # Filtrar atletas baseado no tipo de usuário
    if is_academia:
        academia = request.user.profile.academia
        if not academia:
            messages.error(request, 'Academia não vinculada ao seu perfil.')
            return redirect('eventos:eventos_disponiveis')
        # Academia vê apenas seus atletas
        atletas = Atleta.objects.filter(academia=academia).order_by('nome')
        # Buscar atletas já inscritos da mesma academia
        inscritos_ids = evento.evento_atletas.filter(academia=academia).values_list('atleta_id', flat=True)
        # Classes para filtro
        classes = Atleta.objects.filter(academia=academia).exclude(classe='').values_list('classe', flat=True).distinct().order_by('classe')
    else:
        # Operacional vê todos os atletas
        atletas = Atleta.objects.all().order_by('nome')
        # Buscar todos os atletas já inscritos
        inscritos_ids = evento.evento_atletas.all().values_list('atleta_id', flat=True)
        # Classes para filtro
        classes = Atleta.objects.exclude(classe='').values_list('classe', flat=True).distinct().order_by('classe')
    
    # Filtros
    nome_filtro = request.GET.get('nome', '').strip()
    classe_filtro = request.GET.get('classe', '')
    academia_filtro = request.GET.get('academia', '')
    
    if nome_filtro:
        atletas = atletas.filter(nome__icontains=nome_filtro)
    
    if classe_filtro:
        atletas = atletas.filter(classe=classe_filtro)
    
    # Filtro de academia (apenas para operacional)
    if is_operacional and academia_filtro:
        try:
            atletas = atletas.filter(academia_id=int(academia_filtro))
        except (ValueError, TypeError):
            pass
    
    # Calcular classe para cada atleta (se ainda não tiver)
    for atleta in atletas:
        if not atleta.classe:
            idade = atleta.idade
            atleta.classe = calcular_classe_por_idade(idade)
    
    if request.method == 'POST':
        # ✅ BLOQUEIO: Verificar novamente no POST
        if evento.is_expired:
            return JsonResponse({"error": "Inscrições encerradas. O evento já aconteceu."}, status=400)
        
        atletas_selecionados = request.POST.getlist('atletas')
        
        if not atletas_selecionados:
            messages.warning(request, 'Selecione pelo menos um atleta para inscrever.')
        else:
            # ✅ NOVO: Validar que atleta pertence à academia (se for academia)
            if is_academia:
                academia = request.user.profile.academia
                atletas_validos = Atleta.objects.filter(
                    id__in=atletas_selecionados,
                    academia=academia
                )
                if atletas_validos.count() != len(atletas_selecionados):
                    messages.error(request, "Alguns atletas selecionados não pertencem à sua academia e não podem ser inscritos.")
                    return redirect('eventos:inscrever_atletas', evento_id=evento.id)
            inscritos = 0
            for atleta_id in atletas_selecionados:
                # Verificar permissão: academia só pode inscrever seus atletas
                if is_academia:
                    atleta = get_object_or_404(Atleta, id=atleta_id, academia=academia)
                else:
                    atleta = get_object_or_404(Atleta, id=atleta_id)
                
                # Verificar se já está inscrito
                if not evento.evento_atletas.filter(atleta=atleta).exists():
                    # ✅ NOVO: Obter dados de federação do POST (podem ser diferentes do cadastro)
                    federado = request.POST.get(f'federado_{atleta_id}') == 'on'
                    zempo = request.POST.get(f'zempo_{atleta_id}', '').strip() if federado else ''
                    
                    # ✅ NOVO: Validação: se federado, deve ter ZEMPO
                    if federado and not zempo:
                        messages.error(request, f'Atleta "{atleta.nome}" é federado mas não possui número ZEMPO informado.')
                        continue
                    
                    # ✅ NOVO: Calcular classe do atleta (congelar no momento da inscrição)
                    from atletas.utils import calcular_classe
                    classe_calculada = calcular_classe(atleta.ano_nasc)
                    
                    # ✅ NOVO: Obter categoria inicial do atleta (pode mudar na pesagem)
                    categoria_inicial = atleta.categoria if hasattr(atleta, 'categoria') and atleta.categoria else None
                    
                    # Calcular valor da inscrição baseado no status federado
                    valor_inscricao = evento.valor_federado if federado else evento.valor_nao_federado
                    
                    # ✅ NOVO: Criar EventoAtleta com todos os dados obrigatórios
                    EventoAtleta.objects.create(
                        evento=evento,
                        atleta=atleta,
                        academia=atleta.academia,  # Sempre usa a academia do atleta
                        inscrito_por=request.user,
                        valor_inscricao=valor_inscricao,
                        status='OK',  # Status geral (OK, ELIMINADO_PESO, etc)
                        status_pesagem='PENDENTE',  # ✅ NOVO: Status específico da pesagem
                        federado=federado,  # ✅ NOVO: Dados de federação na inscrição
                        zempo=zempo,  # ✅ NOVO: ZEMPO na inscrição
                        classe=classe_calculada,  # ✅ NOVO: Classe congelada
                        categoria_inicial=categoria_inicial,  # ✅ NOVO: Categoria inicial
                        categoria_final=None,  # ✅ NOVO: Será definida na pesagem
                        peso_oficial=None  # ✅ NOVO: Será definido na pesagem
                    )
                    inscritos += 1
            
            if inscritos > 0:
                messages.success(request, f'{inscritos} atleta(s) inscrito(s) com sucesso!')
            else:
                messages.info(request, 'Todos os atletas selecionados já estão inscritos neste evento.')
            
            return redirect('eventos:inscrever_atletas', evento_id=evento.id)
    
    # Buscar academias para filtro (apenas operacional)
    academias = None
    if is_operacional:
        academias = Academia.objects.all().order_by('nome')
    
    # ✅ BLOQUEIO: Verificar se evento está expirado
    evento_expirado = evento.is_expired
    
    return render(request, 'eventos/academia/inscrever_atletas.html', {
        'evento': evento,
        'atletas': atletas,
        'inscritos_ids': list(inscritos_ids),
        'classes': classes,
        'academias': academias,
        'nome_filtro': nome_filtro,
        'classe_filtro': classe_filtro,
        'academia_filtro': academia_filtro,
        'is_academia': is_academia,
        'is_operacional': is_operacional,
        'evento_expirado': evento_expirado,  # ✅ NOVO
    })


@operacional_required
def remover_inscrito(request, evento_id, evento_atleta_id):
    """Remove um atleta inscrito do evento"""
    evento = get_object_or_404(Evento, id=evento_id)
    evento_atleta = get_object_or_404(EventoAtleta, id=evento_atleta_id, evento=evento)
    
    # ✅ BLOQUEIO: Não permitir remover após o evento
    if evento.is_expired:
        messages.error(request, "Não é possível remover atletas após o evento.")
        return redirect('eventos:ver_inscritos', evento_id=evento.id)
    
    if request.method == 'POST':
        atleta_nome = evento_atleta.atleta.nome
        evento_atleta.delete()
        messages.success(request, f'Atleta "{atleta_nome}" removido do evento com sucesso!')
    
    return redirect('eventos:ver_inscritos', evento_id=evento.id)


@login_required
def cadastrar_atleta_rapido(request, evento_id):
    """Cadastra um novo atleta rapidamente durante a inscrição"""
    evento = get_object_or_404(Evento, id=evento_id)
    
    # ✅ BLOQUEIO: Não permitir cadastrar atleta após o evento
    if evento.is_expired:
        messages.error(request, "Não é possível cadastrar atletas após o evento.")
        return redirect('eventos:inscrever_atletas', evento_id=evento.id)
    
    # Verificar tipo de usuário
    is_academia = hasattr(request.user, 'profile') and request.user.profile.tipo_usuario == 'academia'
    is_operacional = hasattr(request.user, 'profile') and request.user.profile.tipo_usuario in ['operacional', 'admin']
    
    if not (is_academia or is_operacional):
        messages.error(request, 'Você não tem permissão para acessar esta página.')
        return redirect('index')
    
    # Para academia, pegar a academia do perfil
    academia = None
    if is_academia:
        academia = request.user.profile.academia
        if not academia:
            messages.error(request, 'Academia não vinculada ao seu perfil.')
            return redirect('eventos:inscrever_atletas', evento_id=evento.id)
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        ano_nasc = int(request.POST.get('ano_nasc'))
        sexo = request.POST.get('sexo')
        faixa = request.POST.get('faixa')
        
        # Para operacional, pegar academia do formulário
        if is_operacional:
            academia_id = request.POST.get('academia')
            if not academia_id:
                messages.error(request, 'Selecione uma academia.')
                academias = Academia.objects.all().order_by('nome')
                return render(request, 'eventos/academia/cadastrar_atleta_rapido.html', {
                    'evento': evento,
                    'academias': academias,
                    'is_academia': False,
                    'is_operacional': True,
                })
            academia = get_object_or_404(Academia, id=academia_id)
        else:
            # Para academia, usar a academia do perfil (já validada acima)
            if not academia:
                messages.error(request, 'Academia não vinculada ao seu perfil.')
                return redirect('eventos:inscrever_atletas', evento_id=evento.id)
        
        # Calcular classe baseado no ano de nascimento
        idade = date.today().year - ano_nasc
        classe = calcular_classe_por_idade(idade)
        
        # Campos de federação
        federado = request.POST.get('federado') == 'on'
        zempo = request.POST.get('zempo', '').strip() if federado else None
        
        # Validação: se federado, zempo é obrigatório
        if federado and not zempo:
            messages.error(request, 'Número ZEMPO é obrigatório para atletas federados.')
            academias = Academia.objects.all().order_by('nome') if is_operacional else None
            return render(request, 'eventos/academia/cadastrar_atleta_rapido.html', {
                'evento': evento,
                'academias': academias,
                'is_academia': is_academia,
                'is_operacional': is_operacional,
            })
        
        atleta = Atleta.objects.create(
            nome=nome,
            ano_nasc=ano_nasc,
            sexo=sexo,
            faixa=faixa,
            academia=academia,
            classe=classe,
            federado=federado,
            zempo=zempo if federado else None
        )
        
        messages.success(request, f'Atleta "{nome}" cadastrado com sucesso!')
        # ✅ NOVO: Redirecionar para inscrição com o atleta recém-cadastrado pré-selecionado
        return redirect(f"{reverse('eventos:inscrever_atletas', args=[evento.id])}?novo_atleta={atleta.id}")
    
    # Buscar academias para operacional
    academias = None
    if is_operacional:
        academias = Academia.objects.all().order_by('nome')
    
    return render(request, 'eventos/academia/cadastrar_atleta_rapido.html', {
        'evento': evento,
        'academias': academias,
        'is_academia': is_academia,
        'is_operacional': is_operacional,
    })


@login_required
def meus_inscritos(request, evento_id):
    """Visualiza atletas inscritos em um evento"""
    evento = get_object_or_404(Evento, id=evento_id)
    
    # Verificar tipo de usuário
    is_academia = hasattr(request.user, 'profile') and request.user.profile.tipo_usuario == 'academia'
    is_operacional = hasattr(request.user, 'profile') and request.user.profile.tipo_usuario in ['operacional', 'admin']
    
    if is_academia:
        academia = request.user.profile.academia
        if not academia:
            messages.error(request, 'Academia não vinculada ao seu perfil.')
            return redirect('eventos:eventos_disponiveis')
        # Academia vê apenas seus inscritos
        evento_atletas = evento.evento_atletas.filter(academia=academia).select_related('atleta', 'categoria').order_by('atleta__nome')
    else:
        # Operacional vê todos os inscritos
        evento_atletas = evento.evento_atletas.all().select_related('atleta', 'academia', 'categoria').order_by('atleta__nome')
    
    return render(request, 'eventos/academia/meus_inscritos.html', {
        'evento': evento,
        'evento_atletas': evento_atletas,
        'is_operacional': is_operacional,
    })
