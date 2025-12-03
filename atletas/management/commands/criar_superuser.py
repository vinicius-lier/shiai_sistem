"""
Comando para criar superuser no Render
Uso: python manage.py criar_superuser --username admin --email admin@exemplo.com --password senha123
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from atletas.models import UsuarioOperacional


class Command(BaseCommand):
    help = 'Cria um superuser e garante que tenha perfil operacional vitalício'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, required=True, help='Nome de usuário')
        parser.add_argument('--email', type=str, default='', help='E-mail do usuário')
        parser.add_argument('--password', type=str, required=True, help='Senha do usuário')
        parser.add_argument('--first-name', type=str, default='', help='Primeiro nome')
        parser.add_argument('--last-name', type=str, default='', help='Último nome')

    def handle(self, *args, **options):
        username = options['username']
        email = options.get('email', '')
        password = options['password']
        first_name = options.get('first_name', '')
        last_name = options.get('last_name', '')
        
        # Verificar se o usuário já existe
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Usuário "{username}" já existe. Atualizando...'))
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            if email:
                user.email = email
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Usuário "{username}" atualizado como superuser!'))
        else:
            # Criar novo superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" criado com sucesso!'))
        
        # Garantir que tenha perfil operacional vitalício
        try:
            perfil = user.perfil_operacional
            perfil.pode_resetar_campeonato = True
            perfil.pode_criar_usuarios = True
            perfil.data_expiracao = None  # Vitalício
            perfil.ativo = True
            perfil.senha_alterada = True  # Não precisa mudar senha
            perfil.save()
            self.stdout.write(self.style.SUCCESS(f'Perfil operacional atualizado para vitalício.'))
        except UsuarioOperacional.DoesNotExist:
            # Criar perfil operacional vitalício
            UsuarioOperacional.objects.create(
                user=user,
                pode_resetar_campeonato=True,
                pode_criar_usuarios=True,
                data_expiracao=None,  # Vitalício
                ativo=True,
                senha_alterada=True  # Não precisa mudar senha
            )
            self.stdout.write(self.style.SUCCESS(f'Perfil operacional vitalício criado.'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Superuser "{username}" pronto para uso!'))
        self.stdout.write(self.style.SUCCESS(f'   Usuário: {username}'))
        self.stdout.write(self.style.SUCCESS(f'   Senha: {password}'))
        self.stdout.write(self.style.SUCCESS(f'   Acesse: /login/operacional/'))

