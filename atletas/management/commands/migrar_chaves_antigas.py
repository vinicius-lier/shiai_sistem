"""
Comando para migrar chaves antigas (sem evento) para eventos.
Pergunta ao administrador a qual evento cada chave pertence e vincula corretamente.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from atletas.models import Chave, Luta
from eventos.models import Evento


class Command(BaseCommand):
    help = 'Migra chaves antigas (sem evento) para eventos específicos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--evento-id',
            type=int,
            help='ID do evento para vincular todas as chaves sem evento (se não informado, pergunta para cada chave)',
        )
        parser.add_argument(
            '--auto',
            action='store_true',
            help='Vincula automaticamente ao evento mais recente (não pergunta)',
        )

    def handle(self, *args, **options):
        # Buscar todas as chaves sem evento
        chaves_sem_evento = Chave.objects.filter(evento__isnull=True)
        
        if not chaves_sem_evento.exists():
            self.stdout.write(self.style.SUCCESS('✅ Nenhuma chave sem evento encontrada. Tudo está atualizado!'))
            return
        
        total_chaves = chaves_sem_evento.count()
        self.stdout.write(self.style.WARNING(f'⚠️  Encontradas {total_chaves} chave(s) sem evento.'))
        
        # Listar eventos disponíveis
        eventos = Evento.objects.all().order_by('-data_evento')
        if not eventos.exists():
            self.stdout.write(self.style.ERROR('❌ Nenhum evento encontrado. Crie um evento primeiro.'))
            return
        
        self.stdout.write('\n📋 Eventos disponíveis:')
        for evento in eventos:
            self.stdout.write(f'   [{evento.id}] {evento.nome} - {evento.data_evento}')
        
        # Determinar evento a usar
        evento_selecionado = None
        
        if options['evento_id']:
            try:
                evento_selecionado = Evento.objects.get(id=options['evento_id'])
                self.stdout.write(self.style.SUCCESS(f'\n✅ Usando evento: {evento_selecionado.nome}'))
            except Evento.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Evento com ID {options["evento_id"]} não encontrado.'))
                return
        elif options['auto']:
            # Usar evento mais recente
            evento_selecionado = eventos.first()
            self.stdout.write(self.style.SUCCESS(f'\n✅ Usando evento mais recente: {evento_selecionado.nome}'))
        else:
            # Perguntar para cada chave
            self.stdout.write('\n')
        
        # Processar cada chave
        vinculadas = 0
        ignoradas = 0
        
        for chave in chaves_sem_evento:
            evento = evento_selecionado
            
            # Se não foi definido um evento global, perguntar para cada chave
            if not evento:
                self.stdout.write(f'\n📦 Chave: {chave.classe} - {chave.get_sexo_display()} - {chave.categoria}')
                self.stdout.write(f'   Criada em: {chave.criada_em}')
                self.stdout.write(f'   Atletas: {chave.atletas.count()}')
                
                evento_id_input = input('   Digite o ID do evento (ou "p" para pular): ').strip()
                
                if evento_id_input.lower() == 'p':
                    self.stdout.write(self.style.WARNING('   ⏭️  Chave ignorada.'))
                    ignoradas += 1
                    continue
                
                try:
                    evento_id = int(evento_id_input)
                    evento = Evento.objects.get(id=evento_id)
                except (ValueError, Evento.DoesNotExist):
                    self.stdout.write(self.style.ERROR(f'   ❌ Evento inválido. Chave ignorada.'))
                    ignoradas += 1
                    continue
            
            # Vincular chave e lutas ao evento
            with transaction.atomic():
                chave.evento = evento
                chave.save()
                
                # Atualizar todas as lutas desta chave
                lutas_atualizadas = Luta.objects.filter(chave=chave).update(evento=evento)
                
                self.stdout.write(self.style.SUCCESS(
                    f'   ✅ Chave vinculada ao evento "{evento.nome}" (atualizadas {lutas_atualizadas} luta(s))'
                ))
                vinculadas += 1
        
        # Resumo
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'✅ Migração concluída!'))
        self.stdout.write(f'   📦 Total de chaves: {total_chaves}')
        self.stdout.write(self.style.SUCCESS(f'   ✅ Vinculadas: {vinculadas}'))
        if ignoradas > 0:
            self.stdout.write(self.style.WARNING(f'   ⏭️  Ignoradas: {ignoradas}'))

