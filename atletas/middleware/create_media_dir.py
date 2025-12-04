import os


def create_media_directory(get_response):
    """
    Middleware simples que garante que /var/data/media exista no Render.
    Evita erro 404 nas imagens.
    """
    media_root = os.environ.get("RENDER") and "/var/data/media"

    if media_root and not os.path.exists(media_root):
        try:
            os.makedirs(media_root, exist_ok=True)
            os.chmod(media_root, 0o777)
        except Exception:
            pass

    def middleware(request):
        return get_response(request)

    return middleware

