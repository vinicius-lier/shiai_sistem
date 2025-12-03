# 🔧 Solução: Migration não aplicada no Render

## ❌ Problema

Erro ao executar `criar_organizador`:
```
sqlite3.OperationalError: no such table: atletas_organizador
```

**Causa:** A migration `0038_add_multi_tenant` não foi aplicada no banco de dados do Render.

## ✅ Solução Imediata

Execute manualmente no shell do Render:

```bash
# 1. Aplicar migrations
python manage.py migrate --noinput

# 2. Verificar se foi aplicada
python manage.py showmigrations atletas | grep "0038_add_multi_tenant"

# 3. Se ainda não aplicada, forçar:
python manage.py migrate atletas 0038_add_multi_tenant --fake
python manage.py migrate --noinput
```

## 🔄 Solução Permanente

O `build.sh` foi atualizado para garantir que todas as migrations sejam aplicadas:

```bash
python manage.py migrate --noinput --run-syncdb
```

## 📋 Passos para Corrigir Agora

### No Render (Shell):

1. **Aplicar migrations:**
   ```bash
   python manage.py migrate --noinput
   ```

2. **Verificar se a tabela foi criada:**
   ```bash
   python manage.py shell
   ```
   ```python
   from atletas.models import Organizador
   print(Organizador.objects.count())  # Deve retornar 0 (sem erro)
   ```

3. **Criar organizador:**
   ```bash
   python manage.py criar_organizador \
     --nome "Organizador Padrão" \
     --email admin@exemplo.com \
     --associar-dados \
     --usuario vinicius
   ```

## 🚀 Próximo Deploy

O `build.sh` atualizado garantirá que:
- ✅ Todas as migrations sejam aplicadas
- ✅ Nenhuma migration fique pendente
- ✅ O banco esteja sempre atualizado

## ⚠️ Importante

Se o erro persistir após aplicar migrations, pode ser necessário:

1. **Verificar se a migration existe:**
   ```bash
   ls -la atletas/migrations/0038_add_multi_tenant.py
   ```

2. **Forçar recriação (CUIDADO - apenas se necessário):**
   ```bash
   python manage.py migrate atletas zero
   python manage.py migrate atletas
   ```

3. **Verificar logs do build no Render:**
   - Vá em **Logs** no painel do Render
   - Procure por erros durante o build
   - Verifique se `migrate` foi executado

