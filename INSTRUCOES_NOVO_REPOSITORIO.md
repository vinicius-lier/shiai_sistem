# 📦 Como Criar um Novo Repositório

Este guia mostra como criar um novo repositório Git para o projeto SHIAI SISTEM.

## 🎯 Opções Disponíveis

### Opção 1: Criar Novo Repositório no GitHub (Recomendado)

#### Pré-requisitos:
- GitHub CLI instalado: `sudo apt install gh`
- Autenticado: `gh auth login`

#### Método Automático (Script):
```bash
./criar_novo_repositorio.sh
```

#### Método Manual:

1. **Criar repositório no GitHub via CLI:**
```bash
gh repo create novo-nome-repositorio --public --description "Descrição do repositório" --source=. --remote=novo-origin --push
```

2. **Ou criar via interface web:**
   - Acesse: https://github.com/new
   - Preencha nome, descrição e visibilidade
   - **NÃO** inicialize com README, .gitignore ou licença
   - Clique em "Create repository"

3. **Conectar repositório local ao novo remoto:**
```bash
# Adicionar novo remote
git remote add novo-origin https://github.com/SEU_USUARIO/NOVO_REPOSITORIO.git

# Fazer push
git push -u novo-origin render-deploy
```

### Opção 2: Criar Repositório Local Novo

Se você quer começar um repositório Git completamente novo (sem histórico):

```bash
# ⚠️ ATENÇÃO: Isso remove todo o histórico Git atual
rm -rf .git
git init
git add .
git commit -m "Initial commit"
```

### Opção 3: Fazer Fork do Repositório Atual

Para criar uma cópia do repositório atual:

1. No GitHub, vá para: https://github.com/vinicius-lier/shiai_sistem
2. Clique em "Fork"
3. Escolha onde fazer o fork
4. Clone o fork:
```bash
git clone https://github.com/SEU_USUARIO/shiai_sistem.git
```

## 🔧 Configuração de Remotes

### Ver remotes atuais:
```bash
git remote -v
```

### Adicionar novo remote:
```bash
git remote add NOME https://github.com/USUARIO/REPOSITORIO.git
```

### Remover remote:
```bash
git remote remove NOME
```

### Alterar URL de um remote:
```bash
git remote set-url origin https://github.com/NOVO_USUARIO/NOVO_REPO.git
```

## 📋 Exemplo Completo: Criar Repositório para Deploy

```bash
# 1. Criar repositório no GitHub
gh repo create shiai-sistem-producao --public \
  --description "SHIAI SISTEM - Sistema de Gestão de Competições de Judô" \
  --source=. \
  --remote=producao \
  --push

# 2. Verificar remotes
git remote -v

# 3. Fazer push de todas as branches
git push producao --all
git push producao --tags
```

## ⚠️ Importante

- **Backup:** Sempre faça backup antes de alterar remotes
- **Histórico:** Criar novo repositório local remove todo o histórico
- **Colaboradores:** Adicione colaboradores no GitHub após criar o repositório

## 🆘 Troubleshooting

### Erro: "remote origin already exists"
```bash
# Remover remote antigo
git remote remove origin

# Adicionar novo
git remote add origin https://github.com/USUARIO/REPO.git
```

### Erro: "GitHub CLI not authenticated"
```bash
gh auth login
```

### Verificar status de autenticação:
```bash
gh auth status
```

---

**Última atualização:** Dezembro 2025

