from django.test import TestCase
from atletas.models import (
    Organizador,
    Academia,
    Classe,
    Categoria,
    Atleta,
    Campeonato,
    Inscricao,
)
from atletas.utils import gerar_chave


class GerarChaveTests(TestCase):
    def setUp(self):
        self.organizador = Organizador.objects.create(nome="Org Teste", slug="org-teste")
        self.academia = Academia.objects.create(
            nome="Academia Teste",
            cidade="SP",
            estado="SP",
            organizador=self.organizador,
        )
        self.classe = Classe.objects.create(nome="SUB11", idade_min=10, idade_max=11)
        self.categoria = Categoria.objects.create(
            classe=self.classe,
            sexo="M",
            categoria_nome="Leve",
            limite_min=30,
            limite_max=35,
            label="SUB11 - Leve (30-35kg)",
        )
        self.campeonato = Campeonato.objects.create(
            nome="Copa Teste", organizador=self.organizador, ativo=True
        )

    def _criar_inscricao(self, nome_atleta: str, peso: float):
        atleta = Atleta.objects.create(
            nome=nome_atleta,
            sexo="M",
            academia=self.academia,
            ano_nasc=2014,
        )
        return Inscricao.objects.create(
            atleta=atleta,
            campeonato=self.campeonato,
            classe_escolhida=self.classe.nome,
            categoria_escolhida=self.categoria.categoria_nome,
            peso=peso,
            status_inscricao="aprovado",
        )

    def test_melhor_de_3_para_dois_atletas(self):
        self._criar_inscricao("Atleta 1", 32.0)
        self._criar_inscricao("Atleta 2", 33.5)

        chave = gerar_chave(
            categoria_nome=self.categoria.categoria_nome,
            classe=self.classe.nome,
            sexo="M",
            campeonato=self.campeonato,
        )

        self.assertEqual(chave.estrutura.get("tipo"), "melhor_de_3")
        self.assertEqual(chave.lutas.count(), 3)

    def test_round_robin_para_tres_atletas(self):
        self._criar_inscricao("Atleta 1", 31.0)
        self._criar_inscricao("Atleta 2", 32.0)
        self._criar_inscricao("Atleta 3", 33.0)

        chave = gerar_chave(
            categoria_nome=self.categoria.categoria_nome,
            classe=self.classe.nome,
            sexo="M",
            campeonato=self.campeonato,
        )

        self.assertEqual(chave.estrutura.get("tipo"), "round_robin")
        # 3 atletas => 3 lutas
        self.assertEqual(chave.lutas.count(), 3)


