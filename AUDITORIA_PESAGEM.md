# Auditoria do Módulo de Pesagem (Shiai System)

## Arquivos analisados
- `atletas/views.py`: `_montar_contexto_pesagem`, `pesagem`, `pesagem_mobile_view`, `registrar_peso`, `confirmar_remanejamento`, geração de chaves; helper `_calcular_categoria_por_peso`.
- `atletas/models.py`: `Inscricao`, `PesagemHistorico`, `OcorrenciaAtleta` (novo), `AcademiaPontuacao`.
- Templates:
  - `atletas/templates/atletas/pesagem.html` (desktop, modal remanejamento + JS completo)
  - `atletas/templates/atletas/pesagem_mobile.html` (versão mobile, modal duplicado)
  - `atletas/templates/atletas/inscrever_atletas.html` (inscrição captura peso? não)
- URLs: `atletas/urls_org.py` expõe `pesagem`, `pesagem_mobile`, `registrar_peso`, `confirmar_remanejamento`.

## Fluxo REAL (implementado)
- Inscrição operacional (`inscrever_atletas`): agora calcula categoria automaticamente em Python usando `_calcular_categoria_por_peso`, grava `categoria_calculada/escolhida`, `peso_informado`, status inicial `pendente_pesagem`. **Template ainda pede categoria manual (inconsistência).**
- Pesagem:
  - `_montar_contexto_pesagem` carrega inscrições com status `pendente_pesagem|ok|remanejado|aprovado`.
  - Tela desktop/mobile lista atletas com limites min/max e permite input de peso.
  - `registrar_peso` sempre grava peso e histórico; se dentro da categoria: status `ok`; se fora: status `pendente_pesagem`, resposta JSON com `precisa_confirmacao` e sugestões. **Não bloqueia salvamento ao estar fora; modal abre mas peso já persistiu.**
  - Modal (JS) só abre no front quando `status_pesagem == PESO_FORA`; botões “Remanejar” (submit) e “Desclassificar” (fetch).
  - `confirmar_remanejamento`: remaneja (status `remanejado`, ocorrência, -1 ponto em `AcademiaPontuacao`) ou desclassifica (status `desclassificado`, ocorrência). Não remove chaves existentes nem exige nova inscrição em código.
- Chaves: geração usa inscrições status `ok|remanejado|aprovado`; desclassificados/pendentes ficam fora. Não há remoção automática de chaves existentes ao desclassificar.

## Fluxo ESPERADO (do enunciado)
- Inscrição: técnico informa peso obrigatório; sistema define categoria inicial automaticamente; técnico não escolhe categoria.
- Pesagem: ao registrar peso oficial fora do limite, **modal obrigatório antes de salvar**; escolha explícita entre Remanejar ou Desclassificar.
- Remanejar: recalcula categoria pelo peso, grava ocorrência, desconta 1 ponto da academia, permite chaveamento.
- Desclassificar: grava ocorrência, bloqueia chaveamento, remove de chaves, exige nova inscrição para retornar.
- Integração com ranking e chaves consistente; status e histórico alinhados.

## Principais diferenças / problemas
- **Inscrição UI vs lógica**: template ainda exige seleção de categoria; não coleta `peso_atual`, logo fluxo novo não roda; risco de 500 ao não enviar peso.
- **Persistência antes da escolha**: `registrar_peso` já salva peso e histórico mesmo fora dos limites; modal vem depois. Regra pede “nenhum peso fora do limite pode ser salvo sem escolha explícita”.
- **Resposta JSON incompleta**: não envia `atleta_nome`, `inscricao_id` etc. de forma garantida; modal depende do front preencher.
- **Remoção de chaves/chaveamento**: não há remoção de chaves existentes ao desclassificar; não há bloqueio explícito de chaveamento além do filtro de status no gerar chave.
- **Pontuação**: remanejamento debita 1 ponto, ok; desclassificação não mexe em pontos (conforme regra), mas não garante ajuste se já havia pontos.
- **Ocorrências**: modelo criado, mas ficha de atleta não exibe; ocorrência de desclassificação/remanejamento só em `confirmar_remanejamento`; registrar_peso não cria ocorrência de “peso fora” se o operador abandonar.
- **Status legado no front**: templates exibem “OK”, “Fora do limite”, “Eliminado Peso” etc.; não refletem novos status (`ok`, `remanejado`, `desclassificado`, `pendente_pesagem`).
- **Duplica layouts/JS**: `pesagem.html` e `pesagem_mobile.html` têm JS e modais duplicados, facilitando divergência.
- **Categoria sugerida**: se não existir categoria compatível, backend apenas retorna `categoria_nova=None`; não força desclassificação automática como pedido.
- **Conferência de pagamento / academias**: filtros de pesagem consideram permissões e pagamentos, ok, mas não há travas adicionais ao desclassificar.
- **Registro histórico**: histórico é gravado mesmo em peso fora do limite (antes da decisão), podendo poluir log.

## Itens verificados vs regras
- Modal em peso incorreto: front abre modal, mas backend já salvou peso/status pendente.
- Status após decisão: remanejamento → `remanejado`; desclassificar → `desclassificado` (ok). Mas registros prévios já salvos com `pendente_pesagem`.
- Ocorrência: criada só em `confirmar_remanejamento`, não no “peso fora” inicial.
- Desconto de ponto: só no remanejar, ok.
- Impedir chaveamento: apenas por filtro de status; não remove chaves já existentes.
- Exigir nova inscrição: não implementado (desclassificado mantém inscrição).
- Peso informado na inscrição: lógica em view, mas UI não coleta (quebra).
- Recalcular categoria na inscrição: helper existe, UI não aciona.
- Botão registrar abrir modal: front chama modal, mas falta bloqueio de persistência até decisão.

