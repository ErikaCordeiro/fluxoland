# Guia rápido: Notificações WhatsApp (BotConversa)

Este guia explica como habilitar e usar as notificações automáticas via WhatsApp no FluxoLand.

## O que o sistema faz

- Envia mensagens automaticamente quando uma proposta muda de status.
- Permite cadastrar contatos por tipo de notificação (Simulação, Cotação, Envio).
- Para **Envio**, o sistema notifica o **vendedor responsável** (telefone no usuário/proposta).

### Status x quem recebe

| Status da proposta | Tipo de notificação | Quem recebe |
|---|---|---|
| `PENDENTE_SIMULACAO` | `simulacao` | Contatos cadastrados como Simulação |
| `PENDENTE_COTACAO` | `cotacao` | Contatos cadastrados como Cotação |
| `PENDENTE_ENVIO` | `envio` | Vendedor responsável (`responsavel_telefone`) |

Obs.: em alguns fluxos de reimportação do Bling o sistema pode **forçar notificação** mesmo sem “mudança real” de status, para não perder alertas do kanban.

## Configuração

### 1) Criar webhook no BotConversa

1. Acesse https://app.botconversa.com.br/
2. Vá em **Webhooks** (ou Automations/Webhooks)
3. Crie um webhook para receber:
   - `phone` (telefone WhatsApp)
   - `text` (mensagem)
4. Copie o token/URL no formato semelhante a: `13954/eHmb0sGpjqpG`

### 2) Configurar `.env`

Adicione/ajuste:

```env
WHATSAPP_BOT_CONVERSA_TOKEN=13954/eHmb0sGpjqpG
```

### 3) Banco de dados

Em desenvolvimento, normalmente basta rodar:

```bash
python create_tables.py
```

Em produção, use as migrações do projeto (pasta `migrations/`) conforme seu fluxo.

### 4) Cadastrar contatos

Acesse a tela:

- `http://localhost:8000/contatos-notificacao`

Cadastre 1 ou mais contatos por tipo.

#### Formato do telefone

- Correto: `5547999999999` (55 + DDD + número)
- Evitar: `+55 47 99999-9999` (com símbolos/espaços)

## Fallback (Cotação → Simulação)

Se você **não tiver contatos cadastrados para Cotação**, o sistema usa automaticamente os contatos de **Simulação** como fallback.

Isso ajuda a não “sumir” notificação quando a equipe cadastrou apenas um grupo.

## Testes rápidos

1) Importe uma proposta do Bling
- Deve notificar Simulação

2) Conclua Simulação → vira Cotação
- Deve notificar Cotação (ou Simulação, se fallback ativar)

3) Finalize Cotação → vira Envio
- Deve notificar o vendedor responsável

## Arquivos relacionados

- `services/whatsapp_service.py`
- `routers/contatos_notificacao.py`
- `models.py` (model/enum de contatos)

**Última atualização:** 28/01/2026
