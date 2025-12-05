# 📋 Instruções: Popular Categorias no Render

## 🎯 Objetivo

Popular o banco de dados com as categorias de peso conforme regulamento específico.

## 🚀 Como Executar no Render

### Opção 1: Via Shell do Render (Recomendado)

1. Acesse o painel do Render: https://dashboard.render.com
2. Selecione seu serviço: **shiai-sistem**
3. Clique em **Shell** (ou **SSH**)
4. Execute o comando:

```bash
python manage.py popular_categorias_regulamento
```

### Opção 2: Via Terminal Local (se tiver acesso SSH)

```bash
python manage.py popular_categorias_regulamento
```

## 📊 O que o Comando Faz

1. **Parseia strings de peso:**
   - `"Até 23 kg"` → limite_min=0, limite_max=23
   - `"+23 a 26 kg"` → limite_min=23, limite_max=26
   - `"+50 kg"` → limite_min=50, limite_max=None

2. **Mapeia classes:**
   - `SUB-9` → busca por "SUB 9", "SUB-9", "SUB9"
   - `SUB-11` → busca por "SUB 11", "SUB-11", "SUB11"
   - `SÊNIOR/VET` → busca por "SÊNIOR", "SENIOR", "VETERANOS"

3. **Cria/Atualiza categorias:**
   - Se a categoria não existe, cria
   - Se já existe, atualiza os limites

## ✅ Categorias Criadas

O comando cria **142 categorias** no total:

- **Masculino:**
  - SUB-9: 9 categorias
  - SUB-11: 9 categorias
  - SUB-13: 9 categorias
  - SUB-15: 9 categorias
  - SUB-18: 9 categorias
  - SÊNIOR/VET: 7 categorias

- **Feminino:**
  - SUB-9: 9 categorias
  - SUB-11: 9 categorias
  - SUB-13: 9 categorias
  - SUB-15: 9 categorias
  - SUB-18: 8 categorias
  - SÊNIOR/VET: 7 categorias

## 🔍 Verificação

Após executar, verifique:

```bash
# Contar total de categorias
python manage.py shell -c "from atletas.models import Categoria; print(f'Total: {Categoria.objects.count()}')"

# Ver algumas categorias
python manage.py shell -c "from atletas.models import Categoria; [print(c) for c in Categoria.objects.all()[:10]]"
```

## ⚠️ Requisitos

- As classes devem existir no banco de dados
- Execute `python manage.py migrate` antes se necessário
- O comando é idempotente (pode executar múltiplas vezes sem problemas)

## 🐛 Troubleshooting

### Erro: "Classe 'SUB-9' não encontrada"

**Solução:** Verifique se as classes foram criadas:
```bash
python manage.py shell -c "from atletas.models import Classe; [print(c) for c in Classe.objects.all()]"
```

Se não existirem, execute:
```bash
python manage.py migrate
```

### Erro: "Formato de peso não reconhecido"

**Solução:** Verifique se o formato está correto. O comando aceita:
- `"Até X kg"`
- `"+X a Y kg"`
- `"+X kg"`

## 📝 Notas

- O comando usa `update_or_create`, então é seguro executar múltiplas vezes
- Categorias existentes serão atualizadas se os limites mudarem
- O comando mostra progresso em tempo real

---

**Comando criado:** `atletas/management/commands/popular_categorias_regulamento.py`

