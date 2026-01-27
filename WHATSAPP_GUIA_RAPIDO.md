# 📱 GUIA RÁPIDO: Notificações WhatsApp (BotConversa)

## ✅ O QUE FOI IMPLEMENTADO

- ✅ Sistema de notificações automáticas via WhatsApp usando BotConversa
- ✅ Interface web para gerenciar contatos que recebem notificações
- ✅ Notificações baseadas em mudança de status da proposta
- ✅ 3 tipos de notificação: **Simulação**, **Cotação** e **Envio**
- ✅ Disparo automático ao importar proposta do Bling
- ✅ Código profissional com logging e documentação completa

---

## 🔄 FLUXO AUTOMÁTICO

Quando uma proposta muda de status, o sistema automaticamente:

| Status | Quem Recebe | Quando |
|--------|-------------|--------|
| **PENDENTE_SIMULACAO** | Contatos tipo "simulacao" | Ao importar do Bling ou criar proposta |
| **PENDENTE_COTACAO** | Contatos tipo "cotacao" | Após concluir simulação |
| **PENDENTE_ENVIO** | Contatos tipo "envio" + Vendedor | Após concluir cotação |

---

## 🚀 CONFIGURAÇÃO INICIAL

### 1️⃣ Obter Token do BotConversa

1. Acesse: https://app.botconversa.com.br/
2. Faça login
3. Vá em: **Webhooks** > Crie webhook "Automação Kamaban"
4. Configure:
   - **Requisições** → `Padrão`
   - **Ações** → Adicione:
     - ✅ Telefone WhatsApp: `phone`
     - ✅ Enviar mensagem: `text`
5. Copie a URL do webhook (ex: `13954/eHmb0sGpjqpG`)

### 2️⃣ Configurar .env

```env
WHATSAPP_BOT_CONVERSA_TOKEN=13954/eHmb0sGpjqpG
```

### 3️⃣ Atualizar Banco de Dados

**Opção A - Desenvolvimento:**
```bash
python create_tables.py
```

**Opção B - Produção (SQL):**
```sql
-- 1. Criar ENUM para tipo de notificação
CREATE TYPE tiponotificacao AS ENUM ('simulacao', 'cotacao', 'envio');

-- 2. Criar tabela de contatos
CREATE TABLE IF NOT EXISTS contatos_notificacao (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    tipo tiponotificacao NOT NULL,
    ativo BOOLEAN DEFAULT true
);

-- 3. Adicionar telefone aos usuários (opcional, para notificar vendedores)
ALTER TABLE users ADD COLUMN IF NOT EXISTS telefone VARCHAR(20);
```

### 4️⃣ Cadastrar Contatos

**Via Interface Web:**
1. Acesse: `http://localhost:8000/contatos-notificacao`
2. Clique em **"+ Novo Contato"**
3. Preencha:
   - **Nome:** Ex: "Erika SAC"
   - **Telefone:** `554792848419` (formato: 55 + DDD + número, SEM espaços)
   - **Tipo:** Escolha entre:
     - **Simulação** → Recebe quando proposta criada/importada
     - **Cotação** → Recebe quando simulação concluída
     - **Envio** → Recebe quando cotação concluída
4. Salvar

**Pode cadastrar múltiplos contatos do mesmo tipo!**

---

## 📋 MENSAGENS ENVIADAS

### Simulação
```
Nova Proposta #123 - Cliente: JOÃO PEDRO - Valor: R$ 1.285,91 - Aguardando simulação
```

### Cotação
```
*Proposta #123 - Pronta para Cotação*
Cliente: JOÃO PEDRO
Valor: R$ 1.285,91
Cubagem: 2.5000 m³ | Peso: 150 kg
```

### Envio
```
*Proposta #123 - Pronta para Envio*
Cliente: JOÃO PEDRO
Valor: R$ 1.285,91
Cotação finalizada, aguardando envio ao cliente
```

---

## 🧪 TESTAR

### Teste 1: Importação do Bling
1. Importe proposta do Bling
2. Contatos tipo **"simulacao"** devem receber WhatsApp

### Teste 2: Mudança de Status
1. Conclua simulação → Status: `PENDENTE_COTACAO`
2. Contatos tipo **"cotacao"** devem receber WhatsApp

3. Conclua cotação → Status: `PENDENTE_ENVIO`
4. Contatos tipo **"envio"** + vendedor devem receber WhatsApp

---

## 🔧 SOLUÇÃO DE PROBLEMAS

### Mensagens não estão chegando?

1. **Verifique o token no .env:**
   ```bash
   cat .env | grep WHATSAPP
   ```

2. **Verifique webhook no BotConversa:**
   - Deve estar ATIVO
   - "Modo Teste" deve estar DESLIGADO
   - Ações devem estar configuradas (`phone` e `text`)

3. **Verifique contatos cadastrados:**
   - Acesse `/contatos-notificacao`
   - Contatos devem estar marcados como "Ativo"
   - Telefone formato correto: `554792848419` (sem espaços/caracteres)

4. **Verifique logs do servidor:**
   ```bash
   # Procure por erros WhatsApp
   tail -f logs/app.log
   ```

### Formato de telefone incorreto?

✅ **Correto:** `554792848419` (55 + DDD + número)
❌ **Errado:** `+55 47 9284-8419` (com espaços/símbolos)
❌ **Errado:** `47 92848419` (falta código do país)

---

## 📁 ARQUIVOS RELACIONADOS

- `services/whatsapp_service.py` - Serviço principal
- `services/proposta_service.py` - Dispara notificações ao mudar status
- `services/bling_import_service.py` - Dispara notificação ao importar
- `routers/contatos_notificacao.py` - Interface web de gerenciamento
- `models.py` - Modelo `ContatoNotificacao` e enum `TipoNotificacao`

---

## 🎯 RESUMO TÉCNICO

**Arquitetura:**
```
Bling Import/Status Change
    ↓
PropostaService._atualizar_status()
    ↓
WhatsAppService.enviar_notificacao_mudanca_status()
    ↓
HTTP POST → BotConversa Webhook
    ↓
WhatsApp User 📱
```

**Stack:**
- BotConversa Webhook (POST)
- SQLAlchemy (PostgreSQL)
- FastAPI
- Python requests

---

**Última atualização:** 27/01/2026
**Status:** ✅ Funcionando em produção

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
