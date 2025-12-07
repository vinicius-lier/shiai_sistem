# Auditoria Técnica – Módulo de Chaveamento (Shiai System)

## Escopo e fontes analisadas
- `atletas/utils.py`: `gerar_chave`, `gerar_chave_automatica`, `gerar_chave_escolhida`, `gerar_chave_olimpica_manual`, auxiliares de agrupamento.
- `atletas/views.py`: `gerar_chave_view`, `gerar_todas_chaves`, `gerar_chave_manual`, `lista_chaves`, `detalhe_chave`.
- `atletas/models.py`: `Chave`, `Luta`, `Inscricao` (campos de status, peso, `bloqueado_chave`).
- `atletas/urls_org.py`: rotas de chaveamento.
- Templates: `atletas/gerar_chave.html`, `atletas/lista_chaves.html`, `atletas/detalhe_chave.html`, `atletas/chave_mobile.html` (e equivalentes se existirem).
- JS: não há arquivo dedicado a chave; comportamento de geração é server-side.

## Fluxo REAL (atual)
1) **Entrada de dados**:  
   - `gerar_chave_view` (GET) lista classes com peso confirmado (`Inscricao.status in ['ok','remanejado','aprovado']` e `peso` não nulo).  
   - `gerar_chave_view` (POST) chama `utils.gerar_chave(classe, sexo, categoria, modelo, campeonato)` sem filtrar `bloqueado_chave` na fase de oferta de categorias/classes.
2) **Geração central** (`utils.gerar_chave`):  
   - Filtra inscrições: `status in ['ok','remanejado']`, `bloqueado_chave=False`, `peso` não nulo, `classe_escolhida` = classe, `sexo` = atleta.sexo, `categoria_escolhida/ajustada` compatível (padrões montados).  
   - Exclui `Festival`, `peso=0`.  
   - Cria/atualiza `Chave`; limpa lutas/atletas antigos; define estrutura automática ou manual; salva.  
3) **Gerar todas** (`gerar_todas_chaves`):  
   - Busca combinações com `status in ['ok','remanejado','aprovado']`, `peso` não nulo, sem `bloqueado_chave` e sem filtrar `desclassificado`. Usa `categoria_ajustada or categoria_escolhida`. Para cada combinação chama `utils.gerar_chave` (aí sim aplica filtros corretos).
4) **Chave manual / luta casada** (`gerar_chave_manual`):  
   - Cria chave tipo “manual”, recebe lista arbitrária de atletas (sem validações de faixa/categoria/peso) e cria lutas pareadas sequenciais.
5) **Listagem** (`lista_chaves`):  
   - Lista `Chave` por campeonato ativo; filtros simples por classe/sexo/categoria; não refaz validações.

## Fluxo ESPERADO (pedido)
- Só entram na chave atletas com `status` **OK** ou **Remanejado**, `bloqueado_chave=False`, peso registrado dentro da categoria final; nunca `pendente`, `desclassificado`, `bloqueado_chave=True`.
- Respeitar: classe (idade), sexo, faixa/grupo de faixas, categoria (peso), e evento (campeonato).
- Desclassificar/remanejar deve remover/ajustar atleta nas chaves existentes automaticamente.
- Luta casada apenas se não houver chave automática, mantendo integridade de categoria/faixa/sexo/idade.

## Pontos corretos (atual)
- `utils.gerar_chave` já filtra `status in ['ok','remanejado']`, `bloqueado_chave=False`, `peso` não nulo, exclui `peso=0` e `Festival`.
- `confirmar_remanejamento` (pesagem) remove atleta das chaves ao remanejar/desclassificar.
- Atualização de chave reaproveita `Chave` existente e limpa lutas/atletas antes de regravar.

## Problemas detectados
1) **Filtros inconsistentes antes de gerar**:  
   - `gerar_chave_view` e `gerar_todas_chaves` usam `status in ['ok','remanejado','aprovado']` e não filtram `bloqueado_chave`, permitindo oferecer combinações com atletas bloqueados/desclassificados na seleção inicial.
