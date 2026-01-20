"""
Script para criar atletas com pesagem aprovada em todas as combinaes possveis de chaves
Uso: python manage.py seed_atletas_chaves_completas
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from organizations.models import Organization
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

from atletas.models import (
    Academia, Atleta, Campeonato, Inscricao, Categoria, Classe,
    PesagemHistorico
)
from atletas.utils import calcular_classe


class Command(BaseCommand):
    help = 'Cria atletas com pesagem aprovada em todas as combinaes possveis de chaves para testes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpa inscries e atletas existentes antes de criar novos',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('  Limpando dados existentes...'))
            PesagemHistorico.objects.all().delete()
            Inscricao.objects.all().delete()
            Atleta.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(' Dados limpos!'))

        self.stdout.write(self.style.SUCCESS('\n Criando atletas para todas as combinaes de chaves...\n'))

        # Buscar campeonato ativo
        campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
        if not campeonato_ativo:
            self.stdout.write(self.style.ERROR(' Nenhum campeonato ativo encontrado. Crie um campeonato ativo primeiro.'))
            return

        # Buscar ou criar academias
        academias = self.obter_academias()
        
        # Buscar todas as categorias
        categorias = Categoria.objects.all().select_related('classe').order_by('classe__idade_min', 'sexo', 'limite_min')
        
        # Agrupar categorias por classe e sexo
        categorias_por_combinacao = {}
        for categoria in categorias:
            chave = (categoria.classe.nome, categoria.sexo, categoria.categoria_nome)
            if chave not in categorias_por_combinacao:
                categorias_por_combinacao[chave] = []
            categorias_por_combinacao[chave].append(categoria)
        
        self.stdout.write(f' Total de combinaes nicas: {len(categorias_por_combinacao)}')
        
        # Criar atletas para cada combinao
        atletas_criados = 0
        inscricoes_criadas = 0
        pesagens_aprovadas = 0
        
        # Nomes fictcios
        nomes_masculinos = [
            'Joo Silva', 'Carlos Santos', 'Lucas Oliveira', 'Gabriel Almeida', 'Rafael Costa',
            'Felipe Rodrigues', 'Bruno Ferreira', 'Thiago Martins', 'Matheus Souza', 'Pedro Lima',
            'Vinicius Arajo', 'Gustavo Pereira', 'Leonardo Nunes', 'Rodrigo Barbosa', 'Andr Luiz',
            'Diego Alves', 'Marcelo Ribeiro', 'Ricardo Campos', 'Fernando Dias', 'Paulo Csar',
            'Roberto Junior', 'Eduardo Santos', 'Fbio Moreira', 'Daniel Cunha', 'Alexandre Rocha',
            'Marcos Vinicius', 'Saulo Vinicius', 'Marcus Vinicius', 'Henrique Silva', 'Caio Mendes',
            'Igor Santos', 'Renato Alves', 'Juliano Costa', 'Leandro Silva', 'Wagner Oliveira',
            'Anderson Lima', 'Fabiano Souza', 'Cristiano Rocha', 'Adriano Santos', 'Maurcio Pereira',
            'Bruno Henrique', 'Felipe Augusto', 'Lucas Gabriel', 'Pedro Henrique', 'Rafael Augusto',
            'Thiago Henrique', 'Matheus Henrique', 'Gabriel Henrique', 'Lucas Henrique', 'Felipe Henrique',
        ]
        
        nomes_femininos = [
            'Maria Silva', 'Ana Santos', 'Juliana Oliveira', 'Fernanda Costa', 'Camila Rodrigues',
            'Beatriz Almeida', 'Larissa Ferreira', 'Gabriela Martins', 'Isabella Souza', 'Mariana Lima',
            'Amanda Arajo', 'Bruna Pereira', 'Letcia Nunes', 'Jssica Barbosa', 'Patrcia Luiz',
            'Vanessa Alves', 'Priscila Ribeiro', 'Tatiane Campos', 'Renata Dias', 'Carla Csar',
            'Daniela Junior', 'Adriana Santos', 'Simone Moreira', 'Cristina Cunha', 'Monique Rocha',
            'Thais Vinicius', 'Luciana Silva', 'Pamela Mendes', 'Bianca Santos', 'Raquel Alves',
            'Natlia Costa', 'Andressa Silva', 'Karina Oliveira', 'Juliana Lima', 'Tain Souza',
            'Lorena Rocha', 'Nathalia Santos', 'Yasmin Pereira', 'Vitria Almeida', 'Giovanna Ferreira',
            'Maria Eduarda', 'Ana Carolina', 'Juliana Beatriz', 'Fernanda Beatriz', 'Camila Beatriz',
            'Beatriz Maria', 'Larissa Maria', 'Gabriela Maria', 'Isabella Maria', 'Mariana Beatriz',
        ]
        
        # Faixas de jud
        faixas = ['BRANCA', 'CINZA', 'AZUL', 'AMARELA', 'LARANJA', 'VERDE', 'ROXA', 'MARRON', 'PRETA']
        
        # Criar usurio para pesagem
        User = get_user_model()
        organizacao = Organization.objects.first()
        if not organizacao:
            self.stdout.write(self.style.ERROR('Nenhuma organizacao encontrada. Crie uma organizacao primeiro.'))
            return
        user_pesagem, _ = User.objects.get_or_create(
            email='pesagem@shiai.com',
            defaults={
                'organization': organizacao,
                'role': User.Roles.WEIGHING_OFFICIAL,
                'is_active': True,
            },
        )
        
        hoje = timezone.now().date()
        contador_nomes_m = 0
        contador_nomes_f = 0
        
        # Para cada combinao, criar pelo menos 2 atletas (para haver confrontos)
        for (classe_nome, sexo, categoria_nome), categorias_list in categorias_por_combinacao.items():
            categoria = categorias_list[0]  # Usar a primeira categoria da lista
            
            # Calcular ano de nascimento baseado na classe
            ano_nasc = self.calcular_ano_nascimento_por_classe(classe_nome)
            
            # Criar 2-4 atletas por combinao (para ter confrontos)
            num_atletas = random.randint(2, 4)
            
            for i in range(num_atletas):
                academia = random.choice(academias)
                
                # Escolher nome
                if sexo == 'M':
                    nome = nomes_masculinos[contador_nomes_m % len(nomes_masculinos)]
                    contador_nomes_m += 1
                else:
                    nome = nomes_femininos[contador_nomes_f % len(nomes_femininos)]
                    contador_nomes_f += 1
                
                # Garantir nome nico
                nome_completo = f"{nome} {classe_nome} {i+1}"
                while Atleta.objects.filter(nome=nome_completo, academia=academia).exists():
                    nome_completo = f"{nome} {classe_nome} {i+1} {random.randint(1, 1000)}"
                
                # Calcular peso dentro da faixa da categoria
                peso = self.calcular_peso_categoria(categoria)
                
                # Criar atleta
                atleta = Atleta.objects.create(
                    nome=nome_completo,
                    data_nascimento=f"{ano_nasc}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                    sexo=sexo,
                    academia=academia,
                    faixa=random.choice(faixas),
                    federado=random.choice([True, False]),
                    classe_inicial=classe_nome,
                    status_ativo=True,
                )
                atletas_criados += 1
                
                # Criar inscrio
                inscricao = Inscricao.objects.create(
                    atleta=atleta,
                    campeonato=campeonato_ativo,
                    classe_escolhida=classe_nome,
                    categoria_escolhida=categoria.label,
                    status_inscricao='aprovado',  # J aprovado
                    peso=peso,  # Peso j registrado
                    categoria_ajustada=categoria.label,  # Categoria ajustada = categoria escolhida
                    data_pesagem=timezone.now(),
                )
                inscricoes_criadas += 1
                
                # Criar histrico de pesagem
                PesagemHistorico.objects.create(
                    inscricao=inscricao,
                    campeonato=campeonato_ativo,
                    peso_registrado=peso,
                    categoria_ajustada=categoria.label,
                    pesado_por=user_pesagem,
                )
                pesagens_aprovadas += 1
        
        # Resumo
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS(' SEED CONCLUDO COM SUCESSO!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        self.stdout.write(f'\n RESUMO:\n')
        self.stdout.write(f'    Atletas criados: {atletas_criados}')
        self.stdout.write(f'    Inscries criadas: {inscricoes_criadas}')
        self.stdout.write(f'     Pesagens aprovadas: {pesagens_aprovadas}')
        self.stdout.write(f'    Campeonato: {campeonato_ativo.nome}')
        self.stdout.write(f'    Combinaes cobertas: {len(categorias_por_combinacao)}')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS(' Agora voc pode gerar todas as chaves!'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

    def obter_academias(self):
        """Busca ou cria academias"""
        academias = list(Academia.objects.all())
        if not academias:
            # Criar academias se no existirem
            academias_data = [
                {'nome': 'Academia 63', 'cidade': 'Volta Redonda', 'estado': 'RJ'},
                {'nome': 'Judo Clube Solera', 'cidade': 'Volta Redonda', 'estado': 'RJ'},
                {'nome': 'Academia Tigre', 'cidade': 'Barra Mansa', 'estado': 'RJ'},
            ]
            for data in academias_data:
                academia = Academia.objects.create(**data)
                academias.append(academia)
        return academias

    def calcular_ano_nascimento_por_classe(self, classe_nome):
        """Calcula ano de nascimento baseado na classe"""
        hoje = timezone.now().date()
        
        # Mapear classe para idade
        idade_por_classe = {
            'FESTIVAL': (4, 6),
            'SUB 9': (7, 8),
            'SUB 11': (9, 10),
            'SUB 13': (11, 12),
            'SUB 15': (13, 14),
            'SUB 18': (15, 17),
            'SUB 21': (18, 20),
            'SNIOR': (21, 29),
            'VETERANOS': (30, 45),
        }
        
        idade_range = idade_por_classe.get(classe_nome, (15, 20))
        idade = random.randint(idade_range[0], idade_range[1])
        return hoje.year - idade

    def calcular_peso_categoria(self, categoria):
        """Calcula peso dentro da faixa da categoria"""
        limite_min = float(categoria.limite_min)
        
        if categoria.limite_max:
            limite_max = float(categoria.limite_max)
            # Peso no meio da faixa, com pequena variao
            peso_base = (limite_min + limite_max) / 2
            variacao = (limite_max - limite_min) * 0.2  # 20% da faixa
            peso = peso_base + random.uniform(-variacao/2, variacao/2)
        else:
            # Super Pesado (sem limite mximo)
            peso = limite_min + random.uniform(5, 15)
        
        return round(peso, 1)


