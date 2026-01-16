# Copilot / Agentes: instruções específicas do projeto FluxoLand

**Objetivo:** Contexto sucinto para agentes entenderem rapidamente arquitetura, padrões, fluxos de dados e convenções específicas do FluxoLand.

## Visão Geral da Arquitetura

**Stack:** FastAPI + SQLAlchemy (SQLite local) + Jinja2 templates + Session middleware para autenticação.

**Fluxo canônico:** HTTP Router → Service (regra de negócio) → ORM Model → DB.

**Exemplo fim-a-fim:** `routers/bling_import.py` recebe link do Bling → `BlingParserService` extrai dados → `BlingImportService.importar_proposta_bling()` cria Cliente/Proposta/PropostaProduto com status `pendente_simulacao` → redireciona para `/propostas`.

## Modelos e Estados de Proposta

**Domínio central:** `Proposta` representa uma cotação que passa por estados: `pendente_simulacao` → `pendente_cotacao` → `pendente_envio` → `concluida`|`cancelada`.

**Enums críticos (sempre use, nunca strings):**
- `PropostaStatus`: pendente_simulacao, pendente_cotacao, pendente_envio, concluida, cancelada
- `PropostaOrigem`: manual, BLING
- `PropostaHistorico` registra cada mudança de status com observação

**Relacionamentos principais:**
- `Proposta → Cliente` (N:1): muitas propostas por cliente
- `Proposta → PropostaProduto` (1:N): itens com quantidade, preço_unitario, preco_total
- `PropostaProduto → Produto` (N:1): referência ao catálogo (sku, medidas para cálculo de volume)
- `Proposta → Simulacao` (1:1, opcional): tipo (manual|volumes) e descrição
- `Proposta → CotacaoFrete` (1:N): múltiplas cotações, uma selecionada
- `Proposta → EnvioProposta` (1:1, opcional): rastreamento de envio

**Métodos híbridos e propriedades:**
- `Proposta.valor_total`: hybrid_property que soma `preco_total` dos itens
- `Proposta.cubagem_final_m3()`: retorna cubagem ajustada se `cubagem_ajustada=True`, senão `cubagem_m3`
- `Proposta.todos_produtos_possuem_medidas()`: valida se itens têm altura, largura, comprimento, peso

## Serviços e Camada de Negócio

**Padrão:** Cada serviço é uma classe com métodos estáticos que recebem `db: Session`.

**Serviços principais:**
- `BlingImportService.importar_proposta_bling()`: cria proposta a partir de dados do Bling (valida duplicidade por `id_bling`)
- `PropostaService`: criação, mudança de status, histórico
- `SimulacaoVolumesService`: calcula cubagem a partir de produtos com medidas
- `CotacaoFreteService`: consulta transportadoras e cria cotações
- `EnvioService`: finaliza proposta com rastreamento

**Transações explícitas:** Serviços usam `db.add()`, `db.flush()` (garante IDs antes de relacionamentos), `db.commit()`, `db.refresh()` conforme necessário. **Não confie em autocommit.**

## Autenticação e Autorização

**Padrão session:** `request.session` armazena `user_id`, `user_nome`, `user_role` após login bem-sucedido.

**Dependências (em `dependencies.py`):**
- `get_current_user_html()`: para rotas que retornam templates; redireciona para /login se não autenticado
- `get_current_user_api()`: para endpoints JSON; lança HTTPException 401 se não autenticado
- `require_lider_html()`: valida role=lider
- Rotas protegidas usam `Depends(get_current_user_html)` ou `Depends(get_current_user_api)`

**Senhas:** bcrypt via `passlib.context.CryptContext` → `get_password_hash()` e `verify_password()` em `auth.py`.

## Desenvolvimento Local

**Executar:**
```bash
# Opção 1: script principal (já tem uvicorn dentro)
python main.py

# Opção 2: uvicorn direto
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Criar usuário admin:** `python create_admin.py` (interativo: nome, email, senha).

**Criar apenas tabelas:** `python create_tables.py` (sem rodar servidor).

**Limpar DB local:** `Remove-Item .\fluxoland.db -Force` (PowerShell) ou `rm ./fluxoland.db` (Bash).

**Config `.env`:**
```
SESSION_SECRET_KEY=algum-segredo-local
```

## Padrões Observados

1. **Routers** (em `routers/`) delegam a **Services** (em `services/`); Services manipulam DB e regras; Models definem esquema.
2. **RedirectResponse com HTTP 303** para flows pós-form: `RedirectResponse(url, status_code=HTTP_303_SEE_OTHER)`.
3. **Jinja2 templates** em `templates/`; arquivos estáticos em `static/` (montado em `/static`).
4. **ORM joinedload** para eager-loading de relacionamentos em queries (ex.: `joinedload(Proposta.cliente)`).
5. **Validação de duplicidade** antes de criar (ex.: checar `id_bling` já existe antes de importar).
6. **Histórico imutável:** `PropostaHistorico` registra cada mudança via `_registrar_historico()`.

## Arquivos-Chave

- `main.py`: inicialização, middlewares, routers
- `database.py`: engine, SessionLocal, Base, get_db()
- `models.py`: todas as tabelas e Enums
- `auth.py`, `dependencies.py`: autenticação e autorização
- `routers/{propostas,bling_import,transportadoras,caixas}.py`: endpoints HTTP
- `services/*.py`: lógica de domínio
- `integrations/bling/`: parsers e clients do Bling

## Limitações Conhecidas

- **Sem migrations (Alembic):** mudanças de esquema exigem remover `fluxoland.db` manualmente em dev.
- **Sem testes automatizados:** valide impacto manualmente antes de alterar modelos.
- **DB local:** SQLite apenas; `DATABASE_URL = "sqlite:///./fluxoland.db"` em `database.py`.



