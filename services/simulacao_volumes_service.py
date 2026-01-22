# services/simulacao_volumes_service.py

from sqlalchemy.orm import Session

from models import (
    Proposta,
    Simulacao,
    TipoSimulacao,
    PropostaStatus,
    Caixa,
)

from services.proposta_service import PropostaService


class SimulacaoVolumesService:
    """
    Responsável por calcular simulação por volumes (caixas)
    e salvar a simulação estruturada no banco.
    """

    @staticmethod
    def simular_por_volumes(
        db: Session,
        proposta: Proposta,
        caixas_payload: list[dict],
    ) -> Simulacao:
        """
        caixas_payload = [
            {"caixa_id": 1, "quantidade": 2},
            {"caixa_id": 3, "quantidade": 1},
        ]
        """

        if not caixas_payload:
            raise ValueError("Nenhuma caixa informada para simulação")

        # --------------------------------------------------
        # 0. REMOVE SIMULAÇÃO ANTERIOR (SE EXISTIR)
        # --------------------------------------------------
        if proposta.simulacao:
            db.delete(proposta.simulacao)
            db.flush()

        volume_total_cm3 = 0.0
        descricao_linhas: list[str] = []
        quantidade_total_volumes = 0

        # --------------------------------------------------
        # 1. PROCESSA CAIXAS
        # --------------------------------------------------
        for item in caixas_payload:
            try:
                caixa_id = int(item.get("caixa_id"))
                quantidade = int(item.get("quantidade", 0))
            except (TypeError, ValueError):
                continue

            if quantidade <= 0:
                continue

            caixa = db.get(Caixa, caixa_id)
            if not caixa:
                continue

            volume_unitario_cm3 = caixa.volume_cm3
            volume_total_cm3 += volume_unitario_cm3 * quantidade
            quantidade_total_volumes += quantidade

            descricao_linhas.append(
                f"{quantidade}x {caixa.nome} "
                f"({caixa.comprimento_cm}x{caixa.largura_cm}x{caixa.altura_cm} cm)"
            )

        if volume_total_cm3 <= 0:
            raise ValueError("Volume total inválido para simulação")

        # --------------------------------------------------
        # 2. CONVERTE PARA M³
        # --------------------------------------------------
        volume_total_m3 = volume_total_cm3 / 1_000_000

        # --------------------------------------------------
        # 3. SALVA SIMULAÇÃO
        # --------------------------------------------------
        simulacao = Simulacao(
            proposta_id=proposta.id,
            tipo=TipoSimulacao.volumes,
            descricao="\n".join(descricao_linhas),
        )

        db.add(simulacao)
        db.flush()

        # --------------------------------------------------
        # 4. ATUALIZA PROPOSTA
        # --------------------------------------------------
        proposta.cubagem_m3 = round(volume_total_m3, 4)
        proposta.cubagem_ajustada = False

        PropostaService._atualizar_status(
            db=db,
            proposta=proposta,
            novo_status=PropostaStatus.pendente_cotacao,
            observacao="Simulação por volumes realizada",
        )

        db.commit()
        db.refresh(simulacao)

        return simulacao
