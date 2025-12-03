"""
Comando para atualizar perfil de usuário existente para ter permissões de principal
Uso: python manage.py atualizar_perfil_principal --username vinicius
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from atletas.models import UsuarioOperacional
from django.utils import timezone


class Command(BaseCommand):
    help = 'Atualiza perfil de usuário existente para ter permissões de principal (pode criar usuários e resetar campeonato)'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, required=True, help='Nome de usuário a atualizar')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Usuário "{username}" não encontrado.'))
            return
        
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
        
        self.stdout.write(self.style.SUCCESS('\n✅ Perfil principal configurado:'))
        self.stdout.write(f'   Usuário: {username}')
        self.stdout.write(f'   Permissões: Resetar Campeonato ✓ | Criar Usuários ✓')
        self.stdout.write(f'   Validade: Vitalício')
        self.stdout.write(self.style.SUCCESS('\n✅ O botão "Usuários Operacionais" agora deve aparecer no menu!'))

