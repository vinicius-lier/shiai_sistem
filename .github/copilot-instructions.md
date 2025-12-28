<!-- Instruções concisas para agentes de IA que irão editar esse repositório -->
# Copilot / Agente — Guia Rápido para contribuir com SHIAI SISTEM

Objetivo: fornecer contexto prático e exemplos para agentes de IA serem produtivos imediatamente.

- **Visão geral (big picture)**: projeto Django monolítico com apps específicos para domínio de competições de judô. Backend principal executa em `manage.py` no root; há um sub-projeto `competition_api/` com componentes próprios. Dados por padrão em `db.sqlite3`.

- **Principais apps & responsabilidades**:
  - `atletas/`: modelos de Atleta, lógica de inscrição, pesagem, geração de chaves. Ver: `atletas/models.py`, `atletas/utils.py`, `atletas/constants.py`.
  - `atletas/management/commands/`: comandos customizados (ex.: `criar_usuario_principal`). Use `python3 manage.py <command>`.
  - `accounts/`: autenticação/usuários administrativos e serviços em `accounts/services.py`.
  - `competition_api/`: código de API separado — confira `competition_api/manage.py` antes de mudanças que alterem endpoints públicos.

- **Fluxos críticos e comandos** (execute localmente para reproduzir):
  - Instalação: `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
  - Migrações: `python3 manage.py migrate`
  - Criar usuário operacional: `python3 manage.py criar_usuario_principal --username <user> --password <pass>` (comando custom descrito no README)
  - Rodar servidor: `python3 manage.py runserver` (ou `0.0.0.0:8000` para rede)
  - Testes: `python3 manage.py test` (cada app tem tests/ ou testes em `tests.py`)
  - Build de estáticos / deploy helper: `./build.sh` e scripts em `configurar_heroku.sh`, `RENDER_DEPLOY.md`.

- **Padrões de código e convenções do projeto**:
  - Arquitetura por app: modelos em `models.py`, lógica de aplicação em `services.py` (quando existir), utilitários em `utils.py`.
  - Autorização: roles simples (`ADMIN`/`STAFF`) — não confiar em `auth_permission` por padrão; veja `atletas/academia_auth.py` e middlewares em `atletas/middleware/`.
  - Templates: design system consolidado em `templates/base.html`. Prefira reutilizar classes/partials existentes.
  - Gerenciamento de estado por campeonato ativo: muitos fluxos dependem do "campeonato ativo" — cuidado ao alterar pontos onde a app escolhe evento ativo (pode afetar inscrições, chaves e ranking).

- **Pontos sensíveis / integrações**:
  - Envios via WhatsApp / comunicação externa são usados em funcionalidades de academia (ver `atletas/` e `administracao`), revisar antes de modificar.
  - Dependências externas e deploy: `requirements.txt`, `build.sh`, e scripts `configurar_heroku.sh` / `RENDER_DEPLOY.md` descrevem passos de deploy e ambiente.

- **Onde buscar lógica de negócio importante** (exemplos):
  - Geração de chaves: `atletas/utils.py` / `atletas/services.py` (alterar com testes locais).
  - Pesagem/validação de categoria: `atletas/utils_historico.py` e `atletas/utils_tenant.py` / `atletas/views.py` (fluxo de aprovação/reprovação).
  - Regras de pontuação e ranking: `ranking_api/` e `atletas` (procure funções de cálculo de pontos).

- **Regras ao editar**:
  - Sempre rodar migrações e testes locais ao modificar modelos ou lógica de banco (`python3 manage.py migrate` e `python3 manage.py test`).
  - Ao alterar templates, verifique `base.html` e classes CSS para manter design system.
  - Alterações que impactam fluxo de inscrição/pesagem/chaves exigem testes manuais em ambiente local com um campeonato de teste.

- **Exemplos rápidos de buscas úteis**:
  - Encontrar comandos customizados: `ls atletas/management/commands/`
  - Ver onde `criar_usuario_principal` é definido: `grep -R "criar_usuario_principal" -n .`

- **Observações finais**:
  - Há documentação interna e auditorias em vários arquivos `.md` na raiz (`AUDITORIA_*.md`, `RELATORIO_*.md`) — consultar antes de grandes mudanças.
  - Banco de desenvolvimento padrão: `db.sqlite3` (há um backup `db.sqlite3.bak-2025-12-06`).

Se desejar, posso ajustar o arquivo incluindo referências de linhas exatas ou mesclar conteúdo de outro arquivo de instrução caso você queira incorporar texto adicional. Quer que eu rode a suíte de testes local depois desta alteração?
