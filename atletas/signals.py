from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Campeonato, Academia

User = get_user_model()

@receiver(post_save, sender=Campeonato)
def criar_usuarios_operacionais(sender, instance, created, **kwargs):
    """
    Sempre que um novo campeonato é criado,
    cada academia recebe um usuário operacional temporário.
    """
    if not created:
        return

    academias = Academia.objects.all()

    for academia in academias:
        username = f"academia_{academia.id}"
        senha = f"academia{academia.id}2025"

        user, new_user = User.objects.get_or_create(username=username)

        # Atualiza dados básicos
        user.email = f"{username}@shiai.com"
        user.set_password(senha)

        # Vínculo com a Academia (se existir esse campo no User)
        if hasattr(user, "academia"):
            user.academia = academia
        else:
            print(f"⚠ AVISO: O usuário {username} não possui campo 'academia'. Verificar modelo User.")

        user.save()

        print("✔ Usuário criado/atualizado:", username, "→", academia.nome)
