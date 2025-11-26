from django.core.management.base import BaseCommand

from atletas.models import Atleta, Academia


class Command(BaseCommand):
    help = "Importa os 21 alunos de Festival do Campeonato Verbo Divino para a academia IJC"

    def handle(self, *args, **options):
        # Garantir que a academia exista
        academia, _ = Academia.objects.get_or_create(
            nome="IJC",
            defaults={"cidade": "", "estado": ""}
        )

        atletas_data = [
            ("João Gabriel Lopes Cavalcanti", "Branca", "M"),
            ("Pedro Francisco Britte Bruno Valva", "Branca", "M"),
            ("Enrico Saboya Cambraia", "Branca", "M"),
            ("Benjamin Nardoto Conde Baltazar", "Branca", "M"),
            ("Wenzo Primo da Silva Viana", "Branca", "M"),
            ("Lucas Ramos Martins", "Cinza", "M"),
            ("Bento Bizarro Werneck", "Branca", "M"),
            ("Miguel Ruiz de Oliveira Alves", "Branca", "M"),
            ("Gael Ferreira Pires", "Branca", "M"),
            ("Arthur Tostis dos Santos", "Cinza", "M"),
            ("Hemily Laura Rodrigues Velozo", "Branca", "F"),
            ("Nina Carreiro Alves Sodré", "Branca", "F"),
            ("Davi Consani Ozorio Machado", "Branca", "M"),
            ("Samuel Alves Silva", "Cinza", "M"),
            ("Pedro Magalhães Collet Ribeiro", "Cinza", "M"),
            ("Helena Pimentel Castro de Almeida", "Branca", "F"),
            ("Martin Coutinho Parreira Braule", "Cinza", "M"),
            ("Bernardo Gehtti Rodrgues Nader", "Branca", "M"),
            ("Felipe Ghetti Rodrgues Nader", "Branca", "M"),
            ("Davi Carvalho Cruz", "Branca", "M"),
            ("Benício Velozo Januário", "Branca", "M"),
        ]

        criados = 0
        ano_nasc = 2018

        for nome, faixa, sexo in atletas_data:
            atleta, created = Atleta.objects.get_or_create(
                nome=nome,
                ano_nasc=ano_nasc,
                sexo=sexo,
                faixa=faixa,
                academia=academia,
                classe="Festival",
                categoria_nome="Festival",
                defaults={
                    "categoria_limite": "Não compete",
                    "status": "OK",
                },
            )
            if created:
                criados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Importação concluída. Atletas criados: {criados}"
            )
        )


