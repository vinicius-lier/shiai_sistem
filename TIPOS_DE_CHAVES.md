# DESCRIÇÃO DOS TIPOS DE CHAVES DO SISTEMA

## Resumo Executivo

O sistema **SHIAI SISTEM** gera automaticamente diferentes tipos de chaves de competição baseado no **número de atletas** inscritos em cada categoria. O tipo de chave é determinado automaticamente pelo sistema conforme as regras abaixo.

---

## TIPOS DE CHAVES DISPONÍVEIS

### 1. **CHAVE VAZIA** (0 atletas)
- **Quando ocorre**: Nenhum atleta inscrito na categoria
- **Estrutura**: Nenhuma luta criada
- **Resultado**: Nenhum campeão definido
- **Status**: Chave não pode ser competida

```json
{
  "tipo": "vazia",
  "atletas": 0
}
```

---

### 2. **CAMPEÃO AUTOMÁTICO** (1 atleta)
- **Quando ocorre**: Apenas 1 atleta inscrito na categoria
- **Estrutura**: Nenhuma luta criada
- **Resultado**: O atleta é automaticamente declarado campeão
- **Pontuação**: Academia do atleta recebe 1 ouro automaticamente

```json
{
  "tipo": "campeao_automatico",
  "atletas": 1,
  "vencedor": [id_do_atleta]
}
```

**Observação**: Em competições reais, isso pode ocorrer quando:
- Apenas uma academia tem atleta naquela categoria específica
- Outros atletas foram desclassificados na pesagem
- Categoria com pouca participação

---

### 3. **MELHOR DE 3** (2 atletas)
- **Quando ocorre**: Exatamente 2 atletas inscritos na categoria
- **Estrutura**: 3 lutas criadas (máximo necessário)
- **Regra**: O primeiro atleta a vencer 2 lutas é declarado campeão
- **Formato**: 
  - Luta 1: Atleta A vs Atleta B
  - Luta 2: Atleta A vs Atleta B
  - Luta 3: Atleta A vs Atleta B (se necessário)
- **Resultado**: 
  - Campeão: Atleta com 2 vitórias
  - Vice: Atleta derrotado

```json
{
  "tipo": "melhor_de_3",
  "atletas": 2,
  "lutas": [id_luta1, id_luta2, id_luta3]
}
```

**Exemplo Visual**:
```
┌─────────────┐
│ Atleta A    │──┐
│             │  │
└─────────────┘  │
                 ├─── Luta 1
┌─────────────┐  │
│ Atleta B    │──┘
│             │
└─────────────┘

[Repete para Luta 2 e Luta 3 se necessário]
```

---

### 4. **TRIANGULAR** (3 atletas)
- **Quando ocorre**: Exatamente 3 atletas inscritos na categoria
- **Estrutura**: 3 lutas (todos contra todos)
- **Regra**: Cada atleta luta contra os outros dois
- **Formato**:
  - Luta 1: Atleta A vs Atleta B
  - Luta 2: Atleta A vs Atleta C
  - Luta 3: Atleta B vs Atleta C
- **Critérios de Classificação**:
  1. Número de vitórias
  2. Em caso de empate: confronto direto
  3. Se necessário: diferença de pontos (Wazari = 1pt, Ippon = 10pts)
- **Resultado**: 
  - 1º lugar: Atleta com mais vitórias
  - 2º lugar: Segundo colocado
  - 3º lugar: Terceiro colocado

```json
{
  "tipo": "triangular",
  "atletas": 3,
  "lutas": [id_luta1, id_luta2, id_luta3]
}
```

**Exemplo Visual**:
```
┌─────────────┐
│ Atleta A    │──┐
└─────────────┘  │
                 ├─── Luta 1
┌─────────────┐  │
│ Atleta B    │──┘
└─────────────┘
       │
       │ Luta 3
       │
┌─────────────┐
│ Atleta C    │
└─────────────┘
       │
       │ Luta 2
       │
       ▼
┌─────────────┐
│ Atleta A    │ (já lutou contra C)
└─────────────┘
```

