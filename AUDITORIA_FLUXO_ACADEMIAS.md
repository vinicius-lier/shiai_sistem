## Auditoria do Fluxo de Academias (multi-tenant por Organização)

### Escopo verificado
- Modelos, views, URLs e templates de academias no app `atletas`.
- Garantias de isolamento por organização (`organizacao_slug` / `request.organizacao`).
- Ajustes necessários de banco (nova coluna `owner` em `Organizador`).

### Problemas encontrados
- `Organizador` sem coluna `owner` no banco (erro `no such column: atletas_organizador.owner_id`), pois faltava migration para o novo campo.
- Views de academias ainda usavam filtro `organizacao=` ou não filtravam por organização em todos os pontos.
- Signatures de views sem `organizacao_slug` em alguns casos e redirecionamentos sem slug.
- Verbose de FK de Academia ainda referindo “Organizador” (ajuste menor de UX/admin).

### Correções aplicadas
- **Modelo `Organizador`**: adicionado campo `owner = FK(settings.AUTH_USER_MODEL, null=True, blank=True)`; `email` agora permite nulo/vazio. (Migration 0005 adicionada.)
- **Views de academias** (`atletas/views.py`):
  - `lista_academias`: filtra `Academia.objects.filter(organizador=request.organizacao)` com `@organizacao_required`.
  - `cadastrar_academia`: recebe `organizacao_slug`, seta `organizador=organizacao` ao criar; vincula apenas a campeonatos ativos da mesma organização; redireciona com slug.
  - `detalhe_academia`: exige slug e filtra academia pela organização.
  - `deletar_academia`: exige slug, filtra academia pela organização, e redireciona com slug.
  - `editar_academia`: exige slug, filtra academia pela organização, e redireciona com slug.
- **Migration**: criada `0005_add_owner_organizador.py` para incluir `owner` e permitir `email` nulo.
- **Verbose**: `Academia.organizador` rotulado como “Organização”.

### Pendências / Ações manuais
- Rodar migrations: `python manage.py migrate` (após conferência em ambiente local). Se necessário, antes: `python manage.py makemigrations` não é preciso porque a migration já foi criada.
- Conferir dados órfãos: `Academia.objects.filter(organizador__isnull=True)` e atribuir à organização correta (ou à ativa) conforme regra de negócio.
- Ajustar login/redirect (fora deste patch) para: superuser → painel de organizações; operacional → organização vinculada.

### Isolamento e segurança
- Todas as views de academias agora usam `@organizacao_required` e filtram por `organizador=organizacao`, impedindo CRUD cruzado.
- Templates de academias já usavam `organizacao_slug=request.organizacao.slug`; nada adicional requerido aqui.

### Testes recomendados
- `python manage.py migrate`
- Acessar `/painel/organizacoes/` (superuser) → entrar em uma organização → `/slug/academias/`.
- CRUD de academia dentro do slug:
  - Criar academia.
  - Editar academia.
  - Listar academias (ver contagem de atletas).
  - Tentar acessar URL de academia de outra org → deve 404/403.
- Fluxo de pesagem/listas após a migration (erro de coluna deve sumir).

### Arquivos alterados
- `atletas/models.py`
- `atletas/views.py`
- `atletas/migrations/0005_add_owner_organizador.py`
- `AUDITORIA_FLUXO_ACADEMIAS.md` (este relatório)

