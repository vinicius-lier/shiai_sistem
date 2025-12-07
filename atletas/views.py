# Importações das views de ajuda
from atletas.views_ajuda import ajuda_manual, ajuda_manual_web, ajuda_documentacao_tecnica

# Importar todas as views principais de um arquivo separado

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from types import SimpleNamespace
from django.contrib.auth import login as django_login, logout as django_logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import (
    Organizador,
    Academia, Atleta, Chave, Luta, Inscricao, Campeonato,
    Classe, Categoria, AcademiaPontuacao, AcademiaCampeonato, Despesa,
    UsuarioOperacional, AcademiaCampeonatoSenha, FormaPagamento,
    EquipeTecnicaCampeonato, PessoaEquipeTecnica, CategoriaInsumo, InsumoEstrutura,
    PesagemHistorico, ConferenciaPagamento, HistoricoSistema, Ocorrencia
)
from .academia_auth import (
    academia_required,
    operacional_required,
    operacional_ou_academia_required,
    pode_resetar_required,
    pode_criar_usuarios_required,
    organizacao_required,
)
from .utils import gerar_chave, get_resultados_chave, calcular_pontuacao_academias
from .utils_historico import registrar_historico
from .utils_tenant import get_organizador_usuario
from .services.pesagem import (
    registrar_peso as service_registrar_peso,
    confirmar_remanejamento as service_confirmar_remanejamento,
    calcular_categoria_por_peso,
)
from .services.inscricoes_service import inscrever_atleta as service_inscrever_atleta, aprovar as service_aprovar, remanejar as service_remanejar, desclassificar as service_desclassificar
from .services.inscricoes_service import inscrever_atleta as service_inscrever_atleta
from datetime import datetime, timedelta, date
import json

# Importar views de conferência de pagamentos e ocorrências
from .views_conferencia_pagamentos import (
    conferencia_pagamentos_lista,
    conferencia_pagamentos_detalhe,
    conferencia_pagamentos_salvar,
    gerar_mensagem_whatsapp,
    calcular_valor_esperado_academia,
)
from .views_ocorrencias import (
    ocorrencias_lista,
    ocorrencias_criar,
    ocorrencias_detalhe,
    ocorrencias_historico,
)

# ========== LOGIN E AUTENTICAÇÃO ==========

def landing_page(request):
    """Landing page do sistema"""
    return render(request, 'atletas/landing.html')

def selecionar_tipo_login(request):
    """Página inicial - seleção de tipo de login"""
    return render(request, 'atletas/academia/selecionar_login.html')


def landing_publica(request):
    """Landing page pública (sem organização)."""
    return render(request, 'atletas/landing.html')


def _redirect_dashboard(request, user):
    """
    Compat: usa a nova lógica de pós-login centralizada.
    """
    return _redirect_pos_login(request, user)

def login_operacional(request):
    """Login operacional - SEMPRE exige usuário e senha do Django (sem cache, sem login automático)"""
    import logging
    logger = logging.getLogger('atletas')
    
    try:
        # Se está logado como academia, redirecionar
        if request.session.get('academia_id'):
            return redirect('academia_painel')
        
        # Se já está autenticado, verificar perfil e redirecionar
        # IMPORTANTE: Mesmo autenticado, se a sessão expirar, será redirecionado aqui novamente
        if request.user.is_authenticated:
            # Superusers sempre têm acesso direto
            if request.user.is_superuser:
                # Garantir que superuser tenha perfil com senha_alterada=True
                try:
                    perfil = request.user.perfil_operacional
                    if not perfil.senha_alterada:
                        perfil.senha_alterada = True
                        perfil.data_expiracao = None  # Vitalício
                        perfil.pode_resetar_campeonato = True
                        perfil.pode_criar_usuarios = True
                        perfil.save()
                except UsuarioOperacional.DoesNotExist:
                    UsuarioOperacional.objects.create(
                        user=request.user,
                        pode_resetar_campeonato=True,
                        pode_criar_usuarios=True,
                        data_expiracao=None,
                        ativo=True,
                        senha_alterada=True
                    )
                return _redirect_dashboard(request, request.user)
            
            try:
                perfil = request.user.perfil_operacional
                
                # Verificar se está ativo
                if not perfil.ativo:
                    django_logout(request)
                    messages.error(request, 'Seu acesso operacional foi desativado.')
                    return render(request, 'atletas/login_operacional.html')
                
                # Verificar expiração (apenas para usuários temporários)
                # Usuários com data_expiracao=None são vitalícios e nunca expiram
                if perfil.esta_expirado:
                    django_logout(request)
                    messages.error(request, f'Seu acesso operacional expirou em {perfil.data_expiracao.strftime("%d/%m/%Y")}.')
                    return render(request, 'atletas/login_operacional.html')
                
                # Verificar se precisa alterar senha no primeiro acesso (apenas usuários não-superuser)
                if not perfil.senha_alterada:
                    return redirect('alterar_senha_obrigatorio')
                
                # Usuário válido e autenticado - redirecionar para dashboard
                return _redirect_dashboard(request, request.user)
            except UsuarioOperacional.DoesNotExist:
                # Usuário não tem perfil operacional - permitir criar ao fazer login
                pass
            except Exception as e:
                logger.error(f'Erro ao verificar perfil operacional: {str(e)}', exc_info=True)
                messages.error(request, 'Erro ao verificar perfil. Tente novamente.')
                return render(request, 'atletas/login_operacional.html')
        
        if request.method == 'POST':
            # Verificar CSRF token
            if not request.POST.get('csrfmiddlewaretoken'):
                logger.error('CSRF token ausente no POST')
                messages.error(request, 'Erro de segurança. Recarregue a página e tente novamente.')
                return render(request, 'atletas/login_operacional.html')
            
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
            
            if not username or not password:
                messages.error(request, 'Por favor, preencha usuário e senha.')
                return render(request, 'atletas/login_operacional.html')
            
            try:
                # Autenticar usuário (sem cache, sem login automático)
                user = authenticate(request, username=username, password=password)
                
                if user is not None:
                    # Superusers sempre têm acesso direto
                    if user.is_superuser:
                        # Garantir que superuser tenha perfil com senha_alterada=True
                        try:
                            perfil = user.perfil_operacional
                            if not perfil.senha_alterada:
                                perfil.senha_alterada = True
                                perfil.data_expiracao = None  # Vitalício
                                perfil.pode_resetar_campeonato = True
                                perfil.pode_criar_usuarios = True
                                perfil.save()
                        except UsuarioOperacional.DoesNotExist:
                            from datetime import timedelta
                            perfil = UsuarioOperacional.objects.create(
                                user=user,
                                pode_resetar_campeonato=True,
                                pode_criar_usuarios=True,
                                data_expiracao=None,  # Vitalício
                                ativo=True,
                                senha_alterada=True  # Superuser não precisa mudar senha
                            )
                        
                        django_login(request, user)
                        messages.success(request, f'Bem-vindo, {user.username}!')
                        return _redirect_pos_login(request, user)
                    
                    # Verificar perfil operacional e status para usuários normais
                    try:
                        perfil = user.perfil_operacional
                        
                        # Verificar se está ativo
                        if not perfil.ativo:
                            messages.error(request, 'Seu acesso operacional foi desativado.')
                            return render(request, 'atletas/login_operacional.html')
                        
                        # Verificar expiração (apenas para usuários temporários)
                        # Usuários com data_expiracao=None são vitalícios e nunca expiram
                        if perfil.esta_expirado:
                            messages.error(request, f'Seu acesso operacional expirou em {perfil.data_expiracao.strftime("%d/%m/%Y")}.')
                            return render(request, 'atletas/login_operacional.html')
                        
                    except UsuarioOperacional.DoesNotExist:
                        # Usuário não tem perfil operacional - criar um padrão (30 dias, temporário)
                        from datetime import timedelta
                        perfil = UsuarioOperacional.objects.create(
                            user=user,
                            pode_resetar_campeonato=False,
                            pode_criar_usuarios=False,
                            data_expiracao=timezone.now() + timedelta(days=30),  # Temporário por padrão
                            ativo=True,
                            senha_alterada=False  # Precisa alterar senha no primeiro acesso
                        )
                        messages.info(request, 'Perfil operacional criado. Acesso válido por 30 dias.')
                    except Exception as e:
                        logger.error(f'Erro ao criar/verificar perfil: {str(e)}', exc_info=True)
                        messages.error(request, 'Erro ao processar perfil. Tente novamente.')
                        return render(request, 'atletas/login_operacional.html')
                    
                    # Fazer login (sem cache, sem login automático)
                    # A sessão expira conforme configuração do Django (SESSION_COOKIE_AGE)
                    django_login(request, user)
                    
                    # Verificar se precisa alterar senha no primeiro acesso (apenas usuários não-superuser)
                    if not perfil.senha_alterada:
                        return redirect('alterar_senha_obrigatorio')
                    
                    # Limpar qualquer flag de validação de senha operacional (não usamos mais)
                    if 'senha_operacional_validada' in request.session:
                        del request.session['senha_operacional_validada']
                    
                    messages.success(request, f'Bem-vindo, {user.username}!')
                    return _redirect_pos_login(request, user)
                else:
                    messages.error(request, 'Usuário ou senha incorretos.')
                    return render(request, 'atletas/login_operacional.html')
            except Exception as e:
                logger.error(f'Erro ao autenticar usuário: {str(e)}', exc_info=True)
                messages.error(request, 'Erro ao processar login. Tente novamente.')
                return render(request, 'atletas/login_operacional.html')
        
        # GET: Sempre mostrar tela de login (nunca permitir acesso direto)
        return render(request, 'atletas/login_operacional.html')
    except Exception as e:
        logger.error(f'Erro geral em login_operacional: {str(e)}', exc_info=True)
        messages.error(request, 'Erro inesperado. Tente novamente.')
        return render(request, 'atletas/login_operacional.html')

def _redirect_pos_login(request, user):
    """
    Redireciona após login:
    - Superuser: seletor de organização
    - Operacional: para slug da organização vinculada (academia.organizador)
    - Se usuário de academia (sessão academia_id): para painel da academia
    """
    # Se é academia (login separado)
    if request.session.get('academia_id'):
        return redirect('academia_painel')
    # Superuser vai para seletor
    if user.is_superuser:
        return redirect('selecionar_organizacao')
    # Usuário operacional: tentar achar organização via perfil/academia
    try:
        perfil = user.perfil_operacional
        if perfil and perfil.ativo and perfil.organizacao:
            return redirect('index', organizacao_slug=perfil.organizacao.slug)
    except Exception:
        pass
    # Fallback: landing
    return redirect('landing_publica')


def logout_geral(request):
    """Realiza o logout tanto da sessão de academia quanto da sessão operacional - SEM cache, SEM login automático"""
    # Limpar sessão de academia
    if 'academia_id' in request.session:
        del request.session['academia_id']
    if 'academia_nome' in request.session:
        del request.session['academia_nome']
    if 'campeonato_id_ativo' in request.session:
        del request.session['campeonato_id_ativo']
    if 'campeonato_nome_ativo' in request.session:
        del request.session['campeonato_nome_ativo']
    if 'credencial_id' in request.session:
        del request.session['credencial_id']
    
    # Limpar qualquer flag de validação de senha operacional (não usamos mais)
    if 'senha_operacional_validada' in request.session:
        del request.session['senha_operacional_validada']
    
    # Fazer logout do Django (limpa autenticação)
    if request.user.is_authenticated:
        django_logout(request)
    
    # Limpar flags antigas
    if 'operacional_logado' in request.session:
        del request.session['operacional_logado']
    
    # Limpar toda a sessão (SEM cache)
    request.session.flush()
    request.session.delete()
    
    # Deletar cookies (garantir que não há login automático)
    response = redirect('login')
    response.delete_cookie('sessionid')
    response.delete_cookie('csrftoken')
    
    messages.success(request, 'Logout realizado com sucesso.')
    return response

def academia_login(request):
    """Login da academia - APENAS credenciais temporárias por evento"""
    if request.method == 'POST':
        login = request.POST.get('login', '').strip().upper()  # Converter para maiúsculas
        senha = request.POST.get('senha', '').strip()
        
        if not login or not senha:
            messages.error(request, 'Por favor, preencha login e senha.')
            return render(request, 'atletas/academia/login.html')
        
        # Buscar credencial temporária pelo login gerado
        # Primeiro tenta buscar no campeonato ativo, depois em qualquer campeonato
        credencial = None
        campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
        
        if campeonato_ativo:
            # Tentar buscar no campeonato ativo primeiro
            try:
                credencial = AcademiaCampeonatoSenha.objects.select_related('academia', 'campeonato').get(
                    login__iexact=login,
                    campeonato=campeonato_ativo
                )
            except AcademiaCampeonatoSenha.DoesNotExist:
                pass
            except AcademiaCampeonatoSenha.MultipleObjectsReturned:
                # Se houver múltiplas, pegar a mais recente do campeonato ativo
                credencial = AcademiaCampeonatoSenha.objects.select_related('academia', 'campeonato').filter(
                    login__iexact=login,
                    campeonato=campeonato_ativo
                ).order_by('-data_criacao').first()
        
        # Se não encontrou no campeonato ativo, buscar em qualquer campeonato
        if not credencial:
            try:
                credencial = AcademiaCampeonatoSenha.objects.select_related('academia', 'campeonato').filter(
                    login__iexact=login
                ).order_by('-data_criacao').first()  # Pegar a mais recente
            except Exception as e:
                messages.error(request, f'Erro ao buscar credenciais: {str(e)}')
                return render(request, 'atletas/academia/login.html')
        
        if not credencial:
            messages.error(request, f'Login "{login}" não encontrado. Verifique se o login está correto.')
            return render(request, 'atletas/academia/login.html')
        
        # Verificar se está expirado
        if credencial.esta_expirado:
            messages.error(request, 'O acesso temporário da sua academia expirou. Para acessar novos eventos, aguarde o envio de novo convite.')
            return render(request, 'atletas/academia/login.html')
        
        # Verificar senha
        if not credencial.verificar_senha(senha):
            messages.error(request, 'Senha incorreta. Verifique se digitou corretamente.')
            return render(request, 'atletas/academia/login.html')
        
        # Verificar se academia está ativa
        if not credencial.academia.ativo_login:
            messages.error(request, 'Academia inativa. Entre em contato com o organizador.')
            return render(request, 'atletas/academia/login.html')
        
        # Verificar se o campeonato está ativo
        if not credencial.campeonato.ativo:
            messages.warning(request, f'O campeonato "{credencial.campeonato.nome}" não está ativo no momento.')
            # Mesmo assim permite o login para visualizar dados
        
        # Login válido - criar sessão
        request.session['academia_id'] = credencial.academia.id
        request.session['academia_nome'] = credencial.academia.nome
        request.session['campeonato_id_ativo'] = credencial.campeonato.id
        request.session['campeonato_nome_ativo'] = credencial.campeonato.nome
        request.session['credencial_id'] = credencial.id
        
        # Marcar como enviado se ainda não foi
        if not credencial.enviado_whatsapp:
            credencial.enviado_whatsapp = True
            credencial.data_envio_whatsapp = timezone.now()
            credencial.save()
        
        messages.success(request, f'Bem-vindo, {credencial.academia.nome}!')
        return redirect('academia_painel')
    
    return render(request, 'atletas/academia/login.html')

def academia_logout(request):
    """Logout da academia"""
    if 'academia_id' in request.session:
        del request.session['academia_id']
    if 'academia_nome' in request.session:
        del request.session['academia_nome']
    if 'campeonato_id_ativo' in request.session:
        del request.session['campeonato_id_ativo']
    if 'campeonato_nome_ativo' in request.session:
        del request.session['campeonato_nome_ativo']
    messages.success(request, 'Logout realizado com sucesso.')
    return redirect('login')


def painel_organizacoes(request):
    """
    Painel global de organizações (apenas superuser).
    Permite escolher em qual organização entrar.
    """
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, 'Apenas superusuários podem acessar o painel de organizações.')
        return redirect('login')

    organizacoes = Organizador.objects.all().order_by('nome')
    return render(request, 'atletas/painel_organizacoes.html', {
        'organizacoes': organizacoes,
    })

# ========== DASHBOARD E PÁGINAS PRINCIPAIS ==========

@operacional_required
@organizacao_required
def index(request, organizacao_slug=None):
    """Página inicial - Dashboard"""
    organizacao = getattr(request, "organizacao", None)
    if not organizacao:
        return redirect('landing_publica')

    if request.session.get('academia_id'):
        return redirect('academia_painel')
    
    if not request.user.is_authenticated:
        return redirect('login')
    
    campeonato_ativo = Campeonato.objects.filter(ativo=True, organizador=organizacao).first()
    
    # Estatísticas básicas
    total_atletas = Atleta.objects.filter(academia__organizador=organizacao).count()
    total_academias = Academia.objects.filter(organizador=organizacao).count()
    
    # Ranking Global de Atletas
    ranking_global_atletas = []
    if campeonato_ativo:
        from .utils import calcular_pontuacao_academias, get_resultados_chave
        
        # Calcular pontuação das academias primeiro
        calcular_pontuacao_academias(campeonato_ativo.id)
        
        academias_permitidas_ids = list(AcademiaCampeonato.objects.filter(
            campeonato=campeonato_ativo,
            permitido=True
        ).values_list('academia_id', flat=True))
        
        # Contar inscrições
        inscricoes_query = Inscricao.objects.filter(campeonato=campeonato_ativo)
        if academias_permitidas_ids:
            inscricoes_query = inscricoes_query.filter(atleta__academia_id__in=academias_permitidas_ids)
        total_inscricoes = inscricoes_query.count()
        
        # Contar federados e não federados
        inscricoes_federados = inscricoes_query.filter(atleta__federado=True).count()
        inscricoes_nao_federados = total_inscricoes - inscricoes_federados
        
        total_chaves = Chave.objects.filter(campeonato=campeonato_ativo).count()
        
        # Ranking completo de academias
        ranking_academias_completo = AcademiaPontuacao.objects.filter(
            campeonato=campeonato_ativo
        ).select_related('academia')
        
        # Se houver academias permitidas, filtrar por elas
        if academias_permitidas_ids:
            ranking_academias_completo = ranking_academias_completo.filter(academia_id__in=academias_permitidas_ids)
        
        ranking_academias_completo = ranking_academias_completo.order_by('-pontos_totais', '-ouro', '-prata', '-bronze')
        
        # Preparar dados do ranking de academias
        ranking_academias_list = []
        for pontuacao in ranking_academias_completo:
            # Contar atletas ativos da academia no campeonato
            total_atletas_ativos = Inscricao.objects.filter(
                campeonato=campeonato_ativo,
                atleta__academia=pontuacao.academia,
                status_inscricao='aprovado'
            ).count()
            
            ranking_academias_list.append({
                'academia': pontuacao.academia,
                'ouro': pontuacao.ouro,
                'prata': pontuacao.prata,
                'bronze': pontuacao.bronze,
                'pontos_totais': pontuacao.pontos_totais,
                'total_atletas_ativos': total_atletas_ativos,
            })
        
        # Ranking top 5 apenas de academias permitidas (para compatibilidade)
        top_academias = ranking_academias_completo[:5]
        
        # Calcular ranking global de atletas
        chaves = Chave.objects.filter(campeonato=campeonato_ativo)
        medalhas_por_atleta = {}
        
        for chave in chaves:
            resultados = get_resultados_chave(chave)
            if not resultados:
                continue
            
            # 1º lugar = ouro, 2º lugar = prata, 3º lugar = bronze
            for idx, atleta_id in enumerate(resultados[:3], 1):
                if not atleta_id:
                    continue
                
                if atleta_id not in medalhas_por_atleta:
                    try:
                        atleta = Atleta.objects.get(id=atleta_id)
                        medalhas_por_atleta[atleta_id] = {
                            'atleta': atleta,
                            'ouro': 0,
                            'prata': 0,
                            'bronze': 0,
                            'total_medalhas': 0,
                        }
                    except Atleta.DoesNotExist:
                        continue
                
                if idx == 1:
                    medalhas_por_atleta[atleta_id]['ouro'] += 1
                elif idx == 2:
                    medalhas_por_atleta[atleta_id]['prata'] += 1
                elif idx == 3:
                    medalhas_por_atleta[atleta_id]['bronze'] += 1
                
                medalhas_por_atleta[atleta_id]['total_medalhas'] = (
                    medalhas_por_atleta[atleta_id]['ouro'] +
                    medalhas_por_atleta[atleta_id]['prata'] +
                    medalhas_por_atleta[atleta_id]['bronze']
                )
        
        # Ordenar por total de medalhas (ouro > prata > bronze)
        ranking_global_atletas = sorted(
            medalhas_por_atleta.values(),
            key=lambda x: (x['total_medalhas'], x['ouro'], x['prata'], x['bronze']),
            reverse=True
        )
    else:
        total_inscricoes = 0
        inscricoes_federados = 0
        inscricoes_nao_federados = 0
        total_chaves = 0
        top_academias = []
        ranking_academias_list = []
        ranking_global_atletas = []
    
    context = {
        'campeonato_ativo': campeonato_ativo,
        'total_atletas': total_atletas,
        'total_academias': total_academias,
        'total_inscricoes': total_inscricoes,
        'inscricoes_federados': inscricoes_federados,
        'inscricoes_nao_federados': inscricoes_nao_federados,
        'total_chaves': total_chaves,
        'top_academias': top_academias,
        'ranking_global_atletas': ranking_global_atletas,
        'ranking_academias_completo': ranking_academias_list if campeonato_ativo else [],
    }
    
    return render(request, 'atletas/index.html', context)

# ========== STUBS PARA VIEWS NECESSÁRIAS ==========
# Estas views precisam ser implementadas completamente
# Por enquanto, retornam mensagens de erro ou redirecionam

