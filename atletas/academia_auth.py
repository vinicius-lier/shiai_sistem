"""
Sistema de autenticação para Login de Academia e Operacional
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from .models import Academia, UsuarioOperacional, AcademiaCampeonatoSenha


def academia_required(view_func):
    """Decorator para verificar se o usuário está logado como academia"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        academia_id = request.session.get('academia_id')
        credencial_id = request.session.get('credencial_id')
        
        if not academia_id:
            messages.warning(request, 'Você precisa fazer login como academia para acessar esta página.')
            return redirect('academia_login')
        
        try:
            academia = Academia.objects.get(id=academia_id, ativo_login=True)
            
            # Verificar se credencial temporária está expirada
            if credencial_id:
                try:
                    credencial = AcademiaCampeonatoSenha.objects.get(id=credencial_id)
                    if credencial.esta_expirado:
                        messages.error(request, 'O acesso temporário da sua academia expirou. Para acessar novos eventos, aguarde o envio de novo convite.')
                        request.session.flush()
                        return redirect('academia_login')
                except AcademiaCampeonatoSenha.DoesNotExist:
                    pass
            
            request.academia = academia  # Adicionar academia ao request
            return view_func(request, *args, **kwargs)
        except Academia.DoesNotExist:
            messages.error(request, 'Academia não encontrada ou inativa.')
            request.session.flush()
            return redirect('academia_login')
    
    return _wrapped_view


def operacional_required(view_func):
    """Decorator para verificar se é acesso operacional (não academia) - SEMPRE exige login e senha"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Remover slug da organização dos kwargs para evitar TypeError em views que não o recebem
        kwargs.pop('organizacao_slug', None)
        # Se está logado como academia, redirecionar
        if request.session.get('academia_id'):
            messages.warning(request, 'Você está logado como academia. Faça logout para acessar o módulo operacional.')
            return redirect('academia_painel')
        
        # Verificar se está autenticado operacionalmente (Django auth) - OBRIGATÓRIO
        if not request.user.is_authenticated:
            messages.warning(request, 'Você precisa fazer login operacional para acessar esta página.')
            return redirect('login')
        
        # Superusers sempre têm acesso
        if request.user.is_superuser:
            # Garantir que superuser tenha perfil
            try:
                perfil = request.user.perfil_operacional
                if not perfil.senha_alterada:
                    perfil.senha_alterada = True
                    perfil.data_expiracao = None
                    perfil.pode_resetar_campeonato = True
                    perfil.pode_criar_usuarios = True
                    perfil.save()
            except UsuarioOperacional.DoesNotExist:
                from datetime import timedelta
                UsuarioOperacional.objects.create(
                    user=request.user,
                    pode_resetar_campeonato=True,
                    pode_criar_usuarios=True,
                    data_expiracao=None,
                    ativo=True,
                    senha_alterada=True
                )
            return view_func(request, *args, **kwargs)
        
        # Verificar se o usuário tem perfil operacional e se está ativo
        try:
            perfil = request.user.perfil_operacional
            if not perfil.ativo:
                messages.error(request, 'Seu acesso operacional foi desativado.')
                return redirect('login')
            
            # Verificar expiração
            if perfil.esta_expirado:
                messages.error(request, f'Seu acesso operacional expirou em {perfil.data_expiracao.strftime("%d/%m/%Y")}.')
                return redirect('login')
        except UsuarioOperacional.DoesNotExist:
            # Usuário não tem perfil operacional - criar um padrão (30 dias)
            from datetime import timedelta
            perfil = UsuarioOperacional.objects.create(
                user=request.user,
                pode_resetar_campeonato=False,
                pode_criar_usuarios=False,
                data_expiracao=timezone.now() + timedelta(days=30),
                ativo=True,
                senha_alterada=False  # Precisa alterar senha
            )
            messages.info(request, 'Perfil operacional criado. Acesso válido por 30 dias.')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def operacional_ou_academia_required(view_func):
    """
    Permite acesso tanto para login operacional quanto para login de academia.
    - Se houver sessão de academia, reaproveita a validação de academia_required.
    - Caso contrário, valida como operacional.
    """
    academia_wrapper = academia_required(view_func)
    operacional_wrapper = operacional_required(view_func)

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.session.get('academia_id'):
            return academia_wrapper(request, *args, **kwargs)
        return operacional_wrapper(request, *args, **kwargs)

    return _wrapped_view

def pode_resetar_required(view_func):
    """Decorator para verificar se o usuário pode resetar campeonato"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Você precisa estar autenticado.')
            return redirect('login')
        
        try:
            perfil = request.user.perfil_operacional
            if not perfil.pode_resetar_campeonato:
                messages.error(request, 'Você não tem permissão para resetar campeonato.')
                organizacao = getattr(request, "organizacao", None)
                if organizacao and getattr(organizacao, "slug", None):
                    return redirect('index', organizacao_slug=organizacao.slug)
                return redirect('landing_publica')
        except UsuarioOperacional.DoesNotExist:
            messages.error(request, 'Você não tem permissão para resetar campeonato.')
            organizacao = getattr(request, "organizacao", None)
            if organizacao and getattr(organizacao, "slug", None):
                return redirect('index', organizacao_slug=organizacao.slug)
            return redirect('landing_publica')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def pode_criar_usuarios_required(view_func):
    """Decorator para verificar se o usuário pode criar outros usuários
    Permite acesso para:
    - Superusers (is_superuser = True)
    - Usuários com organizador (user.profile.organizador)
    - Usuários com perfil_operacional.pode_criar_usuarios = True
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Você precisa estar autenticado.')
            return redirect('login')
        
        # Superusers sempre têm acesso
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # Usuários com organizador têm acesso
        try:
            if hasattr(request.user, 'profile') and request.user.profile.organizador:
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        
        # Usuários com perfil operacional e permissão específica
        try:
            perfil = request.user.perfil_operacional
            if perfil.pode_criar_usuarios:
                return view_func(request, *args, **kwargs)
        except UsuarioOperacional.DoesNotExist:
            pass
        
        # Se chegou aqui, não tem permissão
        messages.error(request, 'Você não tem permissão para criar usuários operacionais.')
        # Se estivermos em um contexto multi-tenant, tentar redirecionar para o dashboard da organização
        organizacao = getattr(request, "organizacao", None)
        if organizacao and getattr(organizacao, "slug", None):
            return redirect('index', organizacao_slug=organizacao.slug)
        return redirect('landing_publica')
    
    return _wrapped_view

from functools import wraps
from django.shortcuts import redirect
from .models import AcademiaCampeonatoSenha, Academia

def academia_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        academia_id = request.session.get("academia_id")

        # Se não tem sessão → redireciona
        if not academia_id:
            return redirect("academia_login")

        # Carrega a academia na requisição
        try:
            request.academia = Academia.objects.get(id=academia_id)
        except Academia.DoesNotExist:
            request.session.flush()
            return redirect("academia_login")

        return view_func(request, *args, **kwargs)

    return wrapper


def organizacao_required(view_func):
    """
    Garante que a request está associada a uma organização válida.
    Usado apenas em rotas multi-tenant (que passam por OrganizacaoMiddleware).
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Remover slug da organização dos kwargs para evitar TypeError em views que não o recebem
        kwargs.pop('organizacao_slug', None)
        organizacao = getattr(request, "organizacao", None)
        if not organizacao or not getattr(organizacao, "slug", None):
            messages.error(request, "Organização não encontrada ou inativa.")
            return redirect("landing_publica")
        return view_func(request, *args, **kwargs)

    return _wrapped_view
