import os
from django.conf import settings


def create_media_directory(get_response):
    """
    Middleware simples que garante que MEDIA_ROOT exista no Render.
    Evita erro 404 nas imagens.
    """
    # Garantir que a pasta media existe (tanto local quanto Render)
    media_root = str(settings.MEDIA_ROOT)
    
    if not os.path.exists(media_root):
        try:
            os.makedirs(media_root, exist_ok=True)
            # Dar permissões adequadas
            os.chmod(media_root, 0o755)
        except Exception as e:
            # Log do erro em produção (se necessário)
            pass

    def middleware(request):
        # Verificar novamente a cada requisição (caso tenha sido deletado)
        if not os.path.exists(media_root):
            try:
                os.makedirs(media_root, exist_ok=True)
                os.chmod(media_root, 0o755)
            except Exception:
                pass
        return get_response(request)

    return middleware

