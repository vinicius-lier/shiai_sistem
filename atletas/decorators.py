from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def academia_required(view_func):
    """Decorator que verifica se o usuário é do tipo academia"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'Perfil de usuário não encontrado.')
            return redirect('login_tipo')
        
        if request.user.profile.tipo_usuario != 'academia':
            messages.error(request, 'Acesso restrito a academias.')
            return redirect('index')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def operacional_required(view_func):
    """Decorator que verifica se o usuário é operacional ou admin"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'Perfil de usuário não encontrado.')
            return redirect('login_tipo')
        
        if request.user.profile.tipo_usuario not in ['operacional', 'admin']:
            messages.error(request, 'Acesso restrito a usuários operacionais.')
            return redirect('academia_painel')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """Decorator que verifica se o usuário é admin ou superuser"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        if not hasattr(request.user, 'profile'):
            messages.error(request, 'Perfil de usuário não encontrado.')
            return redirect('login_tipo')
        
        if request.user.profile.tipo_usuario != 'admin' and not request.user.is_superuser:
            messages.error(request, 'Acesso restrito a administradores.')
            return redirect('index')
        
        return view_func(request, *args, **kwargs)
    return wrapper

