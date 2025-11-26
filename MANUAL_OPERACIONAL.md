# 📘 Manual do Usuário Operacional - SHIAI SISTEM

**Versão:** 1.0  
**Para:** Gestores e Organizadores de Competições de Judô

---

## 📋 Índice

1. [Primeiro Acesso](#1-primeiro-acesso)
2. [Criar Campeonatos](#2-criar-campeonatos)
3. [Abrir Inscrições](#3-abrir-inscrições)
4. [Confirmar Inscrições](#4-confirmar-inscrições)
5. [Pesagem](#5-pesagem)
6. [Gerar Chaves](#6-gerar-chaves)
7. [Registrar Resultados](#7-registrar-resultados)
8. [Ver Rankings](#8-ver-rankings)
9. [Financeiro](#9-financeiro)
10. [Usuários do Sistema](#10-usuários-do-sistema)
11. [Relatórios](#11-relatórios)
12. [Dicas e Atalhos](#12-dicas-e-atalhos)

---

## 1. Primeiro Acesso

### 1.1 Acessar o Sistema

1. Abra o navegador e acesse o endereço do sistema (fornecido pelo administrador)
2. Na tela inicial, clique em **"Login Operacional"**
3. Digite seu **usuário** e **senha** (fornecidos pelo administrador principal)
4. Clique em **"Entrar"**

> ⚠️ **Importante:** Se você não tem credenciais, entre em contato com o administrador principal do sistema.

### 1.2 Tela Inicial (Dashboard)

Após o login, você verá o **Dashboard Operacional** com:
- **Estatísticas gerais** do campeonato ativo
- **Ranking preview** (top 5 academias)
- **Links rápidos** para principais funcionalidades

---

## 2. Criar Campeonatos

### 2.1 Criar Novo Campeonato

1. No menu lateral, clique em **"Campeonatos"**
2. Clique no botão **"Novo Campeonato"** (canto superior direito)
3. Preencha os dados:

   **Informações Básicas:**
   - **Nome do Campeonato**: Ex: "Campeonato Regional de Judô 2024"
   - **Data de Início**: Data em que as inscrições começam
   - **Data da Competição**: Data do evento
   - **Data Limite de Inscrição**: Último dia para inscrições

   **Valores de Inscrição:**
   - **Valor Federado**: Valor para atletas federados (ex: 50.00)
   - **Valor Não Federado**: Valor para atletas não federados (ex: 60.00)

   **Regulamento:**
   - Cole ou digite o regulamento do campeonato no campo de texto

4. Marque **"Ativo"** se este será o campeonato ativo (apenas um pode estar ativo por vez)
5. Clique em **"Salvar"**

> ✅ **Dica:** Ao criar um campeonato, o sistema automaticamente:
> - Gera senhas únicas para cada academia
> - Envia convites via WhatsApp (se configurado)
> - Cria o campeonato como ativo (se marcado)

### 2.2 Ativar um Campeonato Existente

1. Vá em **"Campeonatos"**
2. Na lista, encontre o campeonato desejado
3. Clique no botão **"Ativar"** ao lado do campeonato
4. Confirme a ação

> ⚠️ **Atenção:** Ao ativar um campeonato, o anterior é automaticamente desativado.

### 2.3 Editar Campeonato

1. Vá em **"Campeonatos"**
2. Clique no botão **"Editar"** ao lado do campeonato
3. Modifique os campos desejados
4. Clique em **"Salvar"**

### 2.4 Gerenciar Senhas das Academias

1. Vá em **"Campeonatos"**
2. Clique no botão **"Senhas"** ao lado do campeonato
3. Você verá uma tabela com todas as academias e suas senhas
4. Para reenviar uma senha:
   - Clique em **"Reenviar WhatsApp"** ao lado da academia
   - O sistema abrirá o WhatsApp com a mensagem pré-formatada
   - Envie a mensagem

> 📱 **Nota:** As senhas são geradas automaticamente ao criar o campeonato. Cada academia recebe uma senha única por campeonato.

---

## 3. Abrir Inscrições

### 3.1 Verificar Campeonato Ativo

Antes de abrir inscrições, certifique-se de que há um **campeonato ativo**:

1. Vá em **"Campeonatos"**
2. Verifique se há um campeonato marcado como **"Ativo"**
3. Se não houver, ative um campeonato (veja seção 2.2)

### 3.2 Cadastrar Academias

As academias precisam estar cadastradas antes de inscrever atletas:

1. No menu lateral, clique em **"Academias"**
2. Clique em **"Nova Academia"**
3. Preencha os dados:
   - **Nome**: Nome da academia
   - **Cidade**: Cidade da academia
   - **Estado**: UF (ex: SP, RJ)
   - **Telefone**: Telefone de contato (para envio de senhas)
   - **Responsável**: Nome do responsável
   - **Login**: Login único da academia (gerado automaticamente se vazio)
   - **Senha**: Senha para login geral (opcional)
4. Clique em **"Salvar"**

> ✅ **Dica:** O sistema pode gerar o login automaticamente baseado no telefone ou ID da academia.

### 3.3 Cadastrar Categorias

As categorias oficiais precisam estar cadastradas:

1. No menu lateral, clique em **"Categorias"**
2. Clique em **"Nova Categoria"**
3. Preencha os dados:
   - **Classe**: Ex: SUB 9, SUB 11, SUB 13, SUB 15, SUB 18, SUB 21, SÊNIOR, VETERANOS
   - **Sexo**: Masculino ou Feminino
   - **Nome da Categoria**: Ex: Meio Leve, Leve, Médio
   - **Limite Mínimo**: Peso mínimo em kg (ex: 45.0)
   - **Limite Máximo**: Peso máximo em kg (ex: 50.0)
4. Clique em **"Salvar"**

> 📋 **Importante:** Cadastre todas as categorias oficiais antes de abrir as inscrições.

### 3.4 Inscrições pelas Academias

As academias fazem suas próprias inscrições através do **Módulo de Academia**:

1. As academias recebem senha por WhatsApp ao criar o campeonato
2. Elas acessam o sistema e fazem login com a senha recebida
3. Inscrevem seus atletas no campeonato
4. As inscrições ficam com status **"Pendente"** aguardando sua confirmação

> ✅ **Nota:** Você não precisa fazer as inscrições manualmente. As academias fazem isso através do painel delas.

---

## 4. Confirmar Inscrições

### 4.1 Acessar Conferência de Inscrições

1. No menu lateral, vá em **"Administração"** → **"Conferência de Inscrições"**
2. Você verá uma lista de todas as inscrições pendentes

### 4.2 Revisar Inscrições

Para cada inscrição, você verá:
- **Nome do Atleta**
- **Academia**
- **Classe Escolhida**
- **Categoria Escolhida**
- **Status**: Pendente

### 4.3 Confirmar Inscrições

**Confirmar Individualmente:**
1. Marque a caixa ao lado da inscrição
2. Clique em **"Confirmar Selecionadas"**
3. A inscrição muda para status **"Confirmado"**

**Confirmar em Lote:**
1. Marque várias inscrições
2. Clique em **"Confirmar Selecionadas"**
3. Todas as inscrições selecionadas são confirmadas de uma vez

**Confirmar Todas:**
1. Clique em **"Confirmar Todas"**
2. Todas as inscrições pendentes são confirmadas

> 💰 **Importante:** Inscrições confirmadas contam para o **"Dinheiro em Caixa"** no módulo financeiro.

### 4.4 Reprovar Inscrições

Se uma inscrição estiver incorreta:
1. Marque a inscrição
2. Clique em **"Reprovar"**
3. A inscrição muda para status **"Reprovado"** e não conta para o campeonato

> ⚠️ **Atenção:** Inscrições reprovadas não podem ser usadas para gerar chaves.

### 4.5 Envio Automático de Confirmação

Após confirmar inscrições de uma academia:
- O sistema envia automaticamente uma mensagem WhatsApp para a academia
- A mensagem informa quantos atletas foram confirmados e o valor total

---

## 5. Pesagem

### 5.1 Acessar Tela de Pesagem

1. No menu lateral, clique em **"Pesagem"**
2. Você verá uma lista de todas as inscrições confirmadas ou aprovadas

### 5.2 Filtrar Inscrições

Use os filtros no topo da página:
- **Nome**: Buscar por nome do atleta
- **Classe**: Filtrar por classe (SUB 9, SUB 11, etc.)
- **Categoria**: Filtrar por categoria
- **Academia**: Filtrar por academia

### 5.3 Registrar Peso

**Método 1 - Desktop:**
1. Na linha do atleta, digite o peso no campo **"Peso Oficial"**
2. Clique em **"Registrar"**
3. O sistema valida automaticamente:
   - Se o peso está dentro dos limites da categoria → **Aprova**
   - Se o peso está acima → **Sugere categoria inferior** ou **Elimina**
   - Se o peso está abaixo → **Permite subir categoria** (se aplicável)

**Método 2 - Mobile (Recomendado):**
1. Acesse **"Pesagem"** → **"Versão Mobile"** ou `/pesagem/mobile/`
2. Use a interface otimizada para celular/tablet
3. Digite o peso e registre

### 5.4 Ajuste de Categoria

Se o peso do atleta não está dentro dos limites:

**Opção 1 - Aprovar Remanejamento:**
1. O sistema sugere uma categoria adequada
2. Clique em **"Aprovar Remanejamento"**
3. O atleta é remanejado para a categoria sugerida
4. Status muda para **"Aprovado"**

**Opção 2 - Rebaixar Categoria:**
1. Clique em **"Rebaixar Categoria"**
2. Selecione a categoria inferior desejada
3. Confirme o rebaixamento

**Opção 3 - Eliminar:**
1. Se o peso está muito acima e não há categoria inferior:
2. O atleta é **eliminado** da competição
3. Status muda para **"Reprovado"**

### 5.5 Status Após Pesagem

- **Aprovado**: Peso dentro dos limites, pode gerar chave
- **Remanejado**: Peso ajustado para outra categoria, pode gerar chave
- **Reprovado**: Eliminado da competição

> ✅ **Dica:** Use a versão mobile da pesagem durante o evento para maior agilidade.

---

## 6. Gerar Chaves

### 6.1 Acessar Geração de Chaves

1. No menu lateral, clique em **"Chaves"**
2. Clique em **"Gerar Nova Chave"**

### 6.2 Selecionar Categoria

1. Selecione a **Classe** (ex: SUB 11, SÊNIOR)
2. Selecione o **Sexo** (Masculino ou Feminino)
3. Selecione a **Categoria** (ex: Meio Leve, Leve)
4. Clique em **"Gerar Chave"**

> ⚠️ **Importante:** Apenas inscrições com status **"Aprovado"** são usadas para gerar chaves.

### 6.3 Tipo de Chave Automático

O sistema determina automaticamente o tipo de chave baseado no número de atletas:

- **1 atleta**: Campeão automático
- **2 atletas**: Melhor de 3
- **3 atletas**: Triangular
- **4 atletas**: Olímpica 4
- **5-8 atletas**: Olímpica 8
- **9-16 atletas**: Olímpica 16
- **17-32 atletas**: Olímpica 32
- **33+ atletas**: Round Robin (todos contra todos)

### 6.4 Selecionar Modelo de Chave Manualmente

Se desejar forçar um tipo específico:
1. Na tela de geração, selecione **"Modelo de Chave"**
2. Escolha o tipo desejado
3. Clique em **"Gerar Chave"**

> ✅ **Dica:** O modelo automático geralmente é o mais adequado.

### 6.5 Gerar Chave Manual (Lutas Casadas)

Para criar lutas casadas (não competitivas):
1. Vá em **"Chaves"** → **"Gerar Chave Manual"**
2. Selecione os atletas desejados (mínimo 2)
3. Defina nome, classe e sexo da chave
4. Clique em **"Gerar"**
5. O sistema cria lutas 1x1 na ordem selecionada

> 📋 **Nota:** Chaves manuais não contam para ranking.

### 6.6 Visualizar Chave Gerada

Após gerar, você será redirecionado para a **"Detalhe da Chave"** onde verá:
- Estrutura completa da chave
- Todas as lutas organizadas por round
- Atletas em cada luta
- Campos para registrar resultados

---

## 7. Registrar Resultados

### 7.1 Acessar Detalhe da Chave

1. Vá em **"Chaves"**
2. Clique em **"Ver Detalhes"** na chave desejada

### 7.2 Registrar Vencedor de uma Luta

**Método 1 - Desktop:**
1. Na luta desejada, selecione o **"Vencedor"** (Atleta A ou Atleta B)
2. Selecione o **"Tipo de Vitória"** (Ippon, Wazari, Yuko)
3. Clique em **"Registrar Resultado"**
4. O sistema atualiza automaticamente:
   - Marca a luta como concluída
   - Avança o vencedor para a próxima luta
   - Atualiza a estrutura da chave

**Método 2 - Mobile (Recomendado):**
1. Acesse a chave em **"Versão Mobile"** ou `/chave/mobile/<id>/`
2. Toque na luta desejada
3. Selecione vencedor e tipo de vitória
4. Registre o resultado

### 7.3 Registrar Luta Individual (Mobile)

1. Acesse `/luta/mobile/<id_da_luta>/`
2. Você verá apenas uma luta por vez
3. Registre o resultado
4. O sistema avança automaticamente para a próxima luta

### 7.4 Pódio Automático

Ao finalizar todas as lutas de uma chave:
- O sistema calcula automaticamente o **pódio**:
  - **1º Lugar (Ouro)**
  - **2º Lugar (Prata)**
  - **3º Lugar (Bronze)** - dois atletas
- A pontuação é atribuída automaticamente à academia
- O ranking é atualizado em tempo real

> ✅ **Dica:** Use a versão mobile durante a competição para registrar resultados rapidamente.

---

## 8. Ver Rankings

### 8.1 Ranking do Evento

1. No menu lateral, clique em **"Ranking"**
2. Você verá o ranking das academias no **campeonato ativo**
3. O ranking mostra:
   - **Posição**
   - **Nome da Academia**
   - **Medalhas** (Ouro, Prata, Bronze)
   - **Pontos Totais**

### 8.2 Ranking Global

1. No menu lateral, clique em **"Ranking Global"**
2. Você verá o ranking consolidado de **todos os eventos**
3. O ranking mostra a soma de todas as pontuações

### 8.3 Calcular Pontuação

Se o ranking não estiver atualizado:
1. Vá em **"Ranking"**
2. Clique em **"Calcular Pontuação"**
3. O sistema recalcula todas as pontuações baseado nas chaves finalizadas

> ⚠️ **Nota:** O sistema atualiza o ranking automaticamente ao registrar resultados, mas você pode recalcular manualmente se necessário.

### 8.4 Sistema de Pontuação

- **1º Lugar (Ouro)**: 10 pontos
- **2º Lugar (Prata)**: 7 pontos
- **3º Lugar (Bronze)**: 5 pontos (cada)
- **4º Lugar**: 3 pontos
- **5º Lugar**: 1 ponto

---

## 9. Financeiro

### 9.1 Acessar Módulo Financeiro

1. No menu lateral, vá em **"Administração"** → **"Financeiro"**
2. Você verá o painel financeiro completo

### 9.2 Visão Geral Financeira

O painel mostra:

**Entradas:**
- **Entradas Previstas**: Soma de todas as inscrições (pendentes + confirmadas)
- **Dinheiro em Caixa**: Soma apenas de inscrições confirmadas
- **Pagamentos Pendentes**: Soma de inscrições pendentes

**Saídas:**
- **Total de Despesas**: Soma de todas as despesas
- **Despesas Pagas**: Despesas já pagas
- **Despesas Pendentes**: Despesas não pagas

**Bônus:**
- **Bônus de Professores**: Total de bônus calculados

**Saldo:**
- **Saldo Final**: Caixa - Despesas Pagas - Bônus

### 9.3 Gerenciar Despesas

1. No módulo financeiro, clique em **"Despesas e Receitas"**
2. Clique em **"Nova Despesa"**
3. Preencha:
   - **Categoria**: Árbitros, Mesários, Insumos, etc.
   - **Nome**: Nome da despesa
   - **Valor**: Valor em reais
   - **Status**: Pago ou Pendente
   - **Observação**: Detalhes adicionais
   - **Contato**: Nome e WhatsApp (opcional)
4. Clique em **"Salvar"**

### 9.4 Marcar Despesa como Paga

1. Na lista de despesas, encontre a despesa
2. Clique em **"Editar"**
3. Altere o **Status** para **"Pago"**
4. Preencha a **Data de Pagamento**
5. Clique em **"Salvar"**

### 9.5 Bônus de Professores

O bônus é calculado automaticamente baseado nas configurações de cada academia:

**Bônus Percentual:**
- Definido em **"Academias"** → **"Editar Academia"**
- Exemplo: 5% sobre valor total de inscrições confirmadas

**Bônus Fixo:**
- Definido em **"Academias"** → **"Editar Academia"**
- Exemplo: R$ 10,00 por atleta confirmado

> 💰 **Nota:** O bônus é calculado automaticamente e aparece no painel financeiro.

---

## 10. Usuários do Sistema

### 10.1 Acessar Gerenciamento de Usuários

1. No menu lateral, vá em **"Usuários Operacionais"**
2. Você verá a lista de todos os usuários do sistema

> ⚠️ **Importante:** Apenas o usuário principal pode criar outros usuários.

### 10.2 Criar Novo Usuário

1. Na tela de usuários, preencha o formulário:
   - **Nome de Usuário**: Login único
   - **Senha**: Senha de acesso
   - **E-mail**: E-mail (opcional)
   - **Permissões**:
     - ☐ Pode Resetar Campeonato (apenas principal)
     - ☐ Pode Criar Outros Usuários (apenas principal)
   - **Data de Expiração**: Deixe em branco para vitalício ou escolha uma data
   - **Status**: Ativo ou Inativo
2. Clique em **"Criar Usuário"**

> ⏰ **Nota:** Usuários criados têm validade de 30 dias por padrão. O usuário principal é vitalício.

### 10.3 Editar Usuário

1. Na lista, clique em **"Editar"** ao lado do usuário
2. Modifique os campos desejados
3. Clique em **"Salvar Alterações"**

> ⚠️ **Atenção:** Apenas o criador do usuário ou o usuário principal pode editar a data de expiração.

### 10.4 Remover Usuário

1. Na lista, clique em **"Remover"** ao lado do usuário
2. Confirme a ação
3. O usuário é removido permanentemente

> ⚠️ **Atenção:** Você não pode remover seu próprio usuário.

### 10.5 Verificar Validade do Acesso

Na lista de usuários, você verá:
- **Vitalício**: Usuário sem data de expiração
- **Expira em DD/MM/AAAA**: Data de expiração
- **Dias Restantes**: Quantos dias faltam para expirar
- **Status**: Ativo ou Inativo

---

## 11. Relatórios

### 11.1 Acessar Relatórios

1. No menu lateral, vá em **"Administração"** → **"Relatórios Administrativos"**
2. Você verá opções de relatórios disponíveis

### 11.2 Relatórios Disponíveis

**Relatório Financeiro:**
- Exporta dados financeiros em PDF
- Inclui entradas, despesas, bônus e saldo

**Relatório de Equipe:**
- Lista todos os membros da equipe técnica
- Inclui árbitros, mesários, coordenadores, etc.

**Relatório de Estrutura:**
- Lista recursos operacionais
- Inclui ambulâncias, insumos, estrutura

**Relatório de Patrocínios:**
- Lista todos os patrocínios
- Inclui valores e contatos

### 11.3 Exportar Relatórios

1. Selecione o tipo de relatório
2. Clique em **"Exportar PDF"**
3. O arquivo será gerado e baixado automaticamente

> 📄 **Nota:** Alguns relatórios podem ser exportados em CSV (quando disponível).

### 11.4 Relatórios de Métricas

1. No menu lateral, clique em **"Métricas"**
2. Você verá um dashboard com:
   - Estatísticas de inscrições
   - Estatísticas de pesagem
   - Estatísticas de chaves
   - Gráficos e visualizações

### 11.5 Imprimir Chaves

1. Vá em **"Chaves"**
2. Clique em **"Ver Detalhes"** na chave desejada
3. Clique em **"Imprimir"** (canto superior direito)
4. A chave será formatada para impressão em A4

> 🖨️ **Dica:** Use a impressão para criar cópias físicas das chaves durante a competição.

---

## 12. Dicas e Atalhos

### 12.1 Atalhos Úteis

- **Dashboard**: `/dashboard/` ou clique no logo
- **Pesagem Mobile**: `/pesagem/mobile/`
- **Chave Mobile**: `/chave/mobile/<id>/`
- **Luta Mobile**: `/luta/mobile/<id>/`

### 12.2 Boas Práticas

1. **Sempre verifique o campeonato ativo** antes de começar
2. **Confirme inscrições em lote** para agilizar
3. **Use a versão mobile** durante a pesagem e competição
4. **Registre resultados imediatamente** após cada luta
5. **Mantenha o financeiro atualizado** marcando despesas como pagas

### 12.3 Resolução de Problemas

**Problema: Não consigo gerar chave**
- Verifique se há inscrições com status "Aprovado"
- Verifique se a categoria está correta

**Problema: Ranking não atualizado**
- Vá em "Ranking" → "Calcular Pontuação"
- Verifique se todas as chaves estão finalizadas

**Problema: Academia não consegue fazer login**
- Verifique se a senha foi enviada via WhatsApp
- Reenvie a senha em "Campeonatos" → "Senhas"

**Problema: Despesa não aparece no saldo**
- Verifique se a despesa está marcada como "Paga"
- O saldo considera apenas despesas pagas

### 12.4 Suporte

Para dúvidas ou problemas:
1. Consulte esta documentação
2. Verifique os logs do sistema (se disponível)
3. Entre em contato com o administrador principal

---

## 📝 Glossário

- **Campeonato Ativo**: O campeonato que está sendo usado no momento (apenas um pode estar ativo)
- **Inscrição Pendente**: Inscrição aguardando confirmação do organizador
- **Inscrição Confirmada**: Inscrição confirmada pelo organizador (conta para caixa)
- **Inscrição Aprovada**: Inscrição aprovada na pesagem (pode gerar chave)
- **Remanejamento**: Mudança de categoria após pesagem
- **Chave Olímpica**: Sistema eliminatório (4, 8, 16, 32 atletas)
- **Round Robin**: Sistema onde todos competem contra todos
- **KPI**: Indicador-chave de performance (métricas)

---

**Última Atualização:** 2024  
**Versão do Manual:** 1.0

