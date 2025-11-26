from django.core.management.base import BaseCommand

from atletas.models import Atleta, Chave
from atletas.utils import gerar_chave, get_resultados_chave


class Command(BaseCommand):
    help = (
        "Gera ou refaz chaves (sem Festival). "
        "Cria novas chaves onde não existem e REFAZ apenas as chaves que ainda "
        "não têm nenhum resultado (sem medalhas). Chaves com resultados são mantidas."
    )

    def handle(self, *args, **options):
        # Combinações de atletas aptos (sem Festival)
        combinacoes = (
            Atleta.objects.filter(status="OK")
            .exclude(classe="Festival")
            .values_list("classe", "sexo", "categoria_nome")
            .distinct()
        )

        total_criadas = 0
        total_refeitas = 0
        total_mantidas = 0

        for classe, sexo, categoria_nome in combinacoes:
            qs = Chave.objects.filter(classe=classe, sexo=sexo, categoria=categoria_nome)

            if not qs.exists():
                # Não existe chave ainda -> criar
                gerar_chave(categoria_nome, classe, sexo)
                total_criadas += 1
                continue

            chave = qs.first()

            # Verificar se já existem resultados (medalhas) para esta chave
            resultados = get_resultados_chave(chave)
            if resultados:
                # Já tem resultado -> manter, não refazer
                total_mantidas += 1
                continue

            # Sem resultados -> refazer chave (regera lutas com base nos atletas atuais)
            gerar_chave(categoria_nome, classe, sexo)
            total_refeitas += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Chaves criadas: {total_criadas}. "
                f"Chaves refeitas (sem resultados): {total_refeitas}. "
                f"Chaves mantidas (já com resultados): {total_mantidas}."
            )
        )