@operacional_required
@organizacao_required
def lista_academias(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Lista todas as academias com contagem de atletas"""
    academias = Academia.objects.filter(
        organizador=organizacao
    ).annotate(
        total_atletas=Count('atletas', filter=Q(atletas__status_ativo=True))
    ).order_by('nome')
    return render(request, 'atletas/lista_academias.html', {'academias': academias})

@operacional_required
@organizacao_required
def cadastrar_academia(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Cadastrar nova academia - SEM campos de login/senha"""
    if request.method == 'POST':
        try:
            academia = Academia.objects.create(
                organizador=organizacao,
                nome=request.POST.get('nome', '').strip(),
                cidade=request.POST.get('cidade', '').strip(),
                estado=request.POST.get('estado', '').strip().upper(),
                telefone=request.POST.get('telefone', '').strip(),
                responsavel=request.POST.get('responsavel', '').strip(),
                endereco=request.POST.get('endereco', '').strip(),
                bonus_percentual=request.POST.get('bonus_percentual') or None,
                bonus_fixo=request.POST.get('bonus_fixo') or None,
            )
            
            # Upload de foto
            if 'foto_perfil' in request.FILES:
                academia.foto_perfil = request.FILES['foto_perfil']
                academia.save()
            
            # Vincular automaticamente ao campeonato ativo (se houver) e gerar senha
            campeonato_ativo = Campeonato.objects.filter(ativo=True, organizador=organizacao).first()
            if campeonato_ativo:
                # Vincular ao campeonato (verificar se já existe antes)
                if not AcademiaCampeonato.objects.filter(academia=academia, campeonato=campeonato_ativo).exists():
                    AcademiaCampeonato.objects.create(
                        academia=academia,
                        campeonato=campeonato_ativo,
                        permitido=True
                    )
                
                # Gerar senha temporária para o campeonato
                import random
                import string
                from datetime import timedelta
                from datetime import datetime as dt
                
                login = f"ACADEMIA_{academia.id:03d}"
                senha_plana = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                
                # Calcular data de expiração (5 dias após término do campeonato)
                data_expiracao = None
                if campeonato_ativo.data_competicao:
                    data_expiracao = timezone.make_aware(
                        dt.combine(campeonato_ativo.data_competicao, dt.min.time())
                    ) + timedelta(days=5)
                
                # Criar ou atualizar senha
                senha_obj, created = AcademiaCampeonatoSenha.objects.get_or_create(
                    academia=academia,
                    campeonato=campeonato_ativo,
                    defaults={
                        'login': login,
                        'senha_plana': senha_plana,
                        'data_expiracao': data_expiracao,
                    }
                )
                
                if not created:
                    senha_obj.login = login
                    senha_obj.senha_plana = senha_plana
                    senha_obj.data_expiracao = data_expiracao
                    senha_obj.save()
                
                senha_obj.definir_senha(senha_plana)
                senha_obj.save()
            
            messages.success(request, f'Academia "{academia.nome}" cadastrada com sucesso!')
            if campeonato_ativo:
                messages.info(request, f'Academia automaticamente vinculada ao campeonato ativo: {campeonato_ativo.nome}. Senha temporária gerada.')
            return redirect('lista_academias', organizacao_slug=organizacao.slug if organizacao else None)
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar academia: {str(e)}')
    
    return render(request, 'atletas/cadastrar_academia.html')

@operacional_required
@organizacao_required
def detalhe_academia(request, organizacao_slug=None, academia_id=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Exibe detalhes da academia incluindo lista de atletas"""
    academia = get_object_or_404(Academia, id=academia_id, organizador=organizacao)
    
    # Buscar todos os atletas da academia (incluindo inativos)
    atletas = Atleta.objects.filter(academia=academia).order_by('nome')
    
    # Calcular estatísticas
    total_atletas = atletas.count()
    total_atletas_ativos = atletas.filter(status_ativo=True).count()
    total_federados = atletas.filter(federado=True).count()
    
    context = {
        'academia': academia,
        'atletas': atletas,
        'total_atletas': total_atletas,
        'total_atletas_ativos': total_atletas_ativos,
        'total_federados': total_federados,
    }
    
    return render(request, 'atletas/detalhe_academia.html', context)

@operacional_required
@organizacao_required
def deletar_academia(request, organizacao_slug=None, academia_id=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Deletar academia"""
    academia = get_object_or_404(Academia, id=academia_id, organizador=organizacao)
    
    if request.method == 'POST':
        try:
            nome_academia = academia.nome
            
            # Verificar se há atletas vinculados
            total_atletas = Atleta.objects.filter(academia=academia).count()
            if total_atletas > 0:
                messages.error(request, f'Não é possível excluir a academia "{nome_academia}" pois ela possui {total_atletas} atleta(s) vinculado(s). Remova os atletas primeiro.')
                return redirect('detalhe_academia', organizacao_slug=organizacao.slug, academia_id=academia_id)
            
            # Verificar se há inscrições em campeonatos
            total_inscricoes = Inscricao.objects.filter(atleta__academia=academia).count()
            if total_inscricoes > 0:
                messages.error(request, f'Não é possível excluir a academia "{nome_academia}" pois ela possui {total_inscricoes} inscrição(ões) em campeonatos.')
                return redirect('detalhe_academia', organizacao_slug=organizacao.slug, academia_id=academia_id)
            
            # Deletar vínculos com campeonatos
            AcademiaCampeonato.objects.filter(academia=academia).delete()
            AcademiaCampeonatoSenha.objects.filter(academia=academia).delete()
            
            # Deletar a academia
            academia.delete()
            
            messages.success(request, f'Academia "{nome_academia}" excluída com sucesso!')
            return redirect('lista_academias', organizacao_slug=organizacao.slug if organizacao else None)
        except Exception as e:
            messages.error(request, f'Erro ao excluir academia: {str(e)}')
            return redirect('detalhe_academia', organizacao_slug=organizacao.slug if organizacao else None, academia_id=academia_id)
    
    # GET: Mostrar confirmação
    total_atletas = Atleta.objects.filter(academia=academia).count()
    total_inscricoes = Inscricao.objects.filter(atleta__academia=academia).count()
    
    context = {
        'academia': academia,
        'total_atletas': total_atletas,
        'total_inscricoes': total_inscricoes,
    }
    
    return render(request, 'atletas/deletar_academia.html', context)

@operacional_required
@organizacao_required
def editar_academia(request, organizacao_slug=None, academia_id=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Editar academia - SEM campos de login/senha"""
    academia = get_object_or_404(Academia, id=academia_id, organizador=organizacao)
    
    if request.method == 'POST':
        try:
            academia.nome = request.POST.get('nome', '').strip()
            academia.cidade = request.POST.get('cidade', '').strip()
            academia.estado = request.POST.get('estado', '').strip().upper()
            academia.telefone = request.POST.get('telefone', '').strip()
            academia.responsavel = request.POST.get('responsavel', '').strip()
            academia.endereco = request.POST.get('endereco', '').strip()
            
            if request.POST.get('bonus_percentual'):
                academia.bonus_percentual = request.POST.get('bonus_percentual')
            else:
                academia.bonus_percentual = None
                
            if request.POST.get('bonus_fixo'):
                academia.bonus_fixo = request.POST.get('bonus_fixo')
            else:
                academia.bonus_fixo = None
            
            # Upload de foto (se nova foto foi enviada)
            if 'foto_perfil' in request.FILES:
                academia.foto_perfil = request.FILES['foto_perfil']
            
            academia.save()
            messages.success(request, f'Academia "{academia.nome}" atualizada com sucesso!')
            return redirect('lista_academias', organizacao_slug=organizacao.slug if organizacao else None)
        except Exception as e:
            messages.error(request, f'Erro ao atualizar academia: {str(e)}')
    
    return render(request, 'atletas/editar_academia.html', {'academia': academia})

@operacional_required
@organizacao_required
def lista_categorias(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Lista todas as categorias com filtros opcionais"""
    # Aplicar filtros
    classe_filtro = request.GET.get('classe', '').strip()
    sexo_filtro = request.GET.get('sexo', '').strip()
    categoria_filtro = request.GET.get('categoria', '').strip()
    
    # Buscar categorias com select_related para evitar N+1 queries
    categorias_query = Categoria.objects.select_related('classe').all()
    
    # Aplicar filtros
    if classe_filtro:
        categorias_query = categorias_query.filter(classe__nome=classe_filtro)
    if sexo_filtro:
        categorias_query = categorias_query.filter(sexo=sexo_filtro)
    if categoria_filtro:
        categorias_query = categorias_query.filter(
            categoria_nome__icontains=categoria_filtro
        ) | categorias_query.filter(
            label__icontains=categoria_filtro
        )
    
    categorias = categorias_query.order_by('classe__idade_min', 'sexo', 'limite_min')
    
    # Buscar classes para o filtro
    classes = Classe.objects.all().order_by('idade_min').values_list('nome', flat=True)
    
    context = {
        'categorias': categorias,
        'classes': classes,
        'classe_filtro': classe_filtro,
        'sexo_filtro': sexo_filtro,
        'categoria_filtro': categoria_filtro,
    }
    
    return render(request, 'atletas/lista_categorias.html', context)

def cadastrar_categoria(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    return render(request, 'atletas/cadastrar_categoria.html')

@operacional_required
@organizacao_required
def lista_atletas(request, organizacao_slug=None, *args, **kwargs):
    """Lista todos os atletas da organização corrente com relacionamento otimizado"""
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    atletas = Atleta.objects.select_related('academia').filter(
        academia__organizador=organizacao
    ).order_by('academia__nome', 'nome')
    context = {
        'atletas': atletas,
        'total_encontrados': atletas.count(),
    }
    return render(request, 'atletas/lista_atletas.html', context)


@operacional_required
@organizacao_required
def cadastrar_atleta(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Cadastrar novo atleta pela equipe operacional (escolhendo a academia)"""
    academias = Academia.objects.filter(
        ativo_login=True,
        organizador=organizacao
    ).order_by('nome')

    if request.method == 'POST':
        try:
            nome = request.POST.get('nome', '').strip()
            data_nascimento = request.POST.get('data_nascimento')
            sexo = request.POST.get('sexo')
            federado = request.POST.get('federado') == 'on'
            faixa = request.POST.get('faixa', '').strip() or None
            numero_zempo = request.POST.get('numero_zempo', '').strip() or None
            academia_id = request.POST.get('academia')
            telefone = request.POST.get('telefone', '').strip() or None
            pode_ser_equipe_tecnica = request.POST.get('pode_ser_equipe_tecnica') == 'on'
            funcao_equipe_tecnica = request.POST.get('funcao_equipe_tecnica', '').strip() or None
            chave_pix = request.POST.get('chave_pix', '').strip() or None
            
            if not nome or not data_nascimento or not sexo or not academia_id:
                messages.error(request, 'Preencha todos os campos obrigatórios e escolha uma academia.')
                return redirect('cadastrar_atleta', organizacao_slug=request.organizacao.slug)

            academia = Academia.objects.filter(
                id=academia_id,
                ativo_login=True,
                organizador=request.organizacao
            ).first()
            if not academia:
                messages.error(request, 'Selecione uma academia válida.')
                return redirect('cadastrar_atleta', organizacao_slug=request.organizacao.slug)

            atleta = Atleta.objects.create(
                nome=nome,
                data_nascimento=data_nascimento,
                sexo=sexo,
                academia=academia,
                federado=federado,
                faixa=faixa,
                numero_zempo=numero_zempo,
                telefone=telefone,
                pode_ser_equipe_tecnica=pode_ser_equipe_tecnica,
                funcao_equipe_tecnica=funcao_equipe_tecnica,
                chave_pix=chave_pix,
            )

            # Upload de foto
            if 'foto_perfil' in request.FILES:
                atleta.foto_perfil = request.FILES['foto_perfil']

            # Upload de documento oficial
            if 'documento_oficial' in request.FILES:
                atleta.documento_oficial = request.FILES['documento_oficial']

            atleta.save()

            messages.success(request, f'Atleta "{atleta.nome}" cadastrado com sucesso!')
            return redirect('lista_atletas', organizacao_slug=request.organizacao.slug)
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar atleta: {str(e)}')

    return render(request, 'atletas/cadastrar_atleta.html', {
        'academias': academias
    })

@organizacao_required
@operacional_ou_academia_required
def editar_atleta(request, organizacao_slug=None, atleta_id=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Editar atleta existente (academia ou operacional)"""

    if getattr(request, "academia", None):
        academia = request.academia
        atleta = get_object_or_404(Atleta, id=atleta_id, academia=academia)
    else:
        academia = None
        atleta = get_object_or_404(Atleta, id=atleta_id, academia__organizador=organizacao)

    if request.method == 'POST':
        try:
            atleta.nome = request.POST.get('nome', '').strip()
            atleta.data_nascimento = request.POST.get('data_nascimento')
            atleta.sexo = request.POST.get('sexo')
            atleta.federado = request.POST.get('federado') == 'on'
            atleta.faixa = request.POST.get('faixa', '').strip() or None
            atleta.numero_zempo = request.POST.get('numero_zempo', '').strip() or None

            # Foto
            if 'foto_perfil' in request.FILES:
                atleta.foto_perfil = request.FILES['foto_perfil']

            # Documento oficial
            if 'documento_oficial' in request.FILES:
                atleta.documento_oficial = request.FILES['documento_oficial']

            atleta.save()

            messages.success(request, f'Atleta "{atleta.nome}" atualizado!')
            return redirect('perfil_atleta', organizacao_slug=request.organizacao.slug, atleta_id=atleta.id)
        except Exception as e:
            messages.error(request, f'Erro ao atualizar atleta: {str(e)}')

    return render(request, 'atletas/editar_atleta.html', {
        'atleta': atleta,
        'academia': academia
    })


@operacional_required
@organizacao_required
def cadastrar_festival(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    return render(request, 'atletas/cadastrar_festival.html')

@operacional_required
@organizacao_required
def importar_atletas(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    return render(request, 'atletas/importar_atletas.html')

@operacional_required
@organizacao_required
def get_categorias_ajax(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    return JsonResponse({'categorias': []})

@operacional_required
@organizacao_required
def get_categorias_por_sexo(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Retorna categorias filtradas por sexo e classe, apenas com atletas com peso confirmado"""
    try:
        sexo = request.GET.get('sexo', '').strip()
        classe = request.GET.get('classe', '').strip()
        
        if not sexo:
            return JsonResponse({'categorias': []})
        
        campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
        if not campeonato_ativo:
            return JsonResponse({'categorias': []})
        
        # Buscar inscrições com peso confirmado
        inscricoes_com_peso = Inscricao.objects.filter(
            campeonato=campeonato_ativo,
            status_inscricao='aprovado',
            atleta__sexo=sexo,
            peso__isnull=False
        ).exclude(
            classe_escolhida='Festival'
        ).exclude(
            peso=0
        )
        
        # Filtrar por classe se fornecida
        if classe:
            inscricoes_com_peso = inscricoes_com_peso.filter(classe_escolhida=classe)
        
        # Obter categorias únicas (escolhida ou ajustada) que têm atletas com peso confirmado
        categorias_nomes = set()
        for insc in inscricoes_com_peso:
            if insc.categoria_escolhida:
                categorias_nomes.add(insc.categoria_escolhida)
            if insc.categoria_ajustada:
                categorias_nomes.add(insc.categoria_ajustada)
        
        # Buscar informações das categorias no banco
        from .models import Categoria
        categorias = []
        for cat_nome in sorted(categorias_nomes):
            if not cat_nome or not cat_nome.strip():
                continue
                
            # Tentar encontrar a categoria no banco
            # O nome pode estar no formato "CLASSE - Nome da Categoria"
            categoria_obj = None
            try:
                if ' - ' in cat_nome:
                    partes = cat_nome.split(' - ', 1)
                    classe_cat = partes[0].strip()
                    nome_cat = partes[1].strip()
                    categoria_obj = Categoria.objects.filter(
                        classe=classe_cat,
                        sexo=sexo,
                        nome=nome_cat
                    ).first()
                else:
                    # Tentar buscar pelo nome direto
                    categoria_obj = Categoria.objects.filter(
                        sexo=sexo,
                        nome=cat_nome
                    ).first()
                
                if categoria_obj:
                    categorias.append({
                        'nome': cat_nome,
                        'label': f"{categoria_obj.classe} - {categoria_obj.nome} ({categoria_obj.limite_min}-{categoria_obj.limite_max}kg)"
                    })
                else:
                    # Se não encontrou no banco, usar o nome como está
                    categorias.append({
                        'nome': cat_nome,
                        'label': cat_nome
                    })
            except Exception as e:
                # Em caso de erro, adicionar a categoria mesmo assim
                categorias.append({
                    'nome': cat_nome,
                    'label': cat_nome
                })
        
        return JsonResponse({'categorias': categorias})
    except Exception as e:
        import traceback
        print(f"Erro em get_categorias_por_sexo: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'categorias': [], 'error': str(e)})

def _montar_contexto_pesagem(request):
    """Monta o contexto de pesagem (desktop/mobile) já filtrando por organização."""
    organizador = getattr(request, "organizacao", None)
    campeonatos_qs = Campeonato.objects.all().order_by('-data_competicao', '-data_inicio')
    if organizador:
        campeonatos_qs = campeonatos_qs.filter(organizador=organizador)

    campeonato_id = request.GET.get('campeonato_id')
    if campeonato_id:
        try:
            campeonato_selecionado = campeonatos_qs.get(id=campeonato_id)
        except Campeonato.DoesNotExist:
            campeonato_selecionado = None
    else:
        campeonato_selecionado = campeonatos_qs.filter(ativo=True).first()
    
    if not campeonato_selecionado:
        return {
            'atletas': [],
            'campeonato_ativo': campeonatos_qs.filter(ativo=True).first(),
            'campeonato_selecionado': None,
            'campeonatos': list(campeonatos_qs),
            'classes': [],
            'categorias': [],
            'classe_filtro': '',
            'sexo_filtro': '',
            'categoria_filtro': '',
        }
    
    # Filtrar academias permitidas e confirmadas dentro do campeonato
    academias_permitidas_ids = list(AcademiaCampeonato.objects.filter(
        campeonato=campeonato_selecionado,
        permitido=True
    ).values_list('academia_id', flat=True))
    
    academias_confirmadas_ids = list(ConferenciaPagamento.objects.filter(
        campeonato=campeonato_selecionado,
        status='CONFIRMADO'
    ).values_list('academia_id', flat=True))

    inscricoes = Inscricao.objects.filter(
        campeonato=campeonato_selecionado,
        status_atual__in=['pendente', 'inscrito', 'aprovado', 'remanejado', 'desclassificado']
    ).select_related('atleta', 'atleta__academia', 'classe_real', 'categoria_real')
    
    # Mostrar apenas academias permitidas no campeonato
    if academias_permitidas_ids:
        inscricoes = inscricoes.filter(atleta__academia_id__in=academias_permitidas_ids)
    
    # Se houver conferência confirmada, prioriza filtragem; caso contrário não esvazia a lista
    if academias_confirmadas_ids:
        inscricoes = inscricoes.filter(atleta__academia_id__in=academias_confirmadas_ids)
    
    # Filtros
    classe_filtro = request.GET.get('classe', '').strip()
    sexo_filtro = request.GET.get('sexo', '').strip()
    categoria_filtro = request.GET.get('categoria', '').strip()
    
    if classe_filtro:
        inscricoes = inscricoes.filter(classe_real__nome=classe_filtro)
    if sexo_filtro:
        inscricoes = inscricoes.filter(atleta__sexo=sexo_filtro)
    if categoria_filtro:
        inscricoes = inscricoes.filter(categoria_real__categoria_nome=categoria_filtro)
    
    inscricoes = inscricoes.order_by('atleta__nome')

    atletas = []
    status_label_map = {
        'aprovado': 'OK',
        'remanejado': 'Remanejado',
        'desclassificado': 'Desclassificado',
        'pendente': 'Pendente',
        'inscrito': 'Inscrito',
    }
    for inscricao in inscricoes:
        atleta = inscricao.atleta
        categoria_nome_raw = (inscricao.categoria_real.categoria_nome if inscricao.categoria_real else '') or ''
        classe_atleta = inscricao.classe_real.nome if inscricao.classe_real else atleta.get_classe_atual()
        
        categoria_encontrada = inscricao.categoria_real
        if not categoria_encontrada and categoria_nome_raw and classe_atleta:
            categoria_encontrada = Categoria.objects.filter(
                categoria_nome=categoria_nome_raw,
                classe__nome=classe_atleta,
                sexo=atleta.sexo
            ).first()
        if not categoria_encontrada and classe_atleta:
            peso_base = inscricao.peso_real
            if peso_base is not None:
                try:
                    from decimal import Decimal
                    categoria_encontrada = calcular_categoria_por_peso(classe_atleta, atleta.sexo, Decimal(peso_base))
                except Exception:
                    categoria_encontrada = None
                
        limite_min = float(categoria_encontrada.limite_min) if categoria_encontrada else None
        limite_max = float(categoria_encontrada.limite_max) if categoria_encontrada and categoria_encontrada.limite_max is not None else None

        if categoria_encontrada:
            if limite_min == 0:
                limite_texto = f"Até {categoria_encontrada.limite_max:.1f} kg"
            elif limite_max is None or limite_max >= 999:
                limite_texto = f"+{limite_min:.1f} kg"
            else:
                limite_texto = f"{limite_min:.1f} a {limite_max:.1f} kg"
            categoria_label = categoria_encontrada.label
        else:
            limite_texto = '-'
            categoria_label = categoria_nome_raw or '-'

        historico_pesagens = list(PesagemHistorico.objects.filter(
            inscricao=inscricao,
            campeonato=campeonato_selecionado
        ).order_by('-data_hora')[:5])
        
        peso_oficial = inscricao.peso_real
        status_codigo = inscricao.status_atual
        status_pesagem = status_label_map.get(status_codigo, 'Pendente')
        peso_fora_categoria = False
        
        if peso_oficial is not None and categoria_encontrada and limite_min is not None:
            max_real = limite_max if limite_max is not None and limite_max < 999 else None
            peso_fora_categoria = not (peso_oficial >= limite_min and (max_real is None or peso_oficial <= max_real))
        
        atletas.append(SimpleNamespace(
            id=atleta.id,
            inscricao_id=inscricao.id,
            inscricao_obj=inscricao,
            nome=atleta.nome,
            academia=atleta.academia,
            sexo=atleta.sexo,
            classe=classe_atleta,
            categoria_nome=categoria_nome_raw,
            categoria_ajustada=categoria_nome_raw,
            categoria_label=categoria_label,
            categoria_real_nome=categoria_encontrada.categoria_nome if categoria_encontrada else categoria_nome_raw or '',
            limite_categoria_real=limite_texto,
            limite_min=limite_min,
            limite_max=limite_max,
            limite_texto=limite_texto,
            peso_oficial=peso_oficial,
            remanejado=inscricao.remanejado,
            motivo_ajuste=inscricao.motivo_ajuste or '',
            status=status_pesagem,
            status_codigo=status_codigo,
            peso_fora_categoria=peso_fora_categoria,
            historico_pesagens=historico_pesagens,
            get_sexo_display=atleta.get_sexo_display,
            bloqueado_chave=inscricao.bloqueado_chave,
        ))

    classes = sorted(set(Inscricao.objects.filter(
        campeonato=campeonato_selecionado, 
        status_atual__in=['aprovado', 'remanejado']
    ).exclude(classe_real__isnull=True).values_list('classe_real__nome', flat=True).distinct()))
    
    categorias = sorted(set(Inscricao.objects.filter(
        campeonato=campeonato_selecionado, 
        status_atual__in=['aprovado', 'remanejado']
    ).exclude(categoria_real__isnull=True).values_list('categoria_real__categoria_nome', flat=True).distinct()))
    
    return {
        'atletas': atletas,
        'campeonato_ativo': campeonatos_qs.filter(ativo=True).first(),
        'campeonato_selecionado': campeonato_selecionado,
        'campeonatos': list(campeonatos_qs),
        'classes': classes,
        'categorias': categorias,
        'classe_filtro': classe_filtro,
        'sexo_filtro': sexo_filtro,
        'categoria_filtro': categoria_filtro,
    }
    
@operacional_required
@organizacao_required
def pesagem(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    context = _montar_contexto_pesagem(request)
    if not context.get('campeonato_selecionado'):
        messages.warning(request, 'Nenhum evento selecionado ou encontrado.')
    return render(request, 'atletas/pesagem.html', context)

@operacional_required
@organizacao_required
def pesagem_mobile_view(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    context = _montar_contexto_pesagem(request)
    if not context.get('campeonato_selecionado'):
        messages.warning(request, 'Nenhum evento selecionado ou encontrado.')
    return render(request, 'atletas/pesagem_mobile.html', context)

@operacional_required
@organizacao_required
@require_http_methods(["POST"])
def registrar_peso(request, organizacao_slug=None, inscricao_id=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Registra peso oficial de uma inscrição. Fora do limite: não salva, retorna decisão."""
    try:
        inscricao = get_object_or_404(
            Inscricao,
            id=inscricao_id,
            campeonato__organizador=organizacao
        )
        from decimal import Decimal, InvalidOperation
        try:
            peso_oficial = Decimal(str(request.POST.get('peso_oficial', '0'))).quantize(Decimal('0.1'))
        except (InvalidOperation, ValueError):
            return JsonResponse({'success': False, 'message': 'Peso inválido. Use apenas números.'})

        observacoes = request.POST.get('observacoes', '').strip()
        if peso_oficial <= 0:
            return JsonResponse({'success': False, 'message': 'Peso inválido. Deve ser maior que zero.'})

        resultado = service_registrar_peso(
            inscricao,
            peso_oficial,
            observacoes=observacoes,
            usuario=request.user
        )

        if resultado.get('categoria_ok'):
            # Atualizar status_atual para aprovado
            try:
                service_aprovar(inscricao, peso_oficial)
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'Erro ao aprovar inscrição: {e}'})

            return JsonResponse({
                'success': True,
                'categoria_ok': True,
                'status_pesagem': resultado.get('status_pesagem'),
                'categoria_encontrada': resultado.get('categoria_encontrada'),
                'limite_min': float(resultado.get('limite_min')) if resultado.get('limite_min') is not None else None,
                'limite_max': float(resultado.get('limite_max')) if resultado.get('limite_max') is not None else None,
                'organizacao_slug': request.organizacao.slug if getattr(request, "organizacao", None) else '',
            })

        resultado.update({
            'success': True,
            'inscricao_id': inscricao.id,
            'atleta_nome': inscricao.atleta.nome,
            'peso': float(peso_oficial),
            'opcoes': ['remanejamento', 'desclassificacao'],
            'organizacao_slug': request.organizacao.slug if getattr(request, "organizacao", None) else '',
            'limite_atual_min': float(resultado.get('limite_atual_min')) if resultado.get('limite_atual_min') is not None else None,
            'limite_atual_max': float(resultado.get('limite_atual_max')) if resultado.get('limite_atual_max') is not None else None,
            'limite_novo_min': float(resultado.get('limite_novo_min')) if resultado.get('limite_novo_min') is not None else None,
            'limite_novo_max': float(resultado.get('limite_novo_max')) if resultado.get('limite_novo_max') is not None else None,
        })
        return JsonResponse(resultado)
        
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Peso inválido. Use apenas números.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erro ao registrar peso: {str(e)}'})

@operacional_required
@organizacao_required
def confirmar_remanejamento(request, organizacao_slug=None, inscricao_id=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido.'}, status=405)

    try:
        inscricao = get_object_or_404(
            Inscricao,
            id=inscricao_id,
            campeonato__organizador=organizacao
        )

        acao = request.POST.get('acao')
        categoria_nova_nome = request.POST.get('categoria_nova', '').strip()
        observacoes = request.POST.get('observacoes', '').strip()
        from decimal import Decimal, InvalidOperation
        try:
            peso = Decimal(str(request.POST.get('peso_oficial') or '0')).quantize(Decimal('0.1'))
        except (InvalidOperation, ValueError):
            return JsonResponse({'success': False, 'message': 'Peso inválido.'}, status=400)

        categoria_sugerida = None
        if categoria_nova_nome:
            categoria_sugerida = Categoria.objects.filter(
                categoria_nome=categoria_nova_nome,
                classe=inscricao.classe_real,
                sexo=inscricao.atleta.sexo
            ).first()

        status_final, categoria_final = service_confirmar_remanejamento(
            inscricao,
            peso,
            acao,
            categoria_sugerida=categoria_sugerida,
            observacoes=observacoes,
            usuario=request.user
        )

        registrar_historico(
            tipo_acao='PESAGEM',
            descricao=f'Pesagem confirmada: {inscricao.atleta.nome} - {peso}kg - Ação: {acao}',
            usuario=request.user if request.user.is_authenticated else None,
            campeonato=inscricao.campeonato,
            academia=inscricao.atleta.academia,
            atleta=inscricao.atleta,
            dados_extras={'acao': acao, 'peso': peso, 'categoria_nova': categoria_nova_nome},
            request=request
        )

        return JsonResponse({
            'success': True,
            'status_final': status_final,
            'categoria_nova': categoria_final.categoria_nome if categoria_final else None,
            'organizacao_slug': request.organizacao.slug if getattr(request, "organizacao", None) else '',
        })
    except Exception as exc:
        return JsonResponse({'success': False, 'message': f'Erro ao confirmar remanejamento: {exc}'})

@operacional_required
@organizacao_required
def rebaixar_categoria(request, organizacao_slug=None, atleta_id=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    return JsonResponse({'success': False})

@operacional_required
@organizacao_required
def lista_chaves(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    """Lista todas as chaves do campeonato ativo"""
    organizador = getattr(request, "organizacao", None)
    campeonato_ativo = Campeonato.objects.filter(ativo=True, organizador=organizador) if organizador else Campeonato.objects.filter(ativo=True)
    campeonato_ativo = campeonato_ativo.first()
    
    if not campeonato_ativo:
        messages.warning(request, 'Nenhum campeonato ativo encontrado.')
        return render(request, 'atletas/lista_chaves.html', {
            'chaves': [],
            'campeonato_ativo': None,
            'total_chaves': 0,
            'classes': [],
            'categorias': [],
        })
    
    # Buscar chaves do campeonato ativo
    chaves_query = Chave.objects.filter(campeonato=campeonato_ativo).select_related('campeonato').order_by('classe', 'sexo', 'categoria')
    
    # Aplicar filtros
    classe_filtro = request.GET.get('classe', '').strip()
    sexo_filtro = request.GET.get('sexo', '').strip()
    categoria_filtro = request.GET.get('categoria', '').strip()
    
    if classe_filtro:
        chaves_query = chaves_query.filter(classe=classe_filtro)
    if sexo_filtro:
        chaves_query = chaves_query.filter(sexo=sexo_filtro)
    if categoria_filtro:
        chaves_query = chaves_query.filter(categoria=categoria_filtro)
    
    chaves = list(chaves_query)
    
    # Obter classes, sexos e categorias disponíveis
    classes = sorted(set(Chave.objects.filter(campeonato=campeonato_ativo).exclude(classe='').values_list('classe', flat=True).distinct()))
    categorias = sorted(set(Chave.objects.filter(campeonato=campeonato_ativo).exclude(categoria='').values_list('categoria', flat=True).distinct()))
    
    context = {
        'chaves': chaves,
        'campeonato_ativo': campeonato_ativo,
        'total_chaves': len(chaves),
        'classes': classes,
        'categorias': categorias,
        'classe_filtro': classe_filtro,
        'sexo_filtro': sexo_filtro,
        'categoria_filtro': categoria_filtro,
    }
    
    return render(request, 'atletas/lista_chaves.html', context)

@operacional_required
@organizacao_required
def gerar_chave_view(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    """Gerar chave - mostra apenas classes/categorias com atletas com peso confirmado"""
    organizador = getattr(request, "organizacao", None)
    campeonato_ativo = Campeonato.objects.filter(ativo=True, organizador=organizador) if organizador else Campeonato.objects.filter(ativo=True)
    campeonato_ativo = campeonato_ativo.first()
    
    if not campeonato_ativo:
        messages.warning(request, 'Nenhum campeonato ativo encontrado.')
        return redirect('lista_campeonatos', organizacao_slug=request.organizacao.slug)
    
    # Processar POST para gerar chave
    if request.method == 'POST':
        classe = request.POST.get('classe', '').strip()
        sexo = request.POST.get('sexo', '').strip()
        categoria_nome = request.POST.get('categoria', '').strip()
        modelo_chave = request.POST.get('modelo_chave', 'automatico')
        
        if not classe or not sexo or not categoria_nome:
            messages.error(request, 'Preencha todos os campos obrigatórios.')
        else:
            try:
                from .utils import gerar_chave
                chave = gerar_chave(
                    categoria_nome=categoria_nome,
                    classe=classe,
                    sexo=sexo,
                    modelo_chave=modelo_chave if modelo_chave != 'automatico' else None,
                    campeonato=campeonato_ativo
                )
                messages.success(request, f'Chave gerada com sucesso para {categoria_nome}!')
                return redirect('detalhe_chave', organizacao_slug=request.organizacao.slug, chave_id=chave.id)
            except Exception as e:
                messages.error(request, f'Erro ao gerar chave: {str(e)}')
    
    # GET: Buscar classes que têm atletas aptos (novo modelo normalizado)
    inscricoes_com_peso = Inscricao.objects.filter(
        campeonato=campeonato_ativo,
        status_atual__in=['aprovado', 'remanejado'],
        peso_real__isnull=False,
        bloqueado_chave=False,
        classe_real__isnull=False,
        categoria_real__isnull=False
    ).exclude(
        classe_real__nome__iexact='Festival'
    ).exclude(
        peso_real=0
    )
    
    # Obter classes únicas que têm atletas aptos
    classes_com_peso = sorted(set(inscricoes_com_peso.values_list('classe_real__nome', flat=True).distinct()))
    
    context = {
        'classes': classes_com_peso,
        'campeonato_ativo': campeonato_ativo,
    }
    
    return render(request, 'atletas/gerar_chave.html', context)

@operacional_required
@organizacao_required
def gerar_todas_chaves(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    """Gera todas as chaves possíveis de uma única vez"""
    organizador = getattr(request, "organizacao", None)
    campeonato_ativo = Campeonato.objects.filter(ativo=True, organizador=organizador) if organizador else Campeonato.objects.filter(ativo=True)
    campeonato_ativo = campeonato_ativo.first()
    
    if not campeonato_ativo:
        messages.error(request, 'Nenhum campeonato ativo encontrado.')
        return redirect('lista_chaves', organizacao_slug=request.organizacao.slug)
    
    # Buscar todas as combinações únicas de classe, sexo e categoria
    # que têm inscrições aprovadas/remanejadas com peso confirmado (normalizado)
    base_qs = Inscricao.objects.filter(
        campeonato=campeonato_ativo,
        classe_real__isnull=False,
        categoria_real__isnull=False
    ).exclude(
        classe_real__nome__iexact='Festival'
    )

    inscricoes_aptas = base_qs.filter(
        status_inscricao__in=['aprovado', 'remanejado'],
        bloqueado_chave=False,
        peso_real__gt=0
    )
    
    # Agrupar por classe, sexo e categoria (usando campos normalizados)
    combinacoes = {}
    for inscricao in inscricoes_aptas:
        classe = inscricao.classe_real.nome if inscricao.classe_real else ''
        sexo = inscricao.atleta.sexo
        categoria = inscricao.categoria_real.categoria_nome if inscricao.categoria_real else ''
        
        if not categoria:
            continue
        
        chave_combinacao = (classe, sexo, categoria)
        if chave_combinacao not in combinacoes:
            combinacoes[chave_combinacao] = {
                'classe': classe,
                'sexo': sexo,
                'categoria': categoria,
                'count': 0
            }
        combinacoes[chave_combinacao]['count'] += 1
    
    # Gerar chaves para cada combinação
    chaves_criadas = 0
    chaves_atualizadas = 0
    chaves_erro = []
    
    for combinacao in combinacoes.values():
        try:
            # Verificar se chave já existe
            chave_existente = Chave.objects.filter(
                campeonato=campeonato_ativo,
                classe=combinacao['classe'],
                sexo=combinacao['sexo'],
                categoria=combinacao['categoria']
            ).first()
            
            # Gerar chave (a função gerar_chave cria ou atualiza automaticamente)
            chave = gerar_chave(
                categoria_nome=combinacao['categoria'],
                classe=combinacao['classe'],
                sexo=combinacao['sexo'],
                modelo_chave=None,  # Automático
                campeonato=campeonato_ativo
            )
            
            if chave_existente:
                chaves_atualizadas += 1
            else:
                chaves_criadas += 1
                
        except Exception as e:
            chaves_erro.append({
                'combinacao': f"{combinacao['classe']} - {combinacao['sexo']} - {combinacao['categoria']}",
                'erro': str(e)
            })

    # Log simples para diagnóstico em dev
    total_combinacoes = len(combinacoes)
    total_inscricoes = inscricoes_aptas.count()
    print(f"[GERAR TODAS CHAVES] inscricoes_aptas={total_inscricoes} combinacoes={total_combinacoes} criadas={chaves_criadas} atualizadas={chaves_atualizadas} erros={len(chaves_erro)}")
    
    # Mensagem de sucesso
    if chaves_criadas > 0 or chaves_atualizadas > 0:
        mensagem = f"✅ {chaves_criadas} chave(s) criada(s) e {chaves_atualizadas} chave(s) atualizada(s) com sucesso!"
        if chaves_erro:
            mensagem += f" ⚠️ {len(chaves_erro)} erro(s) encontrado(s)."
        messages.success(request, mensagem)
    else:
        messages.warning(request, 'Nenhuma chave foi gerada. Verifique se há inscrições aprovadas com peso confirmado.')
    
    if chaves_erro:
        for erro in chaves_erro[:5]:  # Mostrar apenas os 5 primeiros erros
            messages.error(request, f"Erro em {erro['combinacao']}: {erro['erro']}")
    
    return redirect('lista_chaves', organizacao_slug=request.organizacao.slug)

@operacional_required
@organizacao_required
def gerar_chave_manual(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    """Gerar lutas casadas (chave manual) - apenas atletas com peso confirmado"""
    organizador = getattr(request, "organizacao", None)
    campeonato_ativo = Campeonato.objects.filter(ativo=True, organizador=organizador) if organizador else Campeonato.objects.filter(ativo=True)
    campeonato_ativo = campeonato_ativo.first()
    
    if not campeonato_ativo:
        messages.warning(request, 'Nenhum campeonato ativo encontrado.')
        return redirect('lista_campeonatos')
    
    # Processar POST para criar chave manual
    if request.method == 'POST':
        nome_chave = request.POST.get('nome_chave', '').strip()
        classe_chave = request.POST.get('classe_chave', '').strip()
        sexo_chave = request.POST.get('sexo_chave', '').strip()
        atletas_ids = request.POST.getlist('atletas')
        
        if not nome_chave or not sexo_chave or not atletas_ids:
            messages.error(request, 'Preencha todos os campos obrigatórios e selecione pelo menos um atleta.')
        else:
            try:
                from .models import Chave, Luta
                
                # Criar chave manual
                chave = Chave.objects.create(
                    campeonato=campeonato_ativo,
                    classe=classe_chave or 'Lutas Casadas',
                    sexo=sexo_chave,
                    categoria=nome_chave,
                    estrutura={'tipo': 'manual', 'atletas': len(atletas_ids)}
                )
                
                # Adicionar atletas à chave
                atletas = Atleta.objects.filter(id__in=atletas_ids)
                chave.atletas.set(atletas)
                
                # Criar lutas pareadas (1x2, 3x4, 5x6, etc.)
                atletas_list = list(atletas)
                lutas_criadas = []
                for i in range(0, len(atletas_list), 2):
                    atleta_a = atletas_list[i] if i < len(atletas_list) else None
                    atleta_b = atletas_list[i + 1] if i + 1 < len(atletas_list) else None
                    
                    if atleta_a or atleta_b:
                        luta = Luta.objects.create(
                            chave=chave,
                            atleta_a=atleta_a,
                            atleta_b=atleta_b,
                            round=1
                        )
                        lutas_criadas.append(luta.id)
                
                # Atualizar estrutura da chave
                chave.estrutura = {
                    'tipo': 'manual',
                    'atletas': len(atletas_list),
                    'lutas': lutas_criadas,
                    'rounds': {1: lutas_criadas}
                }
                chave.save()
                
                messages.success(request, f'Chave "{nome_chave}" criada com sucesso!')
                return redirect('detalhe_chave', chave_id=chave.id)
            except Exception as e:
                messages.error(request, f'Erro ao criar chave: {str(e)}')
    
    # GET: Buscar atletas com peso confirmado
    # Filtros
    nome_filtro = request.GET.get('nome', '').strip()
    classe_filtro = request.GET.get('classe', '').strip()
    sexo_filtro = request.GET.get('sexo', '').strip()
    academia_filtro = request.GET.get('academia', '').strip()
    
    # Buscar inscrições com peso confirmado
    inscricoes = Inscricao.objects.filter(
        campeonato=campeonato_ativo,
        status_inscricao='aprovado',
        peso__isnull=False
    ).exclude(
        peso=0
    ).select_related('atleta', 'atleta__academia')
    
    # Aplicar filtros
    if nome_filtro:
        inscricoes = inscricoes.filter(atleta__nome__icontains=nome_filtro)
    if classe_filtro:
        inscricoes = inscricoes.filter(classe_escolhida=classe_filtro)
    if sexo_filtro:
        inscricoes = inscricoes.filter(atleta__sexo=sexo_filtro)
    if academia_filtro:
        inscricoes = inscricoes.filter(atleta__academia_id=academia_filtro)
    
    # Extrair atletas únicos
    atletas_ids = inscricoes.values_list('atleta_id', flat=True).distinct()
    atletas = Atleta.objects.filter(id__in=atletas_ids).select_related('academia').order_by('nome')
    
    # Obter classes e academias para filtros
    classes = sorted(set(inscricoes.values_list('classe_escolhida', flat=True).distinct()))
    academias = Academia.objects.filter(
        id__in=inscricoes.values_list('atleta__academia_id', flat=True).distinct()
    ).order_by('nome')
    
    context = {
        'atletas': atletas,
        'classes': classes,
        'academias': academias,
        'nome_filtro': nome_filtro,
        'classe_filtro': classe_filtro,
        'sexo_filtro': sexo_filtro,
        'academia_filtro': academia_filtro,
        'campeonato_ativo': campeonato_ativo,
    }
    
    return render(request, 'atletas/gerar_chave_manual.html', context)

@operacional_required
@organizacao_required
def detalhe_chave(request, organizacao_slug=None, chave_id=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Exibe detalhes da chave com lutas e resultados"""
    chave = get_object_or_404(Chave, id=chave_id, campeonato__organizador=organizacao) if organizacao else get_object_or_404(Chave, id=chave_id)
    
    # Buscar lutas da chave ordenadas por round e ID
    lutas = chave.lutas.all().order_by('round', 'id').select_related('atleta_a', 'atleta_b', 'vencedor', 'atleta_a__academia', 'atleta_b__academia')
    
    # Buscar resultados finais usando a função utilitária
    from .utils import get_resultados_chave
    resultados_ids = get_resultados_chave(chave)
    
    # Converter IDs de resultados em objetos Atleta com academias
    resultados = []
    for atleta_id in resultados_ids:
        try:
            atleta = Atleta.objects.select_related('academia').get(id=atleta_id)
            resultados.append(atleta)
        except Atleta.DoesNotExist:
            continue
    
    context = {
        'chave': chave,
        'lutas': lutas,
        'resultados': resultados,
    }
    
    return render(request, 'atletas/detalhe_chave.html', context)

@operacional_required
@organizacao_required
def imprimir_chave(request, organizacao_slug=None, chave_id=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """View para impressão de chave - layout minimalista para anotação manual"""
    chave = get_object_or_404(Chave, id=chave_id, campeonato__organizador=organizacao) if organizacao else get_object_or_404(Chave, id=chave_id)
    
    # Obter tipo da chave da estrutura
    estrutura = chave.estrutura or {}
    tipo_chave = estrutura.get('tipo', 'vazia')
    
    # Obter lista de atletas (apenas para contar, não mostrar nomes)
    lista_atletas = list(chave.atletas.all())
    num_atletas = len(lista_atletas)
    
    # Determinar número de atletas para estrutura eliminatória
    if tipo_chave in ['eliminatoria_repescagem', 'eliminatoria_simples']:
        tamanho_chave = estrutura.get('tamanho_chave', num_atletas)
        if tamanho_chave < 8:
            tamanho_chave = 8
        elif tamanho_chave < 16:
            tamanho_chave = 16
        else:
            tamanho_chave = 32
    else:
        tamanho_chave = num_atletas
    
    context = {
        'chave': chave,
        'tipo_chave': tipo_chave,
        'lista_atletas': lista_atletas,  # Para contar linhas na tabela round-robin
        'num_atletas': num_atletas,
        'tamanho_chave': tamanho_chave,
    }
    
    return render(request, 'atletas/imprimir_chave.html', context)

@operacional_required
@organizacao_required
def chave_mobile_view(request, organizacao_slug=None, chave_id=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    chave = get_object_or_404(Chave, id=chave_id, campeonato__organizador=organizacao) if organizacao else get_object_or_404(Chave, id=chave_id)
    return render(request, 'atletas/chave_mobile.html', {'chave': chave})

@operacional_required
@organizacao_required
def registrar_vencedor(request, organizacao_slug=None, luta_id=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Registra o vencedor de uma luta e atualiza a chave"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método não permitido'})
    
    try:
        luta = get_object_or_404(Luta, id=luta_id)
        
        # Validar que a luta tem dois atletas
        if not luta.atleta_a or not luta.atleta_b:
            return JsonResponse({
                'success': False,
                'message': 'Luta não pode ser registrada: faltam atletas'
            })
        
        # Validar que a luta não está concluída
        if luta.concluida:
            return JsonResponse({
                'success': False,
                'message': 'Esta luta já foi concluída'
            })
        
        # Obter dados do POST
        vencedor_id = request.POST.get('vencedor')
        tipo_vitoria = request.POST.get('tipo_vitoria', 'IPPON')
        
        if not vencedor_id:
            return JsonResponse({
                'success': False,
                'message': 'Selecione o vencedor'
            })
        
        # Validar que o vencedor é um dos atletas da luta
        vencedor_id = int(vencedor_id)
        if vencedor_id not in [luta.atleta_a.id, luta.atleta_b.id]:
            return JsonResponse({
                'success': False,
                'message': 'Vencedor inválido: deve ser um dos atletas da luta'
            })
        
        # Obter objeto do vencedor
        vencedor = Atleta.objects.get(id=vencedor_id)
        perdedor = luta.atleta_b if vencedor_id == luta.atleta_a.id else luta.atleta_a
        
        # Calcular pontos baseado no tipo de vitória
        pontos_vencedor = 0
        pontos_perdedor = 0
        ippon_count = 0
        wazari_count = 0
        yuko_count = 0
        
        if tipo_vitoria == 'IPPON':
            pontos_vencedor = 10
            pontos_perdedor = 0
            ippon_count = 1
        elif tipo_vitoria == 'WAZARI' or tipo_vitoria == 'WAZARI_WAZARI':
            pontos_vencedor = 7
            pontos_perdedor = 0
            wazari_count = 1 if tipo_vitoria == 'WAZARI' else 2
        elif tipo_vitoria == 'YUKO':
            pontos_vencedor = 1
            pontos_perdedor = 0
            yuko_count = 1
        
        # Atualizar luta
        luta.vencedor = vencedor
        luta.tipo_vitoria = tipo_vitoria
        luta.pontos_vencedor = pontos_vencedor
        luta.pontos_perdedor = pontos_perdedor
        luta.ippon_count = ippon_count
        luta.wazari_count = wazari_count
        luta.yuko_count = yuko_count
        luta.concluida = True
        luta.save()
        
        # Atualizar próxima luta e repescagem
        from .utils import atualizar_proxima_luta
        atualizar_proxima_luta(luta)
        
        # Registrar histórico
        from .utils_historico import registrar_historico
        campeonato = luta.chave.campeonato if luta.chave.campeonato else None
        registrar_historico(
            tipo_acao='LUTA_REGISTRADA',
            descricao=f'Luta registrada: {vencedor.nome} venceu {perdedor.nome} por {luta.get_tipo_vitoria_display()} na chave {luta.chave.categoria}',
            usuario=request.user if request.user.is_authenticated else None,
            campeonato=campeonato,
            dados_extras={
                'luta_id': luta.id,
                'vencedor_id': vencedor.id,
                'perdedor_id': perdedor.id,
                'tipo_vitoria': tipo_vitoria,
                'pontos_vencedor': pontos_vencedor
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Resultado registrado: {vencedor.nome} venceu por {luta.get_tipo_vitoria_display()}',
            'vencedor': {
                'id': vencedor.id,
                'nome': vencedor.nome
            },
            'tipo_vitoria': tipo_vitoria,
            'pontos': pontos_vencedor
        })
        
    except Atleta.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Atleta não encontrado'
        })
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': f'Erro de validação: {str(e)}'
        })
    except Exception as e:
        import traceback
        print(f"ERRO ao registrar vencedor: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'Erro ao registrar resultado: {str(e)}'
        })

@operacional_required
@organizacao_required
def luta_mobile_view(request, organizacao_slug=None, luta_id=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    return render(request, 'atletas/luta_mobile.html', {'luta': get_object_or_404(Luta, id=luta_id)})

@operacional_required
@organizacao_required
def ranking_global(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Ranking global de atletas e academias"""
    campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
    
    if not campeonato_ativo:
        messages.warning(request, 'Nenhum campeonato ativo encontrado.')
        return render(request, 'atletas/ranking_global.html', {
            'campeonato_ativo': None,
            'ranking_atletas_completo': [],
            'top3_academias': [],
            'total_academias': 0,
            'classes_disponiveis': [],
            'categorias_disponiveis': [],
        })
    
    # Aplicar filtros
    classe_filtro = request.GET.get('classe', '').strip()
    sexo_filtro = request.GET.get('sexo', '').strip()
    categoria_filtro = request.GET.get('categoria', '').strip()
    
    # Calcular pontuação das academias primeiro
    calcular_pontuacao_academias(campeonato_ativo.id)
    
    # Buscar pontuações de academias
    pontuacoes = AcademiaPontuacao.objects.filter(
        campeonato=campeonato_ativo
    ).select_related('academia').order_by('-pontos_totais', '-ouro', '-prata', '-bronze')
    
    # Preparar ranking completo de academias
    ranking_academias_completo = []
    for pontuacao in pontuacoes:
        ranking_academias_completo.append({
            'academia': pontuacao.academia,
            'ouro': pontuacao.ouro,
            'prata': pontuacao.prata,
            'bronze': pontuacao.bronze,
            'festival': pontuacao.festival or 0,
            'pontos_totais': pontuacao.pontos_totais,
        })
    
    # Top 3 academias para os cards
    top3_academias = ranking_academias_completo[:3]
    
    # Buscar resultados de todas as chaves para calcular ranking de atletas
    chaves = Chave.objects.filter(campeonato=campeonato_ativo)
    
    # Contar medalhas por atleta
    medalhas_por_atleta = {}
    
    for chave in chaves:
        resultados = get_resultados_chave(chave)
        if not resultados:
            continue
        
        # 1º lugar = ouro, 2º lugar = prata, 3º lugar = bronze
        for idx, atleta_id in enumerate(resultados[:3], 1):
            if not atleta_id:
                continue
            
            if atleta_id not in medalhas_por_atleta:
                try:
                    atleta = Atleta.objects.get(id=atleta_id)
                    medalhas_por_atleta[atleta_id] = {
                        'atleta': atleta,
                        'ouro': 0,
                        'prata': 0,
                        'bronze': 0,
                        'total_medalhas': 0,
                    }
                except Atleta.DoesNotExist:
                    continue
            
            if idx == 1:
                medalhas_por_atleta[atleta_id]['ouro'] += 1
            elif idx == 2:
                medalhas_por_atleta[atleta_id]['prata'] += 1
            elif idx == 3:
                medalhas_por_atleta[atleta_id]['bronze'] += 1
            
            medalhas_por_atleta[atleta_id]['total_medalhas'] = (
                medalhas_por_atleta[atleta_id]['ouro'] +
                medalhas_por_atleta[atleta_id]['prata'] +
                medalhas_por_atleta[atleta_id]['bronze']
            )
    
    # Ordenar por total de medalhas (ouro > prata > bronze)
    ranking_atletas_completo = sorted(
        medalhas_por_atleta.values(),
        key=lambda x: (x['total_medalhas'], x['ouro'], x['prata'], x['bronze']),
        reverse=True
    )
    
    # Top 3 atletas para os cards
    top3_atletas = ranking_atletas_completo[:3]
    
    # Aplicar filtros ao ranking de atletas
    if classe_filtro or sexo_filtro or categoria_filtro:
        ranking_atletas_filtrado = []
        for item in ranking_atletas_completo:
            atleta = item['atleta']
            
            # Filtrar por classe (buscar na inscrição do campeonato)
            if classe_filtro:
                inscricao = Inscricao.objects.filter(
                    atleta=atleta,
                    campeonato=campeonato_ativo,
                    classe_escolhida=classe_filtro
                ).first()
                if not inscricao:
                    continue
            
            # Filtrar por sexo
            if sexo_filtro and atleta.sexo != sexo_filtro:
                continue
            
            # Filtrar por categoria (buscar na inscrição do campeonato)
            if categoria_filtro:
                inscricao = Inscricao.objects.filter(
                    atleta=atleta,
                    campeonato=campeonato_ativo
                ).first()
                if not inscricao or categoria_filtro not in inscricao.categoria_escolhida:
                    continue
            
            ranking_atletas_filtrado.append(item)
        
        ranking_atletas_completo = ranking_atletas_filtrado
        top3_atletas = ranking_atletas_completo[:3]
    
    # Obter classes e categorias disponíveis
    classes_disponiveis = sorted(set(chaves.exclude(classe='').values_list('classe', flat=True).distinct()))
    categorias_disponiveis = sorted(set(chaves.exclude(categoria='').values_list('categoria', flat=True).distinct()))
    
    context = {
        'campeonato_ativo': campeonato_ativo,
        'ranking_atletas_completo': ranking_atletas_completo,
        'top3_atletas': top3_atletas,  # Top 3 para os cards
        'ranking_academias_completo': ranking_academias_completo,  # Lista completa para a tabela
        'top3_academias': top3_academias,  # Top 3 para os cards
        'total_academias': len(ranking_academias_completo),
        'total_atletas': len(ranking_atletas_completo),
        'classes_disponiveis': classes_disponiveis,
        'categorias_disponiveis': categorias_disponiveis,
        'classe_filtro': classe_filtro,
        'sexo_filtro': sexo_filtro,
        'categoria_filtro': categoria_filtro,
    }
    
    return render(request, 'atletas/ranking_global.html', context)

@operacional_required
@organizacao_required
def ranking_academias(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Ranking de academias - calcula pontuação baseada em resultados"""
    campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
    
    if not campeonato_ativo:
        messages.warning(request, 'Nenhum campeonato ativo encontrado.')
        return render(request, 'atletas/ranking_academias.html', {
            'campeonato_ativo': None,
            'ranking_academias': [],
            'top3_academias': [],
            'total_academias': 0,
        })
    
    # Calcular pontuação das academias
    calcular_pontuacao_academias(campeonato_ativo.id)
    
    # Buscar apenas academias permitidas no campeonato
    academias_permitidas_ids = list(AcademiaCampeonato.objects.filter(
        campeonato=campeonato_ativo,
        permitido=True
    ).values_list('academia_id', flat=True))
    
    # Buscar pontuações do campeonato
    pontuacoes = AcademiaPontuacao.objects.filter(
        campeonato=campeonato_ativo
    ).select_related('academia')
    
    # Se houver academias permitidas, filtrar por elas
    if academias_permitidas_ids:
        pontuacoes = pontuacoes.filter(academia_id__in=academias_permitidas_ids)
    
    pontuacoes = pontuacoes.order_by('-pontos_totais', '-ouro', '-prata', '-bronze')
    
    # Preparar dados para o template
    ranking_academias_list = []
    for pontuacao in pontuacoes:
        ranking_academias_list.append({
            'academia': pontuacao.academia,
            'ouro': pontuacao.ouro,
            'prata': pontuacao.prata,
            'bronze': pontuacao.bronze,
            'quarto': pontuacao.quarto,
            'quinto': pontuacao.quinto,
            'festival': pontuacao.festival,
            'remanejamento': pontuacao.remanejamento,
            'pontos_totais': pontuacao.pontos_totais,
        })
    
    # Top 3 academias
    top3_academias = ranking_academias_list[:3]
    
    context = {
        'campeonato': campeonato_ativo,
        'academias_ranking': ranking_academias_list,
        'top3': top3_academias,
        'total_academias': len(ranking_academias_list),
    }
    
    return render(request, 'atletas/ranking_academias.html', context)

@operacional_required
@organizacao_required
def calcular_pontuacao(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Recalcular pontuação das academias e redirecionar para ranking"""
    campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
    
    if campeonato_ativo:
        calcular_pontuacao_academias(campeonato_ativo.id)
        messages.success(request, 'Pontuação recalculada com sucesso!')
    else:
        messages.warning(request, 'Nenhum campeonato ativo encontrado.')
    
    return redirect('ranking_academias', organizacao_slug=request.organizacao.slug)

@operacional_required
@organizacao_required
def api_ranking_academias(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    return JsonResponse({'academias': []})

@organizacao_required
def perfil_atleta(request, organizacao_slug=None, atleta_id=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    atleta = get_object_or_404(Atleta, id=atleta_id, academia__organizador=organizacao)
    
    # Buscar histórico de competições do atleta
    historico = []
    
    # Buscar todas as inscrições do atleta
    inscricoes = Inscricao.objects.filter(
        atleta=atleta,
        status_inscricao='aprovado'
    ).select_related('campeonato')
    
    # Para cada inscrição, buscar a chave correspondente e os resultados
    from .utils import get_resultados_chave
    from .models import Chave
    
    for inscricao in inscricoes:
        # Buscar chave do atleta neste campeonato
        # A chave pode ter sido criada com categoria_ajustada ou categoria_escolhida
        categoria_busca = inscricao.categoria_ajustada or inscricao.categoria_escolhida
        
        chave = Chave.objects.filter(
            campeonato=inscricao.campeonato,
            classe=inscricao.classe_escolhida,
            categoria=categoria_busca
        ).first()
        
        # Se não encontrou, tentar buscar pela categoria escolhida
        if not chave and inscricao.categoria_ajustada:
            chave = Chave.objects.filter(
                campeonato=inscricao.campeonato,
                classe=inscricao.classe_escolhida,
                categoria=inscricao.categoria_escolhida
            ).first()
        
        if chave:
            # Verificar se o atleta participou desta chave
            # Pode estar na lista de atletas da chave ou ter participado de lutas
            atleta_participou = (
                chave.atletas.filter(id=atleta.id).exists() or
                chave.lutas.filter(
                    Q(atleta_a=atleta) | Q(atleta_b=atleta)
                ).exists()
            )
            
            if atleta_participou:
                # Buscar resultados da chave
                resultados_ids = get_resultados_chave(chave)
                
                # Verificar se o atleta está nos resultados e qual a posição
                if atleta.id in resultados_ids:
                    posicao = resultados_ids.index(atleta.id) + 1
                    
                    # Determinar medalha baseado na posição
                    medalha = None
                    if posicao == 1:
                        medalha = 'ouro'
                    elif posicao == 2:
                        medalha = 'prata'
                    elif posicao == 3:
                        medalha = 'bronze'
                    
                    # Adicionar ao histórico
                    historico.append({
                        'campeonato': inscricao.campeonato,
                        'ano': inscricao.campeonato.data_competicao.year if inscricao.campeonato.data_competicao else None,
                        'classe': inscricao.classe_escolhida,
                        'categoria': inscricao.categoria_ajustada or inscricao.categoria_escolhida,
                        'posicao': posicao,
                        'medalha': medalha
                    })
    
    # Ordenar histórico por ano (mais recente primeiro)
    historico.sort(key=lambda x: x['ano'] or 0, reverse=True)
    
    # Calcular indicadores globais
    total_eventos = len(historico)
    total_ouros = sum(1 for item in historico if item['medalha'] == 'ouro')
    total_pratas = sum(1 for item in historico if item['medalha'] == 'prata')
    total_bronzes = sum(1 for item in historico if item['medalha'] == 'bronze')
    
    context = {
        'atleta': atleta,
        'historico': historico,
        'total_eventos': total_eventos,
        'total_ouros': total_ouros,
        'total_pratas': total_pratas,
        'total_bronzes': total_bronzes
    }
    
    return render(request, 'atletas/perfil_atleta.html', context)

@operacional_required
@organizacao_required
def inscrever_atletas(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Inscrever atletas no campeonato ativo da organização - Login Operacional"""
    campeonato_ativo = Campeonato.objects.filter(ativo=True, organizador=organizacao).first()
    
    if not campeonato_ativo:
        messages.warning(request, 'Nenhum campeonato ativo encontrado. Ative um campeonato para inscrever atletas.')
        return render(request, 'atletas/inscrever_atletas.html', {
            'campeonato_ativo': None,
            'atletas': [],
            'academias': [],
            'categorias': [],
        })
    
    # Processar inscrição via POST
    if request.method == 'POST':
        atleta_id = request.POST.get('atleta_id')
        classe_id = request.POST.get('classe_escolhida')
        categoria_id = request.POST.get('categoria_escolhida')
        sexo_post = request.POST.get('sexo')
        peso_informado = request.POST.get('peso_atual') or request.POST.get('peso_informado')

        if not atleta_id or not classe_id or not categoria_id:
            messages.error(request, 'Preencha atleta, classe e categoria para inscrever.')
            return redirect('inscrever_atletas', organizacao_slug=request.organizacao.slug)

        try:
            atleta = get_object_or_404(Atleta, id=atleta_id, academia__organizador=organizacao)
            sexo_atleta = atleta.sexo
            if sexo_post and sexo_post in ['M', 'F'] and sexo_post != sexo_atleta:
                messages.error(request, 'Sexo do atleta não confere.')
                return redirect('inscrever_atletas', organizacao_slug=request.organizacao.slug)

            # Verificar se academia está permitida no campeonato
            academia_permitida = AcademiaCampeonato.objects.filter(
                academia=atleta.academia,
                campeonato=campeonato_ativo,
                permitido=True
            ).exists()
            if not academia_permitida:
                messages.error(request, f'A academia "{atleta.academia.nome}" não está permitida neste campeonato.')
                return redirect('inscrever_atletas', organizacao_slug=request.organizacao.slug)

            try:
                classe_obj = Classe.objects.get(id=int(classe_id))
            except (Classe.DoesNotExist, ValueError, TypeError):
                classe_obj = None
            try:
                categoria_obj = Categoria.objects.get(id=int(categoria_id), sexo=sexo_atleta)
            except (Categoria.DoesNotExist, ValueError, TypeError):
                categoria_obj = None

            if not classe_obj or not categoria_obj:
                messages.error(request, 'Classe ou categoria inválidas.')
                return redirect('inscrever_atletas', organizacao_slug=request.organizacao.slug)

            # Peso opcional
            peso_val = None
            if peso_informado:
                try:
                    peso_val = float(peso_informado)
                except ValueError:
                    peso_val = None

            # Criar inscrição normalizada (status_atual = inscrito)
            ins = service_inscrever_atleta(
                atleta=atleta,
                campeonato=campeonato_ativo,
                classe=classe_obj,
                categoria=categoria_obj,
                peso=peso_val
            )
            messages.success(
                request,
                f'{atleta.nome} inscrito com sucesso em {classe_obj.nome} - {categoria_obj.categoria_nome}. Status: inscrito.'
            )
        except Exception as e:
            messages.error(request, f'Erro ao inscrever atleta: {str(e)}')

        return redirect('inscrever_atletas', organizacao_slug=request.organizacao.slug)
    
    # GET: Listar atletas de academias permitidas no campeonato
    nome_filtro = request.GET.get('nome', '').strip()
    sexo_filtro = request.GET.get('sexo', '').strip()
    academia_filtro = request.GET.get('academia', '').strip()
    
    # Buscar academias permitidas no campeonato
    academias_permitidas_ids = list(AcademiaCampeonato.objects.filter(
        campeonato=campeonato_ativo,
        permitido=True
    ).values_list('academia_id', flat=True))
    
    # Se não houver academias permitidas, mostrar atletas da organização
    if not academias_permitidas_ids:
        atletas_query = Atleta.objects.select_related('academia').filter(
            academia__organizador=organizacao
        )
    else:
        atletas_query = Atleta.objects.filter(
            academia_id__in=academias_permitidas_ids,
            academia__organizador=organizacao
        ).select_related('academia')
    
    # Aplicar filtros opcionais
    if nome_filtro:
        atletas_query = atletas_query.filter(nome__icontains=nome_filtro)
    if sexo_filtro:
        atletas_query = atletas_query.filter(sexo=sexo_filtro)
    if academia_filtro:
        atletas_query = atletas_query.filter(academia_id=academia_filtro)
    
    atletas_query = atletas_query.order_by('academia__nome', 'nome')
    
    # Preparar dados para o template
    atletas = []
    for atleta in atletas_query:
        # Buscar inscrições deste atleta neste campeonato
        inscricoes = Inscricao.objects.filter(
            atleta=atleta,
            campeonato=campeonato_ativo
        )
        
        atletas.append({
            'atleta': atleta,
            'total_inscricoes': inscricoes.count(),
            'inscricoes': inscricoes,
        })
    
    # Buscar academias para o filtro
    # Se não houver academias permitidas, mostrar todas as academias da organização
    if not academias_permitidas_ids:
        academias = Academia.objects.filter(ativo_login=True, organizador=organizacao).order_by('nome')
    else:
        academias = Academia.objects.filter(
            id__in=academias_permitidas_ids,
            ativo_login=True,
            organizador=organizacao
        ).order_by('nome')
    
    # Buscar todas as categorias para o JavaScript
    todas_categorias = Categoria.objects.all().select_related('classe').order_by('classe__idade_min', 'limite_min')
    
    # Preparar categorias no formato esperado pelo template
    categorias_list = []
    for cat in todas_categorias:
        categorias_list.append({
            'id': cat.id,
            'classe': cat.classe.nome,  # Agora classe é ForeignKey, usar .nome
            'classe_id': cat.classe.id,
            'sexo': cat.sexo,
            'label': cat.label,
            'categoria_nome': cat.categoria_nome,
            'limite_min': cat.limite_min,
            'limite_max': cat.limite_max,
        })
    
    context = {
        'campeonato_ativo': campeonato_ativo,
        'atletas': atletas,
        'academias': academias,
        'categorias': categorias_list,
        'nome_filtro': nome_filtro,
        'sexo_filtro': sexo_filtro,
        'academia_filtro': academia_filtro,
    }
    
    return render(request, 'atletas/inscrever_atletas.html', context)

@operacional_required
@organizacao_required
def metricas_evento(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Painel operacional completo com métricas do evento em tempo real"""
    campeonato_ativo = Campeonato.objects.filter(ativo=True, organizador=organizacao).first()
    
    if not campeonato_ativo:
        messages.warning(request, 'Nenhum campeonato ativo encontrado.')
        return render(request, 'atletas/metricas_evento.html', {
            'campeonato_ativo': None,
            'indicadores_pesagem': {},
            'atletas_por_categoria': [],
            'remanejamentos': {},
            'indicadores_chaves': {},
            'progresso_campeonato': 0,
        })
    
    # Filtrar apenas academias permitidas
    academias_permitidas_ids = list(AcademiaCampeonato.objects.filter(
        campeonato=campeonato_ativo,
        permitido=True
    ).values_list('academia_id', flat=True))
    
    # ========== 1. INDICADORES DE PESAGEM ==========
    inscricoes_query = Inscricao.objects.filter(campeonato=campeonato_ativo)
    if academias_permitidas_ids:
        inscricoes_query = inscricoes_query.filter(atleta__academia_id__in=academias_permitidas_ids)
    
    total_inscritos = inscricoes_query.count()
    total_pesados = inscricoes_query.filter(peso__isnull=False).exclude(peso=0).count()
    total_pendentes = total_inscritos - total_pesados
    total_fora_categoria = inscricoes_query.filter(remanejado=True).count()
    
    # Contar remanejados que foram aceitos vs pendentes
    remanejados_aceitos = inscricoes_query.filter(remanejado=True, categoria_ajustada__isnull=False).exclude(categoria_ajustada='').count()
    remanejados_pendentes = inscricoes_query.filter(remanejado=True, categoria_ajustada__isnull=True).count() + inscricoes_query.filter(remanejado=True, categoria_ajustada='').count()
    
    indicadores_pesagem = {
        'total_inscritos': total_inscritos,
        'total_pesados': total_pesados,
        'total_pendentes': total_pendentes,
        'total_fora_categoria': total_fora_categoria,
        'remanejados_aceitos': remanejados_aceitos,
        'remanejados_pendentes': remanejados_pendentes,
        'percentual_pesados': round((total_pesados / total_inscritos * 100) if total_inscritos > 0 else 0, 1),
    }
    
    # ========== 2. ATLETAS POR CATEGORIA ==========
    inscricoes_por_categoria = inscricoes_query.values(
        'classe_escolhida', 'categoria_escolhida', 'categoria_ajustada'
    ).annotate(
        total=Count('id'),
        pesados=Count('id', filter=Q(peso__isnull=False) & ~Q(peso=0)),
        pendentes=Count('id', filter=Q(peso__isnull=True) | Q(peso=0)),
        remanejados=Count('id', filter=Q(remanejado=True))
    ).order_by('classe_escolhida', 'categoria_escolhida')
    
    atletas_por_categoria = []
    for item in inscricoes_por_categoria:
        categoria_nome = item['categoria_ajustada'] if item['categoria_ajustada'] else item['categoria_escolhida']
        atletas_por_categoria.append({
            'classe': item['classe_escolhida'],
            'categoria': categoria_nome,
            'total': item['total'],
            'pesados': item['pesados'],
            'pendentes': item['pendentes'],
            'remanejados': item['remanejados'],
        })
    
    # ========== 3. REMANEJAMENTOS ==========
    remanejamentos_query = inscricoes_query.filter(remanejado=True).select_related('atleta', 'atleta__academia')
    
    remanejamentos_pendentes_list = []
    remanejamentos_resolvidos = 0
    remanejamentos_desclassificados = 0
    
    for inscricao in remanejamentos_query:
        if inscricao.categoria_ajustada and inscricao.categoria_ajustada.strip():
            remanejamentos_resolvidos += 1
        elif inscricao.categoria_ajustada == 'DESCLASSIFICADO' or inscricao.status_inscricao == 'rejeitado':
            remanejamentos_desclassificados += 1
        else:
            remanejamentos_pendentes_list.append({
                'id': inscricao.id,
                'atleta_nome': inscricao.atleta.nome,
                'peso_registrado': inscricao.peso or 0,
                'professor': inscricao.atleta.academia.responsavel if inscricao.atleta.academia else 'N/A',
                'academia': inscricao.atleta.academia.nome if inscricao.atleta.academia else 'N/A',
                'categoria_original': inscricao.categoria_escolhida,
                'categoria_proposta': inscricao.categoria_ajustada or 'Aguardando decisão',
                'classe': inscricao.classe_escolhida,
            })
    
    remanejamentos = {
        'pendentes': len(remanejamentos_pendentes_list),
        'resolvidos': remanejamentos_resolvidos,
        'desclassificados': remanejamentos_desclassificados,
        'total': remanejamentos_query.count(),
        'lista_pendentes': remanejamentos_pendentes_list[:10],  # Limitar a 10 para não sobrecarregar
    }
    
    # ========== 4. INDICADORES DE CHAVES ==========
    chaves_query = Chave.objects.filter(campeonato=campeonato_ativo)
    total_chaves = chaves_query.count()
    
    # Contar chaves por status
    chaves_finalizadas = 0
    chaves_pendentes = 0
    chaves_em_construcao = 0
    total_lutas_geradas = 0
    total_lutas_finalizadas = 0
    
    for chave in chaves_query:
        lutas_chave = chave.lutas.all()
        total_lutas_chave = lutas_chave.count()
        lutas_finalizadas_chave = lutas_chave.filter(concluida=True).count()
        
        total_lutas_geradas += total_lutas_chave
        total_lutas_finalizadas += lutas_finalizadas_chave
        
        if total_lutas_chave == 0:
            chaves_em_construcao += 1
        elif lutas_finalizadas_chave == total_lutas_chave and total_lutas_chave > 0:
            chaves_finalizadas += 1
        else:
            chaves_pendentes += 1
    
    # Calcular progresso do campeonato
    progresso_campeonato = round((total_lutas_finalizadas / total_lutas_geradas * 100) if total_lutas_geradas > 0 else 0, 1)
    
    indicadores_chaves = {
        'total_chaves': total_chaves,
        'chaves_finalizadas': chaves_finalizadas,
        'chaves_pendentes': chaves_pendentes,
        'chaves_em_construcao': chaves_em_construcao,
        'total_lutas_geradas': total_lutas_geradas,
        'total_lutas_finalizadas': total_lutas_finalizadas,
        'progresso_campeonato': progresso_campeonato,
    }
    
    context = {
        'campeonato_ativo': campeonato_ativo,
        'indicadores_pesagem': indicadores_pesagem,
        'atletas_por_categoria': atletas_por_categoria,
        'remanejamentos': remanejamentos,
        'indicadores_chaves': indicadores_chaves,
        'progresso_campeonato': progresso_campeonato,
    }
    
    return render(request, 'atletas/metricas_evento.html', context)

def dashboard(request):
    return render(request, 'atletas/dashboard.html')

def relatorio_atletas_inscritos(request):
    return render(request, 'atletas/relatorio_atletas_inscritos.html')

def relatorio_pesagem_final(request):
    return render(request, 'atletas/relatorio_pesagem_final.html')

def relatorio_chaves(request):
    return render(request, 'atletas/relatorio_chaves.html')

def relatorio_resultados_categoria(request):
    return render(request, 'atletas/relatorio_resultados_categoria.html')

class ResetCompeticaoAPIView(APIView):
    @pode_resetar_required
    def post(self, request, *args, **kwargs):
        return Response({"detail": "Funcionalidade em desenvolvimento"}, status=status.HTTP_501_NOT_IMPLEMENTED)

@operacional_required
@organizacao_required
def lista_campeonatos(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Lista campeonatos da organização e exibe credenciais geradas se houver"""
    campeonatos = Campeonato.objects.filter(organizador=organizacao).annotate(
        total_inscricoes=Count('inscricoes'),
        total_academias=Count('academias_vinculadas', filter=Q(academias_vinculadas__permitido=True))
    ).order_by('-data_competicao', '-data_inicio')
    
    # Verificar se há credenciais na sessão (após criar campeonato)
    credenciais_campeonato = request.session.pop('credenciais_campeonato', None)
    
    context = {
        'campeonatos': campeonatos,
    }
    
    if credenciais_campeonato:
        context['academias_credenciais_campeonato'] = credenciais_campeonato['credenciais']
        context['campeonato_criado'] = {
            'id': credenciais_campeonato['campeonato_id'],
            'nome': credenciais_campeonato['campeonato_nome']
        }
    
    return render(request, 'atletas/lista_campeonatos.html', context)

@operacional_required
@organizacao_required
def cadastrar_campeonato(request, organizacao_slug=None, *args, **kwargs):
    if "organizacao_slug" in kwargs:
        kwargs.pop("organizacao_slug")
    organizacao = getattr(request, "organizacao", None)
    """Cadastrar novo campeonato da organização"""
    from .forms import CampeonatoForm
    
    formas_pagamento = FormaPagamento.objects.filter(ativo=True).order_by('tipo', 'nome')
    
    if request.method == "POST":
        form = CampeonatoForm(request.POST, request.FILES)
        if form.is_valid():
            campeonato = form.save(commit=False)
            campeonato.organizador = organizacao
            campeonato.save()
            
            # Se marcou como ativo, desativar outros
            if campeonato.ativo:
                Campeonato.objects.filter(organizador=organizacao).exclude(id=campeonato.id).update(ativo=False)
            
            # Gerar senhas para academias
            from datetime import timedelta
            academias_ativas = Academia.objects.filter(ativo_login=True, organizador=organizacao)
            
            for academia in academias_ativas:
                # Gerar login e senha
                import random
                import string
                login = f"ACADEMIA_{academia.id:03d}"
                senha_plana = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                
                # Calcular data de expiração (5 dias após término do campeonato)
                data_expiracao = None
                if campeonato.data_competicao:
                    data_expiracao = timezone.make_aware(
                        datetime.combine(campeonato.data_competicao, datetime.min.time())
                    ) + timedelta(days=5)
                
                # Criar ou atualizar senha
                senha_obj, created = AcademiaCampeonatoSenha.objects.get_or_create(
                    academia=academia,
                    campeonato=campeonato,
                    defaults={
                        'login': login,
                        'senha_plana': senha_plana,
                        'data_expiracao': data_expiracao,
                    }
                )
                
                if not created:
                    senha_obj.login = login
                    senha_obj.senha_plana = senha_plana
                    senha_obj.data_expiracao = data_expiracao
                    senha_obj.save()
                
                senha_obj.definir_senha(senha_plana)
                senha_obj.save()
            
            messages.success(request, "Campeonato cadastrado com sucesso!")
            return redirect('lista_campeonatos', organizacao_slug=request.organizacao.slug)
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        form = CampeonatoForm()
    
    return render(request, 'atletas/cadastrar_campeonato.html', {
        'form': form,
        'formas_pagamento': formas_pagamento
    })
    """Cadastrar campeonato e gerar credenciais temporárias para todas as academias"""
    if request.method == 'POST':
        try:
            from decimal import Decimal
            import random
            import string
            
            # Criar campeonato
            campeonato = Campeonato.objects.create(
                nome=request.POST.get('nome', '').strip(),
                data_inicio=request.POST.get('data_inicio') or None,
                data_competicao=request.POST.get('data_competicao') or None,
                data_limite_inscricao=request.POST.get('data_limite_inscricao') or None,
                ativo=request.POST.get('ativo') == 'on',
                regulamento=request.POST.get('regulamento', '').strip(),
                valor_inscricao_federado=request.POST.get('valor_inscricao_federado') or None,
                valor_inscricao_nao_federado=request.POST.get('valor_inscricao_nao_federado') or None,
            )
            
            # Se outro campeonato estava ativo, desativar
            if campeonato.ativo:
                Campeonato.objects.exclude(id=campeonato.id).update(ativo=False)
            
            # Gerar credenciais temporárias para todas as academias
            academias = Academia.objects.filter(ativo_login=True)
            credenciais_geradas = []
            
            for academia in academias:
                # Gerar login único: ACADEMIA_XXX (onde XXX é o ID da academia)
                login = f"ACADEMIA_{academia.id:03d}"
                
                # Gerar senha aleatória de 8 caracteres
                senha_plana = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                
                # Calcular data de expiração: 5 dias após término do campeonato
                data_expiracao = None
                if campeonato.data_competicao:
                    data_expiracao = campeonato.data_competicao + timedelta(days=5)
                
                # Criar ou atualizar credencial
                credencial, created = AcademiaCampeonatoSenha.objects.get_or_create(
                    academia=academia,
                    campeonato=campeonato,
                    defaults={
                        'login': login,
                        'senha_plana': senha_plana,
                        'data_expiracao': data_expiracao,
                    }
                )
                
                # Sempre atualizar login, senha e expiração (mesmo se já existir)
                credencial.login = login
                credencial.senha_plana = senha_plana
                credencial.data_expiracao = data_expiracao
                
                # Definir senha (criptografa) - IMPORTANTE: fazer ANTES do save
                credencial.definir_senha(senha_plana)
                credencial.save()
                
                credenciais_geradas.append({
                    'academia': academia,
                    'login': login,
                    'senha': senha_plana,
                    'telefone': academia.telefone,
                    'responsavel': academia.responsavel,
                })
            
            # Armazenar credenciais na sessão para exibição
            request.session['credenciais_campeonato'] = {
                'campeonato_id': campeonato.id,
                'campeonato_nome': campeonato.nome,
                'credenciais': credenciais_geradas
            }
            
            messages.success(request, f'Campeonato "{campeonato.nome}" criado com sucesso! Credenciais temporárias geradas para {len(credenciais_geradas)} academias.')
            return redirect('lista_campeonatos')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar campeonato: {str(e)}')
    
    return render(request, 'atletas/cadastrar_campeonato.html', {
        'formas_pagamento': formas_pagamento
    })

@operacional_required
def editar_campeonato(request, campeonato_id):
    """Editar campeonato"""
    from .forms import CampeonatoForm
    
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    
    if request.method == "POST":
        form = CampeonatoForm(request.POST, request.FILES, instance=campeonato)
        if form.is_valid():
            campeonato = form.save(commit=False)
            campeonato.chave_pix = request.POST.get('chave_pix', '').strip()
            campeonato.titular_pix = request.POST.get('titular_pix', '').strip()
            campeonato.save()
            
            # Handle ManyToMany for formas_pagamento
            formas_pagamento_ids = request.POST.getlist('formas_pagamento')
            campeonato.formas_pagamento.set(formas_pagamento_ids)
            
            # Se marcou como ativo, desativar outros
            if campeonato.ativo:
                Campeonato.objects.exclude(id=campeonato.id).update(ativo=False)
                # Vincular todas as academias ativas ao campeonato ativo (se ainda não estiverem vinculadas)
                academias_ativas = Academia.objects.filter(ativo_login=True)
                for academia in academias_ativas:
                    AcademiaCampeonato.objects.get_or_create(
                        academia=academia,
                        campeonato=campeonato,
                        defaults={'permitido': True}
                    )
            
            messages.success(request, "Alterações salvas com sucesso.")
            return redirect('lista_campeonatos')
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        form = CampeonatoForm(instance=campeonato)
        formas_pagamento = FormaPagamento.objects.filter(ativo=True).order_by('tipo', 'nome')
    
    return render(request, 'atletas/editar_campeonato.html', {
        'form': form,
        'campeonato': campeonato,
        'formas_pagamento': formas_pagamento,
    })

@operacional_required
def definir_campeonato_ativo(request, campeonato_id):
    """Ativar um campeonato (desativa os outros automaticamente)"""
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    
    # Desativar todos os outros campeonatos
    Campeonato.objects.exclude(id=campeonato.id).update(ativo=False)
    
    # Ativar o campeonato selecionado
    campeonato.ativo = True
    campeonato.save()
    
    # Vincular todas as academias ativas ao campeonato ativo (se ainda não estiverem vinculadas) e gerar senhas
    academias_ativas = Academia.objects.filter(ativo_login=True)
    vinculadas = 0
    senhas_geradas = 0
    
    import random
    import string
    from datetime import timedelta
    from datetime import datetime as dt
    
    for academia in academias_ativas:
        vinculo, created = AcademiaCampeonato.objects.get_or_create(
            academia=academia,
            campeonato=campeonato,
            defaults={'permitido': True}
        )
        if created:
            vinculadas += 1
        
        # Gerar senha se não existir
        senha_obj, senha_created = AcademiaCampeonatoSenha.objects.get_or_create(
            academia=academia,
            campeonato=campeonato,
            defaults={
                'login': f"ACADEMIA_{academia.id:03d}",
                'senha_plana': ''.join(random.choices(string.ascii_letters + string.digits, k=8)),
                'data_expiracao': timezone.make_aware(
                    dt.combine(campeonato.data_competicao, dt.min.time())
                ) + timedelta(days=5) if campeonato.data_competicao else None,
            }
        )
        
        if senha_created:
            senha_obj.definir_senha(senha_obj.senha_plana)
            senha_obj.save()
            senhas_geradas += 1
    
    messages.success(request, f'Campeonato "{campeonato.nome}" ativado com sucesso!')
    if vinculadas > 0:
        messages.info(request, f'{vinculadas} academia(s) vinculada(s) automaticamente ao campeonato.')
    if senhas_geradas > 0:
        messages.info(request, f'{senhas_geradas} senha(s) gerada(s) para as academias.')
    return redirect('lista_campeonatos')

@operacional_required
def gerenciar_academias_campeonato(request, campeonato_id):
    """Gerenciar permissões de academias no campeonato"""
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    
    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        if acao == 'toggle_permissao':
            academia_id = request.POST.get('academia_id')
            permitido = request.POST.get('permitido') == 'true'
            
            if academia_id:
                try:
                    academia = get_object_or_404(Academia, id=academia_id)
                    vinculo, created = AcademiaCampeonato.objects.get_or_create(
                        academia=academia,
                        campeonato=campeonato,
                        defaults={'permitido': True}
                    )
                    vinculo.permitido = permitido
                    vinculo.save()
                    
                    status = 'permitida' if permitido else 'bloqueada'
                    messages.success(request, f'Academia "{academia.nome}" {status} no campeonato.')
                except Exception as e:
                    messages.error(request, f'Erro ao atualizar permissão: {str(e)}')
        
        elif acao == 'adicionar_academia':
            academia_id = request.POST.get('academia_id')
            if academia_id:
                try:
                    academia = get_object_or_404(Academia, id=academia_id)
                    # Verificar se já existe vínculo
                    if AcademiaCampeonato.objects.filter(academia=academia, campeonato=campeonato).exists():
                        messages.warning(request, f'Academia "{academia.nome}" já está vinculada a este campeonato.')
                    else:
                        AcademiaCampeonato.objects.create(
                            academia=academia,
                            campeonato=campeonato,
                            permitido=True
                        )
                        messages.success(request, f'Academia "{academia.nome}" adicionada ao campeonato.')
                except Exception as e:
                    messages.error(request, f'Erro ao adicionar academia: {str(e)}')
        
        return redirect('gerenciar_academias_campeonato', campeonato_id=campeonato_id)
    
    # GET: Listar todas as academias e seus status no campeonato
    todas_academias = Academia.objects.filter(ativo_login=True).order_by('nome')
    vinculos = AcademiaCampeonato.objects.filter(campeonato=campeonato).select_related('academia')
    
    # Criar dicionário de status por academia
    status_academias = {v.academia_id: v.permitido for v in vinculos}
    
    # Separar academias vinculadas e não vinculadas
    academias_vinculadas = []
    academias_nao_vinculadas = []
    
    for academia in todas_academias:
        if academia.id in status_academias:
            vinculo_obj = vinculos.get(academia_id=academia.id)
            academias_vinculadas.append({
                'academia': academia,
                'permitido': status_academias[academia.id],
                'vinculo': vinculo_obj
            })
        else:
            academias_nao_vinculadas.append(academia)
    
    context = {
        'campeonato': campeonato,
        'academias_vinculadas': academias_vinculadas,
        'academias_nao_vinculadas': academias_nao_vinculadas,
        'total_permitidas': sum(1 for a in academias_vinculadas if a['permitido']),
        'total_bloqueadas': sum(1 for a in academias_vinculadas if not a['permitido']),
    }
    
    return render(request, 'atletas/gerenciar_academias_campeonato.html', context)

@operacional_required
def gerenciar_senhas_campeonato(request, campeonato_id):
    """Gerenciar senhas temporárias do campeonato"""
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    
    # Buscar todas as credenciais do campeonato
    credenciais = AcademiaCampeonatoSenha.objects.filter(
        campeonato=campeonato
    ).select_related('academia').order_by('academia__nome')
    
    academias_com_senhas = []
    for credencial in credenciais:
        academias_com_senhas.append({
            'academia': credencial.academia,
            'login': credencial.login,
            'senha_plana': credencial.senha_plana,
            'telefone': credencial.academia.telefone,
            'responsavel': credencial.academia.responsavel,
            'enviado_whatsapp': credencial.enviado_whatsapp,
            'data_envio': credencial.data_envio_whatsapp,
            'data_expiracao': credencial.data_expiracao,
            'esta_expirado': credencial.esta_expirado,
            'credencial_id': credencial.id,
        })
    
    # Se não há credenciais, gerar para todas as academias
    if not academias_com_senhas:
        import random
        import string
        academias = Academia.objects.filter(ativo_login=True)
        
        for academia in academias:
            login = f"ACADEMIA_{academia.id:03d}"
            senha_plana = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            data_expiracao = None
            if campeonato.data_competicao:
                data_expiracao = campeonato.data_competicao + timedelta(days=5)
            
            credencial = AcademiaCampeonatoSenha(
                academia=academia,
                campeonato=campeonato,
                login=login,
                senha_plana=senha_plana,
                data_expiracao=data_expiracao,
            )
            # Definir senha (criptografa) - IMPORTANTE: fazer ANTES do save
            credencial.definir_senha(senha_plana)
            credencial.save()
            
            academias_com_senhas.append({
                'academia': academia,
                'login': login,
                'senha_plana': senha_plana,
                'telefone': academia.telefone,
                'responsavel': academia.responsavel,
                'enviado_whatsapp': False,
                'data_envio': None,
                'data_expiracao': data_expiracao,
                'esta_expirado': False,
                'credencial_id': credencial.id,
            })
    
    # Processar POST (marcar como enviado)
    if request.method == 'POST' and request.POST.get('marcar_enviado'):
        credencial_id = request.POST.get('credencial_id')
        if credencial_id:
            try:
                credencial = AcademiaCampeonatoSenha.objects.get(id=credencial_id, campeonato=campeonato)
                credencial.enviado_whatsapp = True
                credencial.data_envio_whatsapp = timezone.now()
                credencial.save()
                messages.success(request, 'Status de envio atualizado.')
                return redirect('gerenciar_senhas_campeonato', campeonato_id=campeonato.id)
            except AcademiaCampeonatoSenha.DoesNotExist:
                pass
    
    context = {
        'campeonato': campeonato,
        'academias_com_senhas': academias_com_senhas,
        'data_competicao': campeonato.data_competicao.strftime('%d/%m/%Y') if campeonato.data_competicao else 'Não definida',
        'valor_federado': f"R$ {campeonato.valor_inscricao_federado:.2f}" if campeonato.valor_inscricao_federado else 'Não definido',
        'valor_nao_federado': f"R$ {campeonato.valor_inscricao_nao_federado:.2f}" if campeonato.valor_inscricao_nao_federado else 'Não definido',
    }
    
    return render(request, 'atletas/administracao/gerenciar_senhas_campeonato.html', context)

@academia_required
def academia_painel(request):
    """Painel da academia - lista eventos abertos e encerrados"""
    academia = request.academia
    hoje = timezone.now().date()
    
    # Desativar eventos automaticamente após data da competição
    Campeonato.objects.filter(
        data_competicao__lt=hoje,
        ativo=True
    ).update(ativo=False)
    
    # Buscar credenciais da academia (eventos onde ela tem acesso)
    credenciais = AcademiaCampeonatoSenha.objects.filter(
        academia=academia
    ).select_related('campeonato').order_by('-campeonato__data_competicao', '-id')
    
    # Separar eventos: abertos e encerrados (sem duplicação)
    eventos_abertos = []  # Eventos ativos e abertos para inscrição (data_competicao >= hoje AND ativo = True)
    eventos_encerrados = []  # Eventos encerrados (data_competicao < hoje OR ativo = False)
    
    eventos_processados = set()  # Para evitar duplicações
    
    for credencial in credenciais:
        campeonato = credencial.campeonato
        
        # Evitar processar o mesmo evento duas vezes
        if campeonato.id in eventos_processados:
            continue
        eventos_processados.add(campeonato.id)
        
        # Verificar se o evento está encerrado
        # Encerrado APENAS se a data da competição já passou (data_competicao < hoje)
        # Eventos futuros (mesmo com inscrições fechadas) ficam em "abertos" (agenda)
        evento_encerrado = (
            campeonato.data_competicao and 
            campeonato.data_competicao < hoje
        )
        
        if evento_encerrado:
            # Evento encerrado - apenas consulta (já aconteceu)
            eventos_encerrados.append(campeonato)
        else:
            # Evento futuro ou sem data definida - sempre em "abertos" (agenda)
            # Mesmo que as inscrições tenham fechado, se o evento ainda não aconteceu,
            # ele deve aparecer como "agenda" para a academia acompanhar
            eventos_abertos.append(campeonato)
    
    # Ordenar por data (mais recente primeiro)
    eventos_abertos.sort(key=lambda x: x.data_competicao or date.min, reverse=True)
    eventos_encerrados.sort(key=lambda x: x.data_competicao or date.min, reverse=True)
    
    # Calcular rankings para exibir no painel
    ranking_global_atletas = []
    ranking_academias_list = []
    campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
    
    if campeonato_ativo:
        from .utils import calcular_pontuacao_academias, get_resultados_chave
        
        # Calcular pontuação das academias primeiro
        calcular_pontuacao_academias(campeonato_ativo.id)
        
        academias_permitidas_ids = list(AcademiaCampeonato.objects.filter(
            campeonato=campeonato_ativo,
            permitido=True
        ).values_list('academia_id', flat=True))
        
        # Ranking completo de academias
        ranking_academias_completo = AcademiaPontuacao.objects.filter(
            campeonato=campeonato_ativo
        ).select_related('academia')
        
        # Se houver academias permitidas, filtrar por elas
        if academias_permitidas_ids:
            ranking_academias_completo = ranking_academias_completo.filter(academia_id__in=academias_permitidas_ids)
        
        ranking_academias_completo = ranking_academias_completo.order_by('-pontos_totais', '-ouro', '-prata', '-bronze')
        
        # Preparar dados do ranking de academias
        for pontuacao in ranking_academias_completo:
            # Contar atletas ativos da academia no campeonato
            total_atletas_ativos = Inscricao.objects.filter(
                campeonato=campeonato_ativo,
                atleta__academia=pontuacao.academia,
                status_inscricao='aprovado'
            ).count()
            
            ranking_academias_list.append({
                'academia': pontuacao.academia,
                'ouro': pontuacao.ouro,
                'prata': pontuacao.prata,
                'bronze': pontuacao.bronze,
                'pontos_totais': pontuacao.pontos_totais,
                'total_atletas_ativos': total_atletas_ativos,
            })
        
        # Calcular ranking global de atletas
        chaves = Chave.objects.filter(campeonato=campeonato_ativo)
        medalhas_por_atleta = {}
        
        for chave in chaves:
            resultados = get_resultados_chave(chave)
            if not resultados:
                continue
            
            # 1º lugar = ouro, 2º lugar = prata, 3º lugar = bronze
            for idx, atleta_id in enumerate(resultados[:3], 1):
                if not atleta_id:
                    continue
                
                if atleta_id not in medalhas_por_atleta:
                    try:
                        atleta = Atleta.objects.get(id=atleta_id)
                        medalhas_por_atleta[atleta_id] = {
                            'atleta': atleta,
                            'ouro': 0,
                            'prata': 0,
                            'bronze': 0,
                            'total_medalhas': 0,
                        }
                    except Atleta.DoesNotExist:
                        continue
                
                if idx == 1:
                    medalhas_por_atleta[atleta_id]['ouro'] += 1
                elif idx == 2:
                    medalhas_por_atleta[atleta_id]['prata'] += 1
                elif idx == 3:
                    medalhas_por_atleta[atleta_id]['bronze'] += 1
                
                medalhas_por_atleta[atleta_id]['total_medalhas'] = (
                    medalhas_por_atleta[atleta_id]['ouro'] +
                    medalhas_por_atleta[atleta_id]['prata'] +
                    medalhas_por_atleta[atleta_id]['bronze']
                )
        
        # Ordenar por total de medalhas (ouro > prata > bronze)
        ranking_global_atletas = sorted(
            medalhas_por_atleta.values(),
            key=lambda x: (x['total_medalhas'], x['ouro'], x['prata'], x['bronze']),
            reverse=True
        )
    
    context = {
        'academia': academia,
        'eventos_abertos': eventos_abertos,
        'eventos_encerrados': eventos_encerrados,
        'campeonato_ativo': campeonato_ativo,
        'ranking_global_atletas': ranking_global_atletas,
        'ranking_academias_completo': ranking_academias_list,
        'hoje': hoje,  # Data atual para uso no template
    }
    
    return render(request, 'atletas/academia/painel.html', context)

@academia_required
def academia_evento(request, campeonato_id):
    """Página do evento para a academia"""
    academia = request.academia
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    hoje = timezone.now().date()
    
    # Verificar se o evento está inativo
    evento_inativo = not campeonato.ativo or (campeonato.data_competicao and campeonato.data_competicao < hoje)
    
    # Buscar inscrições da academia neste campeonato
    inscricoes = Inscricao.objects.filter(
        atleta__academia=academia,
        campeonato=campeonato
    )
    
    total_inscritos = inscricoes.count()
    aprovados = inscricoes.filter(status_inscricao='aprovado').count()
    pendentes = inscricoes.filter(status_inscricao='pendente').count()
    
    # Calcular resumo financeiro
    valor_federado = campeonato.valor_inscricao_federado or 0
    valor_nao_federado = campeonato.valor_inscricao_nao_federado or 0
    
    inscricoes_aprovadas = inscricoes.filter(status_inscricao='aprovado')
    valor_confirmado = sum(
        valor_federado if ins.atleta.federado else valor_nao_federado
        for ins in inscricoes_aprovadas
    )
    
    inscricoes_pendentes_list = inscricoes.filter(status_inscricao='pendente')
    valor_pendente = sum(
        valor_federado if ins.atleta.federado else valor_nao_federado
        for ins in inscricoes_pendentes_list
    )
    
    valor_previsto = valor_confirmado + valor_pendente
    
    resumo_financeiro = {
        'valor_previsto': valor_previsto,
        'valor_confirmado': valor_confirmado,
        'valor_pendente': valor_pendente,
        'status': 'Tudo confirmado' if pendentes == 0 else f'{pendentes} pendente(s)',
    }
    
    context = {
        'academia': academia,
        'campeonato': campeonato,
        'evento_inativo': evento_inativo,
        'total_inscritos': total_inscritos,
        'aprovados': aprovados,
        'pendentes': pendentes,
        'resumo_financeiro': resumo_financeiro,
        'valor_inscricao_federado': valor_federado,
        'valor_inscricao_nao_federado': valor_nao_federado,
    }
    
    return render(request, 'atletas/academia/evento.html', context)

@academia_required
def academia_lista_atletas(request, campeonato_id=None):
    """Lista atletas da academia - global ou de um evento específico"""
    academia = request.academia
    
    modo_evento = campeonato_id is not None
    campeonato = None
    atletas = []
    resumo_financeiro = None
    
    if modo_evento:
        # Modo evento: listar atletas inscritos no evento
        campeonato = get_object_or_404(Campeonato, id=campeonato_id)
        
        # Buscar inscrições da academia neste campeonato
        inscricoes = Inscricao.objects.filter(
            atleta__academia=academia,
            campeonato=campeonato
        ).select_related('atleta', 'atleta__academia')
        
        # Preparar dados para o template
        atletas = []
        for inscricao in inscricoes:
            atletas.append({
                'atleta': inscricao.atleta,
                'classe_escolhida': inscricao.classe_escolhida,
                'categoria_escolhida': inscricao.categoria_escolhida,
                'status': inscricao.status_inscricao,
            })
        
        # Calcular resumo financeiro
        total_inscritos = inscricoes.count()
        aprovados = inscricoes.filter(status_inscricao='aprovado').count()
        pendentes = inscricoes.filter(status_inscricao='pendente').count()
        
        # Calcular valores
        valor_federado = campeonato.valor_inscricao_federado or 0
        valor_nao_federado = campeonato.valor_inscricao_nao_federado or 0
        
        inscricoes_aprovadas = inscricoes.filter(status_inscricao='aprovado')
        valor_confirmado = sum(
            valor_federado if ins.atleta.federado else valor_nao_federado
            for ins in inscricoes_aprovadas
        )
        
        inscricoes_pendentes = inscricoes.filter(status_inscricao='pendente')
        valor_pendente = sum(
            valor_federado if ins.atleta.federado else valor_nao_federado
            for ins in inscricoes_pendentes
        )
        
        valor_previsto = valor_confirmado + valor_pendente
        
        resumo_financeiro = {
            'quantidade': total_inscritos,
            'aprovados': aprovados,
            'pendentes': pendentes,
            'valor_previsto': valor_previsto,
            'valor_confirmado': valor_confirmado,
            'valor_pendente': valor_pendente,
        }
    else:
        # Modo global: listar todos os atletas da academia
        atletas = Atleta.objects.filter(academia=academia).order_by('nome')
    
    context = {
        'academia': academia,
        'atletas': atletas,
        'modo_evento': modo_evento,
        'campeonato': campeonato,
        'resumo_financeiro': resumo_financeiro,
    }
    
    return render(request, 'atletas/academia/lista_atletas.html', context)

@academia_required
def academia_inscrever_atletas(request, campeonato_id):
    """Inscrever atletas da academia em um campeonato"""
    academia = request.academia
    
    # Debug: verificar se academia foi encontrada
    if not academia:
        messages.error(request, 'Erro: Academia não encontrada na sessão.')
        return redirect('academia_painel')
    
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    hoje = timezone.now().date()
    
    # Verificar se o evento está inativo (bloquear inscrições)
    evento_inativo = not campeonato.ativo or (campeonato.data_competicao and campeonato.data_competicao < hoje)
    
    if evento_inativo:
        messages.warning(request, 'Este evento está inativo. Não é possível fazer novas inscrições, apenas consultar.')
        return redirect('academia_evento', campeonato_id=campeonato_id)
    
    # Verificar data limite para inscrições por academia
    prazo_inscricao_vencido = False
    if campeonato.data_limite_inscricao_academia:
        prazo_inscricao_vencido = hoje > campeonato.data_limite_inscricao_academia
        if prazo_inscricao_vencido:
            messages.warning(request, f'O prazo para inscrições por academia encerrou em {campeonato.data_limite_inscricao_academia.strftime("%d/%m/%Y")}. Apenas a equipe operacional pode realizar inscrições agora.')
    
    # Processar inscrição via POST
    if request.method == 'POST':
        # Bloquear POST se o prazo estiver vencido
        if prazo_inscricao_vencido:
            messages.error(request, 'O prazo para inscrições por academia já encerrou. Entre em contato com a organização do evento.')
            return redirect('academia_inscrever_atletas', campeonato_id=campeonato_id)
        atleta_id = request.POST.get('atleta_id')
        classe_id = request.POST.get('classe_escolhida')
        categoria_id = request.POST.get('categoria_escolhida')
        peso_informado = request.POST.get('peso_atual') or request.POST.get('peso_informado')
        
        if atleta_id and classe_id and categoria_id:
            try:
                atleta = Atleta.objects.get(id=atleta_id, academia=academia)
                classe_obj = Classe.objects.filter(id=classe_id).first()
                categoria_obj = Categoria.objects.filter(id=categoria_id, sexo=atleta.sexo).first()
                if not classe_obj or not categoria_obj:
                    messages.error(request, 'Classe ou categoria inválidas.')
                    return redirect('academia_inscrever_atletas', campeonato_id=campeonato_id)
                
                # Peso opcional
                peso_val = None
                if peso_informado:
                    try:
                        peso_val = float(peso_informado)
                    except ValueError:
                        peso_val = None
                
                ins = service_inscrever_atleta(
                    atleta=atleta,
                    campeonato=campeonato,
                    classe=classe_obj,
                    categoria=categoria_obj,
                    peso=peso_val
                )
                messages.success(request, f'{atleta.nome} inscrito com sucesso em {classe_obj.nome} - {categoria_obj.categoria_nome}. Status: inscrito.')
            except Atleta.DoesNotExist:
                messages.error(request, 'Atleta não encontrado.')
            except Exception as e:
                messages.error(request, f'Erro ao inscrever atleta: {str(e)}')
        
        return redirect('academia_inscrever_atletas', campeonato_id=campeonato_id)
    
    # GET: Listar atletas da academia
    nome_filtro = request.GET.get('nome', '').strip()
    sexo_filtro = request.GET.get('sexo', '').strip()
    
    # Buscar atletas da academia (incluindo inativos para que apareçam na lista)
    atletas_query = Atleta.objects.filter(academia=academia)
    
    # Aplicar filtros
    if nome_filtro:
        atletas_query = atletas_query.filter(nome__icontains=nome_filtro)
    if sexo_filtro:
        atletas_query = atletas_query.filter(sexo=sexo_filtro)
    
    atletas_query = atletas_query.order_by('nome')
    
    # Debug: verificar quantos atletas foram encontrados
    total_atletas_encontrados = atletas_query.count()
    
    # Se não encontrou atletas, verificar se há atletas cadastrados para esta academia
    if total_atletas_encontrados == 0:
        total_geral = Atleta.objects.filter(academia=academia).count()
        if total_geral == 0:
            messages.info(request, f'Nenhum atleta cadastrado para a academia "{academia.nome}". Use o botão "Cadastrar Novo Atleta" para adicionar atletas.')
        else:
            if nome_filtro or sexo_filtro:
                messages.warning(request, f'Encontrados {total_geral} atleta(s) cadastrado(s), mas nenhum corresponde aos filtros aplicados. Tente limpar os filtros.')
            else:
                messages.warning(request, f'Erro: {total_geral} atleta(s) cadastrado(s), mas não foram encontrados na query. Verifique o código.')
    
    # Preparar dados para o template
    atletas = []
    for atleta in atletas_query:
        # Buscar inscrições deste atleta neste campeonato
        inscricoes = Inscricao.objects.filter(
            atleta=atleta,
            campeonato=campeonato
        )
        
        atletas.append({
            'atleta': atleta,
            'total_inscricoes': inscricoes.count(),
            'inscricoes': inscricoes,
        })
    
    # Calcular resumo financeiro
    todas_inscricoes = Inscricao.objects.filter(
        atleta__academia=academia,
        campeonato=campeonato
    )
    
    valor_federado = campeonato.valor_inscricao_federado or 0
    valor_nao_federado = campeonato.valor_inscricao_nao_federado or 0
    
    inscricoes_aprovadas = todas_inscricoes.filter(status_inscricao='aprovado')
    valor_confirmado = sum(
        valor_federado if ins.atleta.federado else valor_nao_federado
        for ins in inscricoes_aprovadas
    )
    
    inscricoes_pendentes = todas_inscricoes.filter(status_inscricao='pendente')
    valor_pendente = sum(
        valor_federado if ins.atleta.federado else valor_nao_federado
        for ins in inscricoes_pendentes
    )
    
    valor_previsto = valor_confirmado + valor_pendente
    
    resumo_financeiro = {
        'valor_previsto': valor_previsto,
        'valor_confirmado': valor_confirmado,
        'valor_pendente': valor_pendente,
    }
    
    # Buscar todas as categorias para o JavaScript
    todas_categorias = Categoria.objects.all().select_related('classe').order_by('classe__idade_min', 'limite_min')
    
    # Preparar categorias no formato esperado pelo template
    categorias_list = []
    for cat in todas_categorias:
        categorias_list.append({
            'id': cat.id,
            'classe': cat.classe.nome,  # Agora classe é ForeignKey, usar .nome
            'sexo': cat.sexo,
            'label': cat.label,  # Campo label do modelo
            'categoria_nome': cat.categoria_nome,
        })
    
    context = {
        'academia': academia,
        'campeonato': campeonato,
        'atletas': atletas,
        'nome_filtro': nome_filtro,
        'sexo_filtro': sexo_filtro,
        'resumo_financeiro': resumo_financeiro,
        'valor_inscricao_federado': valor_federado,
        'valor_inscricao_nao_federado': valor_nao_federado,
        'categorias': categorias_list,
        'prazo_inscricao_vencido': prazo_inscricao_vencido,
        'data_limite_inscricao_academia': campeonato.data_limite_inscricao_academia,
    }
    
    return render(request, 'atletas/academia/inscrever_atletas.html', context)

@academia_required
def academia_cadastrar_atleta(request, campeonato_id=None):
    """Cadastrar novo atleta pela academia"""
    academia = request.academia
    
    if request.method == 'POST':
        try:
            nome = request.POST.get('nome', '').strip()
            data_nascimento = request.POST.get('data_nascimento')
            sexo = request.POST.get('sexo')
            federado = request.POST.get('federado') == 'on'
            rg = request.POST.get('rg', '').strip()
            cpf = request.POST.get('cpf', '').strip()
            telefone = request.POST.get('telefone', '').strip()
            email = request.POST.get('email', '').strip()
            observacoes = request.POST.get('observacoes', '').strip()
            
            if not nome or not data_nascimento or not sexo:
                messages.error(request, 'Preencha todos os campos obrigatórios.')
            else:
                atleta = Atleta.objects.create(
                    nome=nome,
                    data_nascimento=data_nascimento,
                    sexo=sexo,
                    academia=academia,  # Sempre vincula à academia logada
                    federado=federado,
                    rg=rg or None,
                    cpf=cpf or None,
                    telefone=telefone or None,
                    email=email or None,
                    observacoes=observacoes or None,
                )
                
                # Upload de foto
                if 'foto_perfil' in request.FILES:
                    atleta.foto_perfil = request.FILES['foto_perfil']
                    atleta.save()
                
                messages.success(request, f'Atleta "{atleta.nome}" cadastrado com sucesso!')
                
                # Se veio de um evento, redirecionar para inscrição
                if campeonato_id:
                    return redirect('academia_inscrever_atletas', campeonato_id=campeonato_id)
                else:
                    return redirect('academia_lista_atletas')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar atleta: {str(e)}')
    
    # GET: Passar academia e campeonato se houver
    context = {
        'academia': academia,
    }
    
    if campeonato_id:
        context['campeonato'] = get_object_or_404(Campeonato, id=campeonato_id)
    
    return render(request, 'atletas/academia/cadastrar_atleta.html', context)

@academia_required
@academia_required
def academia_ver_chaves(request, campeonato_id):
    """Lista todas as chaves geradas para o campeonato com filtros"""
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    
    # Buscar todas as chaves do campeonato
    chaves_query = Chave.objects.filter(campeonato=campeonato).order_by('classe', 'sexo', 'categoria')
    
    # Aplicar filtros
    classe_filtro = request.GET.get('classe', '').strip()
    sexo_filtro = request.GET.get('sexo', '').strip()
    categoria_filtro = request.GET.get('categoria', '').strip()
    
    if classe_filtro:
        chaves_query = chaves_query.filter(classe=classe_filtro)
    if sexo_filtro:
        chaves_query = chaves_query.filter(sexo=sexo_filtro)
    if categoria_filtro:
        chaves_query = chaves_query.filter(categoria=categoria_filtro)
    
    chaves = list(chaves_query)
    
    # Obter classes, sexos e categorias disponíveis para os filtros
    todas_chaves = Chave.objects.filter(campeonato=campeonato)
    classes = sorted(set(todas_chaves.exclude(classe='').values_list('classe', flat=True).distinct()))
    categorias = sorted(set(todas_chaves.exclude(categoria='').values_list('categoria', flat=True).distinct()))
    
    context = {
        'campeonato': campeonato,
        'chaves': chaves,
        'classes': classes,
        'categorias': categorias,
        'classe_filtro': classe_filtro,
        'sexo_filtro': sexo_filtro,
        'categoria_filtro': categoria_filtro,
    }
    
    return render(request, 'atletas/academia/ver_chaves.html', context)

@academia_required
def academia_detalhe_chave(request, campeonato_id, chave_id):
    """Exibe detalhes da chave para a academia"""
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    chave = get_object_or_404(Chave, id=chave_id, campeonato=campeonato)
    
    # Buscar lutas da chave ordenadas por round e ID
    lutas = chave.lutas.all().order_by('round', 'id').select_related('atleta_a', 'atleta_b', 'vencedor', 'atleta_a__academia', 'atleta_b__academia')
    
    # Agrupar lutas por round
    from itertools import groupby
    lutas_por_round = []
    for round_num, lutas_round in groupby(lutas, key=lambda l: l.round):
        lutas_por_round.append({
            'grouper': round_num,
            'list': list(lutas_round)
        })
    
    # Buscar resultados finais usando a função utilitária
    from .utils import get_resultados_chave
    resultados_ids = get_resultados_chave(chave)
    
    # Converter IDs de resultados em objetos Atleta com academias
    resultados = []
    for atleta_id in resultados_ids:
        try:
            atleta = Atleta.objects.select_related('academia').get(id=atleta_id)
            resultados.append(atleta)
        except Atleta.DoesNotExist:
            continue
    
    context = {
        'campeonato': campeonato,
        'chave': chave,
        'lutas_por_round': lutas_por_round,
        'resultados': resultados,
    }
    
    return render(request, 'atletas/academia/detalhe_chave.html', context)

@academia_required
def academia_baixar_regulamento(request, campeonato_id):
    """Baixa o regulamento do campeonato em formato PDF usando xhtml2pdf"""
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    
    if not campeonato.regulamento:
        messages.error(request, 'Regulamento não disponível para este evento.')
        return redirect('academia_evento', campeonato_id=campeonato_id)
    
    try:
        from .utils_pdf import renderizar_template_para_pdf
        import re
        
        # Processar texto do regulamento para identificar títulos e parágrafos
        texto_regulamento = campeonato.regulamento
        paragrafos = []
        
        # Dividir em parágrafos (linhas vazias indicam novo parágrafo)
        blocos = texto_regulamento.split('\n\n')
        
        for bloco in blocos:
            bloco = bloco.strip()
            if not bloco:
                continue
            
            # Verificar se é um título (linha curta, sem pontuação final, ou começa com número)
            linhas = bloco.split('\n')
            is_titulo = False
            
            if len(linhas) == 1:
                linha = linhas[0].strip()
                # Título se: linha curta (< 80 chars) ou começa com número seguido de ponto/parentese
                if len(linha) < 80 or re.match(r'^\d+[\.\)]\s', linha):
                    is_titulo = True
            
            paragrafos.append({
                'texto': bloco,
                'is_titulo': is_titulo
            })
        
        # Preparar contexto para o template
        context = {
            'campeonato': campeonato,
            'regulamento': campeonato.regulamento,
            'paragrafos': paragrafos,
        }
        
        # Gerar nome do arquivo
        filename = f"regulamento_{campeonato.nome.replace(' ', '_')}.pdf"
        
        # Gerar PDF usando xhtml2pdf
        return renderizar_template_para_pdf(
            template_path='atletas/academia/regulamento_pdf.html',
            context=context,
            filename=filename,
            content_disposition='attachment'
        )
        
    except ImportError as e:
        # Se xhtml2pdf não estiver instalado, retornar como HTML para impressão
        messages.warning(request, 'Biblioteca de PDF não disponível. Retornando HTML para impressão.')
        from django.template.loader import render_to_string
        html_content = render_to_string('atletas/academia/regulamento_pdf.html', {
            'campeonato': campeonato,
            'regulamento': campeonato.regulamento,
            'paragrafos': []
        })
        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = f'inline; filename="regulamento_{campeonato.nome}.html"'
        return response
    except Exception as e:
        messages.error(request, f'Erro ao gerar PDF: {str(e)}')
        return redirect('academia_evento', campeonato_id=campeonato_id)

@academia_required
def tabela_categorias_peso(request):
    """Exibe tabela de categorias de peso por classe e sexo"""
    # Buscar todas as categorias ordenadas
    categorias = Categoria.objects.all().select_related('classe').order_by('classe__idade_min', 'sexo', 'limite_min')
    
    # Organizar por classe e sexo
    categorias_organizadas = {}
    classes = []
    
    for categoria in categorias:
        classe = categoria.classe.nome  # Agora classe é ForeignKey, usar .nome
        sexo_display = categoria.get_sexo_display()
        
        if classe not in categorias_organizadas:
            categorias_organizadas[classe] = {}
            if classe not in classes:
                classes.append(classe)
        
        if sexo_display not in categorias_organizadas[classe]:
            categorias_organizadas[classe][sexo_display] = []
        
        categorias_organizadas[classe][sexo_display].append(categoria)
    
    # Ordenar classes
    ordem_classes = {
        'SUB 9': 1, 'SUB 11': 2, 'SUB 13': 3, 'SUB 15': 4,
        'SUB 18': 5, 'SUB 21': 6, 'SÊNIOR': 7, 'VETERANOS': 8
    }
    classes_ordenadas = sorted(classes, key=lambda x: ordem_classes.get(x, 99))
    
    # Preparar dados para template (lista de tuplas)
    categorias_por_classe = []
    for classe in classes_ordenadas:
        sexos_data = []
        for sexo_display, categorias_list in categorias_organizadas[classe].items():
            sexos_data.append((sexo_display, categorias_list))
        categorias_por_classe.append((classe, sexos_data))
    
    context = {
        'categorias_por_classe': categorias_por_classe,
    }
    
    return render(request, 'atletas/tabela_categorias_peso.html', context)

@operacional_required
def administracao_painel(request):
    """Redireciona para o painel financeiro unificado"""
    return redirect('administracao_financeiro')

@operacional_required
def administracao_conferencia_inscricoes(request):
    return render(request, 'atletas/administracao/conferencia_inscricoes.html')

@operacional_required
def administracao_confirmar_inscricoes(request):
    return redirect('administracao_conferencia_inscricoes')

@operacional_required
def administracao_financeiro(request):
    """Painel financeiro completo e unificado - única fonte de verdade para dados financeiros - 100% vinculado ao evento"""
    # Buscar campeonato ativo ou selecionado via GET
    campeonato_id = request.GET.get('campeonato_id')
    if campeonato_id:
        campeonato_ativo = get_object_or_404(Campeonato, id=campeonato_id)
    else:
        campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
    
    # OBRIGATÓRIO: Sem evento, não pode acessar financeiro
    if not campeonato_ativo:
        messages.warning(request, 'Nenhum evento selecionado. Selecione um evento para acessar o módulo financeiro.')
        return redirect('lista_campeonatos')
    
    # Inicializar todas as variáveis
    ganho_previsto = 0
    dinheiro_caixa = 0
    pagamentos_pendentes = 0
    total_despesas = 0
    despesas_pendentes = 0
    despesas_pagas = 0
    total_bonus = 0
    saldo_final = 0
    lucro_atual = 0
    patrocinios_total = 0
    
    # Inscrições
    inscricoes_pendentes = 0
    inscricoes_confirmadas = 0
    entradas_federado = 0
    entradas_nao_federado = 0
    total_inscricoes = 0  # Total de inscrições para o gráfico
    
    # Operacionais
    operacional_counts = {
        'arbitro': 0,
        'mesario': 0,
        'oficial_mesa': 0,
        'oficial_pesagem': 0,
    }
    
    # Rankings
    ranking_academias = []
    top_custos = []
    
    if campeonato_ativo:
        # ========== CÁLCULOS BASEADOS EM ConferenciaPagamento (FONTE ÚNICA) ==========
        
        # Buscar todas as conferências do campeonato
        conferencias = ConferenciaPagamento.objects.filter(campeonato=campeonato_ativo)
        
        # Dinheiro em caixa: soma de conferências confirmadas
        conferencias_confirmadas = conferencias.filter(status='CONFIRMADO')
        dinheiro_caixa = sum(c.valor_recebido or c.valor_esperado for c in conferencias_confirmadas)
        
        # Pagamentos pendentes: soma de conferências pendentes
        conferencias_pendentes = conferencias.filter(status='PENDENTE')
        pagamentos_pendentes = sum(c.valor_esperado for c in conferencias_pendentes)
        
        # ========== CÁLCULOS DE INSCRIÇÕES (BASEADO EM Inscricao - FONTE REAL) ==========
        # Buscar TODAS as inscrições do campeonato
        inscricoes = Inscricao.objects.filter(campeonato=campeonato_ativo)
        valor_federado = campeonato_ativo.valor_inscricao_federado or 0
        valor_nao_federado = campeonato_ativo.valor_inscricao_nao_federado or 0
        
        # Contar inscrições por status (baseado nas inscrições reais)
        # IMPORTANTE: Incluir todas as inscrições que não estão confirmadas/aprovadas como pendentes
        inscricoes_confirmadas = inscricoes.filter(status_inscricao__in=['confirmado', 'aprovado']).count()
        # Contar todas as inscrições pendentes (status='pendente' ou qualquer outro status que não seja confirmado/aprovado)
        inscricoes_pendentes = inscricoes.exclude(status_inscricao__in=['confirmado', 'aprovado', 'reprovado']).count()
        
        # Calcular entradas por categoria (federado/não federado) baseado nas inscrições reais
        for ins in inscricoes:
            if ins.atleta.federado:
                entradas_federado += valor_federado
            else:
                entradas_nao_federado += valor_nao_federado
        
        # Total de inscrições (para o gráfico de pilhas)
        total_inscricoes = entradas_federado + entradas_nao_federado
        
        # Ganho previsto: soma de todas as inscrições (confirmadas + pendentes)
        ganho_previsto = total_inscricoes
        
        # ========== CÁLCULOS DE DESPESAS ==========
        # IMPORTANTE: Todas as despesas são 100% vinculadas ao campeonato_ativo
        # Não há mistura de valores entre eventos diferentes
        from .models import Despesa
        despesas = Despesa.objects.filter(campeonato=campeonato_ativo)
        total_despesas = sum(d.valor for d in despesas)
        despesas_pendentes = sum(d.valor for d in despesas.filter(status='pendente'))
        despesas_pagas = sum(d.valor for d in despesas.filter(status='pago'))
        
        # Patrocínios: despesas com categoria 'patrocinios' (entrada de dinheiro)
        patrocinios_total = sum(d.valor for d in despesas.filter(categoria='patrocinios', status='pago'))
        
        # ========== CÁLCULOS DE LUCRO/PREJUÍZO ==========
        lucro_atual = dinheiro_caixa + patrocinios_total - total_despesas
        saldo_final = dinheiro_caixa - total_despesas
        
        # ========== INDICADORES OPERACIONAIS ==========
        # Contar pessoas da equipe técnica vinculadas ao campeonato ativo por função
        from .models import EquipeTecnicaCampeonato
        operacional_counts['arbitro'] = EquipeTecnicaCampeonato.objects.filter(
            campeonato=campeonato_ativo,
            funcao='arbitro',
            ativo=True
        ).count()
        operacional_counts['mesario'] = EquipeTecnicaCampeonato.objects.filter(
            campeonato=campeonato_ativo,
            funcao='mesario',
            ativo=True
        ).count()
        operacional_counts['oficial_mesa'] = EquipeTecnicaCampeonato.objects.filter(
            campeonato=campeonato_ativo,
            funcao='oficial_mesa',
            ativo=True
        ).count()
        operacional_counts['oficial_pesagem'] = EquipeTecnicaCampeonato.objects.filter(
            campeonato=campeonato_ativo,
            funcao='oficial_pesagem',
            ativo=True
        ).count()
        
        # ========== RANKINGS ==========
        # Top 5 academias por número de inscrições
        from django.db.models import Count
        academias_permitidas_ids = list(AcademiaCampeonato.objects.filter(
            campeonato=campeonato_ativo,
            permitido=True
        ).values_list('academia_id', flat=True))
        
        if academias_permitidas_ids:
            ranking_academias = Inscricao.objects.filter(
                campeonato=campeonato_ativo,
                atleta__academia_id__in=academias_permitidas_ids
            ).values('atleta__academia').annotate(
                total=Count('id')
            ).order_by('-total')[:5]
            
            # Adicionar objeto academia ao ranking
            ranking_academias_list = []
            for item in ranking_academias:
                try:
                    academia = Academia.objects.get(id=item['atleta__academia'])
                    ranking_academias_list.append({
                        'academia': academia,
                        'total': item['total']
                    })
                except Academia.DoesNotExist:
                    pass
            ranking_academias = ranking_academias_list
        
        # Top 5 custos por categoria
        from django.db.models import Sum
        top_custos_raw = despesas.values('categoria').annotate(
            valor_total=Sum('valor')
        ).order_by('-valor_total')[:5]
        
        top_custos = []
        for item in top_custos_raw:
            # Combinar todas as categorias possíveis (despesa + receita)
            todas_categorias = dict(Despesa.CATEGORIA_DESPESA_CHOICES)
            todas_categorias.update(dict(Despesa.CATEGORIA_RECEITA_CHOICES))
            categoria_display = todas_categorias.get(item['categoria'], item['categoria'])
            top_custos.append({
                'categoria': categoria_display,
                'valor': item['valor_total']
            })
    
    # Despesas recentes - SEMPRE filtrar por campeonato
    from .models import Despesa
    despesas_recentes = Despesa.objects.filter(campeonato=campeonato_ativo).order_by('-data_cadastro')[:10] if campeonato_ativo else Despesa.objects.none()
    
    context = {
        'campeonato_ativo': campeonato_ativo,
        # Financeiros principais
        'ganho_previsto': ganho_previsto,
        'dinheiro_caixa': dinheiro_caixa,
        'pagamentos_pendentes': pagamentos_pendentes,
        'total_despesas': total_despesas,
        'despesas_pendentes': despesas_pendentes,
        'despesas_pagas': despesas_pagas,
        'total_bonus': total_bonus,
        'saldo_final': saldo_final,
        'lucro_atual': lucro_atual,
        'patrocinios_total': patrocinios_total,
        # Inscrições
        'inscricoes_pendentes': inscricoes_pendentes,
        'inscricoes_confirmadas': inscricoes_confirmadas,
        'entradas_federado': entradas_federado,
        'entradas_nao_federado': entradas_nao_federado,
        'total_inscricoes': total_inscricoes,  # Total de inscrições para o gráfico
        # Operacionais
        'operacional_counts': operacional_counts,
        # Rankings
        'ranking_academias': ranking_academias,
        'top_custos': top_custos,
        # Despesas recentes
        'despesas': despesas_recentes,
    }
    
    return render(request, 'atletas/administracao/financeiro.html', context)

@operacional_required
def administracao_despesas(request):
    """Gerenciar despesas e receitas do campeonato - 100% vinculado ao evento"""
    # Buscar campeonato ativo ou selecionado via GET
    campeonato_id = request.GET.get('campeonato_id')
    if campeonato_id:
        campeonato_ativo = get_object_or_404(Campeonato, id=campeonato_id)
    else:
        campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
    
    # OBRIGATÓRIO: Sem evento, não pode acessar despesas
    if not campeonato_ativo:
        messages.warning(request, 'Nenhum evento selecionado. Selecione um evento para acessar despesas e receitas.')
        return redirect('lista_campeonatos')
    
    # Processar ações via POST
    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        if acao == 'criar':
            tipo = request.POST.get('tipo', 'despesa')
            categoria = request.POST.get('categoria', '').strip()
            nome = request.POST.get('nome', '').strip()
            valor = request.POST.get('valor', '').strip()
            status = request.POST.get('status', 'pendente')
            observacao = request.POST.get('observacao', '').strip()
            contato_nome = request.POST.get('contato_nome', '').strip()
            contato_whatsapp = request.POST.get('contato_whatsapp', '').strip()
            data_pagamento = request.POST.get('data_pagamento', '').strip()
            comprovante = request.FILES.get('comprovante_pagamento')
            
            if not categoria or not nome or not valor:
                messages.error(request, 'Preencha todos os campos obrigatórios.')
            else:
                try:
                    valor_decimal = float(valor.replace(',', '.'))
                    if valor_decimal <= 0:
                        messages.error(request, 'O valor deve ser maior que zero.')
                    else:
                        despesa = Despesa.objects.create(
                            campeonato=campeonato_ativo,
                            tipo=tipo,
                            categoria=categoria,
                            nome=nome,
                            valor=valor_decimal,
                            status=status,
                            observacao=observacao,
                            contato_nome=contato_nome,
                            contato_whatsapp=contato_whatsapp,
                            data_pagamento=data_pagamento if data_pagamento else None,
                            comprovante_pagamento=comprovante
                        )
                        tipo_display = "Despesa" if tipo == 'despesa' else "Receita"
                        messages.success(request, f'{tipo_display} "{nome}" cadastrada com sucesso!')
                except ValueError:
                    messages.error(request, 'Valor inválido. Use números com ponto ou vírgula.')
                except Exception as e:
                    messages.error(request, f'Erro ao cadastrar: {str(e)}')
        
        elif acao == 'editar':
            despesa_id = request.POST.get('despesa_id')
            if despesa_id:
                try:
                    despesa = get_object_or_404(Despesa, id=despesa_id, campeonato=campeonato_ativo)
                    despesa.tipo = request.POST.get('tipo', despesa.tipo)
                    despesa.categoria = request.POST.get('categoria', despesa.categoria)
                    despesa.nome = request.POST.get('nome', '').strip()
                    valor = request.POST.get('valor', '').strip()
                    despesa.status = request.POST.get('status', despesa.status)
                    despesa.observacao = request.POST.get('observacao', '').strip()
                    despesa.contato_nome = request.POST.get('contato_nome', '').strip()
                    despesa.contato_whatsapp = request.POST.get('contato_whatsapp', '').strip()
                    data_pagamento = request.POST.get('data_pagamento', '').strip()
                    comprovante = request.FILES.get('comprovante_pagamento')
                    
                    if valor:
                        try:
                            valor_decimal = float(valor.replace(',', '.'))
                            if valor_decimal > 0:
                                despesa.valor = valor_decimal
                        except ValueError:
                            messages.error(request, 'Valor inválido.')
                            return redirect('administracao_despesas')
                    
                    despesa.data_pagamento = data_pagamento if data_pagamento else None
                    if comprovante:
                        despesa.comprovante_pagamento = comprovante
                    despesa.save()
                    
                    tipo_display = "Despesa" if despesa.tipo == 'despesa' else "Receita"
                    messages.success(request, f'{tipo_display} "{despesa.nome}" atualizada com sucesso!')
                except Exception as e:
                    messages.error(request, f'Erro ao atualizar: {str(e)}')
        
        elif acao == 'deletar':
            despesa_id = request.POST.get('despesa_id')
            if despesa_id:
                try:
                    despesa = get_object_or_404(Despesa, id=despesa_id, campeonato=campeonato_ativo)
                    nome = despesa.nome
                    tipo_display = "Despesa" if despesa.tipo == 'despesa' else "Receita"
                    despesa.delete()
                    messages.success(request, f'{tipo_display} "{nome}" removida com sucesso!')
                except Exception as e:
                    messages.error(request, f'Erro ao remover: {str(e)}')
        
        return redirect('administracao_despesas')
    
    # GET: Listar despesas e receitas
    despesas = Despesa.objects.filter(campeonato=campeonato_ativo).order_by('-data_cadastro')
    
    # Filtros
    tipo_filtro = request.GET.get('tipo', '')
    status_filtro = request.GET.get('status', '')
    categoria_filtro = request.GET.get('categoria', '')
    
    if tipo_filtro:
        despesas = despesas.filter(tipo=tipo_filtro)
    if status_filtro:
        despesas = despesas.filter(status=status_filtro)
    if categoria_filtro:
        despesas = despesas.filter(categoria=categoria_filtro)
    
    # Calcular receita de inscrições confirmadas
    receita_inscricoes = 0
    if campeonato_ativo:
        from .models import ConferenciaPagamento
        conferencias_confirmadas = ConferenciaPagamento.objects.filter(
            campeonato=campeonato_ativo,
            status='CONFIRMADO'
        )
        receita_inscricoes = sum(c.valor_recebido or c.valor_esperado for c in conferencias_confirmadas)
    
    # Estatísticas
    total_despesas = sum(d.valor for d in despesas.filter(tipo='despesa'))
    total_receitas = sum(d.valor for d in despesas.filter(tipo='receita')) + receita_inscricoes
    despesas_pagas = sum(d.valor for d in despesas.filter(tipo='despesa', status='pago'))
    receitas_recebidas = sum(d.valor for d in despesas.filter(tipo='receita', status='pago')) + receita_inscricoes
    saldo = total_receitas - total_despesas
    
    context = {
        'campeonato_ativo': campeonato_ativo,
        'despesas': despesas,
        'total_despesas': total_despesas,
        'total_receitas': total_receitas,
        'receita_inscricoes': receita_inscricoes,
        'despesas_pagas': despesas_pagas,
        'receitas_recebidas': receitas_recebidas,
        'saldo': saldo,
        'tipo_filtro': tipo_filtro,
        'status_filtro': status_filtro,
        'categoria_filtro': categoria_filtro,
        'categorias_despesa': Despesa.CATEGORIA_DESPESA_CHOICES,
        'categorias_receita': Despesa.CATEGORIA_RECEITA_CHOICES,
        'status_choices': Despesa.STATUS_CHOICES,
        'tipo_choices': Despesa.TIPO_CHOICES,
    }
    
    return render(request, 'atletas/administracao/despesas.html', context)

@operacional_required
def administracao_equipe(request):
    """Página principal da equipe técnica - mostra cards por tipo"""
    campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
    
    # Contar membros da equipe técnica por função (se houver campeonato ativo)
    cards = [
        {
            'titulo': 'Árbitros',
            'quantidade': EquipeTecnicaCampeonato.objects.filter(campeonato=campeonato_ativo, funcao='arbitro', ativo=True).count() if campeonato_ativo else 0,
            'tipo': 'arbitro',
            'icone': 'M12 2l4 4h-3v6h-2V6H8l4-4z'
        },
        {
            'titulo': 'Mesários',
            'quantidade': EquipeTecnicaCampeonato.objects.filter(campeonato=campeonato_ativo, funcao='mesario', ativo=True).count() if campeonato_ativo else 0,
            'tipo': 'mesario',
            'icone': 'M4 6h16M4 10h16M4 14h16M4 18h16'
        },
        {
            'titulo': 'Oficiais de Mesa',
            'quantidade': EquipeTecnicaCampeonato.objects.filter(campeonato=campeonato_ativo, funcao='oficial_mesa', ativo=True).count() if campeonato_ativo else 0,
            'tipo': 'oficial_mesa',
            'icone': 'M5 4h14l1 4H4l1-4zm0 6h14v8H5v-8z'
        },
        {
            'titulo': 'Oficiais de Pesagem',
            'quantidade': EquipeTecnicaCampeonato.objects.filter(campeonato=campeonato_ativo, funcao='oficial_pesagem', ativo=True).count() if campeonato_ativo else 0,
            'tipo': 'oficial_pesagem',
            'icone': 'M6 3h12v4H6z M4 9h16v10H4z'
        },
        {
            'titulo': 'Coordenadores',
            'quantidade': EquipeTecnicaCampeonato.objects.filter(campeonato=campeonato_ativo, funcao='coordenador', ativo=True).count() if campeonato_ativo else 0,
            'tipo': 'coordenador',
            'icone': 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 1 8 0 4 4 0 0 1-8 0'
        },
    ]
    
    # Total de pessoas na lista fixa
    total_pessoas = PessoaEquipeTecnica.objects.filter(ativo=True).count()
    
    context = {
        'cards': cards,
        'campeonato_ativo': campeonato_ativo,
        'total_pessoas': total_pessoas,
    }
    
    return render(request, 'atletas/administracao/equipe.html', context)

@operacional_required
def administracao_equipe_pessoas_lista(request):
    """Gerenciar lista fixa de pessoas da equipe técnica"""
    # Processar ações via POST
    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        if acao == 'criar_pessoa':
            tipo_pessoa = request.POST.get('tipo_pessoa')  # 'atleta' ou 'externa'
            atleta_id = request.POST.get('atleta_id')
            nome = request.POST.get('nome', '').strip()
            telefone = request.POST.get('telefone', '').strip()
            chave_pix = request.POST.get('chave_pix', '').strip()
            observacao = request.POST.get('observacao', '').strip()
            
            if tipo_pessoa == 'atleta' and atleta_id:
                try:
                    atleta = Atleta.objects.get(id=atleta_id, pode_ser_equipe_tecnica=True)
                    # Verificar se já existe
                    pessoa_existente = PessoaEquipeTecnica.objects.filter(atleta=atleta).first()
                    if pessoa_existente:
                        messages.warning(request, f'{atleta.nome} já está na lista de equipe técnica.')
                    else:
                        # Criar pessoa com nome preenchido automaticamente pelo save()
                        pessoa = PessoaEquipeTecnica(
                            atleta=atleta,
                            telefone=telefone or atleta.telefone or '',
                            chave_pix=chave_pix or atleta.chave_pix or '',
                            observacao=observacao
                        )
                        # O método save() preencherá o nome automaticamente
                        pessoa.save()
                        messages.success(request, f'{pessoa.nome_completo} adicionado à lista de equipe técnica.')
                except Atleta.DoesNotExist:
                    messages.error(request, 'Atleta não encontrado ou não elegível.')
            elif tipo_pessoa == 'externa':
                if not nome:
                    messages.error(request, 'Nome é obrigatório para pessoas externas.')
                elif not telefone:
                    messages.error(request, 'Telefone é obrigatório para pessoas externas.')
                elif not chave_pix:
                    messages.error(request, 'Chave PIX é obrigatória para pessoas externas.')
                else:
                    try:
                        pessoa = PessoaEquipeTecnica.objects.create(
                            nome=nome,
                            telefone=telefone,
                            chave_pix=chave_pix,
                            observacao=observacao
                        )
                        messages.success(request, f'{pessoa.nome} adicionado à lista de equipe técnica.')
                    except Exception as e:
                        messages.error(request, f'Erro ao cadastrar pessoa: {str(e)}')
            else:
                if tipo_pessoa == 'atleta':
                    messages.error(request, 'Selecione um atleta ou preencha os dados da pessoa externa.')
                else:
                    messages.error(request, 'Preencha os campos obrigatórios.')
        
        elif acao == 'editar_pessoa':
            pessoa_id = request.POST.get('pessoa_id')
            if pessoa_id:
                try:
                    pessoa = get_object_or_404(PessoaEquipeTecnica, id=pessoa_id)
                    # Só pode editar se não for atleta (atletas são editados no cadastro de atletas)
                    if pessoa.atleta:
                        messages.warning(request, 'Para editar atletas, use o cadastro de atletas.')
                    else:
                        pessoa.nome = request.POST.get('nome', '').strip()
                        pessoa.telefone = request.POST.get('telefone', '').strip()
                        pessoa.chave_pix = request.POST.get('chave_pix', '').strip()
                        pessoa.observacao = request.POST.get('observacao', '').strip()
                        pessoa.save()
                        messages.success(request, f'{pessoa.nome} atualizado com sucesso.')
                except Exception as e:
                    messages.error(request, f'Erro ao atualizar: {str(e)}')
        
        elif acao == 'deletar_pessoa':
            pessoa_id = request.POST.get('pessoa_id')
            if pessoa_id:
                try:
                    pessoa = get_object_or_404(PessoaEquipeTecnica, id=pessoa_id)
                    nome = pessoa.nome_completo
                    pessoa.delete()
                    messages.success(request, f'{nome} removido da lista.')
                except Exception as e:
                    messages.error(request, f'Erro ao remover: {str(e)}')
        
        elif acao == 'toggle_ativo':
            pessoa_id = request.POST.get('pessoa_id')
            if pessoa_id:
                try:
                    pessoa = get_object_or_404(PessoaEquipeTecnica, id=pessoa_id)
                    pessoa.ativo = not pessoa.ativo
                    pessoa.save()
                    status = 'ativada' if pessoa.ativo else 'desativada'
                    messages.success(request, f'{pessoa.nome_completo} {status}.')
                except Exception as e:
                    messages.error(request, f'Erro: {str(e)}')
        
        return redirect('administracao_equipe_pessoas_lista')
    
    # GET: Listar pessoas
    pessoas = PessoaEquipeTecnica.objects.all().select_related('atleta', 'atleta__academia').order_by('nome')
    
    # Filtros
    nome_filtro = request.GET.get('nome', '').strip()
    tipo_filtro = request.GET.get('tipo', '').strip()
    
    if nome_filtro:
        pessoas = pessoas.filter(nome__icontains=nome_filtro)
    if tipo_filtro == 'atleta':
        pessoas = pessoas.filter(atleta__isnull=False)
    elif tipo_filtro == 'externa':
        pessoas = pessoas.filter(atleta__isnull=True)
    
    # Buscar atletas elegíveis para adicionar
    atletas_elegiveis = Atleta.objects.filter(
        pode_ser_equipe_tecnica=True,
        status_ativo=True
    ).exclude(
        id__in=PessoaEquipeTecnica.objects.filter(atleta__isnull=False).values_list('atleta_id', flat=True)
    ).select_related('academia').order_by('nome')
    
    context = {
        'pessoas': pessoas,
        'atletas_elegiveis': atletas_elegiveis,
        'nome_filtro': nome_filtro,
        'tipo_filtro': tipo_filtro,
    }
    
    return render(request, 'atletas/administracao/equipe_pessoas_lista.html', context)

@operacional_required
def administracao_equipe_gerenciar(request, campeonato_id=None):
    """Gerenciar equipe técnica de um campeonato específico"""
    if campeonato_id:
        campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    else:
        campeonato = Campeonato.objects.filter(ativo=True).first()
        if not campeonato:
            messages.warning(request, 'Nenhum campeonato ativo encontrado. Selecione um campeonato.')
            return redirect('lista_campeonatos')
    
    # Processar ações via POST
    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        if acao == 'adicionar':
            pessoa_id = request.POST.get('pessoa_id')
            funcao = request.POST.get('funcao')
            funcao_customizada = request.POST.get('funcao_customizada', '').strip()
            pro_labore_str = request.POST.get('pro_labore', '0').strip().replace(',', '.')
            observacao = request.POST.get('observacao', '').strip()
            
            if not pessoa_id or not funcao:
                messages.error(request, 'Selecione uma pessoa e uma função.')
            else:
                try:
                    pessoa = get_object_or_404(PessoaEquipeTecnica, id=pessoa_id, ativo=True)
                    
                    # Verificar se já está vinculado nesta função
                    vinculo_existente = EquipeTecnicaCampeonato.objects.filter(
                        pessoa=pessoa,
                        campeonato=campeonato,
                        funcao=funcao
                    ).first()
                    
                    if vinculo_existente:
                        messages.warning(request, f'{pessoa.nome_completo} já está vinculado como {vinculo_existente.get_funcao_display()} neste campeonato.')
                    else:
                        pro_labore = float(pro_labore_str) if pro_labore_str else 0
                        vinculo = EquipeTecnicaCampeonato.objects.create(
                            pessoa=pessoa,
                            campeonato=campeonato,
                            funcao=funcao,
                            funcao_customizada=funcao_customizada if funcao == 'outro' else None,
                            pro_labore=pro_labore,
                            observacao=observacao
                        )
                        
                        # Gerar despesa automaticamente se pró-labore > 0
                        if pro_labore > 0:
                            despesa = criar_despesa_pro_labore(vinculo)
                            vinculo.despesa_gerada = despesa
                            vinculo.save()
                        
                        funcao_display = dict(EquipeTecnicaCampeonato.FUNCAO_CHOICES).get(funcao, funcao_customizada or funcao)
                        messages.success(request, f'{pessoa.nome_completo} adicionado à equipe técnica como {funcao_display}.')
                except ValueError:
                    messages.error(request, 'Valor do pró-labore inválido.')
                except Exception as e:
                    messages.error(request, f'Erro ao adicionar pessoa: {str(e)}')
        
        elif acao == 'atualizar_pro_labore':
            vinculo_id = request.POST.get('vinculo_id')
            pro_labore_str = request.POST.get('pro_labore', '0').strip().replace(',', '.')
            
            if vinculo_id:
                try:
                    vinculo = get_object_or_404(EquipeTecnicaCampeonato, id=vinculo_id, campeonato=campeonato)
                    pro_labore_anterior = vinculo.pro_labore
                    pro_labore_novo = float(pro_labore_str) if pro_labore_str else 0
                    
                    vinculo.pro_labore = pro_labore_novo
                    
                    # Atualizar ou criar despesa
                    if pro_labore_novo > 0:
                        if vinculo.despesa_gerada:
                            # Atualizar despesa existente
                            vinculo.despesa_gerada.valor = pro_labore_novo
                            vinculo.despesa_gerada.nome = f"Pró-labore: {vinculo.pessoa.nome_completo} - {vinculo.get_funcao_display()}"
                            vinculo.despesa_gerada.save()
                        else:
                            # Criar nova despesa
                            despesa = criar_despesa_pro_labore(vinculo)
                            vinculo.despesa_gerada = despesa
                    elif vinculo.despesa_gerada:
                        # Remover despesa se pró-labore = 0
                        vinculo.despesa_gerada.delete()
                        vinculo.despesa_gerada = None
                    
                    vinculo.save()
                    messages.success(request, f'Pró-labore de {vinculo.pessoa.nome_completo} atualizado para R$ {pro_labore_novo:.2f}.')
                except ValueError:
                    messages.error(request, 'Valor do pró-labore inválido.')
                except Exception as e:
                    messages.error(request, f'Erro ao atualizar pró-labore: {str(e)}')
        
        elif acao == 'remover':
            vinculo_id = request.POST.get('vinculo_id')
            if vinculo_id:
                try:
                    vinculo = EquipeTecnicaCampeonato.objects.get(id=vinculo_id, campeonato=campeonato)
                    nome = vinculo.nome_completo
                    vinculo.delete()
                    messages.success(request, f'{nome} removido da equipe técnica.')
                except EquipeTecnicaCampeonato.DoesNotExist:
                    messages.error(request, 'Vínculo não encontrado.')
        
        elif acao == 'toggle_ativo':
            vinculo_id = request.POST.get('vinculo_id')
            if vinculo_id:
                try:
                    vinculo = EquipeTecnicaCampeonato.objects.get(id=vinculo_id, campeonato=campeonato)
                    vinculo.ativo = not vinculo.ativo
                    vinculo.save()
                    status = 'ativado' if vinculo.ativo else 'desativado'
                    messages.success(request, f'{vinculo.nome_completo} {status} na equipe técnica.')
                except EquipeTecnicaCampeonato.DoesNotExist:
                    messages.error(request, 'Vínculo não encontrado.')
        
        elif acao == 'atualizar_pro_labore':
            vinculo_id = request.POST.get('vinculo_id')
            pro_labore_str = request.POST.get('pro_labore', '0').strip().replace(',', '.')
            
            if vinculo_id:
                try:
                    vinculo = get_object_or_404(EquipeTecnicaCampeonato, id=vinculo_id, campeonato=campeonato)
                    pro_labore_anterior = vinculo.pro_labore
                    pro_labore_novo = float(pro_labore_str) if pro_labore_str else 0
                    
                    vinculo.pro_labore = pro_labore_novo
                    
                    # Atualizar ou criar despesa
                    if pro_labore_novo > 0:
                        if vinculo.despesa_gerada:
                            # Atualizar despesa existente
                            vinculo.despesa_gerada.valor = pro_labore_novo
                            funcao_display = vinculo.funcao_customizada if vinculo.funcao == 'outro' and vinculo.funcao_customizada else vinculo.get_funcao_display()
                            vinculo.despesa_gerada.nome = f"Pró-labore: {vinculo.pessoa.nome_completo} - {funcao_display}"
                            vinculo.despesa_gerada.save()
                        else:
                            # Criar nova despesa
                            despesa = criar_despesa_pro_labore(vinculo)
                            vinculo.despesa_gerada = despesa
                    elif vinculo.despesa_gerada:
                        # Remover despesa se pró-labore = 0
                        vinculo.despesa_gerada.delete()
                        vinculo.despesa_gerada = None
                    
                    vinculo.save()
                    messages.success(request, f'Pró-labore de {vinculo.pessoa.nome_completo} atualizado para R$ {pro_labore_novo:.2f}.')
                except ValueError:
                    messages.error(request, 'Valor do pró-labore inválido.')
                except Exception as e:
                    messages.error(request, f'Erro ao atualizar pró-labore: {str(e)}')
        
        return redirect('administracao_equipe_gerenciar', campeonato_id=campeonato.id)
    
    # GET: Listar equipe técnica do campeonato
    equipe = EquipeTecnicaCampeonato.objects.filter(
        campeonato=campeonato
    ).select_related('pessoa', 'pessoa__atleta', 'pessoa__atleta__academia').order_by('funcao', 'pessoa__nome')
    
    # Agrupar por função
    equipe_por_funcao = {}
    for membro in equipe:
        funcao_display = membro.funcao_customizada if membro.funcao == 'outro' and membro.funcao_customizada else membro.get_funcao_display()
        if funcao_display not in equipe_por_funcao:
            equipe_por_funcao[funcao_display] = []
        equipe_por_funcao[funcao_display].append(membro)
    
    # Buscar pessoas disponíveis da lista fixa (apenas as que ainda não estão vinculadas neste campeonato)
    pessoas_vinculadas_ids = equipe.values_list('pessoa_id', flat=True)
    pessoas_disponiveis = PessoaEquipeTecnica.objects.filter(
        ativo=True
    ).exclude(id__in=pessoas_vinculadas_ids).select_related('atleta', 'atleta__academia').order_by('nome')
    
    context = {
        'campeonato': campeonato,
        'equipe': equipe,
        'equipe_por_funcao': equipe_por_funcao,
        'pessoas_disponiveis': pessoas_disponiveis,
        'funcoes': EquipeTecnicaCampeonato.FUNCAO_CHOICES,
    }
    
    return render(request, 'atletas/administracao/equipe_gerenciar.html', context)

def criar_despesa_pro_labore(vinculo):
    """Cria uma despesa automaticamente baseada no pró-labore de um membro da equipe técnica"""
    funcao_display = vinculo.funcao_customizada if vinculo.funcao == 'outro' and vinculo.funcao_customizada else vinculo.get_funcao_display()
    
    # Mapear função para categoria de despesa
    categoria_map = {
        'arbitro': 'arbitros',
        'mesario': 'mesarios',
        'coordenador': 'coordenadores',
        'oficial_pesagem': 'oficiais_pesagem',
        'oficial_mesa': 'oficiais_mesa',
        'outro': 'outras',
    }
    categoria = categoria_map.get(vinculo.funcao, 'outras')
    
    despesa = Despesa.objects.create(
        campeonato=vinculo.campeonato,
        tipo='despesa',
        categoria=categoria,
        nome=f"Pró-labore: {vinculo.pessoa.nome_completo} - {funcao_display}",
        valor=vinculo.pro_labore,
        status='pendente',
        observacao=f"Pró-labore gerado automaticamente para {vinculo.pessoa.nome_completo} na função de {funcao_display}.",
        contato_nome=vinculo.pessoa.nome_completo,
        contato_whatsapp=vinculo.pessoa.telefone or ''
    )
    
    return despesa

@operacional_required
def administracao_insumos(request):
    """Gestão de Insumos e Estrutura"""
    campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
    
    # Processar ações via POST
    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        if acao == 'criar_insumo':
            if not campeonato_ativo:
                messages.error(request, 'Nenhum campeonato ativo encontrado.')
            else:
                try:
                    categoria_id = request.POST.get('categoria')
                    nome = request.POST.get('nome', '').strip()
                    valor = request.POST.get('valor', '').strip()
                    quantidade = request.POST.get('quantidade', '1').strip()
                    fornecedor = request.POST.get('fornecedor', '').strip()
                    contato_nome = request.POST.get('contato_nome', '').strip()
                    contato_whatsapp = request.POST.get('contato_whatsapp', '').strip()
                    observacao = request.POST.get('observacao', '').strip()
                    status = request.POST.get('status', 'pendente')
                    data_pagamento = request.POST.get('data_pagamento', '').strip() or None
                    
                    if not categoria_id or not nome or not valor:
                        messages.error(request, 'Preencha os campos obrigatórios: Categoria, Nome e Valor.')
                    else:
                        categoria = get_object_or_404(CategoriaInsumo, id=categoria_id, ativo=True)
                        insumo = InsumoEstrutura.objects.create(
                            campeonato=campeonato_ativo,
                            categoria=categoria,
                            nome=nome,
                            valor=float(valor.replace(',', '.')),
                            quantidade=int(quantidade) if quantidade else 1,
                            fornecedor=fornecedor or None,
                            contato_nome=contato_nome or None,
                            contato_whatsapp=contato_whatsapp or None,
                            observacao=observacao or None,
                            status=status,
                            data_pagamento=data_pagamento if data_pagamento else None
                        )
                        messages.success(request, f'Insumo "{insumo.nome}" cadastrado com sucesso!')
                except Exception as e:
                    messages.error(request, f'Erro ao cadastrar insumo: {str(e)}')
        
        elif acao == 'criar_categoria':
            try:
                nome = request.POST.get('nome_categoria', '').strip()
                descricao = request.POST.get('descricao_categoria', '').strip()
                
                if not nome:
                    messages.error(request, 'Informe o nome da categoria.')
                else:
                    categoria, created = CategoriaInsumo.objects.get_or_create(
                        nome=nome,
                        defaults={'descricao': descricao}
                    )
                    if created:
                        messages.success(request, f'Categoria "{categoria.nome}" criada com sucesso!')
                    else:
                        messages.warning(request, f'Categoria "{categoria.nome}" já existe.')
            except Exception as e:
                messages.error(request, f'Erro ao criar categoria: {str(e)}')
        
        elif acao == 'editar_insumo':
            insumo_id = request.POST.get('insumo_id')
            if insumo_id:
                try:
                    insumo = get_object_or_404(InsumoEstrutura, id=insumo_id)
                    insumo.categoria = get_object_or_404(CategoriaInsumo, id=request.POST.get('categoria'), ativo=True)
                    insumo.nome = request.POST.get('nome', '').strip()
                    insumo.valor = float(request.POST.get('valor', '0').replace(',', '.'))
                    insumo.quantidade = int(request.POST.get('quantidade', '1'))
                    insumo.fornecedor = request.POST.get('fornecedor', '').strip() or None
                    insumo.contato_nome = request.POST.get('contato_nome', '').strip() or None
                    insumo.contato_whatsapp = request.POST.get('contato_whatsapp', '').strip() or None
                    insumo.observacao = request.POST.get('observacao', '').strip() or None
                    insumo.status = request.POST.get('status', 'pendente')
                    data_pagamento = request.POST.get('data_pagamento', '').strip()
                    insumo.data_pagamento = data_pagamento if data_pagamento else None
                    insumo.save()
                    messages.success(request, f'Insumo "{insumo.nome}" atualizado com sucesso!')
                except Exception as e:
                    messages.error(request, f'Erro ao atualizar insumo: {str(e)}')
        
        elif acao == 'deletar_insumo':
            insumo_id = request.POST.get('insumo_id')
            if insumo_id:
                try:
                    insumo = get_object_or_404(InsumoEstrutura, id=insumo_id)
                    nome = insumo.nome
                    insumo.delete()
                    messages.success(request, f'Insumo "{nome}" removido com sucesso!')
                except Exception as e:
                    messages.error(request, f'Erro ao remover insumo: {str(e)}')
        
        elif acao == 'toggle_categoria':
            categoria_id = request.POST.get('categoria_id')
            if categoria_id:
                try:
                    categoria = get_object_or_404(CategoriaInsumo, id=categoria_id)
                    categoria.ativo = not categoria.ativo
                    categoria.save()
                    status = 'ativada' if categoria.ativo else 'desativada'
                    messages.success(request, f'Categoria "{categoria.nome}" {status} com sucesso!')
                except Exception as e:
                    messages.error(request, f'Erro ao alterar categoria: {str(e)}')
        
        return redirect('administracao_insumos')
    
    # GET: Listar insumos e categorias
    categorias = CategoriaInsumo.objects.all().order_by('nome')
    categorias_ativas = categorias.filter(ativo=True)
    
    if campeonato_ativo:
        insumos = InsumoEstrutura.objects.filter(
            campeonato=campeonato_ativo
        ).select_related('categoria').order_by('-data_cadastro')
        
        # Estatísticas
        total_insumos = insumos.count()
        total_valor = insumos.aggregate(total=Sum('valor'))['total'] or 0
        total_pago = insumos.filter(status='pago').aggregate(total=Sum('valor'))['total'] or 0
        total_pendente = insumos.filter(status='pendente').aggregate(total=Sum('valor'))['total'] or 0
        
        # Agrupar por categoria
        insumos_por_categoria = {}
        for insumo in insumos:
            cat_nome = insumo.categoria.nome
            if cat_nome not in insumos_por_categoria:
                insumos_por_categoria[cat_nome] = {
                    'categoria': insumo.categoria,
                    'insumos': [],
                    'total': 0
                }
            insumos_por_categoria[cat_nome]['insumos'].append(insumo)
            insumos_por_categoria[cat_nome]['total'] += insumo.valor
    else:
        insumos = InsumoEstrutura.objects.none()
        total_insumos = 0
        total_valor = 0
        total_pago = 0
        total_pendente = 0
        insumos_por_categoria = {}
    
    context = {
        'campeonato_ativo': campeonato_ativo,
        'categorias': categorias,
        'categorias_ativas': categorias_ativas,
        'insumos': insumos,
        'insumos_por_categoria': insumos_por_categoria,
        'total_insumos': total_insumos,
        'total_valor': total_valor,
        'total_pago': total_pago,
        'total_pendente': total_pendente,
    }
    
    return render(request, 'atletas/administracao/insumos.html', context)

@operacional_required
def administracao_patrocinios(request):
    return render(request, 'atletas/administracao/patrocinios.html')

@operacional_required
def administracao_relatorios(request):
    return render(request, 'atletas/administracao/relatorios.html')

@operacional_required
def administracao_cadastros_operacionais(request, tipo):
    """Redireciona para lista de pessoas (unificado)"""
    messages.info(request, 'Cadastros Operacionais foram unificados com Equipe Técnica.')
    return redirect('administracao_equipe_pessoas_lista')

@pode_criar_usuarios_required
def gerenciar_usuarios_operacionais(request):
    """Gerencia usuários operacionais - criar, editar, deletar"""
    import logging
    logger = logging.getLogger('atletas')
    
    if request.method == 'POST':
        try:
            # Criar novo usuário
            if request.POST.get('criar') == '1':
                username = request.POST.get('username', '').strip()
                password = request.POST.get('password', '').strip()
                email = request.POST.get('email', '').strip() or None
                primeiro_nome = request.POST.get('primeiro_nome', '').strip() or ''
                ultimo_nome = request.POST.get('ultimo_nome', '').strip() or ''
                telefone = request.POST.get('telefone', '').strip() or None
                
                if not username or not password:
                    messages.error(request, 'Nome de usuário e senha são obrigatórios.')
                elif User.objects.filter(username=username).exists():
                    messages.error(request, f'Usuário "{username}" já existe.')
                else:
                    # Criar usuário Django
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        email=email,
                        first_name=primeiro_nome,
                        last_name=ultimo_nome
                    )
                    
                    # Criar perfil operacional (30 dias de validade, senha não alterada)
                    from datetime import timedelta
                    data_expiracao = timezone.now() + timedelta(days=30)
                    
                    perfil = UsuarioOperacional.objects.create(
                        user=user,
                        pode_resetar_campeonato=False,
                        pode_criar_usuarios=False,
                        data_expiracao=data_expiracao,
                        ativo=True,
                        senha_alterada=False,  # Primeiro acesso precisa mudar senha
                        criado_por=request.user
                    )
                    
                    # Enviar WhatsApp com credenciais se telefone fornecido
                    if telefone:
                        try:
                            import urllib.parse
                            # Normalizar telefone
                            telefone_limpo = telefone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                            if telefone_limpo.startswith('0'):
                                telefone_limpo = telefone_limpo[1:]
                            if not telefone_limpo.startswith('55'):
                                telefone_limpo = '55' + telefone_limpo
                            
                            # Gerar URL de login
                            try:
                                dominio = request.get_host()
                                # Remover porta se estiver em desenvolvimento
                                if ':' in dominio:
                                    dominio = dominio.split(':')[0]
                            except:
                                dominio = 'localhost:8000'
                            
                            login_url = f"https://{dominio}/login/operacional/"
                            
                            # Mensagem WhatsApp
                            nome_completo = f"{primeiro_nome} {ultimo_nome}".strip() or username
                            mensagem = (
                                f"Olá {nome_completo}! 🥋\n\n"
                                f"Suas credenciais de acesso ao sistema SHIAI foram criadas:\n\n"
                                f"🔑 *Usuário:* {username}\n"
                                f"🔒 *Senha:* {password}\n\n"
                                f"*IMPORTANTE:* No primeiro acesso, você precisará alterar sua senha por segurança.\n\n"
                                f"Link de acesso:\n{login_url}\n\n"
                                f"Escolha 'Login Operacional' e use as credenciais acima.\n\n"
                                f"Agradecemos pela confiança! 🙏"
                            )
                            
                            mensagem_encoded = urllib.parse.quote(mensagem)
                            whatsapp_url = f"https://wa.me/{telefone_limpo}?text={mensagem_encoded}"
                            
                            messages.success(request, f'Usuário "{username}" criado com sucesso!')
                            messages.info(request, f'<a href="{whatsapp_url}" target="_blank" style="color: var(--color-success);">📱 Clique aqui para enviar WhatsApp com as credenciais</a>')
                        except Exception as e:
                            logger.error(f'Erro ao gerar link WhatsApp: {str(e)}', exc_info=True)
                            messages.warning(request, f'Usuário criado, mas não foi possível gerar link do WhatsApp. Erro: {str(e)}')
                    else:
                        messages.success(request, f'Usuário "{username}" criado com sucesso!')
                        messages.warning(request, 'Telefone não fornecido. Envie as credenciais manualmente.')
                    
                    logger.info(f'Usuário operacional criado: {username} por {request.user.username}')
                    return redirect('gerenciar_usuarios_operacionais')
            
            # Editar usuário existente
            elif request.POST.get('editar') == '1':
                user_id = request.POST.get('user_id')
                if not user_id:
                    messages.error(request, 'ID do usuário não fornecido.')
                else:
                    try:
                        user = User.objects.get(id=user_id)
                        perfil = user.perfil_operacional
                        
                        # Não permitir editar usuários protegidos (com permissões especiais)
                        if perfil.pode_resetar_campeonato or perfil.pode_criar_usuarios:
                            messages.error(request, 'Não é possível editar usuários protegidos.')
                        else:
                            # Atualizar senha se fornecida
                            nova_senha = request.POST.get('password', '').strip()
                            if nova_senha:
                                user.set_password(nova_senha)
                            
                            # Atualizar outros campos
                            email = request.POST.get('email', '').strip() or None
                            if email:
                                user.email = email
                            
                            user.first_name = request.POST.get('primeiro_nome', '').strip() or ''
                            user.last_name = request.POST.get('ultimo_nome', '').strip() or ''
                            user.save()
                            
                            # Atualizar status ativo
                            perfil.ativo = request.POST.get('ativo') == 'on'
                            perfil.save()
                            
                            messages.success(request, f'Usuário "{user.username}" atualizado com sucesso!')
                            logger.info(f'Usuário operacional editado: {user.username} por {request.user.username}')
                            return redirect('gerenciar_usuarios_operacionais')
                    except User.DoesNotExist:
                        messages.error(request, 'Usuário não encontrado.')
                    except UsuarioOperacional.DoesNotExist:
                        messages.error(request, 'Perfil operacional não encontrado.')
            
            # Deletar usuário
            elif request.POST.get('deletar') == '1':
                user_id = request.POST.get('user_id')
                if not user_id:
                    messages.error(request, 'ID do usuário não fornecido.')
                else:
                    try:
                        user = User.objects.get(id=user_id)
                        perfil = user.perfil_operacional
                        
                        # Não permitir deletar usuários protegidos
                        if perfil.pode_resetar_campeonato or perfil.pode_criar_usuarios:
                            messages.error(request, 'Não é possível remover usuários protegidos.')
                        else:
                            username = user.username
                            user.delete()  # Isso também deleta o perfil operacional (CASCADE)
                            messages.success(request, f'Usuário "{username}" removido com sucesso!')
                            logger.info(f'Usuário operacional deletado: {username} por {request.user.username}')
                            return redirect('gerenciar_usuarios_operacionais')
                    except User.DoesNotExist:
                        messages.error(request, 'Usuário não encontrado.')
                    except UsuarioOperacional.DoesNotExist:
                        messages.error(request, 'Perfil operacional não encontrado.')
        
        except Exception as e:
            logger.error(f'Erro ao gerenciar usuário operacional: {str(e)}', exc_info=True)
            messages.error(request, f'Erro ao processar solicitação: {str(e)}')
    
    # GET: Listar todos os usuários operacionais (exceto o usuário atual)
    usuarios_operacionais = UsuarioOperacional.objects.select_related('user').exclude(
        user=request.user
    ).order_by('-user__date_joined')
    
    # Garantir que o usuário atual tenha perfil operacional vitalício
    try:
        perfil_atual = request.user.perfil_operacional
        # Se não for vitalício, tornar vitalício
        if perfil_atual.data_expiracao is not None:
            perfil_atual.data_expiracao = None
        # Garantir que senha já foi alterada (não forçar mudança)
        if not perfil_atual.senha_alterada:
            perfil_atual.senha_alterada = True
        perfil_atual.save()
    except UsuarioOperacional.DoesNotExist:
        # Criar perfil operacional vitalício para o usuário atual
        UsuarioOperacional.objects.create(
            user=request.user,
            pode_resetar_campeonato=True,
            pode_criar_usuarios=True,
            data_expiracao=None,  # Vitalício
            ativo=True,
            senha_alterada=True  # Usuário atual não precisa mudar senha
        )
    
    return render(request, 'atletas/administracao/gerenciar_usuarios.html', {
        'usuarios_operacionais': usuarios_operacionais
    })


@operacional_required
def alterar_senha_obrigatorio(request):
    """View para alteração obrigatória de senha no primeiro acesso"""
    import logging
    logger = logging.getLogger('atletas')
    
    try:
        perfil = request.user.perfil_operacional
    except UsuarioOperacional.DoesNotExist:
        messages.error(request, 'Perfil operacional não encontrado.')
        return redirect('login')
    
    # Se já alterou a senha, redirecionar
    if perfil.senha_alterada:
        return _redirect_dashboard(request, request.user)
    
    if request.method == 'POST':
        senha_atual = request.POST.get('senha_atual', '').strip()
        nova_senha = request.POST.get('nova_senha', '').strip()
        confirmar_senha = request.POST.get('confirmar_senha', '').strip()
        
        # Validar campos
        if not senha_atual or not nova_senha or not confirmar_senha:
            messages.error(request, 'Preencha todos os campos.')
        elif nova_senha != confirmar_senha:
            messages.error(request, 'As senhas não coincidem.')
        elif len(nova_senha) < 6:
            messages.error(request, 'A nova senha deve ter pelo menos 6 caracteres.')
        elif not request.user.check_password(senha_atual):
            messages.error(request, 'Senha atual incorreta.')
        else:
            # Alterar senha
            request.user.set_password(nova_senha)
            request.user.save()
            
            # Marcar como senha alterada
            perfil.senha_alterada = True
            perfil.save()
            
            messages.success(request, 'Senha alterada com sucesso!')
            logger.info(f'Usuário {request.user.username} alterou senha no primeiro acesso')
            return _redirect_dashboard(request, request.user)
    
    return render(request, 'atletas/alterar_senha_obrigatorio.html')

# ========== MÓDULO DE PAGAMENTOS ==========

@academia_required
def academia_enviar_comprovante(request, campeonato_id):
    """Enviar comprovante de pagamento pela academia"""
    academia = request.academia
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    
    # Calcular valor total
    inscricoes = Inscricao.objects.filter(
        atleta__academia=academia,
        campeonato=campeonato
    )
    
    valor_federado = campeonato.valor_inscricao_federado or 0
    valor_nao_federado = campeonato.valor_inscricao_nao_federado or 0
    
    valor_total = sum(
        valor_federado if ins.atleta.federado else valor_nao_federado
        for ins in inscricoes
    )
    
    # Buscar ou criar conferência de pagamento
    from .views_conferencia_pagamentos import calcular_valor_esperado_academia
    valor_esperado, qtd_atletas = calcular_valor_esperado_academia(academia, campeonato)
    
    conferencia_existente = ConferenciaPagamento.objects.filter(
        academia=academia,
        campeonato=campeonato
    ).first()
    
    if request.method == 'POST':
        if 'comprovante' in request.FILES:
            comprovante = request.FILES['comprovante']
            
            # Validar tipo de arquivo
            extensao = comprovante.name.split('.')[-1].lower()
            if extensao not in ['jpg', 'jpeg', 'png', 'pdf', 'heic']:
                messages.error(request, 'Formato de arquivo inválido. Use JPG, PNG, PDF ou HEIC.')
                return redirect('academia_enviar_comprovante', campeonato_id=campeonato_id)
            
            # Criar ou atualizar conferência de pagamento
            if conferencia_existente:
                conferencia_existente.comprovante = comprovante
                conferencia_existente.valor_esperado = valor_esperado
                conferencia_existente.quantidade_atletas = qtd_atletas
                # Mantém status atual (não muda automaticamente ao enviar comprovante)
                conferencia_existente.save()
                messages.success(request, 'Comprovante atualizado com sucesso! Aguarde conferência do operador.')
            else:
                conferencia = ConferenciaPagamento.objects.create(
                    academia=academia,
                    campeonato=campeonato,
                    valor_esperado=valor_esperado,
                    quantidade_atletas=qtd_atletas,
                    comprovante=comprovante,
                    status='PENDENTE'  # Permanece pendente até conferência manual
                )
                messages.success(request, 'Comprovante enviado com sucesso! Aguarde conferência do operador.')
            
            return redirect('academia_evento', campeonato_id=campeonato_id)
        else:
            messages.error(request, 'Por favor, selecione um arquivo.')
    
    context = {
        'academia': academia,
        'campeonato': campeonato,
        'valor_total': valor_esperado,
        'inscricoes': inscricoes,
        'conferencia': conferencia_existente,
    }
    
    return render(request, 'atletas/academia/enviar_comprovante.html', context)

@operacional_required
def validacao_pagamentos(request):
    """
    DEPRECADO: Esta view foi descontinuada.
    Use 'conferencia_pagamentos_lista' ao invés desta.
    Redireciona para a conferência de pagamentos.
    """
    messages.info(request, 'O módulo de Validação de Pagamentos foi unificado com a Conferência de Pagamentos.')
    return redirect('conferencia_pagamentos_lista')

@operacional_required
def validar_pagamento(request, pagamento_id):
    """
    DEPRECADO: Esta view foi descontinuada.
    Use 'conferencia_pagamentos_detalhe' e 'conferencia_pagamentos_salvar' ao invés desta.
    Redireciona para a conferência de pagamentos.
    """
    messages.info(request, 'O módulo de Validação de Pagamentos foi unificado com a Conferência de Pagamentos.')
    return redirect('conferencia_pagamentos_lista')

@operacional_required
def rejeitar_pagamento(request, pagamento_id):
    """
    DEPRECADO: Esta view foi descontinuada.
    Use 'conferencia_pagamentos_detalhe' e 'conferencia_pagamentos_salvar' com status DIVERGENTE ao invés desta.
    Redireciona para a conferência de pagamentos.
    """
    messages.info(request, 'O módulo de Validação de Pagamentos foi unificado com a Conferência de Pagamentos.')
    return redirect('conferencia_pagamentos_lista')
