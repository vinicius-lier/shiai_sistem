# 📋 DIAGNÓSTICO COMPLETO DOS MODELS

## Models Existentes Relacionados a Competição

### 1. **Atleta** (`atletas/models.py`)
- **Campos de competição (ANTIGOS - serão migrados):**
  - `classe` - Classe do atleta (SUB 9, SUB 11, etc.)
  - `categoria_nome` - Categoria original
  - `categoria_ajustada` - Categoria após remanejamento
  - `peso_previsto` - Peso informado na inscrição
  - `peso_oficial` - Peso registrado na pesagem
  - `status` - OK, Eliminado Peso, Eliminado Indisciplina
  - `remanejado` - Boolean
  - `motivo_ajuste` - Texto

**⚠️ IMPORTANTE:** Este modelo é PERMANENTE. Não deve ser usado para lógica de competição após migração.

---

### 2. **Evento** (`eventos/models.py`) ✅ EXISTE
- **Campos atuais:**
  - `nome` - CharField(200)
  - `descricao` - TextField
  - `local` - CharField(200)
  - `cidade` - CharField(120)
  - `data_evento` - DateField
  - `data_limite_inscricao` - DateField
  - `status` - CharField com choices: ABERTO, INSCRICOES_ABERTAS, PESAGEM, CHAVES, EM_ANDAMENTO, ENCERRADO
  - `ativo` - BooleanField
  - `pesagem_encerrada` - BooleanField
  - `valor_federado`, `valor_nao_federado` - DecimalField

**🔧 AJUSTE NECESSÁRIO:** 
- Status choices devem ser: RASCUNHO, INSCRICOES, PESAGEM, ANDAMENTO, ENCERRADO
- `data_evento` deve permitir null/blank
- `prazo_inscricao` deve ser `data_limite_inscricao` (já existe)

---

### 3. **EventoAtleta** (`eventos/models.py`) ✅ EXISTE
- **Campos atuais:**
  - `evento` - ForeignKey(Evento)
  - `atleta` - ForeignKey(Atleta)
  - `academia` - ForeignKey(Academia)
  - `peso_oficial` - DecimalField
  - `categoria` - ForeignKey(Categoria) - categoria no evento
  - `categoria_ajustada` - CharField - nome da categoria ajustada
  - `categoria_final` - ForeignKey(Categoria) - categoria final
  - `status` - CharField: OK, REMANEJADO, DESCLASSIFICADO, PENDENTE
  - `status_pesagem` - CharField: PENDENTE, OK, REMANEJADO, DESC
  - `remanejado` - BooleanField
  - `desclassificado` - BooleanField
  - `motivo` - TextField
  - `pontos_evento` - IntegerField
  - `valor_inscricao` - DecimalField

**🔧 AJUSTES NECESSÁRIOS:**
- Adicionar `classe` - CharField (congelada para o evento)
- Adicionar `categoria_inicial` - ForeignKey(Categoria) - categoria original da inscrição
- Adicionar `peso_previsto` - DecimalField
- Renomear `pontos_evento` para `pontos` OU manter e adicionar `pontos`
- Status choices devem ser: OK, ELIMINADO_PESO, ELIMINADO_IND
- Remover `status_pesagem` (redundante com status)

---

### 4. **Chave** (`atletas/models.py`) ✅ EXISTE
- **Campos:**
  - `classe`, `sexo`, `categoria` - CharField
  - `atletas` - ManyToManyField(Atleta)
  - `estrutura` - JSONField
  - `evento` - ForeignKey(Evento) ✅ JÁ TEM

**✅ OK:** Já vinculado a Evento

---

### 5. **Luta** (`atletas/models.py`) ✅ EXISTE
- **Campos:**
  - `chave` - ForeignKey(Chave)
  - `atleta_a`, `atleta_b`, `vencedor` - ForeignKey(Atleta)
  - `round`, `concluida`, `tipo_vitoria`, etc.

**✅ OK:** Vinculada via Chave → Evento

---

### 6. **Campeonato** (`atletas/models.py`) ⚠️ ANTIGO
- **Status:** Modelo antigo, deve ser IGNORADO
- **Uso:** Não deve ser usado para nova lógica
- **Migração:** Dados devem ir para Evento

---

### 7. **AcademiaPontuacao** (`atletas/models.py`) ⚠️ ANTIGO
- **Status:** Modelo antigo, deve ser IGNORADO
- **Uso:** Não deve ser usado para nova lógica
- **Migração:** Pontos devem ir para EventoAtleta.pontos

---

## Resumo

✅ **Models que DEVEM ser usados:**
- `Evento` - precisa ajustes nos campos
- `EventoAtleta` - precisa ajustes nos campos
- `Chave` - OK
- `Luta` - OK
- `Atleta` - apenas como referência permanente
- `Academia` - OK
- `Categoria` - OK

❌ **Models que NÃO devem ser usados:**
- `Campeonato` - antigo
- `AcademiaPontuacao` - antigo

---

## Próximos Passos

1. Ajustar campos de Evento e EventoAtleta
2. Criar comando de migração completo
3. Criar evento histórico automaticamente
4. Corrigir pesagem para usar EventoAtleta
5. Corrigir input de peso
6. Remover rotas antigas


