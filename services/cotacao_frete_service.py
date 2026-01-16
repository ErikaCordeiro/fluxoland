from sqlalchemy.orm import Session
from datetime import datetime

from models import (
    Proposta,
    CotacaoFrete,
    Transportadora,
    PropostaStatus,
)

from services.proposta_service import PropostaService


class CotacaoFreteService:
    """
    Service responsável pela ETAPA DE COTAÇÃO DE FRETE.

    Regras:
    - Só pode cotar se a proposta estiver em pendente_cotacao
    - Usa cubagem manual se existir, senão a automática
    - Após cotação, proposta vai para pendente_envio
    """

    @staticmethod
    def criar_cotacao(
        db: Session,
        proposta: Proposta,
        transportadora_id: int,
        preco: float,
        prazo_dias: int,
    ) -> CotacaoFrete:
        # --------------------------------------------------
        # 1. VALIDAÇÕES
        # --------------------------------------------------
        transportadora = db.get(Transportadora, transportadora_id)
        if not transportadora:
            raise ValueError("Transportadora não encontrada")

        if proposta.status != PropostaStatus.pendente_cotacao:
            raise ValueError("Proposta não está pronta para cotação")

        # --------------------------------------------------
        # 2. DEFINE CUBAGEM UTILIZADA
        # --------------------------------------------------
        cubagem_utilizada = proposta.cubagem_final_m3()

        if not cubagem_utilizada or cubagem_utilizada <= 0:
            raise ValueError("Cubagem não definida para a proposta")

        # --------------------------------------------------
        # 3. DESMARCA COTAÇÃO ANTERIOR (SE EXISTIR)
        # --------------------------------------------------
        for c in proposta.cotacoes:
            c.selecionada = False

        # --------------------------------------------------
        # 4. CRIA NOVA COTAÇÃO
        # --------------------------------------------------
        cotacao = CotacaoFrete(
            proposta_id=proposta.id,
            transportadora_id=transportadora.id,
            preco=float(preco),
            prazo_dias=int(prazo_dias),
            selecionada=True,
            criado_em=datetime.utcnow(),
        )

        db.add(cotacao)

        # --------------------------------------------------
        # 5. ATUALIZA STATUS DA PROPOSTA
        # --------------------------------------------------
        PropostaService._atualizar_status(
            db=db,
            proposta=proposta,
            novo_status=PropostaStatus.pendente_envio,
            observacao="Frete cotado e transportadora definida",
        )

        db.commit()
        db.refresh(cotacao)

        return cotacao
