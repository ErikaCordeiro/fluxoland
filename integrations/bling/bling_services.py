from integrations.bling.bling_client import bling_get


def _first_item(payload: dict | None):
    if not payload:
        return None
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, list) and data:
            return data[0]
        if isinstance(data, dict):
            return data
        if "pedido" in payload and isinstance(payload.get("pedido"), dict):
            return payload.get("pedido")
    return None


def _mapear_cliente_api(contato: dict | None) -> dict | None:
    if not contato:
        return None
    if "data" in contato and isinstance(contato.get("data"), dict):
        contato = contato.get("data")

    nome = contato.get("nome") or contato.get("razaoSocial") or contato.get("nomeFantasia")
    documento = contato.get("cpfCnpj") or contato.get("cnpj") or contato.get("cpf")
    email = contato.get("email")
    telefone = contato.get("telefone") or contato.get("fone") or contato.get("celular")

    endereco = contato.get("endereco") or contato.get("rua")
    numero = contato.get("numero")
    bairro = contato.get("bairro")
    cidade = contato.get("cidade")
    uf = contato.get("uf")
    cep = contato.get("cep")

    endereco_parts = [p for p in [endereco, numero, bairro] if p]
    endereco_full = ", ".join(endereco_parts) if endereco_parts else None
    cidade_full = " / ".join([p for p in [cidade, uf] if p]) if (cidade or uf) else None

    return {
        "nome": nome,
        "documento": documento,
        "endereco": endereco_full,
        "cidade": cidade_full,
        "telefone": telefone,
        "email": email,
        "cep": cep,
    }


def _normalize_pedido_payload(payload: dict | None) -> dict | None:
    if not payload or not isinstance(payload, dict):
        return None
    if isinstance(payload.get("data"), dict):
        return payload.get("data")
    if isinstance(payload.get("pedido"), dict):
        return payload.get("pedido")
    return payload


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        value = str(value)
    v = value.strip()
    if not v:
        return None
    try:
        return float(v.replace("R$", "").replace(".", "").replace(",", ".").strip())
    except ValueError:
        return None


def _to_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if not isinstance(value, str):
        value = str(value)
    v = value.strip()
    if not v:
        return None
    try:
        return int(float(v.replace(".", "").replace(",", ".")))
    except ValueError:
        return None


def buscar_pedido_venda_por_numero(numero: str | None) -> dict | None:
    if not numero:
        return None
    for params in ({"numero": numero}, {"numero_loja": numero}):
        try:
            payload = bling_get("/pedidos/vendas", params=params)
            pedido = _first_item(payload)
            if pedido:
                return pedido
        except Exception:
            continue
    return None


def buscar_pedido_venda_por_id(pedido_id: int | str | None) -> dict | None:
    if not pedido_id:
        return None
    try:
        payload = bling_get(f"/pedidos/vendas/{pedido_id}")
        return _normalize_pedido_payload(payload)
    except Exception:
        return None


def buscar_contato_por_id(contato_id: int | str | None) -> dict | None:
    if not contato_id:
        return None
    try:
        return bling_get(f"/contatos/{contato_id}")
    except Exception:
        return None


def buscar_cliente_completo_por_pedido_numero(numero: str | None) -> dict | None:
    pedido = buscar_pedido_venda_por_numero(numero)
    if not pedido:
        return None

    contato = pedido.get("contato") if isinstance(pedido, dict) else None
    contato_id = None
    if isinstance(contato, dict):
        contato_id = contato.get("id") or contato.get("idContato")

    contato_api = buscar_contato_por_id(contato_id) if contato_id else None
    if contato_api:
        return _mapear_cliente_api(contato_api)

    if isinstance(contato, dict):
        return _mapear_cliente_api(contato)

    return None


def buscar_pedido_venda_completo(numero: str | None) -> dict | None:
    pedido = buscar_pedido_venda_por_numero(numero)
    if not pedido:
        return None

    pedido_id = None
    if isinstance(pedido, dict):
        pedido_id = pedido.get("id") or pedido.get("idPedido") or pedido.get("pedidoId")

    if pedido_id:
        pedido_completo = buscar_pedido_venda_por_id(pedido_id)
        if pedido_completo:
            return pedido_completo

    return pedido


def _extrair_itens_pedido(pedido: dict) -> list[dict]:
    raw_items = (
        pedido.get("itens")
        or pedido.get("itensPedido")
        or pedido.get("itensPedidoVenda")
        or pedido.get("itensVenda")
    )

    if isinstance(raw_items, dict):
        raw_items = raw_items.get("data") or raw_items.get("itens") or raw_items.get("items")

    if not isinstance(raw_items, list):
        return []

    itens: list[dict] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue

        produto = item.get("produto") if isinstance(item.get("produto"), dict) else {}
        nome = (
            item.get("descricao")
            or produto.get("descricao")
            or produto.get("nome")
            or item.get("nome")
        )
        if not nome:
            continue

        codigo = produto.get("codigo") or item.get("codigo") or item.get("sku")
        sku = item.get("sku") or codigo
        ncm = produto.get("ncm") or item.get("ncm")

        quantidade = (
            item.get("quantidade")
            or item.get("qtde")
            or item.get("quantidadeVendida")
        )
        quantidade_int = _to_int(quantidade) or 1

        preco_unitario = (
            item.get("valor")
            or item.get("valorUnitario")
            or item.get("preco")
        )
        preco_unitario = _to_float(preco_unitario)

        preco_total = (
            item.get("valorTotal")
            or item.get("valor_total")
        )
        preco_total = _to_float(preco_total)
        if preco_total is None and preco_unitario is not None:
            preco_total = preco_unitario * quantidade_int

        itens.append(
            {
                "nome": str(nome).strip(),
                "sku": str(sku).strip() if sku else None,
                "codigo": str(codigo).strip() if codigo else None,
                "ncm": str(ncm).strip() if ncm else None,
                "quantidade": quantidade_int,
                "preco_unitario": preco_unitario,
                "preco_total": preco_total,
            }
        )

    return itens


def mapear_pedido_para_importacao(pedido_payload: dict | None) -> dict | None:
    pedido = _normalize_pedido_payload(pedido_payload)
    if not pedido:
        return None

    pedido_id = pedido.get("id") or pedido.get("idPedido") or pedido.get("pedidoId")
    numero = pedido.get("numero") or pedido.get("numero_loja") or pedido.get("numeroLoja")

    vendedor = pedido.get("vendedor")
    if isinstance(vendedor, dict):
        vendedor_nome = vendedor.get("nome") or vendedor.get("name")
    else:
        vendedor_nome = vendedor

    desconto = (
        pedido.get("desconto")
        or pedido.get("descontoTotal")
        or pedido.get("valorDesconto")
    )
    desconto = _to_float(desconto)

    contato = pedido.get("contato") or pedido.get("cliente")
    cliente = _mapear_cliente_api(contato) if isinstance(contato, dict) else None

    return {
        "id_bling": pedido_id or numero,
        "pedido": {
            "numero": numero,
            "vendedor": vendedor_nome,
            "desconto": desconto,
        },
        "cliente": cliente,
        "itens": _extrair_itens_pedido(pedido),
    }


def listar_clientes():
    return bling_get("/contatos")


def listar_propostas():
    return bling_get("/pedidos/vendas")

