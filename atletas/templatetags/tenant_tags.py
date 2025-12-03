"""
Template tags para verificar permissões de multi-tenant
"""
from django import template

register = template.Library()


@register.filter
def pode_gerenciar_usuarios(user):
    """
    Verifica se o usuário pode gerenciar usuários operacionais.
    Retorna True para:
    - Superusers
    - Usuários com organizador
    - Usuários com perfil_operacional.pode_criar_usuarios = True
    """
    if not user or not user.is_authenticated:
        return False
    
    # Superusers sempre têm acesso
    if user.is_superuser:
        return True
    
    # Usuários com organizador têm acesso
    try:
        if hasattr(user, 'profile') and user.profile.organizador:
            return True
    except Exception:
        pass
    
    # Usuários com perfil operacional e permissão específica
    try:
        if hasattr(user, 'perfil_operacional') and user.perfil_operacional.pode_criar_usuarios:
            return True
    except Exception:
        pass
    
    return False

