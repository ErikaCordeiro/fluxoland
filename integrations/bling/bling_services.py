from integrations.bling.bling_client import bling_get


def listar_clientes():
    return bling_get("/contatos")


def listar_propostas():
    return bling_get("/pedidos/vendas")