2) **Faixa/grupo de faixas não considerados**: nenhum filtro por graduação ou agrupamento de faixas; risco de misturar faixas proibidas.
3) **Validação de categoria/peso final**: o filtro usa apenas categoria texto; não verifica se peso está dentro do limite da categoria final (assume peso registrado).
4) **Classe/idade**: usa `classe_escolhida` da inscrição; não recalcula classe por idade no momento do chaveamento (se idade mudou, pode haver inconsistência).
5) **Chaves manuais (lutas casadas)**: não validam sexo, faixa, classe, categoria ou peso; podem juntar atletas incompatíveis.
6) **Categoria inexistente/sem atletas**: tratamento é apenas log/print; não há fallback de “luta casada” automática quando zero atletas; gera chave “vazia” silenciosa.
7) **Desclassificação pós-chave**: depende apenas da remoção feita na pesagem. Se um atleta for marcado `bloqueado_chave=True` fora da pesagem, não há rotina automática para reprocessar chaves existentes.
8) **Duplicação de lógica de filtro**: views (`gerar_chave_view`, `gerar_todas_chaves`) e utils aplicam filtros diferentes, aumentando risco de divergência.
9) **Ausência de tratamento explícito para “categoria inexistente”**: gera chave mesmo que categoria não exista como objeto, pois trabalha com string; não há validação.
10) **Integração com faixa e grupos especiais (Masculino/Feminino, agrupamentos)**: não implementado.
11) **Lógica de “luta casada”**: não verifica peso/categoria/faixa; é apenas pareamento sequencial.

## Mapa de filtros por status (atual)
- **utils.gerar_chave**: `status in ['ok','remanejado']`, `bloqueado_chave=False`, `peso is not null`, `peso != 0`, exclui `Festival`. (Correto)
- **views.gerar_chave_view (GET/POST)**: `status in ['ok','remanejado','aprovado']`, não filtra `bloqueado_chave`, não exclui `desclassificado` explicitamente. (Inconsistente)
- **views.gerar_todas_chaves**: `status in ['ok','remanejado','aprovado']`, sem `bloqueado_chave`. (Inconsistente na seleção inicial; ao chamar `utils.gerar_chave`, o filtro final corrige, mas a combinação pode ser gerada de entradas indevidas ou com contagens incorretas.)
- **Geração manual**: sem filtros de status/peso/categoria.

## Cobertura das regras maiores (classe/sexo/faixa/grupo/peso/categoria)
- Classe/sexo: filtrados (classe_escolhida, atleta.sexo) em `utils.gerar_chave`. Faixa/grupo: **não implementado**. Peso/categoria: usa categoria texto; não revalida peso no momento do chaveamento.
- Não há grouping por faixas (masculino branca–verde, roxa–preta, etc.; feminino branca–laranja, verde–preta; Sub18/Sub21/Sênior/Veteranos).

## Exceções e casos limite
- Categoria inexistente/sem atletas: gera chave vazia; não oferece luta casada automaticamente; apenas prints.
- Atleta desclassificado após chave: apenas se `remover_de_chaves` for chamado; não há rotina de revalidação periódica.
- Mudança de categoria/remanejamento: handled via `remover_de_chaves` no serviço de pesagem.
- Luta casada: sem validação; pode misturar categorias/faixas/sexo/idade.

## Impacto da pesagem sobre chave
- `confirmar_remanejamento` (pesagem) chama `remover_de_chaves` ao remanejar ou desclassificar.
- `bloqueado_chave=True` em desclassificação impede nova inclusão via `utils.gerar_chave`, mas views de seleção inicial ainda podem listar esses atletas.

## Lógicas duplicadas / código morto
- Filtro de inscrições aptas duplicado em `gerar_chave_view` e `gerar_todas_chaves` com regras divergentes de `utils.gerar_chave`.
- Chave manual repete montagem básica de lutas (round=1) sem reutilizar helper; não integra validações.

## Proposta de arquitetura correta
1) **Fonte única de dados aptos**: função de serviço `listar_inscricoes_apta_chave(campeonato)` aplicada em todas as entradas (views + gerar_todas + gerar_chave_manual), reutilizando filtros:
   - `status in ['ok','remanejado']`
   - `bloqueado_chave=False`
   - `peso` não nulo e > 0
   - categoria final = `categoria_ajustada or categoria_escolhida`
   - classe/sexo coerentes
