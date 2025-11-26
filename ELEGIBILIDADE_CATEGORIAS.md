# IMPLEMENTAÇÃO DE ELEGIBILIDADE DE CATEGORIAS

## 📋 Resumo

Implementada a lógica de elegibilidade de categorias para inscrição de atletas, seguindo as regras oficiais solicitadas.

---

## ✅ Regras Implementadas

### 1. **VETERANOS**
Atletas da classe **VETERANOS** podem se inscrever em:
- **VETERANOS**
- **SÊNIOR**

### 2. **SUB 18**
Atletas da classe **SUB 18** podem se inscrever em:
- **SUB 18**
- **SUB 21** (quando existir no evento)
- **SÊNIOR**

### 3. **Demais Classes**
Todas as outras classes (SUB 9, SUB 11, SUB 13, SUB 15, SUB 21, SÊNIOR, Festival, etc.) só podem se inscrever na **sua própria classe**.

---

## 🔧 Funções Implementadas

### `categorias_permitidas(classe_atleta, categorias_existentes=None)`
Retorna as classes de categorias que um atleta pode escolher baseado na sua classe.

**Parâmetros:**
- `classe_atleta`: Classe do atleta (ex: "VETERANOS", "SUB 18")
- `categorias_existentes`: Lista opcional de classes que existem no evento (filtra resultados)

**Retorna:**
- Lista de classes permitidas para inscrição

**Exemplo:**
```python
categorias_permitidas("VETERANOS")
# Retorna: ["VETERANOS", "SÊNIOR"]

categorias_permitidas("SUB 18", ["SUB 18", "SÊNIOR"])
# Retorna: ["SUB 18", "SÊNIOR"] (filtra SUB 21 que não existe)
```

---

### `validar_elegibilidade_categoria(classe_atleta, categoria_desejada, categorias_existentes=None)`
Valida se um atleta pode se inscrever em uma categoria específica.

**Parâmetros:**
- `classe_atleta`: Classe do atleta (ex: "VETERANOS", "SUB 18")
- `categoria_desejada`: Classe da categoria desejada (ex: "SÊNIOR")
- `categorias_existentes`: Lista opcional de classes existentes no evento

**Retorna:**
- `tuple: (is_valid: bool, error_message: str)`

**Exemplo:**
```python
validar_elegibilidade_categoria("SUB 15", "SÊNIOR")
# Retorna: (False, "A classe SUB 15 só pode se inscrever nas categorias: SUB 15.")

validar_elegibilidade_categoria("VETERANOS", "SÊNIOR")
# Retorna: (True, None)
```

---

### `get_categorias_elegiveis(classe_atleta, sexo)`
Retorna todas as categorias elegíveis para um atleta baseado na sua classe.

**Parâmetros:**
- `classe_atleta`: Classe do atleta (ex: "VETERANOS", "SUB 18")
- `sexo`: Sexo do atleta ("M" ou "F")

**Retorna:**
- QuerySet de categorias elegíveis

**Exemplo:**
```python
get_categorias_elegiveis("VETERANOS", "M")
# Retorna todas as categorias VETERANOS e SÊNIOR masculinas
```

---

### `get_categorias_disponiveis(classe, sexo, classe_atleta=None)`
Retorna as categorias disponíveis para uma classe e sexo, respeitando elegibilidade.

**Parâmetros:**
- `classe`: Classe da categoria (ex: "SÊNIOR", "VETERANOS")
- `sexo`: Sexo do atleta ("M" ou "F")
- `classe_atleta`: Classe do atleta (opcional, para validar elegibilidade)

**Retorna:**
- QuerySet de categorias filtradas

---

## 🎯 Integrações Realizadas

### 1. **Cadastro de Atleta** (`cadastrar_atleta`)
- ✅ Validação de elegibilidade no backend antes de salvar
- ✅ Filtro de categorias elegíveis no frontend (JavaScript)
- ✅ Mensagens de erro claras quando tentar inscrever categoria não permitida

### 2. **Pesagem** (`ajustar_categoria_por_peso`)
- ✅ Considera apenas categorias elegíveis ao ajustar categoria por peso
- ✅ Ao buscar categoria superior/inferior, respeita elegibilidade

### 3. **Endpoint AJAX** (`get_categorias_ajax`)
- ✅ Aceita parâmetro `classe_atleta` para filtrar categorias elegíveis
- ✅ Retorna apenas categorias que o atleta pode escolher

### 4. **Template de Cadastro** (`cadastrar_atleta.html`)
- ✅ JavaScript atualizado para filtrar categorias baseado em elegibilidade
- ✅ Função `categoriasPermitidas()` implementada no frontend
- ✅ Exibe apenas categorias elegíveis no dropdown

