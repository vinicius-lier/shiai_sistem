from django.core.management.base import BaseCommand

from atletas.models import Atleta
from atletas.utils import calcular_classe


class Command(BaseCommand):
    help = "Recalcula a classe de todos os atletas com base no ano de nascimento"

    def handle(self, *args, **options):
        atualizados = 0
        mantidos_festival = 0

        for atleta in Atleta.objects.all():
            # Não mexer em atletas marcados explicitamente como Festival
            # (casos especiais de festival, independentes da idade oficial)
            if atleta.classe == "Festival":
                mantidos_festival += 1
                continue

            nova_classe = calcular_classe(atleta.ano_nasc)

            if atleta.classe != nova_classe:
                atleta.classe = nova_classe
                atleta.save(update_fields=["classe"])
                atualizados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Recalculo concluído. Classes atualizadas: {atualizados}. "
                f"Atletas mantidos como Festival: {mantidos_festival}."
            )
        )


