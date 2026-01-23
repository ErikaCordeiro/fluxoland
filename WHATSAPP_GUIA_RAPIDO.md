# 📱 GUIA RÁPIDO: Configurar Notificações WhatsApp (Bot Conversa)

## O QUE FOI IMPLEMENTADO

✅ Sistema de notificações automáticas via WhatsApp usando Bot Conversa
✅ Interface web para gerenciar contatos que recebem notificações
✅ Notificações baseadas em mudança de status da proposta
✅ Campo `telefone` nos vendedores para notificações de envio

## COMO FUNCIONA

### Quando uma proposta muda de status:

1. **PENDENTE_SIMULACAO** → Notifica contatos tipo "Simulação" (cadastrados na interface)
2. **PENDENTE_COTACAO** → Notifica contatos tipo "Cotação" (cadastrados na interface)
3. **PENDENTE_ENVIO** → Notifica **Vendedor** responsável (telefone do vendedor)

---

## PASSO A PASSO PARA ATIVAR

### 1️⃣ OBTER TOKEN DO BOT CONVERSA

1. Acesse: https://app.botconversa.com.br/
2. Faça login na sua conta
3. Vá em: **Configurações** > **Webhooks** > **Token de Automação**
4. Copie o token (algo como: `abc123def456...`)

### 2️⃣ CONFIGURAR .ENV

Adicione ao seu arquivo `.env`:

```env
# WhatsApp - Bot Conversa
WHATSAPP_BOT_CONVERSA_TOKEN=seu_token_aqui
```

**Pronto!** Só isso mesmo. Os números são cadastrados pela interface web.

### 3️⃣ ATUALIZAR BANCO DE DADOS

Nova tabela `contatos_notificacao` foi criada. Atualize o banco:

**Opção A: Recriar banco (DEV)**
```bash
python create_tables.py
```

**Opção B: Rodar migração SQL (PROD)**
```sql
-- Adiciona telefone aos usuários/vendedores
ALTER TABLE users ADD COLUMN IF NOT EXISTS telefone VARCHAR(20);

-- Cria tabela de contatos para notificação
CREATE TYPE tiponotificacao AS ENUM ('simulacao', 'cotacao');

CREATE TABLE IF NOT EXISTS contatos_notificacao (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    tipo tiponotificacao NOT NULL,
    ativo BOOLEAN DEFAULT true
);
```

### 4️⃣ CADASTRAR CONTATOS VIA INTERFACE WEB

1. Acesse: http://localhost:8000/contatos-notificacao
2. Clique em "+ Novo Contato"
3. Preencha:
   - Nome: Ex: "Rafael (Rafa)"
   - Telefone: Ex: 5547999999999 ou (47) 99999-9999
   - Tipo: "Simulação" ou "Cotação"
4. Salvar

**Pode cadastrar quantos contatos quiser!** Todos do mesmo tipo receberão a mensagem.

### 5️⃣ CADASTRAR TELEFONE DOS VENDEDORES

Para que vendedores recebam notificação quando proposta vai para envio:

**Opção A: Script Python**
```bash
python update_user_phone.py
```

**Opção B: SQL direto**
```sql
UPDATE users 
SET telefone = '5547999999999' 
WHERE email = 'vendedor@email.com';
```

### 6️⃣ TESTAR

1. Importe uma proposta do Bling
   → Contatos tipo "Simulação" devem receber 📱

2. Faça simulação e conclua
   → Contatos tipo "Cotação" devem receber 📱

3. Salve cotação
   → Vendedor responsável deve receber 📱

**Opção A: Recriar banco (DEV)**
```bash
python create_tables.py
```

**Opção B: Alterar tabela manualmente (PROD)**
```sql
ALTER TABLE users ADD COLUMN telefone VARCHAR(20);
```

### 4️⃣ CADASTRAR TELEFONE DOS VENDEDORES

Execute o script interativo:
```bash
python update_user_phone.py
```

Ou via linha de comando:
```bash
python update_user_phone.py vendedor@email.com 5547999999999
```

### 5️⃣ TESTAR

1. Importe uma proposta do Bling
   → Rafa deve receber mensagem 📱

2. Faça simulação e conclua
   → Você deve receber mensagem 📱

3. Salve cotação
   → Vendedor deve receber mensagem 📱

---

## VERIFICAR SE ESTÁ FUNCIONANDO

Olhe o console quando mudar status:
```
✅ Mensagem WhatsApp enviada para 5547999999999
```

Se der erro:
```
❌ Erro ao enviar WhatsApp: 401 - Unauthorized
⚠️ WhatsApp não configurado - notificação ignorada
```

---

## TROUBLESHOOTING

### ❌ "WhatsApp Bot Conversa não configurado"
- Verifique se adicionou o token no .env
- Rode: `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('WHATSAPP_BOT_CONVERSA_TOKEN'))"`

### ❌ "401 ou 403 Unauthorized"
- Token incorreto ou expirado
- Verifique no painel do Bot Conversa: https://app.botconversa.com.br/

### ❌ "Mensagem não chega"
- Número incorreto (formato deve ser: 5547999999999)
- WhatsApp não está conectado no Bot Conversa
- Verifique status da conexão no painel

### ❌ "Connection timeout"
- Servidor do Bot Conversa pode estar fora
- Tente novamente em alguns minutos

---

## ARQUIVOS CRIADOS/MODIFICADOS

- ✅ `services/whatsapp_service.py` - Serviço de WhatsApp
- ✅ `models.py` - Campo telefone no User
- ✅ `services/proposta_service.py` - Integração com notificações
- ✅ `update_user_phone.py` - Script para atualizar telefones
- ✅ `WHATSAPP_SETUP.md` - Documentação completa
- ✅ `.env.whatsapp.example` - Exemplo de configuração

---

## PRECISA DE AJUDA?

Leia a documentação completa em: `WHATSAPP_SETUP.md`