2) **Validação de faixa/grupo**: inserir checagem de graduação/grupo configurado (masc/fem; sub18/sub21/sênior/veteranos).
3) **Validação de peso/categoria**: opcionalmente recalcular categoria pelo peso registrado e garantir match antes de incluir.
4) **Reprocessamento pós-desclassificação/remanejamento**: agendar/acionar regeneração ou remoção automática (já remove lutas; pode também marcar chave para rebuild).
5) **Chave manual (luta casada) segura**: impor mesmo filtro apto e mesma categoria/sexo/classe/faixa; se não houver grupo compatível, bloquear criação.
6) **Tratamento de exceções**: se zero atletas ou categoria inexistente → oferecer luta casada apenas dentro da mesma faixa/sexo/classe; caso contrário, abortar com mensagem clara.
7) **Unificação de prints/logs**: substituir prints por logger; registrar erros.

## Exemplo de correção (trechos sugeridos)
- **View gerar_chave_view / gerar_todas_chaves**: usar helper central
```python
from .services.chaves import listar_inscricoes_apta_chave
inscricoes_aptas = listar_inscricoes_apta_chave(campeonato_ativo)
```
- **Helper de aptidão** (novo):
```python
def listar_inscricoes_apta_chave(qs):
    return qs.filter(
        status_inscricao__in=['ok','remanejado'],
        bloqueado_chave=False,
        peso__isnull=False
    ).exclude(peso=0).exclude(classe_escolhida='Festival')
```
- **Chave manual**: antes de criar lutas, filtrar atletas aptos e validar categoria/sexo/classe/faixa; abortar se misto.

## Passos e ordem recomendada de refatoração
1) Criar serviço único de seleção de inscrições aptas (status/bloqueio/peso/faixa/categoria).
2) Aplicar serviço em `gerar_chave_view`, `gerar_todas_chaves`, `gerar_chave_manual`.
3) Incluir validação de faixa/grupo (masc/fem) e classe/idade no helper.
4) Adicionar checagem de peso dentro da categoria final (revalidação opcional).
5) Ajustar chave manual para usar mesmas validações e impedir mix inválido.
6) Logar exceções com mensagens claras e fallback de luta casada apenas com atletas compatíveis.
7) Tests automatizados:  
   - incluir: ok/remanejado entram; pendente/desclassificado/bloqueado não entram.  
   - remanejamento → remove chaves e reprocessa.  
   - desclassificação → bloqueia e remove.  
   - luta casada rejeita misturas de sexo/faixa/classe.

## Arquivos a corrigir
- `atletas/views.py`: filtros em `gerar_chave_view`, `gerar_todas_chaves`, `gerar_chave_manual`; reuso de helper central.
- `atletas/utils.py`: opcional – validar faixa/idade/peso final; logger.
- `atletas/services/` (novo `chaves.py` sugerido): helper de aptidão + orquestração de geração.
- Templates de geração/lista: mensagens de erro mais claras quando não houver aptos.

## Dependências (quem chama o quê)
- `views.gerar_chave_view` → `utils.gerar_chave`.
- `views.gerar_todas_chaves` → `utils.gerar_chave` (loop combinações).
- `views.gerar_chave_manual` → cria `Chave`/`Luta` direto (não usa utils).
- `services.pesagem.confirmar_remanejamento` → `services.pesagem.remover_de_chaves` (impacta chave).
- `utils.gerar_chave` → `Chave`, `Luta`, `Inscricao`.

## Resumo de correções essenciais
- Alinhar filtros de aptidão em todas as entradas (status ok/remanejado, `bloqueado_chave=False`, peso registrado > 0).
- Implementar validação de faixa/grupo e bloquear misturas inválidas (inclusive em luta casada).
- Garantir remoção/rebuild de chaves após desclassificação/bloqueio fora da pesagem.
- Validar categoria/peso antes de incluir na chave; tratar categoria inexistente/sem atletas com mensagens e opções controladas.

## Comandos recomendados (após ajustes)
- `python3 manage.py makemigrations` (se criar helper/flags novos)  
- `python3 manage.py migrate`  
- `python3 manage.py test` (adicionar suíte para chaveamento)


