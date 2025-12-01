"""
Comando para criar o usuário principal do sistema operacional
Uso: python manage.py criar_usuario_principal --username admin --password senha123 --email admin@shiai.com
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from atletas.models import UsuarioOperacional
from django.utils import timezone


class Command(BaseCommand):
    help = 'Cria o usuário principal do sistema operacional com permissões totais'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, required=True, help='Nome de usuário')
        parser.add_argument('--password', type=str, required=True, help='Senha do usuário')
        parser.add_argument('--email', type=str, default='', help='E-mail do usuário')
        parser.add_argument('--first-name', type=str, default='', help='Primeiro nome')
        parser.add_argument('--last-name', type=str, default='', help='Último nome')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        email = options.get('email', '')
        first_name = options.get('first_name', '')
        last_name = options.get('last_name', '')
        
        # Verificar se o usuário já existe
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Usuário "{username}" já existe. Atualizando...'))
            user = User.objects.get(username=username)
            user.set_password(password)
            if email:
                user.email = email
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            user.save()
        else:
            # Criar novo usuário
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            self.stdout.write(self.style.SUCCESS(f'Usuário "{username}" criado com sucesso!'))
        
        # Criar ou atualizar perfil operacional
        perfil, created = UsuarioOperacional.objects.get_or_create(
            user=user,
            defaults={
                'pode_resetar_campeonato': True,
                'pode_criar_usuarios': True,
                'data_expiracao': None,  # Vitalício
                'ativo': True
            }
        )
        
        if not created:
            # Atualizar perfil existente
            perfil.pode_resetar_campeonato = True
            perfil.pode_criar_usuarios = True
            perfil.data_expiracao = None  # Vitalício
            perfil.ativo = True
            perfil.save()
            self.stdout.write(self.style.SUCCESS(f'Perfil operacional de "{username}" atualizado com sucesso!'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Perfil operacional de "{username}" criado com sucesso!'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Usuário principal configurado:'))
        self.stdout.write(f'   Usuário: {username}')
        self.stdout.write(f'   Permissões: Resetar Campeonato ✓ | Criar Usuários ✓')
        self.stdout.write(f'   Validade: Vitalício')
        self.stdout.write(self.style.WARNING('\n⚠️  Guarde estas credenciais com segurança!'))




