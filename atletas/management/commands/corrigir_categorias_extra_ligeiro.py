from django.core.management.base import BaseCommand

from atletas.models import Categoria


class Command(BaseCommand):
    help = "Renomeia categorias 'Extra Ligeiro' para 'Super Ligeiro' em todas as classes"

    def handle(self, *args, **options):
        alteradas = 0

        categorias = Categoria.objects.filter(categoria_nome="Extra Ligeiro")
        for cat in categorias:
            cat.categoria_nome = "Super Ligeiro"
            # Atualiza o label para manter padrão usado no sistema
            cat.label = f"{cat.classe} - {cat.sexo} - Super Ligeiro"
            cat.save(update_fields=["categoria_nome", "label"])
            alteradas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Categorias 'Extra Ligeiro' renomeadas para 'Super Ligeiro': {alteradas}."
            )
        )


