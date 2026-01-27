# FluxoLand 🚀

Sistema de gestão de propostas comerciais com integração Bling, simulação de volumes, cotação de frete e **notificações automáticas via WhatsApp**.

## 📋 Funcionalidades

### ✅ Gestão de Propostas
- **Kanban de propostas** com 3 colunas: Simulação → Cotação → Envio
- **Importação automática** do Bling via link do documento
- **Cálculo automático** de valores com desconto
- **Timestamp de atualização** em tempo real ("Atualizado há X minutos")
- **Histórico completo** de alterações

### 📦 Simulação de Volumes
- **Simulação por caixas**: selecione caixas pré-cadastradas
- **Simulação manual**: dimensões e pesos personalizados
- **Cálculo automático** de cubagem em m³
- **Resumo detalhado**: quantidade, peso total e cubagem

### 🚚 Cotação de Frete
- **Múltiplas transportadoras** por proposta
- **Número de cotação** para rastreamento
- **Prazo e valor** de cada transportadora
- **Resumo formatado** para envio ao cliente

### 📱 Notificações WhatsApp (NOVO!)
- **Notificação automática** ao importar proposta do Bling
- **3 tipos de notificação**: Simulação, Cotação e Envio
- **Múltiplos contatos** por tipo de notificação
- **Integração BotConversa** via webhook
- **Interface web** para gerenciar contatos
- 📖 [Guia completo de configuração](WHATSAPP_GUIA_RAPIDO.md)

### 🔗 Integração Bling
- Importação de dados completos do pedido
- Extração de valores financeiros (itens, desconto, frete)
- Sincronização de produtos e clientes
- Atualização automática de propostas existentes

## 🛠️ Tecnologias

- **Backend**: FastAPI (Python)
- **Banco de dados**: PostgreSQL + SQLAlchemy
- **Templates**: Jinja2
- **Frontend**: HTML5, CSS3, JavaScript
- **Parsing**: BeautifulSoup4
- **WhatsApp**: BotConversa API

## 🚀 Como Rodar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente
Crie um arquivo `.env` na raiz:
```env
SESSION_SECRET_KEY=seu-secret-key-aqui
WHATSAPP_BOT_CONVERSA_TOKEN=seu-token-botconversa
DATABASE_URL=postgresql://usuario:senha@localhost:5432/fluxoland
```

### 3. Criar banco de dados
```bash
python create_tables.py
```

### 4. Criar usuário administrador
```bash
python create_admin.py
```

### 5. Rodar aplicação
```bash
python main.py
```

Acesse: http://127.0.0.1:8000

## 📁 Estrutura do Projeto

```
fluxoland/
├── main.py                 # Aplicação FastAPI
├── models.py              # Modelos SQLAlchemy
├── database.py            # Configuração do banco
├── auth.py                # Autenticação
├── dependencies.py        # Dependências FastAPI
├── routers/              # Rotas da aplicação
│   ├── propostas.py      # CRUD de propostas
│   ├── bling_import.py   # Importação Bling
│   ├── caixas.py         # Gestão de caixas
│   ├── transportadoras.py
│   └── simulacoes.py
├── services/             # Lógica de negócio
│   ├── proposta_service.py
│   ├── bling_parser_service.py
│   ├── bling_import_service.py
│   ├── simulacao_volumes_service.py
│   ├── cotacao_frete_service.py
│   └── calculo_service.py
├── integrations/         # Integrações externas
│   └── bling/
├── templates/            # Templates Jinja2
├── static/              # CSS, JS, imagens
├── migrations/          # Scripts de migração
└── utils/              # Funções auxiliares
```

## 🔄 Fluxo de Trabalho

1. **Importar proposta** do Bling (link do documento)
2. **Fazer simulação** de volumes (caixas ou manual)
3. **Cotar frete** com transportadoras
4. **Enviar proposta** ao cliente
5. **Acompanhar** pelo kanban

## 🗃️ Migrações Disponíveis

As migrações executadas incluem:
- `add_desconto_propostas.py` - Campo de desconto
- `add_numero_cotacao.py` - Número de cotação
- `add_atualizado_em.py` - Timestamp de atualização
- `add_simulacao_automatica.py` - Flag de simulação automática

Para executar uma migração:
```bash
python migrations/nome_da_migracao.py
```

## 📊 Modelos Principais

- **Proposta**: Pedido/orçamento principal
- **Cliente**: Dados do cliente
- **PropostaProduto**: Itens da proposta
- **Simulacao**: Simulação de volumes (manual ou por caixas)
- **CotacaoFrete**: Cotações de transportadoras
- **Caixa**: Caixas cadastradas para simulação
- **Transportadora**: Transportadoras disponíveis

## 🎨 Funcionalidades da Interface

- Kanban drag-free com 3 colunas
- Filtros por cliente e vendedor
- Visualização em tempo real dos timestamps
- Formulários intuitivos para simulação
- Resumo completo para envio ao cliente
- Histórico de alterações

## 📝 Regras de Negócio

- **Valor Total**: Soma dos itens - desconto (frete separado)
- **Cubagem**: Calculada em m³ (volume_cm³ ÷ 1.000.000)
- **Status**: pendente_simulacao → pendente_cotacao → pendente_envio → concluida
- **Timestamp**: Atualizado automaticamente em qualquer modificação

## 🔐 Autenticação

- Sistema de login com sessão
- Dois níveis: líder e usuário
- Senha com hash bcrypt
- Proteção de rotas por dependências

## 🤝 Suporte

Para documentação detalhada, consulte `DOCUMENTACAO_FLUXOLAND.md`

---

**Desenvolvido para AM Ferramentas** | Versão 1.0
