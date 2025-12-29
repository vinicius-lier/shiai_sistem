## Visão Geral (Shiai System)

- **Projeto**: `judocomp` • **App**: `atletas` • Multi-tenant pelo modelo `Organizador` (slug usado nas rotas).
- **Camadas chave**: URLs globais em `judocomp/urls.py` (landing/login/painel), rotas multi-tenant em `atletas/urls_org.py` (prefixo `<organizacao_slug>/`), middleware `OrganizacaoMiddleware` define `request.organizacao`.

### Entidades principais
- `Organizador` (tenant) • `Academia` (FK organizador) • `Classe`/`Categoria` (faixa de peso) • `Atleta` (FK academia) • `Campeonato` (FK organizador, único ativo) • `Inscricao` (Atleta↔Campeonato, classe/categoria e peso) • `PesagemHistorico` (log de pesagens) • `Chave`/`Luta` (brackets) • `AcademiaCampeonato` / `AcademiaCampeonatoSenha` (permissão e credencial de academia) • `UsuarioOperacional` + `UserProfile` (perfis operacionais por tenant).

### Fluxos mapeados (principais views/templates)
- **Dashboard e menu**: `index` → `atletas/templates/atletas/base.html` (navbar + sidebar, agora condicionais ao `request.organizacao`).
- **Organizações**: `painel_organizacoes` (superuser) lista `Organizador` ativos (`atletas/painel_organizacoes.html`), permite entrar na organização via slug.
- **Academias**: CRUD via `lista_academias`, `cadastrar_academia`, `detalhe_academia`, `editar_academia`, `deletar_academia`.
- **Atletas**: `lista_atletas`, `cadastrar_atleta`, `editar_atleta`, importação e festival.
- **Campeonatos/Eventos**: `lista_campeonatos`, `cadastrar_campeonato`, `editar_campeonato`, ativação, vinculação de academias (`gerenciar_academias_campeonato`), senhas (`gerenciar_senhas_campeonato`).
- **Inscrições**: `inscrever_atletas` (dashboard operacional), depende de `Inscricao` + `AcademiaCampeonato`.
- **Pesagem**: `pesagem` e `pesagem_mobile` (template desktop/mobile), registram peso via AJAX para `registrar_peso`, confirmação em `confirmar_remanejamento`, histórico em `PesagemHistorico` e exibição no modal/coluna da tabela.
- **Chaves**: `lista_chaves`, `gerar_chave_view`, `gerar_todas_chaves`, `gerar_chave_manual`, `detalhe_chave` e `imprimir_chave` usam utilitários em `atletas/utils.py` (`gerar_chave`, `gerar_chave_automatica`, modelos manual/olímpico/round robin/melhor de 3).
- **Ranking/Relatórios**: `ranking_global`, `ranking_academias`, `metricas_evento`, relatórios em `relatorios_*`.
- **Administração**: páginas `administracao_*`, conferência de pagamentos, ocorrências e resets via API `ResetCompeticaoAPIView`.

### Autenticação / Multi-tenant
- **Rotas públicas**: landing (`landing_publica`), login (`login_operacional`), logout (`logout_geral`), painel de organizações.
- **Após login**: `_redirect_dashboard` envia superuser para painel de organizações; usuários operacionais são redirecionados para `/<organizacao_slug>/dashboard/` usando `UserProfile.organizador`.
- **Academia (temporário)**: login próprio em `/academia/login/` com `AcademiaCampeonatoSenha`; decorador `academia_required`.
- **Proteção**: decoradores `operacional_required` e `organizacao_required` aplicados às rotas multi-tenant; middleware garante `request.organizacao` e filtra por slug.

### Pesagem (lógica atualizada)
- View compartilhada `_montar_contexto_pesagem` filtra sempre por `organizador`, campeonatos permitidos/confirmados, aplica filtros de classe/sexo/categoria e monta limite de peso e status por `Categoria`.
- Exibição (desktop/mobile) mostra **categoria** via label da `Categoria` e **limite** como intervalo min–max; usa último registro de `PesagemHistorico` como peso oficial.
- `registrar_peso` valida intervalo: dentro → status `aprovado`; fora → status `pendente` e responde `precisa_confirmacao` abrindo modal. `confirmar_remanejamento` aplica remanejamento/desclassificação e registra histórico.

### Geração de chaves
- Utilitários em `atletas/utils.py`: seleção de inscritos aprovados com peso, criação/limpeza de lutas e estrutura. Automático: 1=campeão, 2=melhor de 3, 3-5=round robin, 6-8=eliminação com repescagem, >8 olímpica dimensionada. Testes rápidos em `atletas/tests/test_chaves.py` cobrem melhor de 3 (2 atletas) e round robin (3 atletas).

### Ajustes de UI/JS (mobile menu)
- Navbar/Sidebar usam links multi-tenant com `organizacao_slug`; menu ocultado em páginas sem `request.organizacao` (ex.: painel do superuser).
- Script de sidebar simplificado (click/touch) para abrir/fechar overlay em mobile; removidos listeners duplicados/debug que impediam funcionamento em telas pequenas.

### Pontos sensíveis a observar
- Dados legados ainda referem-se a `Organizador`; manter consistência ao vincular novos usuários (garantir `UserProfile.organizador`).
- Status de pesagem fora do limite fica como `pendente` até remanejamento/desclassificação; geração de chaves considera apenas inscrições aprovadas com peso.
- Conferir links/url reversals em templates externos ao contexto multi-tenant antes de usar `base.html`.


