from sqlalchemy.orm import Session
from datetime import datetime

from models import (
    Produto,
    Proposta,
    PropostaProduto,
    PropostaStatus,
)

from services.proposta_service import PropostaService


class GalpaoService:
    """
    Service responsável pelo FLUXO DO GALPÃO.

    Centraliza:
    - salvamento de medidas dos produtos (reutilizáveis)
    - cálculo de peso e cubagem da proposta
    - ajuste manual de cubagem
    - avanço automático de status
    """

    @staticmethod
    def salvar_simulacao_galpao(
        db: Session,
        proposta: Proposta,
        produtos_payload: list[dict],
        cubagem_manual_m3: float | None = None,
    ):
        """
        produtos_payload = [
            {
                "produto_id": 1,
                "comprimento": 50,
                "largura": 40,
                "altura": 30,
                "peso_unitario": 2.5
            }
        ]
        """

        peso_total = 0.0
        volume_total_cm3 = 0.0

        produto_sem_medida = False

        # --------------------------------------------------
        # PROCESSA PRODUTOS DA PROPOSTA
        # --------------------------------------------------
        for item in produtos_payload:
            produto = db.get(Produto, item.get("produto_id"))

            if not produto:
                produto_sem_medida = True
                continue

            # -----------------------------
            # ATUALIZA MEDIDAS DO PRODUTO
            # -----------------------------
            produto.comprimento_cm = item.get("comprimento")
            produto.largura_cm = item.get("largura")
            produto.altura_cm = item.get("altura")
            produto.peso_unitario_kg = item.get("peso_unitario")
            produto.data_atualizacao = datetime.utcnow()

            if not produto.possui_medidas_completas():
                produto_sem_medida = True

            # -----------------------------
            # ITEM NA PROPOSTA
            # -----------------------------
            proposta_item = (
                db.query(PropostaProduto)
                .filter(
                    PropostaProduto.proposta_id == proposta.id,
                    PropostaProduto.produto_id == produto.id,
                )
                .first()
            )

            if not proposta_item:
                produto_sem_medida = True
                continue

            quantidade = proposta_item.quantidade or 1

            # -----------------------------
            # CÁLCULOS
            # -----------------------------
            peso_total += (produto.peso_unitario_kg or 0) * quantidade

            volume_unitario_cm3 = (
                (produto.comprimento_cm or 0)
                * (produto.largura_cm or 0)
                * (produto.altura_cm or 0)
            )

            volume_total_cm3 += volume_unitario_cm3 * quantidade

        # --------------------------------------------------
        # SALVA TOTAIS NA PROPOSTA
        # --------------------------------------------------
        proposta.peso_total_kg = peso_total

        if volume_total_cm3 > 0:
            proposta.cubagem_m3 = volume_total_cm3 / 1_000_000
        else:
            proposta.cubagem_m3 = None

        # --------------------------------------------------
        # AJUSTE MANUAL DE CUBAGEM (GALPÃO)
        # --------------------------------------------------
        if cubagem_manual_m3 is not None:
            proposta.cubagem_manual_m3 = float(cubagem_manual_m3)
            proposta.cubagem_ajustada = True
        else:
            proposta.cubagem_manual_m3 = None
            proposta.cubagem_ajustada = False

        # --------------------------------------------------
        # REGRA AUTOMÁTICA DE STATUS
        # --------------------------------------------------
        novo_status = (
            PropostaStatus.pendente_simulacao
            if produto_sem_medida
            else PropostaStatus.pendente_cotacao
        )

        PropostaService._atualizar_status(
            db=db,
            proposta=proposta,
            novo_status=novo_status,
            observacao="Simulação logística realizada pelo galpão",
        )

        db.commit()
        db.refresh(proposta)

        return proposta
