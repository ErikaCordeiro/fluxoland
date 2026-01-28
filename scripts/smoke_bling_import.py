from __future__ import annotations

import sys
import time
import os
import logging
from pathlib import Path

# Quando executado como arquivo em `scripts/`, o sys.path[0] aponta para `scripts/`.
# Inclui a raiz do projeto para permitir imports como `services.*`.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Por padrão, não queremos o `echo=True` do SQLAlchemy no smoke-test.
# Isso é controlado pelo env `DEBUG` em `database.py`.
# Para reativar SQL verboso, rode com `SMOKE_VERBOSE_SQL=1`.
if os.getenv("SMOKE_VERBOSE_SQL") != "1":
    os.environ.setdefault("DEBUG", "false")

from database import SessionLocal
from models import (
    Cliente,
    Produto,
    Proposta,
    PropostaHistorico,
    PropostaOrigem,
    PropostaProduto,
    PropostaStatus,
    Simulacao,
    TipoSimulacao,
)
from services.bling_import_service import BlingImportService


def _configure_logging() -> None:
    """Reduz ruído de logs (especialmente SQLAlchemy) no smoke-test.

    Para reativar logs verbosos (debug), rode com `SMOKE_VERBOSE_SQL=1`.
    """

    if os.getenv("SMOKE_VERBOSE_SQL") == "1":
        return

    for logger_name in [
        "sqlalchemy.engine",
        "sqlalchemy.engine.Engine",
        "sqlalchemy.orm",
        "sqlalchemy.pool",
    ]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def _print_result(prefix: str, proposta: Proposta) -> None:
    status = proposta.status.value if proposta.status else None
    print(
        f"{prefix}: id={proposta.id} status={status} cubagem_m3={proposta.cubagem_m3} "
        f"peso_total_kg={proposta.peso_total_kg} simulacao={bool(proposta.simulacao)}"
    )


def main() -> int:
    _configure_logging()

    # Nunca enviar WhatsApp em smoke-test.
    os.environ.setdefault("DISABLE_WHATSAPP_NOTIFICATIONS", "1")

    vendedor_id = 1

    # Smoke tests devem ser determinísticos e não depender de integração externa.
    # Vamos criar uma proposta de referência no DB e validar:
    # (1) Import com referência => vai para pendente_cotacao com simulação
    # (2) Import sem referência e sem medidas => fica pendente_simulacao
    run_id = int(time.time())
    smoke_cliente_nome = f"SMOKE CLIENTE {run_id}"
    ref_bling_id = f"smoke_ref_{run_id}"
    import_bling_id = f"smoke_import_{run_id}"
    no_ref_bling_id = f"smoke_noref_{run_id}"
    sku_a = f"SMOKE_A_{run_id}"
    sku_b = f"SMOKE_B_{run_id}"
    sku_sem_medida = f"SMOKE_SEM_MEDIDA_{run_id}"

    with SessionLocal() as db:
        print("[1] Setup reference proposal (manual) …")

        cliente = Cliente(nome=smoke_cliente_nome)
        db.add(cliente)
        db.flush()

        prod_a = Produto(sku=sku_a, nome="Produto A Smoke")
        prod_b = Produto(sku=sku_b, nome="Produto B Smoke")
        db.add(prod_a)
        db.add(prod_b)
        db.flush()

        proposta_ref = Proposta(
            origem=PropostaOrigem.bling,
            id_bling=ref_bling_id,
            cliente_id=cliente.id,
            vendedor_id=vendedor_id,
            observacao_importacao="smoke reference",
            status=PropostaStatus.pendente_cotacao,
        )
        db.add(proposta_ref)
        db.flush()

        db.add(
            PropostaProduto(
                proposta_id=proposta_ref.id,
                produto_id=prod_a.id,
                quantidade=2,
                codigo=sku_a,
                preco_unitario=0,
                preco_total=0,
            )
        )
        db.add(
            PropostaProduto(
                proposta_id=proposta_ref.id,
                produto_id=prod_b.id,
                quantidade=1,
                codigo=sku_b,
                preco_unitario=0,
                preco_total=0,
            )
        )
        db.flush()

        # Simulação MANUAL de referência (automatica=False). O importador deve copiá-la como automatica=True.
        sim_ref = Simulacao(
            proposta_id=proposta_ref.id,
            tipo=TipoSimulacao.manual,
            descricao="SMOKE SIMULACAO MANUAL",
            automatica=False,
        )
        db.add(sim_ref)

        # Campos de cálculo na referência (não obrigatórios para manual, mas úteis para score).
        proposta_ref.cubagem_m3 = 0.1234
        proposta_ref.peso_total_kg = 12.34
        proposta_ref.cubagem_ajustada = False

        db.commit()

        print("[1] Import using reference …")
        proposta1 = BlingImportService.importar_proposta_bling(
            db=db,
            id_bling=import_bling_id,
            cliente={"nome": smoke_cliente_nome},
            itens=[
                {"sku": sku_a, "codigo": sku_a, "nome": "Produto A Smoke", "quantidade": 2, "preco_unitario": 0, "preco_total": 0},
                {"sku": sku_b, "codigo": sku_b, "nome": "Produto B Smoke", "quantidade": 1, "preco_unitario": 0, "preco_total": 0},
            ],
            vendedor_id=vendedor_id,
            observacao="Smoke test import with reference",
            pedido=None,
        )
        db.refresh(proposta1)
        _print_result("REF", proposta1)
        if proposta1.status != PropostaStatus.pendente_cotacao:
            raise SystemExit(
                f"Falhou: esperado pendente_cotacao, veio {proposta1.status} (proposta id={proposta1.id})"
            )
        if not proposta1.simulacao:
            raise SystemExit("Falhou: esperado simulacao copiada da referência")

        print("[2] Import without reference (no measures) …")
        proposta2 = BlingImportService.importar_proposta_bling(
            db=db,
            id_bling=no_ref_bling_id,
            cliente={"nome": smoke_cliente_nome},
            itens=[
                {
                    "sku": sku_sem_medida,
                    "codigo": sku_sem_medida,
                    "nome": "Produto Sem Medida",
                    "quantidade": 1,
                    "preco_unitario": 0,
                    "preco_total": 0,
                    "ncm": None,
                    "imagem_url": None,
                }
            ],
            vendedor_id=vendedor_id,
            observacao="Smoke test import no ref",
            pedido=None,
        )
        db.refresh(proposta2)
        _print_result("NOREF", proposta2)
        if proposta2.status != PropostaStatus.pendente_simulacao:
            raise SystemExit(
                f"Falhou: esperado pendente_simulacao, veio {proposta2.status} (proposta id={proposta2.id})"
            )

        print("[3] Cleanup …")
        # Apaga histórico (se houver), simulações, itens e propostas criadas.
        propostas_ids = [proposta_ref.id, proposta1.id, proposta2.id]

        db.query(PropostaHistorico).filter(PropostaHistorico.proposta_id.in_(propostas_ids)).delete(synchronize_session=False)
        db.query(Simulacao).filter(Simulacao.proposta_id.in_(propostas_ids)).delete(synchronize_session=False)
        db.query(PropostaProduto).filter(PropostaProduto.proposta_id.in_(propostas_ids)).delete(synchronize_session=False)
        db.query(Proposta).filter(Proposta.id.in_(propostas_ids)).delete(synchronize_session=False)

        db.query(Produto).filter(Produto.sku.in_([sku_a, sku_b, sku_sem_medida])).delete(synchronize_session=False)
        db.query(Cliente).filter(Cliente.id == cliente.id).delete(synchronize_session=False)

        db.commit()

    print("Smoke tests OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
