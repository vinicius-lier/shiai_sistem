# 📋 Fluxo de Confirmação de Pagamentos e Inscrições

## 🎯 Visão Geral

Este documento explica o fluxo completo de confirmação de pagamentos e inscrições no sistema SHIAI, desde o envio do comprovante pela academia até a validação pelo operador financeiro.

---

## 🔄 Fluxo Completo

### **1. Academia Envia Comprovante**

**Onde:** Tela do evento (academia)

**Como:**
1. A academia acessa o evento no sistema
2. Vê o valor total a pagar (baseado nas inscrições)
3. Faz o pagamento via PIX ou outra forma de pagamento
4. Envia o comprovante através do botão "Enviar Comprovante"
5. O sistema salva o comprovante e marca o status como `AGUARDANDO`

**Status da Inscrição:** `pendente` (ainda não confirmada)

---

### **2. Operador Financeiro Valida o Pagamento**

**Onde:** Menu Administração → **Inscrições Pagas**

**URL:** `/administracao/pagamentos/`

**O que aparece:**
- Lista de todos os comprovantes aguardando validação
- Informações: Academia, Evento, Valor, Data de Envio
- Botões: **Validar** ou **Rejeitar**

**Como validar:**
1. Clique em **"Validar"** ao lado do pagamento
2. A tela mostra:
   - Informações do pagamento
   - Comprovante para visualização
   - Lista de inscrições que serão confirmadas
3. Revise o comprovante
4. Clique em **"✅ Validar Pagamento e Confirmar Inscrições"**
5. O sistema automaticamente:
   - Marca o pagamento como `VALIDADO`
   - Confirma todas as inscrições da academia (status: `confirmado`)
   - Registra quem validou e quando

**Status da Inscrição:** `confirmado` (pagamento validado, pronto para pesagem)

---

### **3. Rejeitar Pagamento (se necessário)**

**Como rejeitar:**
1. Clique em **"Rejeitar"** ao lado do pagamento
2. Informe o motivo da rejeição (obrigatório)
3. Clique em **"Confirmar Rejeição"**
4. O sistema:
   - Marca o pagamento como `REJEITADO`
   - Salva o motivo da rejeição
   - A academia pode ver o motivo e reenviar

**Status da Inscrição:** Permanece `pendente` (não confirmada)

---

## 📊 Status dos Pagamentos

| Status | Descrição | O que fazer |
|--------|-----------|-------------|
| `PENDENTE` | Academia ainda não enviou comprovante | Aguardar envio |
| `AGUARDANDO` | Comprovante enviado, aguardando validação | **Validar ou Rejeitar** |
| `VALIDADO` | Pagamento confirmado pelo operador | Inscrições confirmadas |
| `REJEITADO` | Pagamento rejeitado (com motivo) | Academia pode reenviar |

---

## 📊 Status das Inscrições

| Status | Descrição | Quando acontece |
|--------|-----------|-----------------|
| `pendente` | Inscrição feita, aguardando pagamento | Academia inscreve atleta |
| `confirmado` | Pagamento validado, inscrição confirmada | **Após validação do pagamento** |
| `aprovado` | Aprovado para gerar chave (após pesagem) | Após pesagem bem-sucedida |
| `reprovado` | Reprovado na pesagem | Peso fora da categoria |

---

## 🎯 Localização no Sistema

### **Para o Operador Financeiro:**

1. **Acessar Validação de Pagamentos:**
   - Menu: **Administração** → **Inscrições Pagas**
   - URL: `/administracao/pagamentos/`

2. **O que você verá:**
   - **Pagamentos Aguardando Validação** (prioridade)
   - Pagamentos Validados Recentemente
   - Pagamentos Rejeitados Recentemente

3. **Ações disponíveis:**
   - **Validar:** Confirma pagamento e todas as inscrições da academia
   - **Rejeitar:** Rejeita com motivo (academia pode reenviar)

---

## ✅ Processo Passo a Passo

### **Cenário: Academia "Judo Clube" enviou comprovante**

1. **Operador acessa:** Administração → Inscrições Pagas
2. **Vê na lista:** "Judo Clube - Copa Modelo - R$ 500,00 - Aguardando"
3. **Clica em "Validar"**
4. **Visualiza:**
   - Comprovante (pode abrir em nova aba)
   - Lista de 5 atletas que serão confirmados
   - Valor total: R$ 500,00
5. **Confirma que está correto**
6. **Clica em "✅ Validar Pagamento e Confirmar Inscrições"**
7. **Sistema confirma:**
   - ✅ Pagamento validado!
   - ✅ 5 inscrições confirmadas automaticamente
8. **Resultado:**
   - Pagamento: Status `VALIDADO`
   - Inscrições: Status `confirmado`
   - Atletas podem ser pesados

---

## 🔍 Verificação de Dados

### **Antes de Validar, verifique:**

- ✅ Valor do comprovante confere com o valor esperado
- ✅ Data do pagamento está dentro do prazo
- ✅ Comprovante está legível
- ✅ Nome da academia/evento está correto
- ✅ Número de inscrições confere

### **Se algo estiver errado:**

- ❌ Use **"Rejeitar"** e informe o motivo específico
- 📝 Exemplos de motivos:
  - "Valor incorreto: comprovante mostra R$ 450,00 mas esperado é R$ 500,00"
  - "Comprovante ilegível, por favor envie foto mais clara"
  - "Data do pagamento (15/01) está fora do prazo de inscrições"

---

## 🔗 Integração com Outros Módulos

### **Após Validação:**

1. **Inscrições confirmadas** aparecem em:
   - Pesagem (podem ser pesados)
   - Conferência de Inscrições (status: confirmado)
   - Dashboard Financeiro (contam para "Dinheiro em Caixa")

2. **Após Pesagem:**
   - Inscrições mudam para `aprovado`
   - Podem gerar chaves
   - Contam para ranking

---

## 📱 Notificações (Futuro)

**Planejado:**
- WhatsApp automático para academia quando pagamento for validado
- WhatsApp automático quando pagamento for rejeitado (com motivo)

---

## ❓ Dúvidas Frequentes

### **P: Onde encontro a tela de validação?**
**R:** Menu **Administração** → **Inscrições Pagas** (`/administracao/pagamentos/`)

### **P: Posso validar sem ver o comprovante?**
**R:** Não recomendado. Sempre visualize o comprovante antes de validar.

### **P: O que acontece se eu rejeitar por engano?**
**R:** A academia pode reenviar um novo comprovante, que aparecerá novamente na lista.

### **P: Posso validar parcialmente (só algumas inscrições)?**
**R:** Não. A validação confirma TODAS as inscrições da academia no evento. Se precisar validar parcialmente, rejeite e peça para a academia reenviar apenas o valor correto.

### **P: As inscrições confirmadas podem ser pesadas?**
**R:** Sim! Inscrições com status `confirmado` aparecem na tela de pesagem.

---

## 🎓 Resumo Visual do Fluxo

```
Academia Envia Comprovante
         ↓
Status: AGUARDANDO
         ↓
Operador Acessa: Administração → Inscrições Pagas
         ↓
Visualiza Comprovante
         ↓
    ┌────┴────┐
    │         │
Validar   Rejeitar
    │         │
    ↓         ↓
Confirmado  Pendente
(pronto     (aguarda
para        reenvio)
pesagem)
```

---

## 📞 Suporte

Se tiver dúvidas sobre o fluxo, consulte este documento ou entre em contato com o administrador do sistema.


