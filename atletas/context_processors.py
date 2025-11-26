from .models import Campeonato
from django.db import connection


def campeonato_ativo(request):
    """Context processor para disponibilizar o campeonato ativo em todos os templates"""
    try:
        campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
        return {'campeonato_ativo': campeonato_ativo}
    except Exception:
        # Em caso de erro (por exemplo, durante migrações), retorna None
        return {'campeonato_ativo': None}

