from __future__ import annotations

import sys
from pathlib import Path

# Quando executado como arquivo em `scripts/`, o sys.path[0] aponta para `scripts/`.
# Inclui a raiz do projeto para permitir imports como `services.*`.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.bling_parser_service import BlingParserService


def main() -> int:
    link = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "https://www.bling.com.br/doc.view.php?id=92acc6310a523720f1eaf98dd56644ff"
    )

    data = BlingParserService.parse_doc_view(link)
    print("id_bling:", data.get("id_bling"))
    print("pedido:", data.get("pedido"))
    itens = data.get("itens") or []
    print("itens:", len(itens))
    for it in itens:
        print(
            "- codigo=", it.get("codigo"),
            " sku=", it.get("sku"),
            " qtd=", it.get("quantidade"),
            " nome=", (it.get("nome") or "")[:80],
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
