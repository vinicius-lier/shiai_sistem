# 📱 Como Acessar o Sistema do Celular

## Requisitos
1. **Servidor rodando** no computador
2. **Celular conectado na mesma rede Wi-Fi** do computador
3. **IP do computador na rede**: `192.168.1.100`

## 📋 Passo a Passo

### 1. Iniciar o Servidor (se não estiver rodando)

No terminal do computador:
```bash
cd /home/vinicius/Documentos/Shiai_sistem
python3 manage.py runserver 0.0.0.0:8000
```

> **Nota**: O `0.0.0.0:8000` permite acesso de qualquer IP na rede local

### 2. Descobrir o IP do Computador (se necessário)

No terminal:
```bash
hostname -I
```

Você verá algo como: `192.168.1.100`

### 3. Acessar do Celular

#### No navegador do celular, digite:

**Página Principal:**
```
http://192.168.1.100:8000
```

**Pesagem Mobile (RECOMENDADO):**
```
http://192.168.1.100:8000/pesagem/mobile/
```

**Chave Mobile:**
```
http://192.168.1.100:8000/chave/mobile/<ID_DA_CHAVE>/
```

**Luta Mobile:**
```
http://192.168.1.100:8000/luta/mobile/<ID_DA_LUTA>/
```

## 🔗 Links Rápidos

Após acessar a página principal do celular:

1. **Pesagem Mobile**: Clique em "Pesagem" → "Versão Mobile"
2. **Chave Mobile**: Na lista de chaves → Detalhes → "Versão Mobile"

## ⚠️ Importante

### Firewall
Se não conseguir acessar, pode ser bloqueio de firewall. Execute:

```bash
sudo ufw allow 8000/tcp
```

Ou desative temporariamente:
```bash
sudo ufw disable
```

### Mesma Rede Wi-Fi
- **Computador e celular DEVEM estar na mesma rede Wi-Fi**
- Não funciona se o celular estiver usando dados móveis

### Se o IP mudar
O IP pode mudar se você reiniciar o roteador. Para descobrir o novo IP:

```bash
hostname -I
```

## 📝 Dica

Para facilitar, você pode salvar nos favoritos do celular:
- `http://192.168.1.100:8000/pesagem/mobile/`
- `http://192.168.1.100:8000/chaves/`

## 🚀 Teste Rápido

1. No computador, abra: `http://localhost:8000`
2. No celular (mesma rede), abra: `http://192.168.1.100:8000`
3. Ambos devem mostrar a mesma página!

## 📞 Problemas?

Se não conseguir acessar:
1. Verifique se o servidor está rodando: `ps aux | grep runserver`
2. Verifique se estão na mesma rede Wi-Fi
3. Tente desabilitar firewall temporariamente
4. Verifique o IP novamente: `hostname -I`

