"""
Utilitário para registrar histórico de ações no sistema
"""
from django.utils import timezone
from .models import HistoricoSistema
import json


def registrar_historico(tipo_acao, descricao, usuario=None, campeonato=None, 
                        academia=None, atleta=None, dados_extras=None, request=None):
    """
    Registra uma ação no histórico do sistema
    
    Args:
        tipo_acao: Tipo da ação (ver TIPO_ACAO_CHOICES em HistoricoSistema)
        descricao: Descrição da ação
        usuario: Usuário que realizou a ação
        campeonato: Campeonato relacionado (opcional)
        academia: Academia relacionada (opcional)
        atleta: Atleta relacionado (opcional)
        dados_extras: Dicionário com dados extras (opcional)
        request: Objeto request para extrair IP (opcional)
    """
    ip_address = None
    if request:
        # Tentar pegar o IP real do cliente
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
    
    # Converter dados_extras para JSON se necessário
    dados_json = None
    if dados_extras:
        try:
            dados_json = json.dumps(dados_extras) if isinstance(dados_extras, dict) else dados_extras
        except:
            dados_json = str(dados_extras)
    
    HistoricoSistema.objects.create(
        tipo_acao=tipo_acao,
        descricao=descricao,
        usuario=usuario,
        campeonato=campeonato,
        academia=academia,
        atleta=atleta,
        dados_extras=dados_json,
        ip_address=ip_address,
        data_hora=timezone.now()
    )



