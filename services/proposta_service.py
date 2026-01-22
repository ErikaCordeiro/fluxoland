# services/proposta_service.py

from datetime import datetime
from sqlalchemy.orm import Session

from models import (
    Proposta,
    PropostaStatus,
    PropostaHistorico,
    Simulacao,
    TipoSimulacao,
    EnvioProposta,
)


class PropostaService:
    """
    Service central da Proposta.
    Toda regra de negócio DEVE ficar aqui.
    """

    # ======================================================
    # CRIAÇÃO BÁSICA (manual / MVP)
    # ======================================================
    @staticmethod
    def criar_proposta_manual(
        db: Session,
        cliente_nome: str,
        vendedor_id: int,
        valor_total: float = 0,
    ) -> Proposta:
        proposta = Proposta(
            cliente_nome=cliente_nome,
            vendedor_id=vendedor_id,
            valor_total=valor_total,
            status=PropostaStatus.pendente_simulacao,
        )

        db.add(proposta)
        db.commit()
        db.refresh(proposta)

        PropostaService._registrar_historico(
            db,
            proposta,
            PropostaStatus.pendente_simulacao,
            "Proposta criada manualmente",
        )

        return proposta

    # ======================================================
    # SIMULAÇÃO (GALPÃO)
    # ======================================================
    @staticmethod
    def salvar_simulacao(
        db: Session,
        proposta: Proposta,
        tipo: TipoSimulacao,
        descricao: str = "",
    ):
        simulacao = proposta.simulacao

        if not simulacao:
            simulacao = Simulacao(proposta=proposta)
            db.add(simulacao)

        simulacao.tipo = tipo
        simulacao.descricao = descricao
        
        # Atualiza timestamp
        proposta.atualizado_em = datetime.utcnow()

        # 🔥 REGRA AUTOMÁTICA DE STATUS
        novo_status = PropostaService.definir_status_automatico(proposta)

        PropostaService._atualizar_status(
            db,
            proposta,
            novo_status,
            "Simulação registrada",
        )

    # ======================================================
    # REGRA CENTRAL DE STATUS
    # ======================================================
    @staticmethod
    def definir_status_automatico(proposta: Proposta) -> PropostaStatus:
        """
        REGRA ATUAL (sem Produto ainda):

        - Se NÃO existe simulação → pendente_simulacao
        - Se existe simulação → pendente_cotacao

        🔮 Futuro:
        - Quando Produto existir:
            - Se todos produtos tiverem medidas → pendente_cotacao
            - Se algum não tiver → pendente_simulacao
        """
        if not proposta.simulacao:
            return PropostaStatus.pendente_simulacao

        return PropostaStatus.pendente_cotacao

    # ======================================================
    # FINALIZA COTAÇÃO
    # ======================================================
    @staticmethod
    def finalizar_cotacao(db: Session, proposta: Proposta):
        proposta.atualizado_em = datetime.utcnow()
        PropostaService._atualizar_status(
            db,
            proposta,
            PropostaStatus.pendente_envio,
            "Cotação finalizada",
        )

    # ======================================================
    # ENVIO AO CLIENTE
    # ======================================================
    @staticmethod
    def registrar_envio(
        db: Session,
        proposta: Proposta,
        resumo_envio: str,
        meio_envio: str,
    ):
        envio = proposta.envio

        if not envio:
            envio = EnvioProposta(proposta=proposta)
            db.add(envio)

        envio.resumo_envio = resumo_envio
        envio.meio_envio = meio_envio
        envio.enviado = True
        envio.enviado_em = datetime.utcnow()
        
        proposta.atualizado_em = datetime.utcnow()

        PropostaService._atualizar_status(
            db,
            proposta,
            PropostaStatus.concluida,
            f"Enviado via {meio_envio}",
        )

    # ======================================================
    # STATUS + HISTÓRICO
    # ======================================================
    @staticmethod
    def _atualizar_status(
        db: Session,
        proposta: Proposta,
        novo_status: PropostaStatus,
        observacao: str = "",
    ):
        if proposta.status == novo_status:
            return

        proposta.status = novo_status
        proposta.atualizado_em = datetime.utcnow()

        PropostaService._registrar_historico(
            db,
            proposta,
            novo_status,
            observacao,
        )

        db.commit()

    @staticmethod
    def _registrar_historico(
        db: Session,
        proposta: Proposta,
        status: PropostaStatus,
        observacao: str = "",
    ):
        historico = PropostaHistorico(
            proposta_id=proposta.id,
            status=status,
            observacao=observacao,
        )
        db.add(historico)
