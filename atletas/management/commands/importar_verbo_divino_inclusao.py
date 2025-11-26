from django.core.management.base import BaseCommand

from atletas.models import Atleta, Academia


class Command(BaseCommand):
    help = "Importa atletas de inclusão (necessidades especiais) do Campeonato Verbo Divino para a academia IJC"

    def handle(self, *args, **options):
        # Garantir que a academia exista
        academia, _ = Academia.objects.get_or_create(
            nome="IJC",
            defaults={"cidade": "", "estado": ""},
        )

        # nome, classe_label, faixa, categoria, ano_nasc
        # anos de nascimento escolhidos para ficarem compatíveis com a classe:
        # SUB 9  -> idade 8 (2017), SUB 11 -> idade 10 (2015), SUB 15 -> idade 14 (2011)
        atletas_inclusao = [
            ("Miguel Agostinho de Souza (Inclusão)", "SUB 9", "Branca", "Leve", 2017),
            ("Gabriel Lucca Capote Otoni (Inclusão)", "SUB 9", "Branca", "Pesado", 2017),
            ("João Pedro Lorenzon Andrade (Inclusão)", "SUB 11", "Cinza", "Médio", 2015),
            ("João Gulherme Costa Toledo Santos", "SUB 15", "Amarela", "M. Médio", 2011),
        ]

        criados = 0

        for nome, classe, faixa, categoria_nome, ano_nasc in atletas_inclusao:
            # Inferir sexo pelo nome (todos aqui são masculinos)
            sexo = "M"

            atleta, created = Atleta.objects.get_or_create(
                nome=nome,
                ano_nasc=ano_nasc,
                sexo=sexo,
                faixa=faixa,
                academia=academia,
                defaults={
                    "classe": classe,
                    "categoria_nome": categoria_nome,
                    "categoria_limite": "",
                    "status": "OK",
                    "motivo_ajuste": "Inclusão - atleta com necessidades especiais"
                    if "Inclusão" in nome
                    else "",
                },
            )

            if created:
                criados += 1
            else:
                # Atualizar apenas a classe e observação, sem mexer em peso ou outros campos
                atleta.classe = classe
                if "Inclusão" in nome:
                    atleta.motivo_ajuste = "Inclusão - atleta com necessidades especiais"
                atleta.save(update_fields=["classe", "motivo_ajuste"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Importação/atualização concluída. Atletas de inclusão processados: {criados} (novos)."
            )
        )


