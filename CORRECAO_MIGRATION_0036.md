# 🔧 Correção: Migration 0036_seed_categorias - IntegrityError

## 📋 Problema Identificado

A migration `0036_seed_categorias.py` estava falhando com o erro:

```
django.db.utils.IntegrityError: NOT NULL constraint failed: atletas_categoria.classe
```

## 🔍 Causa Raiz

O problema ocorria quando o `get_or_create()` tentava criar uma nova categoria. Em alguns casos, especialmente quando usando modelos históricos (`apps.get_model`) em migrations, o Django pode ter dificuldade em resolver ForeignKeys corretamente quando passados como argumentos de busca no `get_or_create()`.

## ✅ Solução Aplicada

A migration foi refatorada para usar uma abordagem mais explícita:

1. **Verificação manual**: Usa `get()` para verificar se a categoria já existe
2. **Atualização explícita**: Se existe, atualiza os campos necessários
3. **Criação explícita**: Se não existe, cria explicitamente usando `create()` com todos os campos

### Código Antes (Problemático):

```python
Categoria.objects.get_or_create(
    classe=classe,
    sexo=sexo,
    categoria_nome=nome,
    defaults={...}
)
```

### Código Depois (Corrigido):

```python
try:
    categoria = Categoria.objects.get(
        classe=classe,
        sexo=sexo,
        categoria_nome=nome
    )
    # Atualizar se já existe
    categoria.limite_min = Decimal(str(minimo))
    categoria.limite_max = Decimal(str(maximo)) if maximo is not None else None
    categoria.label = label
    categoria.save()
except Categoria.DoesNotExist:
    # Criar explicitamente com todos os campos
    Categoria.objects.create(
        classe=classe,
        sexo=sexo,
        categoria_nome=nome,
        limite_min=Decimal(str(minimo)),
        limite_max=Decimal(str(maximo)) if maximo is not None else None,
        label=label
    )
```

## 🚀 Como Aplicar a Correção

### No Render (Shell):

```bash
# 1. Aplicar migrations (a 0036 agora deve funcionar)
python manage.py migrate --noinput

# 2. Verificar se as categorias foram criadas
python manage.py shell -c "from atletas.models import Categoria; print(f'Total de categorias: {Categoria.objects.count()}')"
```

### Localmente:

```bash
python manage.py migrate
```

## ✅ Verificações

Após aplicar a correção, verifique:

1. **Migrations aplicadas**:
   ```bash
   python manage.py showmigrations atletas
   ```

2. **Categorias criadas**:
   ```bash
   python manage.py shell -c "from atletas.models import Categoria, Classe; print(f'Classes: {Classe.objects.count()}'); print(f'Categorias: {Categoria.objects.count()}')"
   ```

3. **Estrutura correta**:
   - Deve haver 9 classes (FESTIVAL, SUB 9, SUB 11, etc.)
   - Deve haver 9 categorias de peso × 2 sexos × 9 classes = 162 categorias

## 📝 Notas Técnicas

- O problema ocorria especificamente com ForeignKeys em migrations usando `apps.get_model()`
- A abordagem explícita (`get()` + `create()`) é mais robusta e previsível
- A migration também inclui verificação para garantir que existem classes antes de criar categorias

## 🔄 Próximos Passos

1. ✅ Commit da correção
2. ✅ Push para o repositório
3. ✅ Deploy no Render
4. ✅ Verificar se as categorias foram criadas corretamente

---

**Última atualização:** Dezembro 2024

