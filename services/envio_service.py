from sqlalchemy.orm import Session
from datetime import datetime

from models import (
    Proposta,
    EnvioProposta,
    PropostaStatus,
)

from services.proposta_service import PropostaService


class EnvioService:
    """
    Service responsável pela ETAPA FINAL – ENVIO AO CLIENTE
    """

    @staticmethod
    def registrar_envio(
        db: Session,
        proposta: Proposta,
        resumo_envio: str,
        meio_envio: str,
        link_bling: str,
    ) -> EnvioProposta:
        """
        Registra o envio da proposta ao cliente e finaliza o fluxo.
        """

        if not proposta:
            raise ValueError("Proposta inválida para envio")

        envio = proposta.envio

        # --------------------------------------------------
        # CRIA REGISTRO DE ENVIO (SE NÃO EXISTIR)
        # --------------------------------------------------
        if not envio:
            envio = EnvioProposta(
                proposta_id=proposta.id,
            )
            db.add(envio)
            db.flush()

        # --------------------------------------------------
        # ATUALIZA DADOS DO ENVIO
        # --------------------------------------------------
        envio.resumo_envio = (
            f"{resumo_envio}\n\nLink Bling: {link_bling}"
        )
        envio.meio_envio = meio_envio
        envio.enviado = True
        envio.enviado_em = datetime.utcnow()

        # --------------------------------------------------
        # ATUALIZA STATUS DA PROPOSTA
        # --------------------------------------------------
        PropostaService._atualizar_status(
            db=db,
            proposta=proposta,
            novo_status=PropostaStatus.concluida,
            observacao="Proposta enviada ao cliente",
        )

        db.commit()
        db.refresh(envio)

        return envio
