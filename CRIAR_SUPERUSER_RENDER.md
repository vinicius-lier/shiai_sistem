# 🔐 Como Criar Superuser no Render

## ⚠️ Problema
O comando `criar_superuser` pode não estar disponível se o deploy não incluiu o arquivo.

## ✅ Solução Rápida (Usar Comandos Django Padrão)

### Opção 1: Usar `createsuperuser` do Django + Atualizar Perfil

```bash
# 1. Criar superuser usando comando padrão do Django
python manage.py createsuperuser

# Você será solicitado a informar:
# - Username: vinicius
# - Email: vinicius@exemplo.com
# - Password: V1n1c1u5@#
# - Password (again): V1n1c1u5@#

# 2. Depois, atualizar o perfil operacional (executar no shell do Django)
python manage.py shell
```

No shell do Django, execute:

```python
from django.contrib.auth.models import User
from atletas.models import UsuarioOperacional

# Buscar o usuário
user = User.objects.get(username='vinicius')

# Garantir que é superuser
user.is_superuser = True
user.is_staff = True
user.save()

# Criar ou atualizar perfil operacional vitalício
perfil, created = UsuarioOperacional.objects.get_or_create(
    user=user,
    defaults={
        'pode_resetar_campeonato': True,
        'pode_criar_usuarios': True,
        'data_expiracao': None,  # Vitalício
        'ativo': True,
        'senha_alterada': True
    }
)

if not created:
    perfil.pode_resetar_campeonato = True
    perfil.pode_criar_usuarios = True
    perfil.data_expiracao = None
    perfil.ativo = True
    perfil.senha_alterada = True
    perfil.save()

print(f"✅ Superuser '{user.username}' configurado com sucesso!")
exit()
```

### Opção 2: Usar `criar_usuario_principal` + Tornar Superuser

```bash
# 1. Criar usuário principal
python manage.py criar_usuario_principal --username vinicius --password V1n1c1u5@# --email vinicius@exemplo.com --first-name Vinicius --last-name Oliveira

# 2. Tornar superuser (executar no shell do Django)
python manage.py shell
```

No shell do Django, execute:

```python
from django.contrib.auth.models import User

user = User.objects.get(username='vinicius')
user.is_superuser = True
user.is_staff = True
user.save()

print(f"✅ Usuário '{user.username}' agora é superuser!")
exit()
```

### Opção 3: Script Python Completo (Copiar e Colar)

Crie um arquivo temporário no Render ou execute direto no shell:

```python
# Executar: python manage.py shell < script_superuser.py
# Ou copiar e colar no shell interativo

from django.contrib.auth.models import User
from atletas.models import UsuarioOperacional

username = 'vinicius'
email = 'vinicius@exemplo.com'
password = 'V1n1c1u5@#'

# Criar ou atualizar usuário
if User.objects.filter(username=username).exists():
    user = User.objects.get(username=username)
    user.set_password(password)
    print(f"Usuário '{username}' atualizado.")
else:
    user = User.objects.create_user(username=username, email=email, password=password)
    print(f"Usuário '{username}' criado.")

# Tornar superuser
user.is_superuser = True
user.is_staff = True
user.save()

# Criar perfil operacional vitalício
perfil, created = UsuarioOperacional.objects.get_or_create(
    user=user,
    defaults={
        'pode_resetar_campeonato': True,
        'pode_criar_usuarios': True,
        'data_expiracao': None,
        'ativo': True,
        'senha_alterada': True
    }
)

if not created:
    perfil.pode_resetar_campeonato = True
    perfil.pode_criar_usuarios = True
    perfil.data_expiracao = None
    perfil.ativo = True
    perfil.senha_alterada = True
    perfil.save()

print(f"\n✅ Superuser '{username}' configurado com sucesso!")
print(f"   Usuário: {username}")
print(f"   Senha: {password}")
print(f"   Acesse: /login/operacional/")
```

## 📝 Passo a Passo Recomendado

1. **Acesse o Shell do Render** (Dashboard → Seu Serviço → Shell)

2. **Execute o script Python:**
   ```bash
   python manage.py shell
   ```

3. **Cole e execute o código da Opção 3 acima**

4. **Saia do shell:**
   ```python
   exit()
   ```

5. **Teste o login:**
   - Acesse: `https://seu-app.onrender.com/login/operacional/`
   - Use: `vinicius` / `V1n1c1u5@#`

## 🔄 Após o Próximo Deploy

Quando o Render fizer deploy do commit `f37daf6`, o comando `criar_superuser` estará disponível e você poderá usar:

```bash
python manage.py criar_superuser --username vinicius --email vinicius@exemplo.com --password V1n1c1u5@# --first-name Vinicius --last-name Oliveira
```

