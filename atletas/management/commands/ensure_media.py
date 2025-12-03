from django.core.management.base import BaseCommand
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Garante que a pasta MEDIA_ROOT existe'

    def handle(self, *args, **kwargs):
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        self.stdout.write(
            self.style.SUCCESS(
                f'Pasta MEDIA criada/verificada: {settings.MEDIA_ROOT}'
            )
        )

