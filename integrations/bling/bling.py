from fastapi import APIRouter, HTTPException

from integrations.bling.bling_services import (
    listar_clientes,
    listar_propostas,
)

router = APIRouter(
    prefix="/integracoes/bling",
    tags=["Bling"]
)


@router.get("/status")
def status():
    return {"status": "OK", "mensagem": "Router do Bling está funcionando"}


@router.get("/clientes")
def clientes():
    try:
        return listar_clientes()
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/propostas")
def propostas():
    try:
        return listar_propostas()
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