## Redundâncias / lógicas espalhadas
- JS e modais duplicados: `pesagem.html` vs `pesagem_mobile.html`.
- Status/labels hardcoded em templates, diferentes dos enums de `Inscricao`.
- Cálculo de categoria: `_calcular_categoria_por_peso` em `views.py`; seleção de categorias no template de inscrição; validação de categoria na pesagem espalhada.
- Históricos/ocorrências/ranking atualizados em locais distintos (`registrar_peso`, `confirmar_remanejamento`) sem transação.

## Proposta de estrutura correta
- Centralizar regras em serviço de pesagem (ex.: `services/pesagem.py`) com funções atômicas:
  - `calcular_categoria_por_peso(classe, sexo, peso)`
  - `registrar_peso(inscricao, peso, usuario)` → não salva se fora do limite; retorna decisão pendente + sugestões.
  - `remanejar(inscricao, categoria_nova, peso, usuario)` → transação: atualiza inscrição, histórico, ocorrência, pontuação, remove de chaves se necessário.
  - `desclassificar(inscricao, peso, usuario)` → transação: status desclassificado, ocorrência, remover de chaves, marcar bloqueio para chaveamento.
- Atualizar modelo `Inscricao`:
  - Campos: `categoria_calculada`, `peso_informado`, `status_inscricao` restrito a novos valores; flag `bloqueado_chave` (se desclassificado).
  - Métodos helper: `eh_apto_chave`, `eh_desclassificado`.
- Ajustar templates:
  - Inscrição: exigir `peso_atual`, não permitir escolher categoria; exibir categoria calculada.
  - Pesagem: botão “Registrar” deve apenas validar e abrir modal se fora; só persistir quando decisão for tomada (ou peso ok).
  - Unificar modal (desktop/mobile) em partial único + JS compartilhado.
- Ajustar geração de chaves:
  - Filtrar `status_inscricao in ['ok','remanejado']`.
  - Ao desclassificar, remover da(s) chave(s) se já existirem; proteger no backend.
- Exibir ocorrências na ficha do atleta.
- Transações/rollback: envolver remanejamento/desclassificação em `transaction.atomic()`.

## Sugestão de refatoração (passos)
1) Inscrição:
   - Template: trocar select de categoria por input obrigatório de peso atual; exibir categoria sugerida calculada (read-only).
   - View: usar `_calcular_categoria_por_peso`; salvar `categoria_calculada/escolhida`, `peso_informado`, status `pendente_pesagem`.
2) Pesagem:
   - `registrar_peso`: não persistir peso/histórico quando fora do limite; apenas retornar JSON com categoria atual/limites/sugestão e marcar decisão pendente em memória (ou payload do modal).
   - `confirmar_remanejamento`: `transaction.atomic`; para remanejar: atualizar inscrição (status `remanejado`, `categoria_ajustada`), ocorrência, histórico, pontuação -1, e invalidar/remover chaves prévias; para desclassificar: status `desclassificado`, ocorrência, remover de chaves, marcar bloqueio.
   - Atualizar respostas JSON para incluir `atleta_nome`, `inscricao_id`, `categoria_atual`, limites.
3) Templates/JS:
   - Centralizar modal JS em um arquivo único; reutilizar em desktop/mobile.
   - Ajustar badges para novos status (`ok`, `remanejado`, `desclassificado`, `pendente_pesagem`).
4) Chaves:
   - Filtro de aptidão só `ok/remanejado`; remover inscrições desclassificadas das chaves existentes.
5) Ocorrências:
   - Exibir `OcorrenciaAtleta` na ficha do atleta; criar também ao detectar peso fora (log de tentativa).
6) Ranking:
   - Garantir que desconto (-1) ocorra uma vez por remanejamento confirmado; evitar múltiplos débitos.

## Telas a revisar/remover
- Unificar `pesagem.html` e `pesagem_mobile.html` (CSS responsivo) ou extrair modal/JS para partial comum; hoje há duplicação.
- Inscrição: remover tabela de categorias manual; substituir por cálculo automático (peso + classe/sexo).

## Comandos necessários
- Após ajustes: `python manage.py makemigrations atletas && python manage.py migrate`.
- Rodar testes automatizados (a criar) para pesagem e inscrição.

## Exemplo de implementação correta (esboço)
- Endpoint `registrar_peso`:
  - Valida peso, encontra categoria; se dentro → status `ok`, grava histórico e resposta JSON simples.
  - Se fora → não salva; retorna `{precisa_confirmacao: true, categoria_atual, limites_atual, categoria_sugerida, limites_sugerida}`.
- Endpoint `confirmar_remanejamento`:
  - `acao=remanejar`: `categoria_ajustada` = sugerida, status `remanejado`, ocorrência, histórico, ranking -1, limpar chaves antigas.
  - `acao=desclassificar`: status `desclassificado`, ocorrência, remover de chaves, bloquear chaveamento; opcionalmente exigir nova inscrição para voltar (`status_inscricao` não usado em geração de chave).

## Problemas detectados (resumo)
- UI de inscrição não coleta peso; categoria ainda escolhida manualmente.
- Pesagem grava peso/histórico antes da escolha do modal (regra violada).
- Modal depende de dados não garantidos na resposta; payload incompleto.
- Desclassificação não remove chaves nem exige nova inscrição.
- Ocorrências não visíveis; não são criadas no passo de detecção inicial.
- Status apresentados no front desatualizados em relação aos novos enums.
- Duplicação de modais/JS e risco de divergência (desktop vs mobile).


