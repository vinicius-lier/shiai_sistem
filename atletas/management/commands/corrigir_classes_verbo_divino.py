from django.core.management.base import BaseCommand

from atletas.models import Atleta


class Command(BaseCommand):
    help = "Corrige manualmente a classe dos atletas do Campeonato Verbo Divino sem alterar pesos"

    def handle(self, *args, **options):
        """
        Usa diretamente a tabela enviada (nome, classe) para ajustar apenas o campo `classe`.
        Mantém pesos, faixas, categorias e demais campos como estão.
        """

        # Conversão do texto da tabela para o padrão usado internamente
        mapa_classe = {
            "Festival": "Festival",
            "Sub 9": "SUB 9",
            "Sub 11": "SUB 11",
            "Sub 13": "SUB 13",
            "Sub 15": "SUB 15",
            "Sub 18": "SUB 18",
        }

        # Lista (nome exato no cadastro, classe como veio na tabela)
        linhas = [
            ("João Gabriel Lopes Cavalcanti", "Festival"),
            ("Pedro Francisco Britte Bruno Valva", "Festival"),
            ("Enrico Saboya Cambraia", "Festival"),
            ("Benjamin Nardoto Conde Baltazar", "Festival"),
            ("Wenzo Primo da Silva Viana", "Festival"),
            ("Lucas Ramos Martins", "Festival"),
            ("Bento Bizarro Werneck", "Festival"),
            ("Miguel Ruiz de Oliveira Alves", "Festival"),
            ("Gael Ferreira Pires", "Festival"),
            ("Arthur Tostis dos Santos", "Festival"),
            ("Hemily Laura Rodrigues Velozo", "Festival"),
            ("Nina Carreiro Alves Sodré", "Festival"),
            ("Davi Consani Ozorio Machado", "Festival"),
            ("Samuel Alves Silva", "Festival"),
            ("Pedro Magalhães Collet Ribeiro", "Festival"),
            ("Helena Pimentel Castro de Almeida", "Festival"),
            ("Martin Coutinho Parreira Braule", "Festival"),
            ("Bernardo Gehtti Rodrgues Nader", "Festival"),
            ("Felipe Ghetti Rodrgues Nader", "Festival"),
            ("Davi Carvalho Cruz", "Festival"),
            ("Benício Velozo Januário", "Festival"),
            ("Letícia Procópio Fialho", "Sub 9"),
            ("Antônio Henriques Andrian", "Sub 9"),
            ("Miguel Agostinho de Souza (Inclusão)", "Sub 9"),
            ("Theo Ribeiro Guimarães", "Sub 9"),
            ("Helena Chieregate da Costa Fontes", "Sub 9"),
            ("Miguel Medeiros de Souza Araújo", "Sub 9"),
            ("Daniel Rocha Viana", "Sub 9"),
            ("Davi Oliveira Castro", "Sub 9"),
            ("Lorenzo Portella Moreira", "Sub 9"),
            ("Eloá Lopes Souza", "Sub 9"),
            ("Laura Concolato Casiraghi", "Sub 9"),
            ("Otávio Henrique Rodrigues Gonçalves", "Sub 9"),
            ("Maria Rita Cruz Francisco", "Sub 9"),
            ("Elis Resende Alves Braga", "Sub 9"),
            ("Cecília Tostes Acuña Calzolari", "Sub 9"),
            ("Lucca Hideki Lopes", "Sub 9"),
            ("Helena Pançardes de Barros Bordão", "Sub 9"),
            ("Isabela Machado de Almeida", "Sub 9"),
            ("Miguel de Oliveira Pereira", "Sub 9"),
            ("Theo Oliveira Breves", "Sub 9"),
            ("Gabriel Lucca Capote Otoni (Inclusão)", "Sub 9"),
            ("João Miguel Curcio Roxo", "Sub 11"),
            ("Maria Luiza Nogueira Sales", "Sub 11"),
            ("João Pedro Lorenzon Andrade (Inclusão)", "Sub 11"),
            ("Enzo Juvenal Ribeiro", "Sub 11"),
            ("Miguel Avelino Maciel", "Sub 11"),
            ("Davi Lucas Lopes Cavalcanti", "Sub 11"),
            ("João Fernando Lima Romanielo Sapede", "Sub 11"),
            ("Miguel Guedes de Andrade Silva", "Sub 11"),
            ("Bernardo Cotrim Moreira Ramos", "Sub 11"),
            ("Caio Ramos Nitole", "Sub 11"),
            ("Wislei Silveira Dinelli", "Sub 11"),
            ("Manuela da Silva Reis", "Sub 11"),
            ("Luis Antonio de Carvalho Neto", "Sub 11"),
            ("Aslan Luka Faria Almeida de Moura Silva", "Sub 11"),
            ("Gabriel Vita da Silva", "Sub 11"),
            ("Arthur Peixoto Lopes Freitas", "Sub 11"),
            ("Isaac Almeida Chagas", "Sub 11"),
            ("Helena Pereira Sareta Corrêa", "Sub 11"),
            ("Theo Velozo Januário", "Sub 11"),
            ("Yuri Andrade Ramos", "Sub 11"),
            ("João Pedro Souza Rocha", "Sub 11"),
            ("Miguel Henriques Alves Ribeiro da Silva", "Sub 11"),
            ("Maria Luiza dos Santos Souza Bilac", "Sub 11"),
            ("Laís de Oliveira Severino", "Sub 11"),
            ("Eduardo Martini Mota", "Sub 11"),
            ("Davi Marques Corrêa Mattoso Flamarion", "Sub 11"),
            ("Miguel Lauro Lima", "Sub 11"),
            ("Joaquim Rodrigues Ignácio Vieira", "Sub 13"),
            ("Arthur Alves da Silva Macário", "Sub 13"),
            ("Luiza Helena Delcourt do Amaral", "Sub 13"),
            ("Lian Ferreira Canuto", "Sub 13"),
            ("Alexa Guida da Cunha Freitas", "Sub 13"),
            ("Filipe Monteiro Giffoni", "Sub 13"),
            ("Milena Tavares Medeiros Cotia", "Sub 13"),
            ("Daniel Porto Matos de Melo", "Sub 13"),
            ("João Nardoto Conde Ramundo", "Sub 13"),
            ("Davi Campos Gouvea", "Sub 13"),
            ("Gabriel de Oliveira Pereira", "Sub 13"),
            ("Maria Clara dos Santos Campos", "Sub 13"),
            ("João Pedro de Andrade Vieira Correia", "Sub 13"),
            ("Paulo Victor de Araújo Azevedo", "Sub 15"),
            ("Bernardo Alves Silva", "Sub 15"),
            ("Isaque Resende Antunes", "Sub 15"),
            ("João Gulherme Costa Toledo Santos", "Sub 15"),
            ("João Miguel da Silva Paulino", "Sub 15"),
            ("Maria Eduarda Esper Oliveira", "Sub 15"),
            ("Yuri Ferreira Canuto", "Sub 15"),
            ("Felipe Zambelli Mattos", "Sub 15"),
            ("Arthur Silvestre Van Opstal", "Sub 18"),
            ("Tiago Guerra Cassiano Vieira", "Sub 18"),
            ("Arthur Marques Nogueira", "Sub 18"),
            ("Maria Eduarda Pinheiro Lopes", "Sub 18"),
        ]

        atualizados = 0
        nao_encontrados = []

        for nome, classe_texto in linhas:
            classe_destino = mapa_classe.get(classe_texto)
            if not classe_destino:
                continue

            qs = Atleta.objects.filter(nome__iexact=nome)
            if not qs.exists():
                nao_encontrados.append(nome)
                continue

            for atleta in qs:
                if atleta.classe != classe_destino:
                    atleta.classe = classe_destino
                    atleta.save(update_fields=["classe"])
                    atualizados += 1

        if nao_encontrados:
            self.stdout.write(
                self.style.WARNING(
                    "Não foram encontrados atletas para os seguintes nomes (verificar ortografia/importação):\n"
                    + "\n".join(f"- {n}" for n in nao_encontrados)
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Correção de classes concluída. Atletas com classe ajustada: {atualizados}."
            )
        )



