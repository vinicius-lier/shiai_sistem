# 🚀 Instruções para Configurar Heroku

## Pré-requisitos

1. **Instalar Heroku CLI**:
   ```bash
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. **Fazer login no Heroku**:
   ```bash
   heroku login
   ```

## Configuração Rápida (Script Automatizado)

Execute o script fornecido:
```bash
./configurar_heroku.sh
```

## Configuração Manual (Passo a Passo)

### 1. Conectar ao App Heroku Existente

Se você já criou o app `shiai-sistem-a1f98abf96a1` no Heroku:

```bash
cd /home/vinicius/Downloads/shiai_sistem-main
heroku git:remote -a shiai-sistem-a1f98abf96a1
```

### 2. Configurar Variáveis de Ambiente

```bash
# Gerar SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Configurar no Heroku (substitua YOUR_SECRET_KEY pelo valor gerado)
heroku config:set SECRET_KEY="YOUR_SECRET_KEY"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS="shiai-sistem-a1f98abf96a1.herokuapp.com,*.herokuapp.com"
```

### 3. Adicionar PostgreSQL

```bash
heroku addons:create heroku-postgresql:mini
```

### 4. Fazer Deploy

```bash
git push heroku main
```

### 5. Executar Migrations

```bash
heroku run python manage.py migrate
```

### 6. Criar Superusuário

```bash
heroku run python manage.py createsuperuser
```

### 7. Verificar Status

```bash
heroku ps
heroku logs --tail
```

## Comandos Úteis

### Ver logs em tempo real
```bash
heroku logs --tail
```

### Abrir app no navegador
```bash
heroku open
```

### Executar comando Django
```bash
heroku run python manage.py <comando>
```

### Ver variáveis de ambiente
```bash
heroku config
```

### Reiniciar app
```bash
heroku restart
```

### Ver informações do app
```bash
heroku apps:info
```

## Troubleshooting

### Erro: "No app specified"
- Certifique-se de que o remote está configurado: `git remote -v`
- Se não estiver, conecte: `heroku git:remote -a nome-do-app`

### Erro: "Database connection"
- Verifique se o PostgreSQL está ativo: `heroku addons`
- Se não estiver, adicione: `heroku addons:create heroku-postgresql:mini`

### Erro: "Static files"
- O WhiteNoise já está configurado no `settings.py`
- Se necessário, desabilite collectstatic: `heroku config:set DISABLE_COLLECTSTATIC=1`

### Verificar se o app está rodando
```bash
heroku ps:scale web=1
```

## Próximos Passos

1. ✅ Configurar domínio personalizado (opcional)
2. ✅ Configurar SSL/HTTPS (automático no Heroku)
3. ✅ Configurar backups do banco de dados
4. ✅ Configurar monitoramento e alertas

