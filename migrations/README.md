# Migrations

Scripts para atualizar o esquema do banco de dados em produção.

## Como executar migrations no Render

1. Acesse o dashboard do Render
2. Vá no seu Web Service
3. Clique em "Shell" (no menu lateral)
4. Execute o comando:

Exemplo executando um script SQL (no shell do Render):

```bash
psql "$DATABASE_URL" -f migrations/add_dashboard_and_whatsapp.sql
```

Se preferir, você também pode executar checagens/migrations simples via:

```bash
python auto_migrate.py
```

## Migrations disponíveis

- `add_dashboard_and_whatsapp.sql`
- `add_responsavel_vendedor.sql`
- `add_tiponotificacao_envio.sql`
