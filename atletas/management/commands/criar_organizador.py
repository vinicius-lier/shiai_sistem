"""
Comando para criar um organizador e associar dados existentes
Uso: python manage.py criar_organizador --nome "Nome do Organizador" --email email@exemplo.com
"""
from django.core.management.base import BaseCommand
from atletas.models import Organizador, Academia, Campeonato, CadastroOperacional, UserProfile
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Cria um organizador e opcionalmente associa dados existentes a ele'

    def add_arguments(self, parser):
        parser.add_argument('--nome', type=str, required=True, help='Nome do organizador')
        parser.add_argument('--email', type=str, required=True, help='E-mail do organizador')
        parser.add_argument('--telefone', type=str, default='', help='Telefone do organizador')
        parser.add_argument('--associar-dados', action='store_true', help='Associar dados existentes (sem organizador) a este organizador')
        parser.add_argument('--usuario', type=str, help='Username do usuário a associar ao organizador')

    def handle(self, *args, **options):
        nome = options['nome']
        email = options['email']
        telefone = options.get('telefone', '')
        associar_dados = options.get('associar_dados', False)
        username = options.get('usuario')

        # Criar organizador
        organizador, created = Organizador.objects.get_or_create(
            email=email,
            defaults={
                'nome': nome,
                'telefone': telefone,
                'ativo': True
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Organizador "{nome}" criado com sucesso!'))
        else:
            organizador.nome = nome
            organizador.telefone = telefone
            organizador.save()
            self.stdout.write(self.style.WARNING(f'⚠️  Organizador com email "{email}" já existe. Atualizado.'))

        # Associar dados existentes se solicitado
        if associar_dados:
            academias_sem_org = Academia.objects.filter(organizador__isnull=True)
            campeonatos_sem_org = Campeonato.objects.filter(organizador__isnull=True)
            cadastros_sem_org = CadastroOperacional.objects.filter(organizador__isnull=True)

            count_academias = academias_sem_org.update(organizador=organizador)
            count_campeonatos = campeonatos_sem_org.update(organizador=organizador)
            count_cadastros = cadastros_sem_org.update(organizador=organizador)

            self.stdout.write(self.style.SUCCESS(f'\n✅ Dados associados:'))
            self.stdout.write(f'   - {count_academias} academias')
            self.stdout.write(f'   - {count_campeonatos} campeonatos')
            self.stdout.write(f'   - {count_cadastros} cadastros operacionais')

        # Associar usuário se fornecido
        if username:
            try:
                user = User.objects.get(username=username)
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'organizador': organizador}
                )
                if not created:
                    profile.organizador = organizador
                    profile.save()
                self.stdout.write(self.style.SUCCESS(f'\n✅ Usuário "{username}" associado ao organizador "{nome}"'))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'\n❌ Usuário "{username}" não encontrado.'))

        self.stdout.write(self.style.SUCCESS(f'\n✅ Organizador configurado:'))
        self.stdout.write(f'   Nome: {organizador.nome}')
        self.stdout.write(f'   Email: {organizador.email}')
        self.stdout.write(f'   ID: {organizador.id}')
        
        if username:
            self.stdout.write(self.style.SUCCESS(f'\n📝 Próximos passos:'))
            self.stdout.write(f'   1. O usuário "{username}" já está associado ao organizador')
            self.stdout.write(f'   2. Configure permissões operacionais se necessário:')
            self.stdout.write(f'      python manage.py atualizar_perfil_principal --username {username}')
            self.stdout.write(f'   3. O usuário pode fazer login em /login/operacional/')