---

### 5. **CHAVE OLÍMPICA** (4 ou mais atletas)
- **Quando ocorre**: 4 ou mais atletas inscritos na categoria
- **Estrutura**: Chave eliminatória (mata-mata)
- **Tamanhos disponíveis**: 4, 8, 16 ou 32 posições
- **Regra**: Sistema eliminatório - perdeu, está fora
- **Disputa de 3º lugar**: Automática quando a chave tem 6+ atletas

#### 5.1. **Chave de 4 posições** (4 atletas)
```
Quartas de Final:
┌─────────┐
│ Atleta 1│──┐
└─────────┘  │
             ├─── Semifinal 1 ──┐
┌─────────┐  │                  │
│ Atleta 2│──┘                  │
└─────────┘                     │
                                ├─── FINAL
┌─────────┐                     │
│ Atleta 3│──┐                  │
└─────────┘  │                  │
             ├─── Semifinal 2 ──┘
┌─────────┐  │
│ Atleta 4│──┘
└─────────┘

Disputa 3º Lugar:
Perdedor SF1 vs Perdedor SF2
```

#### 5.2. **Chave de 8 posições** (5-8 atletas)
```
Oitavas de Final:
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Atleta 1│     │ Atleta 3│     │ Atleta 5│     │ Atleta 7│
└─────────┘     └─────────┘     └─────────┘     └─────────┘
     │               │               │               │
     ├─── OF1 ───────┤               ├─── OF3 ───────┤
     │               │               │               │
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Atleta 2│     │ Atleta 4│     │ Atleta 6│     │ Atleta 8│
└─────────┘     └─────────┘     └─────────┘     └─────────┘
     │               │               │               │
     └───────────────┴───────────────┴───────────────┘
                         │
                    Quartas de Final
                         │
         ┌───────────────┴───────────────┐
         │                               │
    Semifinal 1                      Semifinal 2
         │                               │
         └───────────────┬───────────────┘
                         │
                       FINAL

Disputa 3º Lugar (entre perdedores das semifinais):
Perdedor SF1 vs Perdedor SF2
```

#### 5.3. **Chave de 16 posições** (9-16 atletas)
- Estrutura similar à de 8, mas com uma rodada adicional (oitavas de final)

#### 5.4. **Chave de 32 posições** (17-32 atletas)
- Estrutura similar, com 5 rodadas (32 → 16 → 8 → 4 → 2 → 1)

#### **BYES (Descansos)**
- Se o número de atletas não preenche completamente a chave, o sistema preenche com BYEs
- Exemplo: 5 atletas em chave de 8 → 3 posições ficam como BYE
- Atletas com BYE passam automaticamente para a próxima rodada

**Estrutura JSON**:
```json
{
  "tipo": "chave_olimpica",
  "atletas": 6,
  "tamanho_chave": 8,
  "rounds": {
    "1": [id_luta1, id_luta2, id_luta3, id_luta4],
    "2": [id_luta5, id_luta6],
    "3": [id_luta7]  // Final
  }
}
```

---

## REGRAS DE DISPUTA DE 3º LUGAR

### Quando há disputa de 3º lugar:
- **Chave Olímpica com 6+ atletas**: Sempre há disputa
- **Chave Olímpica com 4-5 atletas**: Conforme regras oficiais
- **Triangular (3 atletas)**: Não há disputa (já tem 3º lugar)
- **Melhor de 3 (2 atletas)**: Não há disputa (apenas 2 colocados)

### Como funciona:
1. Os **perdedores das semifinais** disputam o 3º lugar
2. O vencedor fica em 3º lugar
3. O perdedor fica em 4º lugar
4. Ambos recebem pontos (3º = bronze, 4º = quarto)

---

## PONTUAÇÃO POR COLOCAÇÃO

