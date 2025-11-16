from django.core.management.base import BaseCommand

from atletas.models import Atleta


class Command(BaseCommand):
    help = "Marca todos os atletas como aprovados na pesagem (status OK), limpando motivo_ajuste"

    def handle(self, *args, **options):
        atualizados = Atleta.objects.all().update(status="OK", motivo_ajuste="")

        self.stdout.write(
            self.style.SUCCESS(
                f"Todos os atletas foram marcados como aprovados na pesagem. Registros atualizados: {atualizados}."
            )
        )