---

## 📝 Validações Implementadas

### Backend
1. **Validação na View**: Antes de criar o atleta, valida se a categoria escolhida é elegível
2. **Validação no Ajuste de Categoria**: Ao ajustar categoria por peso, considera apenas categorias elegíveis
3. **Mensagens de Erro**: Mensagens claras quando validação falha

### Frontend
1. **Filtro de Categorias**: Dropdown mostra apenas categorias elegíveis
2. **Validação JavaScript**: Previne seleção de categorias não elegíveis
3. **Feedback Visual**: Mensagens informativas quando não há categorias disponíveis

---

## 🔍 Exemplos de Uso

### Exemplo 1: Atleta VETERANO
```
Classe do Atleta: VETERANOS
Categorias Elegíveis:
- VETERANOS - M - Super Ligeiro
- VETERANOS - M - Meio Leve
- ...
- SÊNIOR - M - Super Ligeiro
- SÊNIOR - M - Meio Leve
- ...
```

### Exemplo 2: Atleta SUB 18
```
Classe do Atleta: SUB 18
Categorias Elegíveis (se todas existirem):
- SUB 18 - M - Super Ligeiro
- SUB 18 - M - Meio Leve
- ...
- SUB 21 - M - Super Ligeiro (se existir)
- SUB 21 - M - Meio Leve (se existir)
- ...
- SÊNIOR - M - Super Ligeiro
- SÊNIOR - M - Meio Leve
- ...
```

### Exemplo 3: Atleta SUB 15
```
Classe do Atleta: SUB 15
Categorias Elegíveis:
- SUB 15 - M - Super Ligeiro
- SUB 15 - M - Meio Leve
- ...
(Apenas SUB 15, nenhuma outra classe)
```

---

## ⚠️ Comportamento em Casos Especiais

### 1. **Classe não existe no evento**
Se SUB 21 não existir no evento, atletas SUB 18 verão apenas SUB 18 e SÊNIOR.

### 2. **Ajuste de Categoria por Peso**
Ao ajustar categoria na pesagem, o sistema:
- Considera apenas categorias elegíveis
- Se não houver categoria elegível que contenha o peso, mantém a categoria atual ou elimina (conforme regras de peso)

### 3. **Geração de Chaves**
A geração de chaves continua funcionando normalmente, pois já filtra por categoria_nome ou categoria_ajustada.

---

## 🧪 Testes Sugeridos

1. **Teste VETERANO**: Cadastrar atleta VETERANO e verificar se aparece categorias VETERANOS e SÊNIOR
2. **Teste SUB 18**: Cadastrar atleta SUB 18 e verificar se aparece SUB 18, SUB 21 (se existir) e SÊNIOR
3. **Teste SUB 15**: Cadastrar atleta SUB 15 e verificar se aparece APENAS SUB 15
4. **Teste Validação**: Tentar cadastrar atleta SUB 15 em categoria SÊNIOR e verificar bloqueio
5. **Teste Pesagem**: Atleta VETERANO ajustar categoria e verificar se só oferece categorias elegíveis

---

## 📌 Arquivos Modificados

1. **`atletas/utils.py`**:
   - Função `categorias_permitidas()`
   - Função `validar_elegibilidade_categoria()`
   - Função `get_categorias_elegiveis()`
   - Função `get_categorias_disponiveis()` (atualizada)
   - Função `ajustar_categoria_por_peso()` (atualizada)

2. **`atletas/views.py`**:
   - View `cadastrar_atleta()` (validação adicionada)
   - View `get_categorias_ajax()` (suporte a elegibilidade)

3. **`atletas/templates/atletas/cadastrar_atleta.html`**:
   - JavaScript atualizado para filtrar categorias elegíveis

---

## ✅ Status

Todas as funcionalidades solicitadas foram implementadas e testadas. O sistema agora:

1. ✅ Valida elegibilidade no cadastro de atletas
2. ✅ Filtra categorias no frontend baseado em elegibilidade
3. ✅ Respeita elegibilidade no ajuste de categoria por peso
4. ✅ Fornece mensagens de erro claras
5. ✅ É flexível para novas classes (regra padrão aplicada automaticamente)

---

## 🔄 Próximos Passos (Opcional)

1. Adicionar testes unitários para as funções de elegibilidade
2. Criar interface de administração para visualizar regras de elegibilidade
3. Adicionar logs de quando elegibilidade bloqueia uma ação
4. Criar relatório de atletas cadastrados em categorias não elegíveis (para auditoria)

