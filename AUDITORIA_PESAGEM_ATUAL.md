# Auditoria Técnica – Módulo de Pesagem (Shiai System)

## Arquivos analisados
- `atletas/views.py`: `_montar_contexto_pesagem`, `pesagem`, `pesagem_mobile_view`, `registrar_peso`, `confirmar_remanejamento`, lógica de inscrição automática.
- `atletas/services/pesagem.py`: cálculo de categoria por peso, validação, registro de peso, remanejamento/desclassificação, remoção de chaves, pontuação.
- `atletas/models.py`: `Inscricao` (campos de pesagem, `bloqueado_chave`), `PesagemHistorico`, `OcorrenciaAtleta`, `AcademiaPontuacao`.
- `atletas/templates/atletas/pesagem.html` (desktop) e `pesagem_mobile.html` (mobile).
- `atletas/templates/atletas/includes/pesagem_modal.html` (modal unificado).
- `static/js/pesagem.js` (JS unificado para desktop/mobile).
- `atletas/urls_org.py` (rotas de pesagem).
- `atletas/utils.py` (gera chave filtra status/peso).

## Fluxo REAL (atual)
1. Listagem de inscritos: `_montar_contexto_pesagem` carrega inscrições por campeonato ativo/selecionado com status `pendente_pesagem|ok|remanejado|desclassificado`, calcula limites de categoria via `Categoria` ou fallback por peso.
2. Desktop/mobile exibem tabela/cartões; formulário POST em `registrar_peso`.
3. `registrar_peso` chama `service_registrar_peso`: se peso dentro do limite, salva imediatamente (`status ok`, histórico); se fora, **não salva** e retorna JSON para abrir modal.
4. Modal (include + `static/js/pesagem.js`) oferece Remanejar ou Desclassificar. Submissão via `confirmar_remanejamento`.
5. `service_confirmar_remanejamento`:
   - Remanejar: recalcula categoria (sugerida ou automática), marca `status remanejado`, `bloqueado_chave=False`, histórico, ocorrência `REMANEJAMENTO`, debita 1 ponto em `AcademiaPontuacao`, remove de chaves.
   - Desclassificar: `status desclassificado`, `bloqueado_chave=True`, histórico, ocorrência `DESCLASSIFICACAO`, remove de chaves.
6. Geração de chave (`utils.py`) usa apenas inscrições `ok|remanejado` e `bloqueado_chave=False` com peso registrado.

## Fluxo ESPERADO (regras solicitadas)
- Peso registrado:
  - Se dentro do limite → salvar peso, status OK.
  - Se fora → não salvar; abrir modal para decisão explícita.
- Remanejamento:
  - Recalcula categoria automaticamente.
  - Grava ocorrência.
  - Debita 1 ponto da academia.
  - Remove de chaves existentes.
  - Permite novo chaveamento (não bloqueado).
- Desclassificação:
  - Grava ocorrência.
  - Bloqueia chaveamento (não entra em chaves).
  - Exige nova inscrição para voltar.
- Status/labels corretos nos templates; modal/JS unificados desktop/mobile.
- Histórico/ocorrências apenas no momento correto.

## Diferenças (Real vs Esperado)
- ✅ Peso fora não é salvo antes da decisão (atual).
- ✅ Modal abre e exige ação.
- ✅ Remanejamento debita 1 ponto, cria ocorrência e limpa chaves.
- ✅ Desclassificação cria ocorrência, limpa chaves, bloqueia chaveamento via `bloqueado_chave`.
- ⚠ Exigir “nova inscrição” pós-desclassificação não está forçado no fluxo; apenas bloqueia chaveamento.
- ⚠ Templates ainda exibem status textuais simples; poderiam alinhar badges às enumerações (`ok`, `remanejado`, `desclassificado`, `pendente_pesagem`).
- ⚠ Há duplicação residual de layout entre `pesagem.html` e `pesagem_mobile.html` (apesar do JS/modal unificados).

## Redundâncias e duplicações
- Templates desktop/mobile mantêm estruturas e estilos duplicados; filtros e cards repetem markup.
- Ainda restam trechos de JS legados removidos do desktop mas mobile retém muito CSS/HTML específico.

## Lógicas de peso e onde estão
- Cálculo/sugestão de categoria: `services/pesagem.py:calcular_categoria_por_peso` e `validar_peso`.
- Registro OK: `services/pesagem.py:registrar_peso_ok`.
- Decisão fora de limite: `services/pesagem.py:confirmar_remanejamento`.
- Remoção de chaves e lutas: `services/pesagem.py:remover_de_chaves`.
- Filtragem de aptidão para chave: `utils.py:gerar_chave` (status e `bloqueado_chave`).
- Construção de contexto/listagem e limites: `_montar_contexto_pesagem` em `views.py`.

