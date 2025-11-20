"""
Comando Django para criar automaticamente o evento "2ª Copa de Judô Iria's"
e migrar todos os dados existentes.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from datetime import date
from atletas.models import Atleta, Academia, Categoria, Chave, Luta
from eventos.models import Evento, EventoAtleta, EventoParametro


class Command(BaseCommand):
    help = 'Cria automaticamente o evento "2ª Copa de Judô Iria\'s" e migra todos os dados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a recriação do evento mesmo se já existir',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando criação do evento histórico...'))
        
        with transaction.atomic():
            # 1. Criar ou obter o evento histórico
            evento, created = self.criar_evento_historico(force)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Evento criado: {evento.nome}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️  Evento já existe: {evento.nome}'))
            
            # 2. Migrar atletas para EventoAtleta
            evento_atletas_criados = self.migrar_atletas(evento)
            self.stdout.write(self.style.SUCCESS(f'✅ {evento_atletas_criados} EventoAtleta(s) criado(s)'))
            
            # 3. Vincular chaves ao evento
            chaves_vinculadas = self.vincular_chaves(evento)
            self.stdout.write(self.style.SUCCESS(f'✅ {chaves_vinculadas} chave(s) vinculada(s) ao evento'))
            
            # 4. Recalcular pontos baseado nas lutas
            pontos_calculados = self.recalcular_pontos(evento)
            self.stdout.write(self.style.SUCCESS(f'✅ Pontos recalculados para {pontos_calculados} atleta(s)'))
            
            # 5. Resumo final
            total_atletas = EventoAtleta.objects.filter(evento=evento).count()
            total_chaves = evento.chaves.count()
            total_pontos = EventoAtleta.objects.filter(evento=evento).aggregate(
                total=Sum('pontos')
            )['total'] or 0
            
            self.stdout.write(self.style.SUCCESS('\n📊 RESUMO DA MIGRAÇÃO:'))
            self.stdout.write(f'   - Evento: {evento.nome}')
            self.stdout.write(f'   - Atletas migrados: {total_atletas}')
            self.stdout.write(f'   - Chaves vinculadas: {total_chaves}')
            self.stdout.write(f'   - Total de pontos: {total_pontos}')
            self.stdout.write(self.style.SUCCESS('\n✅ Migração concluída com sucesso!'))
    
    def criar_evento_historico(self, force=False):
        """Cria o evento histórico se não existir"""
        nome_evento = "2ª Copa de Judô Iria's"
        
        if force:
            # Remover evento existente se force=True
            Evento.objects.filter(nome=nome_evento).delete()
        
        evento, created = Evento.objects.get_or_create(
            nome=nome_evento,
            defaults={
                'descricao': 'Evento histórico - Dados migrados do sistema anterior',
                'local': 'Angra dos Reis',
                'cidade': 'Angra dos Reis',
                'data_evento': date(2024, 11, 10),
                'data_limite_inscricao': date(2024, 11, 5),
                'status': 'ENCERRADO',
                'ativo': True,
                'pesagem_encerrada': True,
            }
        )
        
        # Se evento já existe, atualizar para garantir status correto
        if not created:
            evento.status = 'ENCERRADO'
            evento.pesagem_encerrada = True
            evento.local = 'Angra dos Reis'
            evento.cidade = 'Angra dos Reis'
            if not evento.data_evento:
                evento.data_evento = date(2024, 11, 10)
            evento.save()
        
        if created:
            # Criar parâmetros padrão para o evento
            EventoParametro.objects.get_or_create(
                evento=evento,
                defaults={
                    'idade_min': 3,
                    'idade_max': 99,
                    'usar_pesagem': True,
                    'usar_chaves_automaticas': True,
                    'permitir_festival': True,
                    'pontuacao_primeiro': 10,
                    'pontuacao_segundo': 7,
                    'pontuacao_terceiro': 5,
                    'penalidade_remanejamento': 1,
                }
            )
        
        return evento, created
    
    def migrar_atletas(self, evento):
        """Migra todos os atletas para EventoAtleta"""
        count = 0
        
        for atleta in Atleta.objects.all().select_related('academia'):
            # Verificar se já existe EventoAtleta para este atleta neste evento
            if EventoAtleta.objects.filter(evento=evento, atleta=atleta).exists():
                continue
            
            # Buscar categorias
            categoria_inicial = None
            categoria_final = None
            
            # Categoria inicial (original da inscrição)
            if atleta.categoria_nome and atleta.classe and atleta.sexo:
                categoria_inicial = Categoria.objects.filter(
                    classe=atleta.classe,
                    sexo=atleta.sexo,
                    categoria_nome=atleta.categoria_nome
                ).first()
            
            # Categoria final (após ajustes/remanejamento)
            categoria_nome_final = None
            if atleta.categoria_ajustada:
                categoria_nome_final = atleta.categoria_ajustada
            elif atleta.categoria_nome:
                categoria_nome_final = atleta.categoria_nome
            
            if categoria_nome_final and atleta.classe and atleta.sexo:
                categoria_final = Categoria.objects.filter(
                    classe=atleta.classe,
                    sexo=atleta.sexo,
                    categoria_nome=categoria_nome_final
                ).first()
            
            if not categoria_final:
                categoria_final = categoria_inicial
            
            # Determinar status
            status = 'OK'
            if atleta.status == 'Eliminado Peso':
                status = 'ELIMINADO_PESO'
            elif atleta.status == 'Eliminado Indisciplina':
                status = 'ELIMINADO_IND'
            
            # Criar EventoAtleta
            from decimal import Decimal
            
            peso_previsto_decimal = None
            if atleta.peso_previsto:
                try:
                    peso_previsto_decimal = Decimal(str(atleta.peso_previsto))
                except (ValueError, TypeError):
                    peso_previsto_decimal = None
            
            peso_oficial_decimal = None
            if atleta.peso_oficial:
                try:
                    peso_oficial_decimal = Decimal(str(atleta.peso_oficial))
                except (ValueError, TypeError):
                    peso_oficial_decimal = None
            
            # Determinar status_pesagem: só OK se realmente tem peso_oficial
            # Se não tem peso_oficial, deve ser PENDENTE para permitir pesagem
            status_pesagem_final = 'OK' if peso_oficial_decimal else 'PENDENTE'
            
            EventoAtleta.objects.create(
                evento=evento,
                atleta=atleta,
                academia=atleta.academia,
                classe=atleta.classe or '',
                categoria_inicial=categoria_inicial,
                categoria_final=categoria_final,
                peso_previsto=peso_previsto_decimal,
                peso_oficial=peso_oficial_decimal,
                status=status,
                remanejado=atleta.remanejado if hasattr(atleta, 'remanejado') else False,
                motivo=atleta.motivo_ajuste or '' if hasattr(atleta, 'motivo_ajuste') else '',
                pontos=0,
                pontos_evento=0,
                valor_inscricao=0,
                categoria=categoria_final,
                categoria_ajustada=categoria_nome_final or '',
                status_pesagem=status_pesagem_final,  # PENDENTE se não tem peso, OK se tem
                desclassificado=(atleta.status == 'Eliminado Peso'),
            )
            count += 1
        
        return count
    
    def vincular_chaves(self, evento):
        """Vincula todas as chaves existentes ao evento"""
        count = 0
        
        for chave in Chave.objects.all():
            if chave.evento:
                continue  # Já vinculada
            
            chave.evento = evento
            chave.save()
            count += 1
        
        return count
    
    def recalcular_pontos(self, evento):
        """Recalcula pontos baseado nas lutas e resultados das chaves"""
        from atletas.utils import get_resultados_chave
        
        evento_atletas = EventoAtleta.objects.filter(evento=evento)
        count = 0
        
        # Obter parâmetros do evento
        try:
            parametros = evento.parametros
            pontos_1 = parametros.pontuacao_primeiro
            pontos_2 = parametros.pontuacao_segundo
            pontos_3 = parametros.pontuacao_terceiro
        except EventoParametro.DoesNotExist:
            pontos_1 = 10
            pontos_2 = 7
            pontos_3 = 5
        
        # Resetar pontos
        evento_atletas.update(pontos=0, pontos_evento=0)
        
        # Para cada chave do evento
        for chave in evento.chaves.all():
            resultados = get_resultados_chave(chave)
            
            if not resultados:
                continue
            
            # Atribuir pontos aos atletas baseado na posição
            for posicao, atleta_id in enumerate(resultados[:5], 1):
                if not atleta_id:
                    continue
                
                try:
                    atleta = Atleta.objects.get(id=atleta_id)
                    evento_atleta = EventoAtleta.objects.get(evento=evento, atleta=atleta)
                    
                    pontos = 0
                    if posicao == 1:
                        pontos = pontos_1
                    elif posicao == 2:
                        pontos = pontos_2
                    elif posicao == 3:
                        pontos = pontos_3
                    
                    # Festival sempre 1 ponto
                    if atleta.classe == 'Festival':
                        pontos = 1
                    
                    evento_atleta.pontos = (evento_atleta.pontos or 0) + pontos
                    evento_atleta.pontos_evento = evento_atleta.pontos
                    evento_atleta.save()
                    
                    count += 1
                except (Atleta.DoesNotExist, EventoAtleta.DoesNotExist):
                    continue
        
        # Aplicar penalidade de remanejamento
        try:
            penalidade = evento.parametros_config.penalidade_remanejamento if hasattr(evento, 'parametros_config') else 1
        except EventoParametro.DoesNotExist:
            penalidade = 1
        
        for evento_atleta in evento_atletas.filter(remanejado=True):
            evento_atleta.pontos = max(0, evento_atleta.pontos - penalidade)
            evento_atleta.pontos_evento = evento_atleta.pontos
            evento_atleta.save()
        
        return count

