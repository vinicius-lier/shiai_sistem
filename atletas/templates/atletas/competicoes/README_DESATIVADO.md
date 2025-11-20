# ⚠️ MÓDULO DESATIVADO

Este diretório contém templates do módulo antigo de "Competições" que foi **DESATIVADO**.

## ⚠️ IMPORTANTE

**NÃO USE ESTES TEMPLATES!**

Todo o sistema de competições agora funciona através do módulo **EVENTOS**.

## ✅ Use o módulo correto:

- **Pesagem**: `/eventos/<id>/pesagem/`
- **Gerenciar Eventos**: `/eventos/`
- **Inscrições**: `/eventos/<id>/inscrever/`

## 📝 Templates desativados:

- `lista_competicoes.html` - Use `eventos/operacional/lista_eventos.html`
- `nova_competicao.html` - Use `eventos/operacional/criar_evento.html`
- `competicao_atual.html` - Use `eventos/operacional/ver_inscritos.html`
- `configurar_competicao.html` - Use `eventos/operacional/configurar_evento.html`

## 🔧 Rotas desativadas:

Todas as rotas em `atletas/urls.py` relacionadas a `/competicao/` foram comentadas.


