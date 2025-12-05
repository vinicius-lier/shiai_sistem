import os
from django.conf import settings


def create_media_directory(get_response):
    """
    Middleware simples que garante que MEDIA_ROOT e subpastas existam no Render.
    Evita erro 404 nas imagens de academias e atletas.
    """
    # Garantir que a pasta media existe (tanto local quanto Render)
    media_root = str(settings.MEDIA_ROOT)
    
    # Subpastas necessárias para fotos
    subpastas = [
        'fotos/academias',
        'fotos/atletas',
        'fotos/temp',
        'documentos/temp',
        'comprovantes',
    ]
    
    def criar_pastas():
        """Cria a pasta media e todas as subpastas necessárias"""
        if not os.path.exists(media_root):
            try:
                os.makedirs(media_root, exist_ok=True)
                os.chmod(media_root, 0o755)
            except Exception:
                pass
        
        # Criar subpastas
        for subpasta in subpastas:
            pasta_completa = os.path.join(media_root, subpasta)
            if not os.path.exists(pasta_completa):
                try:
                    os.makedirs(pasta_completa, exist_ok=True)
                    os.chmod(pasta_completa, 0o755)
                except Exception:
                    pass
    
    # Criar pastas na inicialização
    criar_pastas()

    def middleware(request):
        # Verificar novamente a cada requisição (caso tenha sido deletado)
        criar_pastas()
        return get_response(request)

    return middleware

