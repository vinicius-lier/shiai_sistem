"""
Script de povoamento (seed) com dados fictícios para testes do Shiai Sistem
Uso: python manage.py seed_test_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

from atletas.models import (
    Academia, Atleta, Campeonato, Inscricao, Categoria, Classe,
    PessoaEquipeTecnica, EquipeTecnicaCampeonato, UsuarioOperacional,
    PesagemHistorico, AcademiaCampeonato, ConferenciaPagamento
)
from atletas.utils import calcular_classe


class Command(BaseCommand):
    help = 'Cria dados fictícios completos para testes do sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Limpa dados existentes antes de criar novos',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('⚠️  Limpando dados existentes...'))
            Inscricao.objects.all().delete()
            Atleta.objects.all().delete()
            Campeonato.objects.all().delete()
            Academia.objects.all().delete()
            PessoaEquipeTecnica.objects.all().delete()
            EquipeTecnicaCampeonato.objects.all().delete()
            UsuarioOperacional.objects.all().delete()
            User.objects.filter(username__in=['operacional1', 'operacional2']).delete()
            self.stdout.write(self.style.SUCCESS('✅ Dados limpos!'))

        self.stdout.write(self.style.SUCCESS('\n🌱 Iniciando seed de dados de teste...\n'))

        # 1. Criar Academias
        academias = self.criar_academias()
        
        # 2. Criar Atletas
        atletas = self.criar_atletas(academias)
        
        # 3. Criar Eventos
        eventos = self.criar_eventos(academias)
        
        # 4. Criar Inscrições
        inscricoes = self.criar_inscricoes(atletas, eventos)
        
        # 5. Criar Equipe Técnica
        equipe_tecnica = self.criar_equipe_tecnica(eventos[0])  # Evento ativo
        
        # 6. Criar Usuários Operacionais
        usuarios = self.criar_usuarios_operacionais()
        
        # 7. Criar Conferência de Pesagem
        self.criar_conferencia_pesagem(eventos[0], inscricoes['ativo'])  # Evento ativo
        
        # Resumo final
        self.mostrar_resumo(academias, atletas, eventos, inscricoes, equipe_tecnica, usuarios)

    def criar_academias(self):
        """Cria 5 academias"""
        self.stdout.write('📚 Criando academias...')
        
        academias_data = [
            {'nome': 'Academia 63', 'cidade': 'Volta Redonda', 'estado': 'RJ'},
            {'nome': 'Judo Clube Solera', 'cidade': 'Volta Redonda', 'estado': 'RJ'},
            {'nome': 'Academia Tigre', 'cidade': 'Barra Mansa', 'estado': 'RJ'},
            {'nome': 'Projeto Samurai', 'cidade': 'Resende', 'estado': 'RJ'},
            {'nome': 'Judô Kiai VR', 'cidade': 'Volta Redonda', 'estado': 'RJ'},
        ]
        
        academias = []
        for data in academias_data:
            academia, created = Academia.objects.get_or_create(
                nome=data['nome'],
                defaults={
                    'cidade': data['cidade'],
                    'estado': data['estado'],
                    'ativo_login': True,
                }
            )
            academias.append(academia)
            if created:
                self.stdout.write(f'   ✓ {academia.nome}')
        
        return academias

    def criar_atletas(self, academias):
        """Cria 40 atletas distribuídos entre as academias"""
        self.stdout.write('\n👥 Criando atletas...')
        
        # Nomes fictícios realistas
        nomes_masculinos = [
            'João Pedro Silva', 'Carlos Eduardo Santos', 'Lucas Henrique Oliveira',
            'Gabriel Almeida', 'Rafael Costa', 'Felipe Rodrigues', 'Bruno Ferreira',
            'Thiago Martins', 'Matheus Souza', 'Pedro Henrique Lima', 'Vinicius Araújo',
            'Gustavo Pereira', 'Leonardo Nunes', 'Rodrigo Barbosa', 'André Luiz',
            'Diego Alves', 'Marcelo Ribeiro', 'Ricardo Campos', 'Fernando Dias',
            'Paulo César', 'Roberto Junior', 'Eduardo Santos', 'Fábio Moreira',
            'Daniel Cunha', 'Alexandre Rocha', 'Marcos Vinicius', 'Saulo Vinicius',
            'Marcus Vinicius', 'Henrique Silva', 'Caio Mendes', 'Igor Santos',
            'Renato Alves', 'Juliano Costa', 'Leandro Silva', 'Wagner Oliveira',
            'Anderson Lima', 'Fabiano Souza', 'Cristiano Rocha', 'Adriano Santos',
            'Maurício Pereira'
        ]
        
        nomes_femininos = [
            'Maria Eduarda Silva', 'Ana Carolina Santos', 'Juliana Oliveira',
            'Fernanda Costa', 'Camila Rodrigues', 'Beatriz Almeida', 'Larissa Ferreira',
            'Gabriela Martins', 'Isabella Souza', 'Mariana Lima', 'Amanda Araújo',
            'Bruna Pereira', 'Letícia Nunes', 'Jéssica Barbosa', 'Patrícia Luiz',
            'Vanessa Alves', 'Priscila Ribeiro', 'Tatiane Campos', 'Renata Dias',
            'Carla César', 'Daniela Junior', 'Adriana Santos', 'Simone Moreira',
            'Cristina Cunha', 'Monique Rocha', 'Thais Vinicius', 'Luciana Silva',
            'Pamela Mendes', 'Bianca Santos', 'Raquel Alves', 'Natália Costa',
            'Andressa Silva', 'Karina Oliveira', 'Juliana Lima', 'Tainá Souza',
            'Lorena Rocha', 'Nathalia Santos', 'Yasmin Pereira', 'Vitória Almeida',
            'Giovanna Ferreira'
        ]
        
        # Faixas de peso por classe (kg)
        faixas_peso = {
            'FESTIVAL': (15, 35),
            'SUB 9': (20, 45),
            'SUB 11': (25, 50),
            'SUB 13': (28, 60),
            'SUB 15': (40, 75),
            'SUB 18': (50, 90),
            'SUB 21': (55, 95),
            'SÊNIOR': (60, 100),
            'VETERANOS': (65, 105),
        }
        
        # Faixas de judô
        faixas = ['Branca', 'Cinza', 'Azul', 'Amarela', 'Laranja', 'Verde', 'Roxa', 'Marrom', 'Preta']
        
        atletas = []
        hoje = timezone.now().date()
        
        # Distribuir atletas entre academias
        for i in range(40):
            academia = random.choice(academias)
            sexo = random.choice(['M', 'F'])
            nomes = nomes_masculinos if sexo == 'M' else nomes_femininos
            
            # Escolher ano de nascimento para gerar classe válida
            # Vamos criar atletas de diferentes classes
            if i < 5:
                ano_nasc = hoje.year - random.randint(4, 6)  # Festival
            elif i < 10:
                ano_nasc = hoje.year - random.randint(7, 8)  # SUB 9
            elif i < 15:
                ano_nasc = hoje.year - random.randint(9, 10)  # SUB 11
            elif i < 20:
                ano_nasc = hoje.year - random.randint(11, 12)  # SUB 13
            elif i < 25:
                ano_nasc = hoje.year - random.randint(13, 14)  # SUB 15
            elif i < 30:
                ano_nasc = hoje.year - random.randint(15, 17)  # SUB 18
            elif i < 35:
                ano_nasc = hoje.year - random.randint(21, 29)  # SÊNIOR
            else:
                ano_nasc = hoje.year - random.randint(30, 45)  # VETERANOS
            
            classe_calculada = calcular_classe(ano_nasc)
            
            # Garantir nome único
            nome = random.choice(nomes)
            while Atleta.objects.filter(nome=nome, academia=academia).exists():
                nome = f"{nome} {random.randint(1, 100)}"
            
            # Escolher faixa válida
            faixa_escolhida = random.choice(faixas)
            
            atleta = Atleta.objects.create(
                nome=nome,
                data_nascimento=f"{ano_nasc}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                sexo=sexo,
                academia=academia,
                faixa=faixa_escolhida,
                federado=random.choice([True, False]),
                classe_inicial=classe_calculada,
                status_ativo=True,
            )
            atletas.append(atleta)
        
        self.stdout.write(f'   ✓ {len(atletas)} atletas criados')
        return atletas

    def criar_eventos(self, academias):
        """Cria 2 eventos (1 ativo, 1 encerrado)"""
        self.stdout.write('\n🏆 Criando eventos...')
        
        hoje = timezone.now().date()
        
        # Evento ativo
        evento_ativo = Campeonato.objects.create(
            nome='Copa VR de Judô',
            data_competicao=hoje + timedelta(days=7),
            data_limite_inscricao=hoje + timedelta(days=5),
            data_limite_inscricao_academia=hoje + timedelta(days=6),
            ativo=True,
            valor_inscricao_federado=Decimal('60.00'),
            valor_inscricao_nao_federado=Decimal('60.00'),
        )
        
        # Evento encerrado
        evento_encerrado = Campeonato.objects.create(
            nome='Open Volta Redonda',
            data_competicao=hoje - timedelta(days=40),
            data_limite_inscricao=hoje - timedelta(days=45),
            data_limite_inscricao_academia=hoje - timedelta(days=44),
            ativo=False,
            valor_inscricao_federado=Decimal('60.00'),
            valor_inscricao_nao_federado=Decimal('60.00'),
        )
        
        # Vincular todas as academias aos eventos
        for academia in academias:
            AcademiaCampeonato.objects.get_or_create(
                academia=academia,
                campeonato=evento_ativo,
                defaults={'permitido': True}
            )
            AcademiaCampeonato.objects.get_or_create(
                academia=academia,
                campeonato=evento_encerrado,
                defaults={'permitido': True}
            )
        
        self.stdout.write(f'   ✓ {evento_ativo.nome} (Ativo)')
        self.stdout.write(f'   ✓ {evento_encerrado.nome} (Encerrado)')
        
        return [evento_ativo, evento_encerrado]

    def criar_inscricoes(self, atletas, eventos):
        """Cria inscrições: 20 no evento ativo, 12 no encerrado"""
        self.stdout.write('\n📝 Criando inscrições...')
        
        evento_ativo = eventos[0]
        evento_encerrado = eventos[1]
        
        inscricoes_ativo = []
        inscricoes_encerrado = []
        
        # 20 inscrições no evento ativo
        atletas_para_ativo = random.sample(atletas, min(20, len(atletas)))
        for atleta in atletas_para_ativo:
            classe = atleta.get_classe_atual()
            
            # Buscar categoria válida para a classe e sexo do atleta
            categoria = self.buscar_categoria_valida(classe, atleta.sexo)
            
            if categoria:
                inscricao = Inscricao.objects.create(
                    atleta=atleta,
                    campeonato=evento_ativo,
                    classe_escolhida=classe,
                    categoria_escolhida=categoria.label,
                    status_inscricao=random.choice(['pendente', 'confirmado', 'aprovado']),
                )
                inscricoes_ativo.append(inscricao)
        
        # 12 inscrições no evento encerrado
        atletas_restantes = [a for a in atletas if a not in atletas_para_ativo]
        atletas_para_encerrado = random.sample(atletas_restantes, min(12, len(atletas_restantes)))
        
        for atleta in atletas_para_encerrado:
            classe = atleta.get_classe_atual()
            categoria = self.buscar_categoria_valida(classe, atleta.sexo)
            
            if categoria:
                inscricao = Inscricao.objects.create(
                    atleta=atleta,
                    campeonato=evento_encerrado,
                    classe_escolhida=classe,
                    categoria_escolhida=categoria.label,
                    status_inscricao='aprovado',  # Evento encerrado, todos aprovados
                )
                inscricoes_encerrado.append(inscricao)
        
        self.stdout.write(f'   ✓ {len(inscricoes_ativo)} inscrições no evento ativo')
        self.stdout.write(f'   ✓ {len(inscricoes_encerrado)} inscrições no evento encerrado')
        
        return {
            'ativo': inscricoes_ativo,
            'encerrado': inscricoes_encerrado
        }

    def buscar_categoria_valida(self, classe_nome, sexo, peso=None):
        """Busca uma categoria válida para a classe, sexo e peso do atleta"""
        try:
            classe = Classe.objects.get(nome=classe_nome)
        except Classe.DoesNotExist:
            # Tentar normalizar nome
            classe = Classe.objects.filter(nome__icontains=classe_nome.upper()).first()
            if not classe:
                return None
        
        # Buscar categorias da classe e sexo
        categorias = Categoria.objects.filter(
            classe=classe,
            sexo=sexo
        ).order_by('limite_min')
        
        if not categorias.exists():
            return None
        
        # Se peso foi fornecido, encontrar categoria que o peso se encaixa
        if peso is not None:
            for categoria in categorias:
                if categoria.limite_max is None:
                    # Super Pesado (sem limite máximo)
                    if peso >= float(categoria.limite_min):
                        return categoria
                else:
                    # Categoria com limite máximo
                    if float(categoria.limite_min) <= peso <= float(categoria.limite_max):
                        return categoria
        
        # Se não encontrou ou peso não fornecido, retornar categoria aleatória
        return random.choice(list(categorias))

    def criar_equipe_tecnica(self, campeonato):
        """Cria 6 pessoas da equipe técnica"""
        self.stdout.write('\n👨‍💼 Criando equipe técnica...')
        
        pessoas_data = [
            {'nome': 'José Roberto Solera', 'funcao': 'arbitro', 'telefone': '(24) 99999-1111', 'pix': 'jose.solera@email.com'},
            {'nome': 'Leonardo da Silva Irias', 'funcao': 'coordenador', 'telefone': '(24) 99999-2222', 'pix': 'leonardo.irias@email.com'},
            {'nome': 'Carlos Mendes', 'funcao': 'mesario', 'telefone': '(24) 99999-3333', 'pix': '(24) 99999-3333'},
            {'nome': 'Ana Paula Santos', 'funcao': 'oficial_pesagem', 'telefone': '(24) 99999-4444', 'pix': 'ana.santos@email.com'},
            {'nome': 'Roberto Alves', 'funcao': 'oficial_mesa', 'telefone': '(24) 99999-5555', 'pix': 'roberto.alves@email.com'},
            {'nome': 'Maria Silva', 'funcao': 'outro', 'telefone': '(24) 99999-6666', 'pix': 'maria.silva@email.com'},
        ]
        
        pessoas = []
        for data in pessoas_data:
            pessoa = PessoaEquipeTecnica.objects.create(
                nome=data['nome'],
                telefone=data['telefone'],
                chave_pix=data['pix'],
                ativo=True,
            )
            
            # Vincular ao campeonato
            EquipeTecnicaCampeonato.objects.create(
                pessoa=pessoa,
                campeonato=campeonato,
                funcao=data['funcao'],
                funcao_customizada='Gestor' if data['funcao'] == 'outro' else None,
                ativo=True,
            )
            pessoas.append(pessoa)
            self.stdout.write(f'   ✓ {pessoa.nome} - {data["funcao"]}')
        
        return pessoas

    def criar_usuarios_operacionais(self):
        """Cria 2 usuários operacionais"""
        self.stdout.write('\n👤 Criando usuários operacionais...')
        
        usuarios = []
        senha_padrao = 'test1234'
        
        usuarios_data = [
            {'username': 'operacional1', 'email': 'operacional1@shiai.com', 'first_name': 'Operacional', 'last_name': 'Um'},
            {'username': 'operacional2', 'email': 'operacional2@shiai.com', 'first_name': 'Operacional', 'last_name': 'Dois'},
        ]
        
        for data in usuarios_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                }
            )
            user.set_password(senha_padrao)
            user.save()
            
            # Criar perfil operacional
            perfil, _ = UsuarioOperacional.objects.get_or_create(
                user=user,
                defaults={
                    'pode_resetar_campeonato': False,
                    'pode_criar_usuarios': False,
                    'data_expiracao': None,  # Vitalício
                    'ativo': True
                }
            )
            usuarios.append(user)
            self.stdout.write(f'   ✓ {user.username} (senha: {senha_padrao})')
        
        return usuarios

    def criar_conferencia_pesagem(self, campeonato, inscricoes):
        """Cria conferência de pesagem: 10 aprovados, 2 reprovados"""
        self.stdout.write('\n⚖️  Criando conferência de pesagem...')
        
        # Selecionar 12 inscrições para pesagem
        inscricoes_pesagem = random.sample(inscricoes, min(12, len(inscricoes)))
        
        # Criar usuário para "pesado por"
        user_pesagem, _ = User.objects.get_or_create(
            username='pesagem_sistema',
            defaults={'email': 'pesagem@shiai.com'}
        )
        
        aprovados = 0
        reprovados = 0
        
        for i, inscricao in enumerate(inscricoes_pesagem):
            # 10 primeiros aprovados, 2 últimos reprovados
            if i < 10:
                # Gerar peso baseado na categoria escolhida
                categoria_original = Categoria.objects.filter(label=inscricao.categoria_escolhida).first()
                if categoria_original:
                    if categoria_original.limite_max:
                        peso_base = (float(categoria_original.limite_min) + float(categoria_original.limite_max)) / 2
                    else:
                        peso_base = float(categoria_original.limite_min) + 5
                else:
                    peso_base = 60.0  # Peso padrão
                
                peso_oficial = peso_base + random.uniform(-2, 2)
                peso_oficial = round(peso_oficial, 1)
                
                # Buscar categoria ajustada
                categoria_ajustada = self.buscar_categoria_valida(
                    inscricao.classe_escolhida,
                    inscricao.atleta.sexo,
                    peso_oficial
                )
                
                inscricao.peso = peso_oficial
                inscricao.categoria_ajustada = categoria_ajustada.label if categoria_ajustada else inscricao.categoria_escolhida
                inscricao.status_inscricao = 'aprovado'
                inscricao.data_pesagem = timezone.now()
                inscricao.save()
                
                # Criar histórico de pesagem
                PesagemHistorico.objects.create(
                    inscricao=inscricao,
                    campeonato=campeonato,
                    peso_registrado=peso_oficial,
                    categoria_ajustada=inscricao.categoria_ajustada,
                    pesado_por=user_pesagem,
                )
                aprovados += 1
            else:
                # Reprovado (peso fora da categoria)
                # Gerar peso muito acima da categoria
                categoria_original = Categoria.objects.filter(label=inscricao.categoria_escolhida).first()
                if categoria_original and categoria_original.limite_max:
                    peso_oficial = float(categoria_original.limite_max) + random.uniform(5, 10)
                else:
                    peso_oficial = 100.0  # Peso muito alto
                peso_oficial = round(peso_oficial, 1)
                
                inscricao.peso = peso_oficial
                inscricao.status_inscricao = 'reprovado'
                inscricao.data_pesagem = timezone.now()
                inscricao.save()
                
                # Criar histórico de pesagem
                PesagemHistorico.objects.create(
                    inscricao=inscricao,
                    campeonato=campeonato,
                    peso_registrado=peso_oficial,
                    observacoes='Peso fora da categoria permitida',
                    pesado_por=user_pesagem,
                )
                reprovados += 1
        
        self.stdout.write(f'   ✓ {aprovados} atletas aprovados na pesagem')
        self.stdout.write(f'   ✓ {reprovados} atletas reprovados na pesagem')

    def mostrar_resumo(self, academias, atletas, eventos, inscricoes, equipe_tecnica, usuarios):
        """Mostra resumo final dos dados criados"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✅ SEED CONCLUÍDO COM SUCESSO!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        self.stdout.write(f'\n📊 RESUMO DOS DADOS CRIADOS:\n')
        self.stdout.write(f'   📚 Academias: {len(academias)}')
        self.stdout.write(f'   👥 Atletas: {len(atletas)}')
        self.stdout.write(f'   🏆 Eventos: {len(eventos)}')
        self.stdout.write(f'   📝 Inscrições (Ativo): {len(inscricoes["ativo"])}')
        self.stdout.write(f'   📝 Inscrições (Encerrado): {len(inscricoes["encerrado"])}')
        self.stdout.write(f'   👨‍💼 Equipe Técnica: {len(equipe_tecnica)}')
        self.stdout.write(f'   👤 Usuários Operacionais: {len(usuarios)}')
        self.stdout.write(f'   📋 Categorias: {Categoria.objects.count()}')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('🎉 Sistema pronto para testes!'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

