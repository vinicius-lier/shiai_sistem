"""
Script para criar chaves específicas com stand-by (BYE) e repescagem
Uso: python manage.py criar_chaves_standby_repescagem
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import random

from atletas.models import (
    Academia, Atleta, Campeonato, Inscricao, Categoria, Classe,
    PesagemHistorico, Chave
)
from atletas.utils import gerar_chave


class Command(BaseCommand):
    help = 'Cria chaves específicas com stand-by (BYE) e repescagem para testes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🎯 Criando chaves com Stand-by e Repescagem...\n'))

        # Buscar campeonato ativo
        campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
        if not campeonato_ativo:
            self.stdout.write(self.style.ERROR('❌ Nenhum campeonato ativo encontrado.'))
            return

        # Buscar academias
        academias = list(Academia.objects.all())
        if not academias:
            academias = [Academia.objects.create(nome='Academia Teste', cidade='Volta Redonda', estado='RJ')]

        # Buscar categorias para criar combinações específicas
        categorias = Categoria.objects.all().select_related('classe').exclude(classe__nome='FESTIVAL')
        
        if not categorias:
            self.stdout.write(self.style.ERROR('❌ Nenhuma categoria encontrada.'))
            return

        # Escolher categorias específicas (diferentes para evitar conflito)
        categoria_standby = categorias.filter(sexo='M', classe__nome='SUB 9').first()
        categoria_repescagem = categorias.filter(sexo='F', classe__nome='SUB 11').first()
        
        # Se não encontrar, usar qualquer uma disponível
        if not categoria_standby:
            categoria_standby = categorias.filter(sexo='M').first()
        if not categoria_repescagem:
            categoria_repescagem = categorias.filter(sexo='F').exclude(classe__nome=categoria_standby.classe.nome if categoria_standby else None).first()
        
        if not categoria_standby or not categoria_repescagem:
            self.stdout.write(self.style.ERROR('❌ Não há categorias suficientes (precisa M e F).'))
            return

        # Criar usuário para pesagem
        user_pesagem, _ = User.objects.get_or_create(
            username='pesagem_sistema',
            defaults={'email': 'pesagem@shiai.com'}
        )

        # ============================================
        # 1. CHAVE COM STAND-BY (6-7 atletas)
        # ============================================
        self.stdout.write(self.style.SUCCESS('\n📋 1. Criando chave com STAND-BY (6 atletas)...'))
        
        # Limpar chave existente se houver
        Chave.objects.filter(
            campeonato=campeonato_ativo,
            classe=categoria_standby.classe.nome,
            categoria=categoria_standby.label
        ).delete()
        
        # Limpar inscrições existentes para esta categoria
        Inscricao.objects.filter(
            campeonato=campeonato_ativo,
            classe_escolhida=categoria_standby.classe.nome,
            categoria_escolhida=categoria_standby.label
        ).delete()
        
        # Criar 6 atletas para stand-by
        atletas_standby = []
        ano_nasc = self.calcular_ano_nascimento_por_classe(categoria_standby.classe.nome)
        peso = self.calcular_peso_categoria(categoria_standby)
        
        nomes_m = ['João Silva', 'Carlos Santos', 'Lucas Oliveira', 'Gabriel Almeida', 'Rafael Costa', 'Felipe Rodrigues']
        
        for i, nome in enumerate(nomes_m):
            academia = random.choice(academias)
            atleta = Atleta.objects.create(
                nome=f"{nome} Stand-by {i+1}",
                data_nascimento=f"{ano_nasc}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                sexo='M',
                academia=academia,
                faixa=random.choice(['AZUL', 'ROXA', 'MARRON']),
                federado=random.choice([True, False]),
                classe_inicial=categoria_standby.classe.nome,
                status_ativo=True,
            )
            atletas_standby.append(atleta)
            
            # Criar inscrição
            inscricao = Inscricao.objects.create(
                atleta=atleta,
                campeonato=campeonato_ativo,
                classe_escolhida=categoria_standby.classe.nome,
                categoria_escolhida=categoria_standby.label,
                status_inscricao='aprovado',
                peso=peso,
                categoria_ajustada=categoria_standby.label,
                data_pesagem=timezone.now(),
            )
            
            # Criar histórico de pesagem
            PesagemHistorico.objects.create(
                inscricao=inscricao,
                campeonato=campeonato_ativo,
                peso_registrado=peso,
                categoria_ajustada=categoria_standby.label,
                pesado_por=user_pesagem,
            )
        
        # Criar chave com stand-by
        chave_standby = Chave.objects.create(
            campeonato=campeonato_ativo,
            classe=categoria_standby.classe.nome,
            categoria=categoria_standby.label,
        )
        
        # Gerar estrutura da chave (6 atletas em chave de 8 = 2 BYEs)
        inscricoes_standby = Inscricao.objects.filter(
            campeonato=campeonato_ativo,
            classe_escolhida=categoria_standby.classe.nome,
            categoria_escolhida=categoria_standby.label,
            status_inscricao='aprovado'
        )
        atletas_list = [insc.atleta for insc in inscricoes_standby]
        
        from atletas.utils import gerar_chave_escolhida
        estrutura_standby = gerar_chave_escolhida(chave_standby, atletas_list, modelo_chave='eliminatoria_repescagem')
        chave_standby.estrutura = estrutura_standby
        chave_standby.sexo = categoria_standby.sexo
        chave_standby.save()
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ Chave stand-by criada: {chave_standby.classe} - {chave_standby.categoria}'))
        self.stdout.write(self.style.SUCCESS(f'   📊 {len(atletas_list)} atletas (2 BYEs na chave de 8)'))

        # ============================================
        # 2. CHAVE COM REPESCAGEM (8+ atletas)
        # ============================================
        self.stdout.write(self.style.SUCCESS('\n📋 2. Criando chave com REPESCAGEM (8 atletas)...'))
        
        # Limpar chave existente se houver
        Chave.objects.filter(
            campeonato=campeonato_ativo,
            classe=categoria_repescagem.classe.nome,
            categoria=categoria_repescagem.label
        ).delete()
        
        # Limpar inscrições existentes para esta categoria
        Inscricao.objects.filter(
            campeonato=campeonato_ativo,
            classe_escolhida=categoria_repescagem.classe.nome,
            categoria_escolhida=categoria_repescagem.label
        ).delete()
        
        # Criar 8 atletas para repescagem completa
        atletas_repescagem = []
        ano_nasc = self.calcular_ano_nascimento_por_classe(categoria_repescagem.classe.nome)
        peso = self.calcular_peso_categoria(categoria_repescagem)
        
        nomes_f = ['Maria Silva', 'Ana Santos', 'Juliana Oliveira', 'Fernanda Costa', 
                   'Camila Rodrigues', 'Beatriz Almeida', 'Larissa Ferreira', 'Gabriela Martins']
        
        for i, nome in enumerate(nomes_f):
            academia = random.choice(academias)
            atleta = Atleta.objects.create(
                nome=f"{nome} Repescagem {i+1}",
                data_nascimento=f"{ano_nasc}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                sexo='F',
                academia=academia,
                faixa=random.choice(['AZUL', 'ROXA', 'MARRON']),
                federado=random.choice([True, False]),
                classe_inicial=categoria_repescagem.classe.nome,
                status_ativo=True,
            )
            atletas_repescagem.append(atleta)
            
            # Criar inscrição
            inscricao = Inscricao.objects.create(
                atleta=atleta,
                campeonato=campeonato_ativo,
                classe_escolhida=categoria_repescagem.classe.nome,
                categoria_escolhida=categoria_repescagem.label,
                status_inscricao='aprovado',
                peso=peso,
                categoria_ajustada=categoria_repescagem.label,
                data_pesagem=timezone.now(),
            )
            
            # Criar histórico de pesagem
            PesagemHistorico.objects.create(
                inscricao=inscricao,
                campeonato=campeonato_ativo,
                peso_registrado=peso,
                categoria_ajustada=categoria_repescagem.label,
                pesado_por=user_pesagem,
            )
        
        # Criar chave com repescagem
        chave_repescagem = Chave.objects.create(
            campeonato=campeonato_ativo,
            classe=categoria_repescagem.classe.nome,
            categoria=categoria_repescagem.label,
        )
        
        # Gerar estrutura da chave (8 atletas = repescagem completa)
        inscricoes_repescagem = Inscricao.objects.filter(
            campeonato=campeonato_ativo,
            classe_escolhida=categoria_repescagem.classe.nome,
            categoria_escolhida=categoria_repescagem.label,
            status_inscricao='aprovado'
        )
        atletas_list = [insc.atleta for insc in inscricoes_repescagem]
        
        from atletas.utils import gerar_chave_escolhida
        estrutura_repescagem = gerar_chave_escolhida(chave_repescagem, atletas_list, modelo_chave='eliminatoria_repescagem')
        chave_repescagem.estrutura = estrutura_repescagem
        chave_repescagem.sexo = categoria_repescagem.sexo
        chave_repescagem.save()
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ Chave repescagem criada: {chave_repescagem.classe} - {chave_repescagem.categoria}'))
        self.stdout.write(self.style.SUCCESS(f'   📊 {len(atletas_list)} atletas (repescagem completa)'))

        # Resumo
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('✅ CHAVES CRIADAS COM SUCESSO!'))
        self.stdout.write(self.style.SUCCESS('='*60))
        
        self.stdout.write(f'\n📊 RESUMO:\n')
        self.stdout.write(f'   🎯 Chave Stand-by: {chave_standby.id}')
        self.stdout.write(f'      - {chave_standby.classe} - {chave_standby.categoria}')
        self.stdout.write(f'      - {len(atletas_standby)} atletas (2 BYEs)')
        self.stdout.write(f'      - Tipo: Eliminatória com Repescagem')
        
        self.stdout.write(f'\n   🎯 Chave Repescagem: {chave_repescagem.id}')
        self.stdout.write(f'      - {chave_repescagem.classe} - {chave_repescagem.categoria}')
        self.stdout.write(f'      - {len(atletas_repescagem)} atletas (repescagem completa)')
        self.stdout.write(f'      - Tipo: Eliminatória com Repescagem')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('🎉 Chaves prontas para testes!'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

    def calcular_ano_nascimento_por_classe(self, classe_nome):
        """Calcula ano de nascimento baseado na classe"""
        hoje = timezone.now().date()
        
        idade_por_classe = {
            'FESTIVAL': (4, 6),
            'SUB 9': (7, 8),
            'SUB 11': (9, 10),
            'SUB 13': (11, 12),
            'SUB 15': (13, 14),
            'SUB 18': (15, 17),
            'SUB 21': (18, 20),
            'SÊNIOR': (21, 29),
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
            peso_base = (limite_min + limite_max) / 2
            variacao = (limite_max - limite_min) * 0.2
            peso = peso_base + random.uniform(-variacao/2, variacao/2)
        else:
            peso = limite_min + random.uniform(5, 15)
        
        return round(peso, 1)

