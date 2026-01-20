# Copilot / Agentes: instruções específicas do projeto FluxoLand

Objetivo: fornecer contexto sucinto para agentes automatizados entenderem rapidamente arquitetura, padrões e comandos de desenvolvedor neste repositório.

- **Visão geral:** aplicação web FastAPI pequena que usa SQLAlchemy (PostgreSQL), templates Jinja2 e rotas organizadas em `routers/` e lógica de domínio em `services/`.

- **Como rodar localmente (desenvolvimento):**
  - executar `python main.py` (o bloco `if __name__ == "__main__"` já roda `uvicorn` com `reload=True`).
  - alternativa: `uvicorn main:app --reload --host 127.0.0.1 --port 8000`.
  - DB é PostgreSQL (configurado via `DATABASE_URL` no `.env`) e tabelas são criadas automaticamente por `Base.metadata.create_all(bind=engine)` em `main.py`.

- **Config e segredos:** variáveis via `.env` (carregadas por `python-dotenv` em `main.py` / `database.py`). A sessão usa `SESSION_SECRET_KEY` (ver `main.py`).

- **Padrões arquiteturais e fluxo de dados:**
  - Rotas HTTP definidas em `routers/` (ex.: `routers/bling_import.py`) que delegam processamento para `services/` (ex.: `services/bling_import_service.py`).
  - Camada de persistência: `database.py` fornece `SessionLocal`, `get_db()` (dependência FastAPI) e `Base`.
  - Models com regras/hints ficam em `models.py` (Enums para status e origem, métodos híbridos para cálculos como `valor_total`).
  - Serviços manipulam transações explicitamente: usam `db.add()`, `db.flush()`, `db.commit()` e `db.refresh()` conforme necessário (ver `services/bling_import_service.py`).

- **Exemplos concretos a considerar ao modificar código:**
  - Importação do Bling: `routers/bling_import.py` extrai `id` da query e chama `BlingImportService.importar_proposta_bling(...)` (serviço aplica regras de negócio e cria cliente/proposta/itens).
  - Estados de proposta: use os Enums em `models.py` (`PropostaStatus`, `PropostaOrigem`) em vez de strings literais.
  - Evitar duplicidade: muitos serviços primeiro checam existência por campos específicos (ex.: `Proposta.id_bling`) antes de criar.

- **Conveniências e convenções do projeto:**
  - Uso de endpoints que retornam `RedirectResponse` para flows pós-form (ver `auth.py`, `routers/*`).
  - Templates Jinja2 em `templates/`; estática em `static/` (montada em `/static`).
  - Senhas: passlib com `bcrypt` (`auth.py`); ver `get_password_hash` e `verify_password`.
  - Arquitetura simples: controllers (routers) → services → models/DB.

- **Arquivos úteis para desenvolvedores/agents:**
  - inicialização e servidor: `main.py`
  - DB/ORM: `database.py`, `models.py`
  - autenticação: `auth.py`, `create_admin.py` (para criar usuário inicial)
  - integrações: `integrations/bling/*` e `services/bling_import_service.py`
  - regras de negócio principais: `services/proposta_service.py`, `services/calculo_service.py`, `services/cotacao_frete_service.py`

- **Práticas observáveis (faça isto):**
  - Reutilize as Enums de `models.py` para consistência.
  - Preserve transações e chamadas a `db.flush()` quando o código atual as usa para garantir `id`s antes de relacionamentos.
  - Rotas protegidas usam dependências (ex.: `dependencies.get_current_user_api`) — mantenha esse padrão.

- **O que NÃO assumir:**
  - Não há migrations (Alembic) configuradas; alterações de esquema podem exigir remoção manual do arquivo `fluxoland.db` em desenvolvimento.
  - Não há suite de testes automatizados visível; antes de modificar modelos, verifique o impacto manualmente.

- **Checks rápidos que um agente pode executar automaticamente:**
  1. Confirmar que `requirements.txt` lista dependências (ex.: `fastapi`, `uvicorn`, `sqlalchemy`, `psycopg2-binary`).
  2. Validar se `DATABASE_URL` está corretamente configurado no `.env` antes de rodar operações destrutivas.
  3. Procurar usos diretos de strings para status/origem e sugerir substituição por Enums.

Se algo neste resumo estiver incompleto ou se você quer que eu enfatize outro aspecto (ex.: devops, testes, ou integração com Bling), diga qual seção quer detalhar.

## Comandos úteis e snippets

- **Rodar em desenvolvimento:**

```bash
# modo 1 (script principal que já chama uvicorn)
python main.py

# modo 2 (uvicorn direto, recarregamento em dev)
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

- **Criar usuário admin (interativo):**

```bash
python create_admin.py
# segue prompts: Nome, Email, Senha
```

- **Criar apenas as tabelas (sem rodar a app):**

```bash
python create_tables.py
```

- **Arquivo de configuração `.env`:**

  - O projeto usa `python-dotenv`. Valores observáveis:
    - `SESSION_SECRET_KEY` — secret para `SessionMiddleware` (veja `main.py`).
    - `DATABASE_URL` — URL de conexão do PostgreSQL (veja `database.py`).
  - Exemplo mínimo `.env`:

```
SESSION_SECRET_KEY=algum-segredo-local
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fluxoland
```

- **Exemplo de importação do Bling via HTTP (curl):**

```bash
curl -X POST \
  -F "link_bling=https://www.bling.com.br/doc.view.php?id=HASH" \
  http://127.0.0.1:8000/integracoes/bling/importar/
```

- **Verificações rápidas antes de rodar tarefas destrutivas:**
  - Confirme em `database.py` que `DATABASE_URL` aponta para o banco PostgreSQL correto.
  - Faça backup do banco de dados antes de executar scripts que alterem o esquema.

## Exemplos de padrões (rápido)

- `routers/*` → delegam para `services/*` (ex.: `routers/bling_import.py` → `services/bling_import_service.py`).
- Use os `Enum` de `models.py` (`PropostaStatus`, `PropostaOrigem`) em vez de strings literais.
- Serviços frequentemente usam `db.flush()` para garantir `id`s antes de criar relacionamentos (ver `services/bling_import_service.py`).

