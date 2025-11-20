"""
Comando Django para migrar todos os dados existentes para um evento histórico.
Cria o evento "2ª Copa de Judô – Irias Judo Club" e migra todos os dados.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from datetime import date
from atletas.models import Atleta, Academia, Categoria, Chave, Luta
from eventos.models import Evento, EventoAtleta, EventoParametro


class Command(BaseCommand):
    help = 'Migra todos os dados existentes para o evento histórico "2ª Copa de Judô – Irias Judo Club"'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem salvar no banco (apenas simulação)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  MODO DRY-RUN: Nenhum dado será salvo'))
        
        self.stdout.write(self.style.SUCCESS('🚀 Iniciando migração de dados históricos...'))
        
        with transaction.atomic():
            # 1. Criar ou obter o evento histórico
            evento, created = self.criar_evento_historico(dry_run)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Evento criado: {evento.nome}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️  Evento já existe: {evento.nome}'))
            
            # 2. Migrar atletas para EventoAtleta
            evento_atletas_criados = self.migrar_atletas(evento, dry_run)
            self.stdout.write(self.style.SUCCESS(f'✅ {evento_atletas_criados} EventoAtleta(s) criado(s)'))
            
            # 3. Vincular chaves ao evento
            chaves_vinculadas = self.vincular_chaves(evento, dry_run)
            self.stdout.write(self.style.SUCCESS(f'✅ {chaves_vinculadas} chave(s) vinculada(s) ao evento'))
            
            # 4. Recalcular pontos baseado nas lutas
            pontos_calculados = self.recalcular_pontos(evento, dry_run)
            self.stdout.write(self.style.SUCCESS(f'✅ Pontos recalculados para {pontos_calculados} atleta(s)'))
            
            # 5. Atualizar ranking geral (apenas contagem, não altera pontos)
            academias_atualizadas = self.atualizar_ranking_geral(evento, dry_run)
            self.stdout.write(self.style.SUCCESS(f'✅ {academias_atualizadas} academia(s) com pontos calculados'))
            
            # 6. Resumo final
            total_atletas = EventoAtleta.objects.filter(evento=evento).count() if not dry_run else 0
            total_chaves = evento.chaves.count() if not dry_run else 0
            total_pontos = EventoAtleta.objects.filter(evento=evento).aggregate(
                total=Sum('pontos_evento')
            )['total'] or 0 if not dry_run else 0
            
            self.stdout.write(self.style.SUCCESS('\n📊 RESUMO DA MIGRAÇÃO:'))
            self.stdout.write(f'   - Evento: {evento.nome}')
            self.stdout.write(f'   - Atletas migrados: {total_atletas}')
            self.stdout.write(f'   - Chaves vinculadas: {total_chaves}')
            self.stdout.write(f'   - Total de pontos: {total_pontos}')
            
            if dry_run:
                self.stdout.write(self.style.WARNING('\n⚠️  DRY-RUN: Nenhum dado foi salvo. Execute sem --dry-run para aplicar.'))
                transaction.set_rollback(True)
            else:
                self.stdout.write(self.style.SUCCESS('\n✅ Migração concluída com sucesso!'))
                self.stdout.write(self.style.SUCCESS(f'✅ Evento "{evento.nome}" está ENCERRADO e todos os dados foram preservados.'))
    
    def criar_evento_historico(self, dry_run):
        """Cria o evento histórico se não existir"""
        nome_evento = "2ª Copa de Judô Iria's"
        
        evento, created = Evento.objects.get_or_create(
            nome=nome_evento,
            defaults={
                'descricao': 'Evento histórico - Dados migrados do sistema anterior',
                'local': 'Angra dos Reis',
                'cidade': 'Angra dos Reis',
                'data_evento': date(2024, 11, 10),  # Data aproximada
                'data_limite_inscricao': date(2024, 11, 5),  # Prazo já encerrado
                'status': 'ENCERRADO',
                'ativo': True,
                'pesagem_encerrada': True,
            }
        )
        
        # Se evento já existe, atualizar para garantir status correto
        if not created and not dry_run:
            evento.status = 'ENCERRADO'
            evento.pesagem_encerrada = True
            evento.local = 'Angra dos Reis'
            evento.cidade = 'Angra dos Reis'
            if not evento.data_evento:
                evento.data_evento = date(2024, 11, 10)
            evento.save()
        
        if not dry_run and created:
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
    
    def migrar_atletas(self, evento, dry_run):
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
                if not categoria_inicial:
                    categoria_inicial = Categoria.objects.filter(
                        classe=atleta.classe,
                        sexo=atleta.sexo,
                        label__icontains=atleta.categoria_nome
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
                    categoria_final = Categoria.objects.filter(
                        classe=atleta.classe,
                        sexo=atleta.sexo,
                        label__icontains=categoria_nome_final
                    ).first()
            
            # Se não encontrou categoria_final, usar categoria_inicial
            if not categoria_final:
                categoria_final = categoria_inicial
            
            # Determinar status
            status = 'OK'
            if atleta.status == 'Eliminado Peso':
                status = 'ELIMINADO_PESO'
            elif atleta.status == 'Eliminado Indisciplina':
                status = 'ELIMINADO_IND'
            
            # Criar EventoAtleta
            if not dry_run:
                from decimal import Decimal
                
                # Converter pesos de FloatField para DecimalField
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
                
                evento_atleta = EventoAtleta.objects.create(
                    evento=evento,
                    atleta=atleta,
                    academia=atleta.academia,
                    # Dados congelados
                    classe=atleta.classe or '',
                    categoria_inicial=categoria_inicial,
                    categoria_final=categoria_final,
                    # Pesos
                    peso_previsto=peso_previsto_decimal,
                    peso_oficial=peso_oficial_decimal,
                    # Status
                    status=status,
                    remanejado=atleta.remanejado,
                    motivo=atleta.motivo_ajuste or '',
                    # Pontos (será calculado depois)
                    pontos=0,
                    pontos_evento=0,
                    valor_inscricao=0,
                    # Campos de compatibilidade
                    categoria=categoria_final,
                    categoria_ajustada=categoria_nome_final or '',
                    status_pesagem='OK' if atleta.peso_oficial else 'PENDENTE',
                    desclassificado=(atleta.status == 'Eliminado Peso'),
                )
            count += 1
        
        return count
    
    def vincular_chaves(self, evento, dry_run):
        """Vincula todas as chaves existentes ao evento"""
        count = 0
        
        for chave in Chave.objects.all():
            if chave.evento:
                continue  # Já vinculada
            
            if not dry_run:
                chave.evento = evento
                chave.save()
            count += 1
        
        return count
    
    def recalcular_pontos(self, evento, dry_run):
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
            penalidade_remanejamento = parametros.penalidade_remanejamento
        except EventoParametro.DoesNotExist:
            # Valores padrão
            pontos_1 = 10
            pontos_2 = 7
            pontos_3 = 5
            penalidade_remanejamento = 1
        
        # Resetar pontos de todos os EventoAtleta
        if not dry_run:
            evento_atletas.update(pontos=0, pontos_evento=0)
        
        # Para cada chave do evento
        for chave in evento.chaves.all():
            # Obter resultados da chave
            resultados = get_resultados_chave(chave)
            
            if not resultados:
                # Se não há resultados, verificar se há lutas concluídas
                # e tentar calcular resultados manualmente
                lutas_concluidas = chave.lutas.filter(concluida=True, vencedor__isnull=False)
                if lutas_concluidas.exists():
                    # Tentar obter vencedor da luta final
                    # (lógica simplificada - pegar vencedor da última luta concluída)
                    pass  # Continuar sem pontos se não há resultados claros
                continue
            
            # Atribuir pontos aos atletas baseado na posição
            for posicao, atleta_id in enumerate(resultados[:5], 1):  # Até 5º lugar
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
                    # 4º e 5º lugar não recebem pontos adicionais
                    
                    # Verificar se é Festival (sempre 1 ponto)
                    if atleta.classe == 'Festival':
                        pontos = 1
                    
                    if not dry_run:
                        # Somar pontos (não substituir, caso já tenha pontos de outra chave)
                        evento_atleta.pontos_evento = (evento_atleta.pontos_evento or 0) + pontos
                        evento_atleta.save()
                    
                    count += 1
                except (Atleta.DoesNotExist, EventoAtleta.DoesNotExist):
                    continue
        
        # Aplicar penalidade de remanejamento (subtrair pontos)
        for evento_atleta in evento_atletas.filter(remanejado=True):
            if not dry_run:
                # Subtrair penalidade, mas não deixar negativo
                evento_atleta.pontos = max(0, evento_atleta.pontos - penalidade_remanejamento)
                evento_atleta.pontos_evento = evento_atleta.pontos  # Sincronizar
                evento_atleta.save()
        
        return count
    
    def atualizar_ranking_geral(self, evento, dry_run):
        """Atualiza o ranking geral somando pontos do evento"""
        academias_atualizadas = set()
        
        # Agrupar pontos por academia
        from django.db.models import Sum
        pontos_por_academia = EventoAtleta.objects.filter(evento=evento).values('academia').annotate(
            total_pontos=Sum('pontos')
        )
        
        for item in pontos_por_academia:
            academia_id = item['academia']
            total_pontos = item['total_pontos'] or 0
            
            try:
                academia = Academia.objects.get(id=academia_id)
                
                if not dry_run:
                    # Somar pontos ao ranking geral da academia
                    academia.pontos = (academia.pontos or 0) + total_pontos
                    academia.save()
                
                academias_atualizadas.add(academia_id)
            except Academia.DoesNotExist:
                continue
        
        return len(academias_atualizadas)

