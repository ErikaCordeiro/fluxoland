from __future__ import annotations

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from database import SessionLocal
from models import Produto, Proposta
from services.calculo_service import CalculoService

SKU = "AM202"
BLING_ID = "92acc6310a523720f1eaf98dd56644ff"

PESO_UNITARIO_KG = 18.0
COMPRIMENTO_CM = 95.0
LARGURA_CM = 98.0
ALTURA_CM = 120.0


def main() -> None:
    with SessionLocal() as db:
        produto = db.query(Produto).filter(Produto.sku == SKU).first()
        if not produto:
            raise SystemExit(f"Produto {SKU} não encontrado")

        produto.peso_unitario_kg = PESO_UNITARIO_KG
        produto.comprimento_cm = COMPRIMENTO_CM
        produto.largura_cm = LARGURA_CM
        produto.altura_cm = ALTURA_CM
        db.commit()

        proposta = db.query(Proposta).filter(Proposta.id_bling == BLING_ID).first()
        if not proposta:
            print("Produto atualizado. Proposta não encontrada para recalcular.")
            return

        CalculoService.calcular_proposta(db, proposta)
        db.refresh(proposta)
        print(
            "Proposta atualizada:",
            proposta.id,
            "peso_total_kg=",
            proposta.peso_total_kg,
            "cubagem_m3=",
            proposta.cubagem_m3,
        )


if __name__ == "__main__":
    main()
