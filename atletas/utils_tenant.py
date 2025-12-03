"""
Utilitários para multi-tenant
"""
from django.contrib.auth.models import User


def get_organizador_usuario(user):
    """
    Retorna o organizador do usuário.
    Se o usuário tiver profile.organizador, retorna ele.
    Caso contrário, retorna None.
    """
    if not user or not user.is_authenticated:
        return None
    
    try:
        if hasattr(user, 'profile') and user.profile.organizador:
            return user.profile.organizador
    except Exception:
        pass
    
    return None


def filtrar_por_organizador(queryset, user, campo_organizador='organizador'):
    """
    Filtra um queryset por organizador do usuário.
    
    Args:
        queryset: QuerySet a ser filtrado
        user: Usuário autenticado
        campo_organizador: Nome do campo que contém o organizador (padrão: 'organizador')
    
    Returns:
        QuerySet filtrado ou vazio se usuário não tiver organizador
    """
    organizador = get_organizador_usuario(user)
    if not organizador:
        return queryset.none()
    
    filtro = {campo_organizador: organizador}
    return queryset.filter(**filtro)


def verificar_organizador_objeto(obj, user, campo_organizador='organizador'):
    """
    Verifica se um objeto pertence ao organizador do usuário.
    
    Args:
        obj: Objeto a ser verificado
        user: Usuário autenticado
        campo_organizador: Nome do campo que contém o organizador
    
    Returns:
        True se o objeto pertence ao organizador do usuário, False caso contrário
    """
    organizador = get_organizador_usuario(user)
    if not organizador:
        return False
    
    obj_organizador = getattr(obj, campo_organizador, None)
    return obj_organizador == organizador

