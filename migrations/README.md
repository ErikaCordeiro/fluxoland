# Migrations

Scripts para atualizar o esquema do banco de dados em produção.

## Como executar migrations no Render

1. Acesse o dashboard do Render
2. Vá no seu Web Service
3. Clique em "Shell" (no menu lateral)
4. Execute o comando:

```bash
python migrations/add_numero_cotacao.py
```

## Migrations disponíveis

- `add_numero_cotacao.py` - Adiciona coluna numero_cotacao na tabela cotacoes_frete
