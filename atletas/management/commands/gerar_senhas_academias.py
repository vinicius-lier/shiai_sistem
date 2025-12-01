"""
Comando Django para gerar senhas para todas as academias que ainda não têm senha em campeonatos ativos.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime as dt
import random
import string

from atletas.models import Academia, Campeonato, AcademiaCampeonatoSenha, AcademiaCampeonato


class Command(BaseCommand):
    help = 'Gera senhas para todas as academias que estão vinculadas a campeonatos mas não têm senha'

    def add_arguments(self, parser):
        parser.add_argument(
            '--campeonato-id',
            type=int,
            help='ID do campeonato específico (opcional). Se não informado, processa todos os campeonatos.',
        )
        parser.add_argument(
            '--apenas-ativas',
            action='store_true',
            help='Processar apenas campeonatos ativos',
        )

    def handle(self, *args, **options):
        campeonato_id = options.get('campeonato_id')
        apenas_ativas = options.get('apenas_ativas', False)
        
        # Determinar quais campeonatos processar
        if campeonato_id:
            campeonatos = Campeonato.objects.filter(id=campeonato_id)
        elif apenas_ativas:
            campeonatos = Campeonato.objects.filter(ativo=True)
        else:
            campeonatos = Campeonato.objects.all()
        
        if not campeonatos.exists():
            self.stdout.write(self.style.WARNING('Nenhum campeonato encontrado.'))
            return
        
        total_senhas_geradas = 0
        total_academias_processadas = 0
        
        for campeonato in campeonatos:
            self.stdout.write(f'\nProcessando campeonato: {campeonato.nome} (ID: {campeonato.id})')
            
            # Buscar academias vinculadas a este campeonato
            academias_vinculadas = AcademiaCampeonato.objects.filter(
                campeonato=campeonato
            ).select_related('academia')
            
            academias_ids = academias_vinculadas.values_list('academia_id', flat=True)
            academias = Academia.objects.filter(id__in=academias_ids, ativo_login=True)
            
            self.stdout.write(f'  Encontradas {academias.count()} academias vinculadas e ativas.')
            
            senhas_geradas_campeonato = 0
            
            for academia in academias:
                total_academias_processadas += 1
                
                # Verificar se já existe senha
                senha_existente = AcademiaCampeonatoSenha.objects.filter(
                    academia=academia,
                    campeonato=campeonato
                ).first()
                
                if senha_existente:
                    self.stdout.write(
                        self.style.WARNING(f'    {academia.nome}: Senha já existe (Login: {senha_existente.login})')
                    )
                    continue
                
                # Gerar login e senha
                login = f"ACADEMIA_{academia.id:03d}"
                senha_plana = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                
                # Calcular data de expiração (5 dias após término do campeonato)
                data_expiracao = None
                if campeonato.data_competicao:
                    data_expiracao = timezone.make_aware(
                        dt.combine(campeonato.data_competicao, dt.min.time())
                    ) + timedelta(days=5)
                
                # Criar senha
                senha_obj = AcademiaCampeonatoSenha.objects.create(
                    academia=academia,
                    campeonato=campeonato,
                    login=login,
                    senha_plana=senha_plana,
                    data_expiracao=data_expiracao,
                )
                
                # Definir senha (criptografa)
                senha_obj.definir_senha(senha_plana)
                senha_obj.save()
                
                senhas_geradas_campeonato += 1
                total_senhas_geradas += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'    {academia.nome}: Senha gerada - Login: {login} | Senha: {senha_plana}'
                    )
                )
            
            if senhas_geradas_campeonato > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✓ {senhas_geradas_campeonato} senha(s) gerada(s) para o campeonato "{campeonato.nome}".'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  Nenhuma senha nova gerada para o campeonato "{campeonato.nome}".')
                )
        
        # Resumo final
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'\n✓ Processamento concluído!'))
        self.stdout.write(f'  Total de academias processadas: {total_academias_processadas}')
        self.stdout.write(self.style.SUCCESS(f'  Total de senhas geradas: {total_senhas_geradas}'))
        self.stdout.write('='*60 + '\n')


