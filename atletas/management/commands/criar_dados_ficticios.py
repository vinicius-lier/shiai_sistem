"""
Comando para criar dados fictícios completos para testes do sistema Shiai
Uso: python manage.py criar_dados_ficticios [--clear]
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import random

from atletas.models import (
    Organizador, Academia, Atleta, Campeonato, Inscricao, Categoria, Classe,
    PessoaEquipeTecnica, EquipeTecnicaCampeonato, UsuarioOperacional,
    PesagemHistorico, AcademiaCampeonato, ConferenciaPagamento,
    AcademiaCampeonatoSenha, UserProfile
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
        parser.add_argument(
            '--organizadores',
            type=int,
            default=2,
            help='Número de organizadores a criar (padrão: 2)',
        )
        parser.add_argument(
            '--academias',
            type=int,
            default=5,
            help='Número de academias por organizador (padrão: 5)',
        )
        parser.add_argument(
            '--atletas',
            type=int,
            default=50,
            help='Número total de atletas a criar (padrão: 50)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('⚠️  Limpando dados existentes...'))
            self.limpar_dados()
            self.stdout.write(self.style.SUCCESS('✅ Dados limpos!'))

        self.stdout.write(self.style.SUCCESS('\n🌱 Iniciando criação de dados fictícios...\n'))

        # 1. Garantir que Classes e Categorias existem
        self.garantir_classes_categorias()
        
        # 2. Criar Organizadores
        organizadores = self.criar_organizadores(options['organizadores'])
        
        # 3. Criar Academias
        academias = self.criar_academias(organizadores, options['academias'])
        
        # 4. Criar Atletas
        atletas = self.criar_atletas(academias, options['atletas'])
        
        # 5. Criar Campeonatos
        campeonatos = self.criar_campeonatos(organizadores, academias)
        
        # 6. Criar Inscrições
        inscricoes = self.criar_inscricoes(atletas, campeonatos)
        
        # 7. Criar Equipe Técnica
        equipe_tecnica = self.criar_equipe_tecnica(campeonatos[0] if campeonatos else None)
        
        # 8. Criar Usuários Operacionais
        usuarios = self.criar_usuarios_operacionais(organizadores)
        
        # 9. Criar Senhas de Academia para Campeonatos
        self.criar_senhas_academias(campeonatos, academias)
        
        # 10. Criar Conferência de Pesagem
        if campeonatos and inscricoes.get('ativo'):
            self.criar_conferencia_pesagem(campeonatos[0], inscricoes['ativo'])
        
        # Resumo final
        self.mostrar_resumo(organizadores, academias, atletas, campeonatos, inscricoes, equipe_tecnica, usuarios)

    def limpar_dados(self):
        """Limpa dados existentes (exceto superuser)"""
        ConferenciaPagamento.objects.all().delete()
        PesagemHistorico.objects.all().delete()
        Inscricao.objects.all().delete()
        AcademiaCampeonatoSenha.objects.all().delete()
        AcademiaCampeonato.objects.all().delete()
        EquipeTecnicaCampeonato.objects.all().delete()
        PessoaEquipeTecnica.objects.all().delete()
        Atleta.objects.all().delete()
        Campeonato.objects.all().delete()
        Academia.objects.all().delete()
        UsuarioOperacional.objects.all().delete()
        UserProfile.objects.all().delete()
        # Não deletar todos os usuários, apenas os de teste
        User.objects.filter(username__startswith='test_').delete()
        User.objects.filter(username__in=['operacional1', 'operacional2', 'pesagem_sistema']).delete()

    def garantir_classes_categorias(self):
        """Garante que Classes e Categorias existem"""
        self.stdout.write('📋 Verificando classes e categorias...')
        
        classes_data = [
            {'nome': 'FESTIVAL', 'idade_min': 4, 'idade_max': 6},
            {'nome': 'SUB 9', 'idade_min': 7, 'idade_max': 8},
            {'nome': 'SUB 11', 'idade_min': 9, 'idade_max': 10},
            {'nome': 'SUB 13', 'idade_min': 11, 'idade_max': 12},
            {'nome': 'SUB 15', 'idade_min': 13, 'idade_max': 14},
            {'nome': 'SUB 18', 'idade_min': 15, 'idade_max': 17},
            {'nome': 'SUB 21', 'idade_min': 18, 'idade_max': 20},
            {'nome': 'SÊNIOR', 'idade_min': 21, 'idade_max': 30},
            {'nome': 'VETERANOS', 'idade_min': 31, 'idade_max': 99},
        ]
        
        for classe_data in classes_data:
            Classe.objects.get_or_create(
                nome=classe_data['nome'],
                defaults={
                    'idade_min': classe_data['idade_min'],
                    'idade_max': classe_data['idade_max']
                }
            )
        
        # Verificar se há categorias, se não houver, criar algumas básicas
        if Categoria.objects.count() == 0:
            self.stdout.write('   ⚠️  Nenhuma categoria encontrada. Execute: python manage.py popular_categorias_oficiais')
        else:
            self.stdout.write(f'   ✓ {Categoria.objects.count()} categorias disponíveis')

    def criar_organizadores(self, quantidade):
        """Cria organizadores"""
        self.stdout.write(f'\n🏢 Criando {quantidade} organizador(es)...')
        
        organizadores_data = [
            {'nome': 'Federação de Judô do Sul Fluminense', 'email': 'fjsf@email.com', 'telefone': '(24) 3333-1111'},
            {'nome': 'Confederação Brasileira de Judô - Regional RJ', 'email': 'cbj.rj@email.com', 'telefone': '(21) 2222-3333'},
            {'nome': 'Liga de Judô de Volta Redonda', 'email': 'liga.vr@email.com', 'telefone': '(24) 3333-2222'},
            {'nome': 'Associação de Judô do Vale do Paraíba', 'email': 'ajvp@email.com', 'telefone': '(12) 3333-4444'},
        ]
        
        organizadores = []
        for i in range(quantidade):
            if i < len(organizadores_data):
                data = organizadores_data[i]
            else:
                data = {
                    'nome': f'Organizador {i+1}',
                    'email': f'org{i+1}@email.com',
                    'telefone': f'(24) 9999-{i+1:04d}'
                }
            
            org, created = Organizador.objects.get_or_create(
                nome=data['nome'],
                defaults={
                    'email': data['email'],
                    'telefone': data['telefone'],
                    'ativo': True
                }
            )
            organizadores.append(org)
            if created:
                self.stdout.write(f'   ✓ {org.nome}')
        
        return organizadores

    def criar_academias(self, organizadores, academias_por_org):
        """Cria academias distribuídas entre organizadores"""
        self.stdout.write(f'\n📚 Criando academias ({academias_por_org} por organizador)...')
        
        nomes_academias = [
            'Academia 63', 'Judo Clube Solera', 'Academia Tigre', 'Projeto Samurai',
            'Judô Kiai VR', 'Academia Top Team', 'Judô Clube Barra Mansa',
            'Academia Elite Judô', 'Projeto Social Judô', 'Academia Campeões',
            'Judô Clube Resende', 'Academia Força e Honra', 'Judô Clube Sul Fluminense',
            'Academia Nova Geração', 'Judô Clube Vale do Paraíba'
        ]
        
        cidades_estados = [
            ('Volta Redonda', 'RJ'), ('Barra Mansa', 'RJ'), ('Resende', 'RJ'),
            ('Petrópolis', 'RJ'), ('Rio de Janeiro', 'RJ'), ('São Paulo', 'SP')
        ]
        
        academias = []
        idx_nome = 0
        
        for org in organizadores:
            for i in range(academias_por_org):
                if idx_nome < len(nomes_academias):
                    nome = nomes_academias[idx_nome]
                    idx_nome += 1
                else:
                    nome = f'Academia {org.nome[:10]} {i+1}'
                
                cidade, estado = random.choice(cidades_estados)
                
                academia, created = Academia.objects.get_or_create(
                    nome=nome,
                    organizador=org,
                    defaults={
                        'cidade': cidade,
                        'estado': estado,
                        'telefone': f'(24) 9999-{random.randint(1000, 9999)}',
                        'responsavel': f'Responsável {nome}',
                        'endereco': f'Rua {random.randint(1, 999)}, {cidade}',
                        'ativo_login': True,
                    }
                )
                academias.append(academia)
                if created:
                    self.stdout.write(f'   ✓ {academia.nome} ({org.nome})')
        
        return academias

    def criar_atletas(self, academias, quantidade):
        """Cria atletas distribuídos entre academias"""
        self.stdout.write(f'\n👥 Criando {quantidade} atletas...')
        
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
            'Maurício Pereira', 'Lucas Gabriel', 'Enzo Alves', 'Arthur Santos',
            'Miguel Costa', 'Bernardo Lima', 'Davi Oliveira', 'Heitor Silva',
            'Samuel Pereira', 'Theo Almeida', 'Rafael Henrique'
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
            'Giovanna Ferreira', 'Sophia Costa', 'Alice Santos', 'Laura Oliveira',
            'Manuela Lima', 'Valentina Silva', 'Helena Alves', 'Isis Pereira',
            'Antonella Rocha', 'Lívia Santos', 'Cecília Costa'
        ]
        
        faixas = ['BRANCA', 'CINZA', 'AZUL', 'AMARELA', 'LARANJA', 'VERDE', 'ROXA', 'MARRON', 'PRETA']
        
        atletas = []
        hoje = date.today()
        
        for i in range(quantidade):
            academia = random.choice(academias)
            sexo = random.choice(['M', 'F'])
            nomes = nomes_masculinos if sexo == 'M' else nomes_femininos
            
            # Distribuir idades para diferentes classes
            if i < quantidade * 0.1:
                ano_nasc = hoje.year - random.randint(4, 6)  # Festival
            elif i < quantidade * 0.2:
                ano_nasc = hoje.year - random.randint(7, 8)  # SUB 9
            elif i < quantidade * 0.3:
                ano_nasc = hoje.year - random.randint(9, 10)  # SUB 11
            elif i < quantidade * 0.4:
                ano_nasc = hoje.year - random.randint(11, 12)  # SUB 13
            elif i < quantidade * 0.5:
                ano_nasc = hoje.year - random.randint(13, 14)  # SUB 15
            elif i < quantidade * 0.7:
                ano_nasc = hoje.year - random.randint(15, 17)  # SUB 18
            elif i < quantidade * 0.9:
                ano_nasc = hoje.year - random.randint(21, 29)  # SÊNIOR
            else:
                ano_nasc = hoje.year - random.randint(30, 45)  # VETERANOS
            
            classe_calculada = calcular_classe(ano_nasc) or 'SÊNIOR'
            
            nome = random.choice(nomes)
            # Garantir nome único
            contador = 1
            nome_original = nome
            while Atleta.objects.filter(nome=nome, academia=academia).exists():
                nome = f"{nome_original} {contador}"
                contador += 1
            
            atleta = Atleta.objects.create(
                nome=nome,
                data_nascimento=date(ano_nasc, random.randint(1, 12), random.randint(1, 28)),
                sexo=sexo,
                academia=academia,
                faixa=random.choice(faixas),
                federado=random.choice([True, False]),
                numero_zempo=f'Z{random.randint(10000, 99999)}' if random.choice([True, False]) else None,
                classe_inicial=classe_calculada,
                status_ativo=True,
                telefone=f'(24) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}' if random.choice([True, False]) else None,
            )
            atletas.append(atleta)
        
        self.stdout.write(f'   ✓ {len(atletas)} atletas criados')
        return atletas

    def criar_campeonatos(self, organizadores, academias):
        """Cria campeonatos para os organizadores"""
        self.stdout.write('\n🏆 Criando campeonatos...')
        
        hoje = timezone.now().date()
        campeonatos = []
        
        nomes_campeonatos = [
            'Copa VR de Judô', 'Open Volta Redonda', 'Campeonato Sul Fluminense',
            'Torneio Regional de Judô', 'Copa Vale do Paraíba', 'Open Barra Mansa',
            'Campeonato Estadual', 'Torneio Municipal', 'Copa de Inverno',
            'Open de Verão'
        ]
        
        for i, org in enumerate(organizadores):
            # Campeonato ativo
            nome_ativo = nomes_campeonatos[i % len(nomes_campeonatos)]
            campeonato_ativo = Campeonato.objects.create(
                organizador=org,
                nome=nome_ativo,
                data_inicio=hoje - timedelta(days=10),
                data_competicao=hoje + timedelta(days=7),
                data_limite_inscricao=hoje + timedelta(days=5),
                data_limite_inscricao_academia=hoje + timedelta(days=6),
                ativo=True,
                valor_inscricao_federado=Decimal('60.00'),
                valor_inscricao_nao_federado=Decimal('70.00'),
                chave_pix=f'{random.randint(10000000000, 99999999999)}',
                titular_pix=org.nome,
            )
            campeonatos.append(campeonato_ativo)
            self.stdout.write(f'   ✓ {campeonato_ativo.nome} (Ativo) - {org.nome}')
            
            # Vincular academias do organizador ao campeonato
            academias_org = [a for a in academias if a.organizador == org]
            for academia in academias_org:
                AcademiaCampeonato.objects.get_or_create(
                    academia=academia,
                    campeonato=campeonato_ativo,
                    defaults={'permitido': True}
                )
            
            # Campeonato encerrado (opcional)
            if i == 0:  # Apenas para o primeiro organizador
                nome_encerrado = nomes_campeonatos[(i+1) % len(nomes_campeonatos)]
                campeonato_encerrado = Campeonato.objects.create(
                    organizador=org,
                    nome=nome_encerrado,
                    data_inicio=hoje - timedelta(days=60),
                    data_competicao=hoje - timedelta(days=40),
                    data_limite_inscricao=hoje - timedelta(days=45),
                    data_limite_inscricao_academia=hoje - timedelta(days=44),
                    ativo=False,
                    valor_inscricao_federado=Decimal('60.00'),
                    valor_inscricao_nao_federado=Decimal('70.00'),
                )
                campeonatos.append(campeonato_encerrado)
                self.stdout.write(f'   ✓ {campeonato_encerrado.nome} (Encerrado) - {org.nome}')
                
                # Vincular academias
                for academia in academias_org:
                    AcademiaCampeonato.objects.get_or_create(
                        academia=academia,
                        campeonato=campeonato_encerrado,
                        defaults={'permitido': True}
                    )
        
        return campeonatos

    def criar_inscricoes(self, atletas, campeonatos):
        """Cria inscrições para TODOS os atletas cobrindo TODAS as categorias possíveis"""
        self.stdout.write('\n📝 Criando inscrições cobrindo TODAS as categorias possíveis...')
        
        if not campeonatos:
            return {'ativo': [], 'encerrado': []}
        
        # Buscar TODAS as categorias disponíveis
        todas_categorias = Categoria.objects.select_related('classe').all()
        self.stdout.write(f'   📋 Total de categorias disponíveis: {todas_categorias.count()}')
        
        # Separar campeonatos ativos e encerrados
        campeonatos_ativos = [c for c in campeonatos if c.ativo]
        campeonatos_encerrados = [c for c in campeonatos if not c.ativo]
        
        inscricoes_ativo = []
        inscricoes_encerrado = []
        
        # Criar atletas adicionais se necessário para cobrir todas as categorias
        categorias_cobertas = set()
        
        # Inscrições em TODOS os campeonatos ativos
        for campeonato_ativo in campeonatos_ativos:
            academias_campeonato = Academia.objects.filter(
                organizador=campeonato_ativo.organizador
            )
            atletas_campeonato = [a for a in atletas if a.academia in academias_campeonato]
            
            # Primeiro, inscrever todos os atletas existentes
            for atleta in atletas_campeonato:
                classe = atleta.get_classe_atual()
                categoria = self.buscar_categoria_valida(classe, atleta.sexo)
                
                if categoria:
                    chave_categoria = f"{classe}-{atleta.sexo}-{categoria.label}"
                    categorias_cobertas.add(chave_categoria)
                    
                    if not Inscricao.objects.filter(
                        atleta=atleta,
                        campeonato=campeonato_ativo,
                        classe_escolhida=classe,
                        categoria_escolhida=categoria.label
                    ).exists():
                        inscricao = Inscricao.objects.create(
                            atleta=atleta,
                            campeonato=campeonato_ativo,
                            classe_escolhida=classe,
                            categoria_escolhida=categoria.label,
                            status_inscricao=random.choice(['pendente', 'confirmado', 'aprovado']),
                        )
                        inscricoes_ativo.append(inscricao)
            
            # Agora, criar atletas adicionais para cobrir categorias não cobertas
            hoje = date.today()
            categorias_por_classe_sexo = {}
            
            for categoria in todas_categorias:
                classe_nome = categoria.classe.nome
                sexo = categoria.sexo
                chave = f"{classe_nome}-{sexo}-{categoria.label}"
                
                if chave not in categorias_cobertas:
                    if (classe_nome, sexo) not in categorias_por_classe_sexo:
                        categorias_por_classe_sexo[(classe_nome, sexo)] = []
                    categorias_por_classe_sexo[(classe_nome, sexo)].append(categoria)
            
            # Criar atletas para categorias não cobertas
            nomes_masculinos = [
                'João Silva', 'Carlos Santos', 'Lucas Oliveira', 'Gabriel Almeida',
                'Rafael Costa', 'Felipe Rodrigues', 'Bruno Ferreira', 'Thiago Martins',
                'Matheus Souza', 'Pedro Lima', 'Vinicius Araújo', 'Gustavo Pereira',
                'Leonardo Nunes', 'Rodrigo Barbosa', 'André Luiz', 'Diego Alves',
                'Marcelo Ribeiro', 'Ricardo Campos', 'Fernando Dias', 'Paulo César'
            ]
            
            nomes_femininos = [
                'Maria Silva', 'Ana Santos', 'Juliana Oliveira', 'Fernanda Costa',
                'Camila Rodrigues', 'Beatriz Almeida', 'Larissa Ferreira', 'Gabriela Martins',
                'Isabella Souza', 'Mariana Lima', 'Amanda Araújo', 'Bruna Pereira',
                'Letícia Nunes', 'Jéssica Barbosa', 'Patrícia Luiz', 'Vanessa Alves',
                'Priscila Ribeiro', 'Tatiane Campos', 'Renata Dias', 'Carla César'
            ]
            
            atletas_criados_adicional = 0
            for (classe_nome, sexo), categorias_lista in categorias_por_classe_sexo.items():
                # Calcular ano de nascimento baseado na classe
                classe_obj = Classe.objects.get(nome=classe_nome)
                idade_media = (classe_obj.idade_min + classe_obj.idade_max) // 2
                ano_nasc = hoje.year - idade_media
                
                # Escolher uma academia aleatória do organizador
                academia = random.choice(list(academias_campeonato))
                
                # Criar atleta para cada categoria não coberta
                for categoria in categorias_lista[:3]:  # Limitar a 3 atletas por categoria para não criar muitos
                    nomes = nomes_masculinos if sexo == 'M' else nomes_femininos
                    nome = f"{random.choice(nomes)} {classe_nome} {categoria.categoria_nome}"
                    
                    # Garantir nome único
                    contador = 1
                    nome_original = nome
                    while Atleta.objects.filter(nome=nome, academia=academia).exists():
                        nome = f"{nome_original} {contador}"
                        contador += 1
                    
                    atleta = Atleta.objects.create(
                        nome=nome,
                        data_nascimento=date(ano_nasc, random.randint(1, 12), random.randint(1, 28)),
                        sexo=sexo,
                        academia=academia,
                        faixa=random.choice(['BRANCA', 'CINZA', 'AZUL', 'AMARELA', 'LARANJA']),
                        federado=random.choice([True, False]),
                        classe_inicial=classe_nome,
                        status_ativo=True,
                    )
                    atletas_criados_adicional += 1
                    
                    # Criar inscrição
                    inscricao = Inscricao.objects.create(
                        atleta=atleta,
                        campeonato=campeonato_ativo,
                        classe_escolhida=classe_nome,
                        categoria_escolhida=categoria.label,
                        status_inscricao='aprovado',
                    )
                    inscricoes_ativo.append(inscricao)
                    categorias_cobertas.add(f"{classe_nome}-{sexo}-{categoria.label}")
            
            if atletas_criados_adicional > 0:
                self.stdout.write(f'   ✓ {atletas_criados_adicional} atletas adicionais criados para cobrir categorias')
        
        # Inscrições em campeonatos encerrados (todos os atletas também)
        for campeonato_encerrado in campeonatos_encerrados:
            academias_campeonato = Academia.objects.filter(
                organizador=campeonato_encerrado.organizador
            )
            atletas_campeonato = [a for a in atletas if a.academia in academias_campeonato]
            
            for atleta in atletas_campeonato:
                classe = atleta.get_classe_atual()
                categoria = self.buscar_categoria_valida(classe, atleta.sexo)
                
                if categoria:
                    if not Inscricao.objects.filter(
                        atleta=atleta,
                        campeonato=campeonato_encerrado,
                        classe_escolhida=classe,
                        categoria_escolhida=categoria.label
                    ).exists():
                        inscricao = Inscricao.objects.create(
                            atleta=atleta,
                            campeonato=campeonato_encerrado,
                            classe_escolhida=classe,
                            categoria_escolhida=categoria.label,
                            status_inscricao='aprovado',
                        )
                        inscricoes_encerrado.append(inscricao)
        
        # Estatísticas de cobertura
        total_categorias = todas_categorias.count()
        categorias_com_inscricoes = Inscricao.objects.filter(
            campeonato__in=campeonatos_ativos
        ).values_list('classe_escolhida', 'categoria_escolhida').distinct().count()
        
        self.stdout.write(f'   ✓ {len(inscricoes_ativo)} inscrições criadas em campeonatos ativos')
        if inscricoes_encerrado:
            self.stdout.write(f'   ✓ {len(inscricoes_encerrado)} inscrições criadas em campeonatos encerrados')
        self.stdout.write(f'   📊 Cobertura: {categorias_com_inscricoes} categorias únicas com inscrições')
        
        return {
            'ativo': inscricoes_ativo,
            'encerrado': inscricoes_encerrado
        }

    def buscar_categoria_valida(self, classe_nome, sexo, peso=None):
        """Busca uma categoria válida"""
        try:
            classe = Classe.objects.get(nome=classe_nome)
        except Classe.DoesNotExist:
            classe = Classe.objects.filter(nome__icontains=classe_nome.upper()).first()
            if not classe:
                return None
        
        categorias = Categoria.objects.filter(
            classe=classe,
            sexo=sexo
        ).order_by('limite_min')
        
        if not categorias.exists():
            return None
        
        if peso is not None:
            for categoria in categorias:
                if categoria.limite_max is None:
                    if peso >= float(categoria.limite_min):
                        return categoria
                else:
                    if float(categoria.limite_min) <= peso <= float(categoria.limite_max):
                        return categoria
        
        return random.choice(list(categorias))

    def criar_equipe_tecnica(self, campeonato):
        """Cria equipe técnica para o campeonato"""
        if not campeonato:
            return []
        
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
            pessoa, created = PessoaEquipeTecnica.objects.get_or_create(
                nome=data['nome'],
                defaults={
                    'telefone': data['telefone'],
                    'chave_pix': data['pix'],
                }
            )
            
            EquipeTecnicaCampeonato.objects.get_or_create(
                pessoa=pessoa,
                campeonato=campeonato,
                defaults={
                    'funcao': data['funcao'],
                    'funcao_customizada': 'Gestor' if data['funcao'] == 'outro' else None,
                    'ativo': True,
                }
            )
            pessoas.append(pessoa)
            if created:
                self.stdout.write(f'   ✓ {pessoa.nome} - {data["funcao"]}')
        
        return pessoas

    def criar_usuarios_operacionais(self, organizadores):
        """Cria usuários operacionais vinculados aos organizadores"""
        self.stdout.write('\n👤 Criando usuários operacionais...')
        
        usuarios = []
        senha_padrao = 'test1234'
        
        for i, org in enumerate(organizadores):
            username = f'test_operacional_{org.id}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'operacional{i+1}@shiai.com',
                    'first_name': f'Operacional',
                    'last_name': f'{org.nome[:20]}',
                }
            )
            user.set_password(senha_padrao)
            user.save()
            
            # Criar perfil operacional
            perfil, _ = UsuarioOperacional.objects.get_or_create(
                user=user,
                defaults={
                    'pode_resetar_campeonato': i == 0,  # Primeiro tem permissão
                    'pode_criar_usuarios': i == 0,
                    'data_expiracao': None,
                    'ativo': True,
                    'senha_alterada': True
                }
            )
            
            # Criar UserProfile vinculado ao organizador
            UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'organizador': org
                }
            )
            
            usuarios.append(user)
            self.stdout.write(f'   ✓ {user.username} (senha: {senha_padrao}) - {org.nome}')
        
        return usuarios

    def criar_senhas_academias(self, campeonatos, academias):
        """Cria senhas de acesso para academias nos campeonatos"""
        self.stdout.write('\n🔐 Criando senhas de acesso para academias...')
        
        import string
        from datetime import datetime as dt
        
        for campeonato in campeonatos:
            academias_campeonato = Academia.objects.filter(
                organizador=campeonato.organizador
            )
            
            for academia in academias_campeonato:
                login = f"ACADEMIA_{academia.id:03d}"
                senha_plana = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                
                data_expiracao = None
                if campeonato.data_competicao:
                    data_expiracao = timezone.make_aware(
                        dt.combine(campeonato.data_competicao, dt.min.time())
                    ) + timedelta(days=5)
                
                senha_obj, created = AcademiaCampeonatoSenha.objects.get_or_create(
                    academia=academia,
                    campeonato=campeonato,
                    defaults={
                        'login': login,
                        'senha_plana': senha_plana,
                        'data_expiracao': data_expiracao,
                    }
                )
                
                if not created:
                    senha_obj.login = login
                    senha_obj.senha_plana = senha_plana
                    senha_obj.data_expiracao = data_expiracao
                    senha_obj.save()
                
                senha_obj.definir_senha(senha_plana)
                senha_obj.save()
        
        self.stdout.write(f'   ✓ Senhas criadas para {AcademiaCampeonatoSenha.objects.count()} academias')

    def criar_conferencia_pesagem(self, campeonato, inscricoes):
        """Cria conferência de pesagem"""
        self.stdout.write('\n⚖️  Criando conferência de pesagem...')
        
        inscricoes_pesagem = random.sample(inscricoes, min(12, len(inscricoes)))
        
        user_pesagem, _ = User.objects.get_or_create(
            username='pesagem_sistema',
            defaults={'email': 'pesagem@shiai.com'}
        )
        
        aprovados = 0
        reprovados = 0
        
        for i, inscricao in enumerate(inscricoes_pesagem):
            categoria_original = Categoria.objects.filter(label=inscricao.categoria_escolhida).first()
            
            if i < 10:  # Aprovados
                if categoria_original:
                    if categoria_original.limite_max:
                        peso_base = (float(categoria_original.limite_min) + float(categoria_original.limite_max)) / 2
                    else:
                        peso_base = float(categoria_original.limite_min) + 5
                else:
                    peso_base = 60.0
                
                peso_oficial = round(peso_base + random.uniform(-2, 2), 1)
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
                
                PesagemHistorico.objects.create(
                    inscricao=inscricao,
                    campeonato=campeonato,
                    peso_registrado=peso_oficial,
                    categoria_ajustada=inscricao.categoria_ajustada,
                    pesado_por=user_pesagem,
                )
                aprovados += 1
            else:  # Reprovados
                if categoria_original and categoria_original.limite_max:
                    peso_oficial = round(float(categoria_original.limite_max) + random.uniform(5, 10), 1)
                else:
                    peso_oficial = 100.0
                
                inscricao.peso = peso_oficial
                inscricao.status_inscricao = 'reprovado'
                inscricao.data_pesagem = timezone.now()
                inscricao.save()
                
                PesagemHistorico.objects.create(
                    inscricao=inscricao,
                    campeonato=campeonato,
                    peso_registrado=peso_oficial,
                    observacoes='Peso fora da categoria permitida',
                    pesado_por=user_pesagem,
                )
                reprovados += 1
        
        self.stdout.write(f'   ✓ {aprovados} atletas aprovados')
        self.stdout.write(f'   ✓ {reprovados} atletas reprovados')

    def mostrar_resumo(self, organizadores, academias, atletas, campeonatos, inscricoes, equipe_tecnica, usuarios):
        """Mostra resumo final"""
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✅ DADOS FICTÍCIOS CRIADOS COM SUCESSO!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        self.stdout.write(f'\n📊 RESUMO:\n')
        self.stdout.write(f'   🏢 Organizadores: {len(organizadores)}')
        self.stdout.write(f'   📚 Academias: {len(academias)}')
        self.stdout.write(f'   👥 Atletas: {len(atletas)}')
        self.stdout.write(f'   🏆 Campeonatos: {len(campeonatos)}')
        self.stdout.write(f'   📝 Inscrições (Ativo): {len(inscricoes.get("ativo", []))}')
        self.stdout.write(f'   📝 Inscrições (Encerrado): {len(inscricoes.get("encerrado", []))}')
        self.stdout.write(f'   👨‍💼 Equipe Técnica: {len(equipe_tecnica)}')
        self.stdout.write(f'   👤 Usuários Operacionais: {len(usuarios)}')
        self.stdout.write(f'   📋 Categorias: {Categoria.objects.count()}')
        self.stdout.write(f'   🔐 Senhas de Academia: {AcademiaCampeonatoSenha.objects.count()}')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('🎉 Sistema pronto para testes!'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
        
        self.stdout.write(self.style.WARNING('\n💡 DICAS:'))
        self.stdout.write('   • Usuários operacionais: test_operacional_<id> (senha: test1234)')
        self.stdout.write('   • Execute: python manage.py popular_categorias_oficiais (se necessário)')
        self.stdout.write('   • Use --clear para limpar e recriar todos os dados\n')

