# 📋 DOCUMENTAÇÃO TÉCNICA - FLUXOLAND

**Sistema de Gestão de Propostas e Cotações de Frete**  
**AM Ferramentas**  
**Versão 1.0**  
**Data:** Janeiro 2026

---

## 📌 SUMÁRIO

1. [Visão Geral](#visão-geral)
2. [Funcionalidades Principais](#funcionalidades-principais)
3. [Arquitetura do Sistema](#arquitetura-do-sistema)
4. [Fluxo de Trabalho](#fluxo-de-trabalho)
5. [Guia de Uso](#guia-de-uso)
6. [Integrações](#integrações)
7. [Configuração e Deploy](#configuração-e-deploy)
8. [Manutenção](#manutenção)
9. [Segurança](#segurança)
10. [Futuras Melhorias](#futuras-melhorias)

---

## 📖 VISÃO GERAL

### O que é o FluxoLand?

O **FluxoLand** é um sistema web desenvolvido especificamente para a AM Ferramentas para gerenciar todo o processo de cotação e envio de propostas comerciais, desde a importação do pedido até o rastreamento do envio.

### Objetivo

Automatizar e centralizar o fluxo de trabalho de propostas comerciais, integrando-se ao sistema ERP Bling e facilitando a cotação de frete com múltiplas transportadoras.

### Benefícios

- ✅ **Redução de tempo** no processo de cotação
- ✅ **Centralização** de todas as propostas em um único lugar
- ✅ **Rastreabilidade** completa do histórico de cada proposta
- ✅ **Integração automática** com o Bling ERP
- ✅ **Simulação inteligente** de volumes com reaproveitamento de dados
- ✅ **Interface visual** tipo Kanban para acompanhamento

---

## ⚙️ FUNCIONALIDADES PRINCIPAIS

### 1. Gestão de Propostas

**Workflow Completo:**
- Criação manual ou importação automática do Bling
- Gestão de status (Simulação → Cotação → Envio → Concluída)
- Histórico completo de todas as alterações
- Visualização em formato Kanban

**Estados de Proposta:**
- `Pendente Simulação` - Aguardando cálculo de volumes
- `Pendente Cotação` - Aguardando consulta de frete
- `Pendente Envio` - Aguardando finalização
- `Concluída` - Proposta finalizada
- `Cancelada` - Proposta cancelada

### 2. Importação do Bling

**Processo Automático:**
- Extração de dados via link do pedido Bling
- Identificação de propostas duplicadas
- Importação de dados do cliente e produtos
- Extração automática do vendedor
- Manutenção do número do pedido Bling

**Recursos Inteligentes:**
- Reimportação de propostas canceladas/concluídas
- Atualização automática de dados modificados no Bling
- Cópia automática de simulações de propostas idênticas anteriores
- Auto-simulação se produtos já possuem medidas cadastradas

### 3. Simulação de Volumes

**Tipos de Simulação:**

**Manual:**
- Preenchimento direto de altura, largura, comprimento e peso
- Cálculo automático de cubagem total
- Geração de descrição detalhada

**Observação (Simulação manual por texto):**
- O sistema consegue interpretar dimensões dentro do texto e recalcular cubagem automaticamente.
- Exemplos aceitos: `95x95x120`, `4x95x95x1,20` e `(4x)95x95x1,20` (valores `<= 10` são tratados como metros).
- O peso pode ser informado como `peso: 52,18` / `peso=52,18` ou em múltiplas ocorrências `17,3kg` (o sistema soma).
- Quando a proposta já está em **Cotação**, existe um botão para **recalcular cubagem/peso do texto** sem voltar o status.

**Por Volumes (Inteligente):**
- Seleção de caixas pré-cadastradas
- Distribuição automática de produtos nas caixas
- Cálculo de cubagem considerando fator de empilhamento
- Salvamento automático de medidas nos produtos para reuso futuro

**Recursos Avançados:**
- Ajuste manual de cubagem quando necessário
- Validação de produtos com/sem medidas
- Histórico de simulações salvas
- Reaproveitamento de simulações de propostas idênticas

### 4. Cotação de Frete

**Processo:**
- Consulta simultânea em múltiplas transportadoras
- Comparação de preços e prazos
- Seleção da melhor opção
- Registro da cotação escolhida

**Informações Registradas:**
- Nome da transportadora
- Valor do frete
- Prazo de entrega
- Data da cotação

### 5. Envio e Rastreamento

**Finalização:**
- Registro de código de rastreamento
- Observações sobre o envio
- Marcação de data de envio
- Transição automática para status "Concluída"

### 6. Histórico Completo

**Rastreamento de Alterações:**
- Registro de todas as mudanças de status
- Data/hora de cada alteração
- Observações de cada etapa
- Visualização cronológica ordenada

### 7. Gestão de Caixas

**Cadastro de Embalagens:**
- Nome/descrição da caixa
- Dimensões (altura, largura, comprimento)
- Peso da caixa vazia
- Peso máximo suportado
- Gestão completa (criar, editar, excluir)

### 8. Gestão de Transportadoras

**Cadastro:**
- Nome da transportadora
- Informações de contato
- Gestão completa (criar, editar, excluir)

### 9. Gestão de Simulações Salvas

**Repositório Inteligente:**
- Visualização de todas as simulações salvas
- Edição de descrições
- Exclusão de simulações obsoletas
- Busca e filtros
- Vinculação com propostas que as utilizam

---

## 🏗️ ARQUITETURA DO SISTEMA

### Stack Tecnológica

**Backend:**
- **Python 3.13**
- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para banco de dados
- **SQLite** - Banco de dados (produção deve migrar para PostgreSQL)
- **Uvicorn** - Servidor ASGI

**Frontend:**
- **Jinja2** - Templates HTML
- **JavaScript Vanilla** - Interatividade
- **CSS Puro** - Estilização

**Integrações:**
- **BeautifulSoup4** - Parser HTML do Bling
- **Requests** - Cliente HTTP
- **Passlib + Bcrypt** - Hash de senhas

**Deploy:**
- **Render.com** - Plataforma de hospedagem
- **GitHub** - Controle de versão

### Estrutura de Diretórios

```
fluxoland/
├── routers/              # Endpoints da API
│   ├── propostas.py      # Rotas de propostas
│   ├── bling_import.py   # Importação do Bling
│   ├── transportadoras.py
│   ├── caixas.py
│   └── simulacoes.py
├── services/             # Lógica de negócio
│   ├── proposta_service.py
│   ├── bling_import_service.py
│   ├── bling_parser_service.py
│   ├── simulacao_volumes_service.py
│   ├── cotacao_frete_service.py
│   └── envio_service.py
├── integrations/         # Integrações externas
│   └── bling/
├── templates/            # Templates HTML
├── static/               # CSS e JavaScript
│   ├── css/
│   └── js/
├── models.py             # Modelos do banco de dados
├── database.py           # Configuração do banco
├── auth.py               # Autenticação
├── dependencies.py       # Dependências FastAPI
└── main.py               # Ponto de entrada
```

### Banco de Dados

**Principais Tabelas:**

1. **users** - Usuários do sistema
2. **clientes** - Clientes das propostas
3. **produtos** - Catálogo de produtos (com medidas)
4. **propostas** - Propostas comerciais
5. **proposta_produtos** - Itens de cada proposta
6. **simulacoes** - Simulações de volumes salvas
7. **proposta_historico** - Histórico de alterações
8. **cotacoes_frete** - Cotações realizadas
9. **envios_proposta** - Dados de rastreamento
10. **caixas** - Embalagens cadastradas
11. **transportadoras** - Transportadoras cadastradas

**Relacionamentos Principais:**
- Proposta → Cliente (N:1)
- Proposta → PropostaProduto (1:N)
- PropostaProduto → Produto (N:1)
- Proposta → Simulacao (1:1, opcional)
- Proposta → CotacaoFrete (1:N)
- Proposta → EnvioProposta (1:1, opcional)

---

## 🔄 FLUXO DE TRABALHO

### Fluxo Padrão de uma Proposta

```
1. IMPORTAÇÃO/CRIAÇÃO
   ↓
   [Bling] → Sistema cria proposta com status "Pendente Simulação"
   OU
   [Manual] → Usuário cria proposta manualmente
   
2. SIMULAÇÃO
   ↓
   Opção A: Sistema copia simulação de proposta idêntica anterior
   Opção B: Sistema auto-simula se produtos têm medidas
   Opção C: Usuário simula manualmente ou por volumes
   ↓
   Status muda para "Pendente Cotação"
   
3. COTAÇÃO
   ↓
   Usuário consulta transportadoras
   ↓
   Sistema registra cotações
   ↓
   Usuário seleciona melhor opção
   ↓
   Status muda para "Pendente Envio"
   
4. ENVIO
   ↓
   Usuário registra código de rastreamento
   ↓
   Status muda para "Concluída"
```

### Fluxo de Importação do Bling

```
1. Usuário acessa pedido no Bling
2. Copia link do pedido
3. Cola no campo de importação do FluxoLand
4. Sistema extrai:
   - Dados do cliente
   - Lista de produtos
   - Vendedor responsável
   - Número do pedido
5. Sistema verifica:
   - Proposta já existe? → Reimporta e atualiza
   - Existe proposta idêntica anterior? → Copia simulação
   - Produtos têm medidas? → Auto-simula
6. Proposta criada/atualizada
```

### Fluxo de Simulação Inteligente

```
1. Sistema detecta novos produtos na proposta
2. Verifica se produtos têm medidas cadastradas
3. SE tem medidas:
   - Calcula volume unitário de cada produto
   - Multiplica por quantidade
   - Soma volumes
   - Cria simulação automática
   - Avança para "Pendente Cotação"
4. SE não tem medidas:
   - Aguarda simulação manual
```

---

## 📱 GUIA DE USO

### Login

1. Acesse: `https://fluxoland-api.onrender.com`
2. Digite email: `sac@amferramentas.com.br`
3. Digite senha: `AmF123`
4. Clique em "Entrar"

### Importar Proposta do Bling

1. Acesse o pedido no Bling
2. Copie o link completo da barra de endereço
3. No FluxoLand, clique em "Importar do Bling" (menu superior)
4. Cole o link no campo
5. Clique em "Importar"
6. Aguarde confirmação

### Simular Volumes Manualmente

1. Acesse a proposta em "Pendente Simulação"
2. Clique em "Simular"
3. Escolha "Simulação Manual"
4. Preencha altura, largura, comprimento e peso
5. Digite descrição (opcional)
6. Clique em "Salvar Simulação"

### Simular com Caixas

1. Acesse a proposta em "Pendente Simulação"
2. Clique em "Simular"
3. Escolha "Simulação por Volumes"
4. Para cada produto:
   - Selecione a caixa adequada
   - Informe quantidade de caixas
5. Clique em "Calcular e Salvar"

### Cotar Frete

1. Acesse proposta em "Pendente Cotação"
2. Clique em "Cotar Frete"
3. Consulte transportadoras
4. Compare preços e prazos
5. Registre a cotação escolhida
6. Clique em "Salvar Cotação"

### Finalizar Envio

1. Acesse proposta em "Pendente Envio"
2. Clique em "Registrar Envio"
3. Digite código de rastreamento
4. Adicione observações (opcional)
5. Clique em "Finalizar"

### Gerenciar Caixas

1. Clique em "Caixas" no menu
2. Para adicionar:
   - Clique em "Nova Caixa"
   - Preencha dados
   - Salve
3. Para editar: clique no ícone de edição
4. Para excluir: clique no ícone de lixeira

### Visualizar Histórico

1. Acesse qualquer proposta
2. Role até "Histórico de Alterações"
3. Visualize todas as mudanças cronologicamente

---

## 🔗 INTEGRAÇÕES

### Bling ERP

**Tipo:** Web Scraping  
**Método:** Parsing de HTML

**Dados Extraídos:**
- Número do pedido
- Nome do cliente
- Email do cliente
- Telefone do cliente
- Endereço completo
- Lista de produtos (SKU, descrição, quantidade)
- Vendedor responsável

**Limitações:**
- Depende da estrutura HTML do Bling (pode quebrar se mudarem)
- Não é API oficial
- Requer acesso ao link do pedido

**Como Funciona:**
1. Usuário fornece link do pedido
2. Sistema faz requisição HTTP
3. BeautifulSoup faz parsing do HTML
4. Extrai dados via seletores CSS
5. Valida e normaliza dados
6. Cria/atualiza proposta no banco

---

## 🚀 CONFIGURAÇÃO E DEPLOY

### Ambiente Local

**Requisitos:**
- Python 3.13+
- Git

**Instalação:**

```bash
# 1. Clonar repositório
git clone https://github.com/ErikaCordeiro/fluxoland.git
cd fluxoland

# 2. Criar ambiente virtual
python -m venv venv

# 3. Ativar ambiente (Windows)
venv\Scripts\activate

# 4. Instalar dependências
pip install -r requirements.txt

# 5. Configurar variáveis de ambiente
# Criar arquivo .env com:
SESSION_SECRET_KEY=sua-chave-secreta

# 6. Executar
python main.py
```

**Acesso Local:**
`http://127.0.0.1:8000`

### Deploy no Render

**Plataforma:** Render.com  
**Plano:** Free (com limitações)

**Configuração Automática:**
- Blueprint: `render.yaml` já configurado
- Auto-deploy: Push no GitHub dispara deploy automático
- Variáveis de ambiente: Geradas automaticamente

**Limitações do Plano Free:**
- Serviço "dorme" após inatividade (delay de 50s no primeiro acesso)
- Disco efêmero (dados do SQLite podem ser perdidos em reinicializações)
- 750 horas/mês de runtime

**URL Produção:**
`https://fluxoland-api.onrender.com`

**Recomendação para Produção:**
Migrar para PostgreSQL para persistência de dados.

---

## 🔧 MANUTENÇÃO

### Usuário Admin Padrão

**Criação Automática:**
- Email: `sac@amferramentas.com.br`
- Senha: `AmF123`
- Criado automaticamente se não existir nenhum usuário

**Como Alterar:**
- Editar código em `main.py` (linhas 30-50)
- Fazer commit e push

### Atualizar Código

```bash
# 1. Fazer alterações no código
# 2. Testar localmente
python main.py

# 3. Commit e push
git add .
git commit -m "Descrição das alterações"
git push

# 4. Render faz deploy automático
```

### Backup de Dados

**SQLite (Atual):**
- Baixar arquivo `fluxoland.db` quando possível
- **ATENÇÃO:** Plano Free pode perder dados

**Recomendação:**
- Migrar para PostgreSQL no Render
- Configurar backups automáticos

### Logs e Monitoramento

**Acessar Logs:**
1. Dashboard do Render
2. Serviço "fluxoland-api"
3. Menu "Logs"

**Logs Importantes:**
- Criação de usuário admin
- Erros de importação do Bling
- Falhas de autenticação

---

## 🔒 SEGURANÇA

### Autenticação

**Tipo:** Session-based  
**Armazenamento:** Cookie HTTP-only  
**Senhas:** Hash com bcrypt (4.1.2)

**Recursos:**
- Senhas nunca armazenadas em texto plano
- Truncamento automático para limite do bcrypt (72 caracteres)
- Sessions expiram ao fechar navegador

### Autorização

**Roles:**
- `lider` - Acesso completo
- Futuro: roles adicionais conforme necessário

**Proteção de Rotas:**
- Middleware de sessão em todas as rotas
- Dependências FastAPI para validação
- Redirecionamento automático para login

### Boas Práticas Implementadas

✅ Senhas com hash bcrypt  
✅ Sessions seguras  
✅ Validação de entrada em formulários  
✅ Escape automático de HTML (Jinja2)  
✅ Commits de transação explícitos  
✅ Tratamento de exceções  

### Melhorias de Segurança Recomendadas

⚠️ HTTPS obrigatório (Render já fornece)  
⚠️ Rate limiting para login  
⚠️ Log de tentativas de acesso  
⚠️ Senha mais forte para produção  
⚠️ 2FA (autenticação de dois fatores)  

---

## 📊 FUTURAS MELHORIAS

### 🔴 ALTA PRIORIDADE

**1. Migração para PostgreSQL**
- **Motivo:** Persistência de dados em produção
- **Benefício:** Dados seguros mesmo com reinicializações
- **Estimativa:** 4-8 horas
- **Status:** 🔴 Pendente

**2. Gestão de Usuários**
- **Funcionalidade:** CRUD completo de usuários
- **Recursos:** Criar, editar, desativar usuários
- **Roles:** Implementar diferentes níveis de acesso
- **Estimativa:** 6-10 horas
- **Status:** 🔴 Pendente

**3. Dashboard Analítico**
- **Métricas:** Total de propostas, conversão, valores
- **Gráficos:** Evolução temporal, distribuição de status
- **Filtros:** Por período, vendedor, status
- **Estimativa:** 8-12 horas
- **Status:** 🔴 Pendente

---

### 🟡 MÉDIA PRIORIDADE

**4. Exportação para PDF/Excel**
- **Propostas:** Geração de PDF formatado
- **Relatórios:** Export Excel com filtros
- **Templates:** Personalizáveis
- **Estimativa:** 6-8 horas
- **Status:** 🟡 Pendente

**5. Notificações por Email**
- **Eventos:** Nova proposta, mudança de status
- **Destinatários:** Vendedor, gerente
- **Templates:** HTML responsivos
- **Estimativa:** 8-10 horas
- **Status:** 🟡 Pendente

**6. API do Bling (Oficial)**
- **Substituir:** Web scraping por API oficial
- **Benefícios:** Mais estável e confiável
- **Documentação:** https://developer.bling.com.br
- **Estimativa:** 10-16 horas
- **Status:** 🟡 Pendente

**7. Busca Avançada**
- **Filtros:** Múltiplos critérios simultâneos
- **Campos:** Cliente, vendedor, período, valor
- **Salvamento:** Filtros favoritos
- **Estimativa:** 4-6 horas
- **Status:** 🟡 Pendente

**8. Cálculo Automático de Frete (API Transportadoras)**
- **Integração:** Correios, Jadlog, etc.
- **Comparação:** Automática de valores
- **Seleção:** Interface para escolha
- **Estimativa:** 12-20 horas
- **Status:** 🟡 Pendente

---

### 🟢 BAIXA PRIORIDADE

**9. App Mobile**
- **Plataforma:** Progressive Web App (PWA)
- **Funcionalidades:** Visualização e aprovações
- **Offline:** Suporte básico
- **Estimativa:** 20-30 horas
- **Status:** 🟢 Pendente

**10. Chatbot de Suporte**
- **IA:** Respostas automáticas
- **Integração:** WhatsApp Business
- **Contexto:** Base de conhecimento
- **Estimativa:** 15-25 horas
- **Status:** 🟢 Pendente

**11. Múltiplos Idiomas (i18n)**
- **Idiomas:** PT-BR, EN, ES
- **Interface:** Completa traduzida
- **Datas/Moedas:** Formatação localizada
- **Estimativa:** 8-12 horas
- **Status:** 🟢 Pendente

**12. Tema Escuro**
- **Interface:** Dark mode completo
- **Persistência:** Preferência do usuário
- **Toggle:** Botão de alternância
- **Estimativa:** 3-5 horas
- **Status:** 🟢 Pendente

---

### 💡 IDEIAS FUTURAS (A VALIDAR)

**13. Integração com CRM**
- Sincronização bidirecional com CRMs populares
- Histórico de interações com cliente

**14. Assinatura Digital**
- Aprovação de propostas com assinatura digital
- Validade jurídica

**15. Workflow Customizável**
- Usuário define etapas personalizadas
- Automações customizadas

**16. Machine Learning para Precificação**
- Sugestão automática de margens
- Análise de histórico de vendas

**17. Integrações Contábeis**
- Export para sistemas contábeis
- Conciliação automática

**18. Portal do Cliente**
- Cliente acompanha proposta online
- Aprovação self-service

---

## 📝 NOTAS ADICIONAIS

### Convenções de Código

- **Python:** PEP 8
- **Nomes:** snake_case para funções/variáveis, PascalCase para classes
- **Commits:** Mensagens descritivas em português
- **Branches:** `main` para produção

### Contatos e Suporte

**Desenvolvedor:** Erika Cordeiro  
**Email:** erikagcordeiro18@gmail.com  
**Repositório:** https://github.com/ErikaCordeiro/fluxoland

### Changelog

**v1.0 - Janeiro 2026**
- ✅ Sistema inicial completo
- ✅ Importação do Bling
- ✅ Simulação de volumes
- ✅ Gestão de propostas Kanban
- ✅ Histórico completo
- ✅ Deploy em produção

---

**Documento gerado em:** Janeiro 2026  
**Última atualização:** 16/01/2026  
**Versão do documento:** 1.0

---

## 📋 ESPAÇO PARA ANOTAÇÕES E MELHORIAS FUTURAS

_(Use este espaço para documentar melhorias conforme forem sendo implementadas ou ideias que surgirem)_

---

### Melhoria #_____

**Data:** ___/___/______  
**Título:** _________________________________________  
**Descrição:**  
________________________________________________________________  
________________________________________________________________  
________________________________________________________________  
________________________________________________________________  

**Implementado por:** _____________________________  
**Status:** ⬜ Planejado | ⬜ Em Desenvolvimento | ⬜ Concluído  

---

### Melhoria #_____

**Data:** ___/___/______  
**Título:** _________________________________________  
**Descrição:**  
________________________________________________________________  
________________________________________________________________  
________________________________________________________________  
________________________________________________________________  

**Implementado por:** _____________________________  
**Status:** ⬜ Planejado | ⬜ Em Desenvolvimento | ⬜ Concluído  

---

### Melhoria #_____

**Data:** ___/___/______  
**Título:** _________________________________________  
**Descrição:**  
________________________________________________________________  
________________________________________________________________  
________________________________________________________________  
________________________________________________________________  

**Implementado por:** _____________________________  
**Status:** ⬜ Planejado | ⬜ Em Desenvolvimento | ⬜ Concluído  

---

### Melhoria #_____

**Data:** ___/___/______  
**Título:** _________________________________________  
**Descrição:**  
________________________________________________________________  
________________________________________________________________  
________________________________________________________________  
________________________________________________________________  

**Implementado por:** _____________________________  
**Status:** ⬜ Planejado | ⬜ Em Desenvolvimento | ⬜ Concluído  

---

### Melhoria #_____

**Data:** ___/___/______  
**Título:** _________________________________________  
**Descrição:**  
________________________________________________________________  
________________________________________________________________  
________________________________________________________________  
________________________________________________________________  

**Implementado por:** _____________________________  
**Status:** ⬜ Planejado | ⬜ Em Desenvolvimento | ⬜ Concluído  

---

**FIM DO DOCUMENTO**