## Estado de idade/categoria/limites/sexo/faixa
- Idade/classe não recalculada na pesagem; usa `classe_escolhida` da inscrição.
- Categoria inicial vem do peso informado na inscrição (`categoria_calculada/categoria_escolhida`), coerente com regra.
- Limites min/max buscados na categoria associada; peso oficial comparado antes de salvar.
- Sexo respeitado em todas as queries de categoria.

## Comportamento com peso incorreto (atual)
- POST `registrar_peso` fora do limite → retorna JSON `precisa_confirmacao=true`; modal abre via `static/js/pesagem.js`.
- Status só muda após `confirmar_remanejamento` (remanejar ou desclassificar).
- Ocorrência é criada apenas na decisão (remanejamento/desclassificação), não no momento da detecção.
- Ponto da academia debitado apenas em remanejamento confirmado.
- `bloqueado_chave` aplicado em desclassificação, impedindo chaveamento.
- Não força criação de nova inscrição; apenas bloqueia/remoção de chaves.

## Problemas detectados
1. Exigir nova inscrição após desclassificação não implementado (apenas bloqueio).
2. Status/badges nos templates não exibem enum completa nem textos claros; falta harmonizar mensagens.
3. Duplicação de templates (desktop vs mobile) aumenta risco de divergência.
4. Mobile mantém ações de filtro “Limpar” hardcoded; desktop corrigido, mas mobile precisava do slug (corrigido agora).
5. Ocorrência não é registrada na etapa de detecção inicial (somente na decisão).
6. Não há validação de idade/classe na pesagem; depende da inscrição prévia.

## Sugestão de estrutura correta (final)
- **Service único** (`services/pesagem.py`): calcular_categoria_por_peso, validar_peso, registrar_peso (somente OK), confirmar_remanejamento (remanejar/desclassificar), remover_de_chaves.
- **Views finas**: `registrar_peso` apenas delega ao service e retorna JSON; `confirmar_remanejamento` idem.
- **Templates/JS unificados**: manter modal único (`includes/pesagem_modal.html`) e JS único (`static/js/pesagem.js`); transformar `pesagem_mobile.html` em variação responsiva do desktop ou usar mesmo template com CSS responsivo.
- **Status/Cards**: mapear status a badges (`ok`, `remanejado`, `desclassificado`, `pendente_pesagem`), exibir motivo/ocorrência.
- **Regras extra**: em desclassificação, marcar flag `exige_nova_inscricao` (ou reutilizar `bloqueado_chave`) e ocultar botões de pesagem para reentrada até nova inscrição.
- **Ocorrências**: registrar também o evento “peso fora do limite” se o operador abandonar a decisão.

## Exemplo de implementação correta (resumido)
```python
# registrar_peso (view)
resultado = service_registrar_peso(inscricao, peso, observacoes, usuario=request.user)
return JsonResponse(resultado_payload(resultado, inscricao))

# confirmar_remanejamento (service)
@transaction.atomic
if acao == 'remanejar':
    categoria_final = categoria_sugerida or calcular_categoria_por_peso(...)
    salva peso/status=remanejado, ocorrência, histórico, -1 ponto, remover_de_chaves
elif acao == 'desclassificar':
    salva peso/status=desclassificado, bloqueado_chave=True, ocorrência, histórico, remover_de_chaves
```

## Refatoração proposta
1. Consolidar `pesagem.html` e `pesagem_mobile.html` em um único template responsivo; manter apenas include do modal.
2. Garantir todas as URLs usam `organizacao_slug`.
3. Exibir status padronizados e motivos no front.
4. Adicionar flag explícita para “exige nova inscrição” em desclassificação (ou usar `bloqueado_chave` + bloqueio de reabertura de pesagem).
5. Registrar ocorrência também ao detectar peso fora (log de tentativa).
6. Testes automatizados cobrindo: peso OK, peso fora + remanejar, peso fora + desclassificar, bloqueio de chaveamento, débito de ponto, tentativa de chave com desclassificado.

## Comandos necessários
- `python3 manage.py makemigrations atletas && python3 manage.py migrate`
- Executar suíte de testes (a criar) para pesagem.

## Telas a remover ou juntar
- Remover duplicidade: fundir `pesagem_mobile.html` no template principal com CSS responsivo.
- Manter apenas um modal (`includes/pesagem_modal.html`) e um JS (`static/js/pesagem.js`).

## Lógicas a centralizar
- Todo cálculo/validação/salvamento de pesagem em `services/pesagem.py`.
- Geração de chaves já filtrando `bloqueado_chave` e status aptos em `utils.py`.


