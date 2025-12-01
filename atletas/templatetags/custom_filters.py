"""
Filtros customizados para templates Django
"""
from django import template
import re

register = template.Library()


@register.filter(name='whatsapp_clean')
def whatsapp_clean(value):
    """
    Limpa o telefone removendo espaços, hífens, parênteses e outros caracteres
    para uso em links do WhatsApp.
    Exemplo: "(11) 98765-4321" -> "11987654321"
    """
    if not value:
        return ''
    
    # Remove todos os caracteres não numéricos, exceto o sinal de +
    cleaned = re.sub(r'[^\d+]', '', str(value))
    return cleaned


@register.filter(name='replace')
def replace(value, arg):
    """
    Filtro replace customizado para templates Django.
    Uso: {{ value|replace:"old":"new" }}
    """
    if not value:
        return ''
    
    # O arg deve vir no formato "old:new"
    if ':' not in str(arg):
        return value
    
    old, new = str(arg).split(':', 1)
    return str(value).replace(old, new)