| Colocação | Medalha | Pontos para Academia |
|-----------|---------|----------------------|
| 1º lugar  | 🥇 Ouro | +1 nouro |
| 2º lugar  | 🥈 Prata | +1 prata |
| 3º lugar  | 🥉 Bronze | +1 bronze |
| 4º lugar  | -       | +1 quarto |
| 5º lugar  | -       | +1 quinto |

---

## FLUXO DE GERAÇÃO DE CHAVES

### 1. **Critérios para Inclusão**
- Atleta deve ter `status = 'OK'` (aprovado na pesagem)
- Atleta não pode ser da classe 'Festival'
- Atleta deve estar na categoria correta (`categoria_nome` ou `categoria_ajustada`)

### 2. **Processo Automático**
```
┌─────────────────────┐
│  Contar Atletas     │
│  na Categoria       │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │ Quantos?     │
    └──┬───┬───┬───┘
       │   │   │
    ┌──┘   │   └──┐
    │      │      │
    ▼      ▼      ▼
   0     1-3   4+
    │      │      │
    │      │      └──► Chave Olímpica
    │      │           (4, 8, 16, 32)
    │      │
    │      └──────────► Triangular (3)
    │                   Melhor de 3 (2)
    │                   Campeão Auto (1)
    │
    └──────────────────► Vazia (0)
```

### 3. **Atualização Automática**
- Quando uma luta é finalizada, o sistema automaticamente:
  1. Identifica a próxima luta na sequência
  2. Coloca o vencedor na posição correta
  3. Quando todas as lutas de um round terminam, o próximo round é habilitado

---

## EXEMPLOS PRÁTICOS

### Exemplo 1: Categoria com 5 atletas
- **Tipo**: Chave Olímpica de 8 posições
- **Rounds**: 
  - Round 1: 3 lutas (1 BYE automático)
  - Round 2: Semifinais (2 lutas)
  - Round 3: Final (1 luta)
  - Disputa 3º lugar: 1 luta

### Exemplo 2: Categoria com 2 atletas
- **Tipo**: Melhor de 3
- **Lutas**: 3 lutas (máximo)
- **Vencedor**: Primeiro a vencer 2 lutas

### Exemplo 3: Categoria com 12 atletas
- **Tipo**: Chave Olímpica de 16 posições
- **Rounds**:
  - Round 1: Oitavas (6 lutas + 4 BYEs)
  - Round 2: Quartas (4 lutas)
  - Round 3: Semifinais (2 lutas)
  - Round 4: Final (1 luta)
  - Disputa 3º lugar: 1 luta

---

## OBSERVAÇÕES IMPORTANTES

1. **Festival não gera chaves**: Atletas da classe Festival não competem em chaves
2. **Reclassificação**: Se um atleta for reclassificado de categoria após a pesagem, a chave pode ser regerada
3. **Chaves com resultados**: Chaves que já têm resultados registrados não são automaticamente regeradas
4. **WO (Walkover)**: Se um atleta não comparecer, o oponente vence automaticamente
5. **BYEs**: São atribuídos automaticamente pelo sistema nas posições necessárias

---

## COMANDO DE GERAÇÃO EM MASSA

O sistema possui um comando para gerar todas as chaves automaticamente:

```bash
python manage.py gerar_todas_chaves
```

Este comando:
- Cria chaves para todas as combinações de classe/sexo/categoria
- Não refaz chaves que já têm resultados
- Refaz apenas chaves sem resultados registrados

---

## CONCLUSÃO

O sistema oferece **5 tipos principais de chaves**, cobrindo todos os cenários possíveis de competição de Judô:

1. ✅ Vazia (0 atletas)
2. ✅ Campeão Automático (1 atleta)
3. ✅ Melhor de 3 (2 atletas)
4. ✅ Triangular (3 atletas)
5. ✅ Chave Olímpica (4+ atletas: 4, 8, 16, 32 posições)

Todos os tipos são gerados **automaticamente** pelo sistema, sem necessidade de intervenção manual, seguindo as regras oficiais de competição de Judô.

