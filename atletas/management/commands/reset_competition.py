from django.core.management.base import BaseCommand

from atletas.models import AcademiaPontuacao, Atleta, Campeonato, Chave, Luta


class Command(BaseCommand):
    help = "Remove lutas, chaves, atletas e campeonatos para reiniciar a competição."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Executa sem pedir confirmação interativa.",
        )

    def handle(self, *args, **options):
        if not options.get("force"):
            confirm = input(
                "Isso apagará lutas, chaves, atletas e campeonatos. Deseja continuar? (digite 'SIM' para confirmar): "
            )
            if confirm.strip().upper() != "SIM":
                self.stdout.write(self.style.WARNING("Operação cancelada."))
                return

        deletions = {
            "lutas": Luta.objects.count(),
            "chaves": Chave.objects.count(),
            "atletas": Atleta.objects.count(),
            "pontuacoes": AcademiaPontuacao.objects.count(),
            "campeonatos": Campeonato.objects.count(),
        }

        # Ordem importa para evitar violação de FK
        Luta.objects.all().delete()
        Chave.objects.all().delete()
        AcademiaPontuacao.objects.all().delete()
        Atleta.objects.all().delete()
        Campeonato.objects.all().delete()

        for model_name, count in deletions.items():
            self.stdout.write(
                self.style.SUCCESS(f"Removidos {count} registro(s) de {model_name}.")
            )

        self.stdout.write(
            self.style.SUCCESS("Dados removidos. Pronto para nova competição.")
        )
