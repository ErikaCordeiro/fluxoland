  # FluxoLand

Sistema de gestão de propostas e cotações de frete para AM Ferramentas.

## Funcionalidades

- 📋 Gestão de propostas com workflow Kanban
- 🔄 Importação automática do Bling ERP
- 📦 Simulação de volumes e cálculo de cubagem
- 💰 Cotação de frete com múltiplas transportadoras
- 📊 Histórico completo de alterações
- 👥 Gestão de usuários e permissões

## Tecnologias

- **Backend:** FastAPI + SQLAlchemy
- **Frontend:** Jinja2 Templates + JavaScript
- **Banco de Dados:** SQLite
- **Autenticação:** Session-based com bcrypt

## Instalação Local

1. Clone o repositório:
```bash
git clone <seu-repositorio>
cd fluxoland
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

5. Configure as variáveis de ambiente:
Crie um arquivo `.env` na raiz do projeto:
```
SESSION_SECRET_KEY=sua-chave-secreta-aqui
```

6. Crie um usuário administrador:
```bash
python create_admin.py
```

7. Execute o servidor:
```bash
python main.py
```

O sistema estará disponível em `http://127.0.0.1:8000`

## Deploy no Render

1. Faça push do código para o GitHub
2. Conecte seu repositório no Render
3. O arquivo `render.yaml` já está configurado
4. Após o deploy, crie um usuário admin via shell do Render

## Estrutura do Projeto

```
fluxoland/
├── routers/           # Endpoints da API
├── services/          # Lógica de negócio
├── models.py          # Modelos do banco de dados
├── templates/         # Templates HTML
├── static/            # CSS e JavaScript
├── integrations/      # Integrações externas (Bling)
└── main.py            # Ponto de entrada
```

## Workflow de Propostas

1. **Simulação:** Importar do Bling ou criar manual → calcular cubagem
2. **Cotação:** Consultar transportadoras → escolher melhor opção
3. **Envio:** Finalizar proposta → gerar rastreamento

## Licença

Uso interno - AM Ferramentas
