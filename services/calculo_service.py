from sqlalchemy.orm import Session

from models import (
    Proposta,
    PropostaProduto,
    TipoSimulacao,
)

from utils.medidas import format_dimensoes_m


class CalculoService:
    """
    Service responsável por cálculos automáticos
    de peso e cubagem da proposta.
    """

    # ======================================================
    # CÁLCULO AUTOMÁTICO COMPLETO (PRODUTOS)
    # ======================================================
    @staticmethod
    def calcular_proposta(db: Session, proposta: Proposta):
        """
        Calcula automaticamente:
        - peso total (kg)
        - cubagem total (m³)
        com base nos produtos vinculados à proposta.
        """

        peso_total = 0.0
        volume_total_cm3 = 0.0

        produtos = (
            db.query(PropostaProduto)
            .filter(PropostaProduto.proposta_id == proposta.id)
            .all()
        )

        if not produtos:
            return

        descricao_linhas: list[str] = []

        for pp in produtos:
            produto = pp.produto
            qtd = pp.quantidade

            # -------------------------------
            # PESO
            # -------------------------------
            if produto.peso_unitario_kg:
                peso_total += produto.peso_unitario_kg * qtd

            # -------------------------------
            # CUBAGEM
            # -------------------------------
            if (
                produto.comprimento_cm
                and produto.largura_cm
                and produto.altura_cm
            ):
                volume_unitario = (
                    produto.comprimento_cm
                    * produto.largura_cm
                    * produto.altura_cm
                )
                volume_total_cm3 += volume_unitario * qtd

                # Monta descrição no mesmo padrão do BlingImportService
                nome = (produto.nome or "").strip() or (produto.sku or "Produto")
                descricao_linhas.append(
                    f"{qtd}x {nome} ({format_dimensoes_m(produto.comprimento_cm, produto.largura_cm, produto.altura_cm)} m)"
                )

        # -------------------------------
        # SALVA RESULTADOS
        # -------------------------------
        proposta.peso_total_kg = round(peso_total, 3)

        # converte cm³ para m³
        proposta.cubagem_m3 = round(volume_total_cm3 / 1_000_000, 6)

        proposta.cubagem_ajustada = False

        # Se existe simulação automática por volumes, mantém a descrição sincronizada
        # com as dimensões atuais dos produtos.
        if (
            getattr(proposta, "simulacao", None)
            and proposta.simulacao.automatica
            and proposta.simulacao.tipo == TipoSimulacao.volumes
            and descricao_linhas
        ):
            proposta.simulacao.descricao = "\n".join(descricao_linhas)

        db.commit()

    # ======================================================
    # AJUSTE MANUAL (GALPÃO)
    # ======================================================
    @staticmethod
    def ajuste_manual(
        db: Session,
        proposta: Proposta,
        cubagem_manual_m3: float | None = None,
        peso_total_kg: float | None = None,
    ):
        """
        Permite override manual feito pelo galpão.
        """

        if peso_total_kg is not None:
            proposta.peso_total_kg = peso_total_kg

        if cubagem_manual_m3 is not None:
            proposta.cubagem_manual_m3 = cubagem_manual_m3
            proposta.cubagem_ajustada = True

        db.commit()

    # ======================================================
    # VERIFICA SE PROPOSTA ESTÁ PRONTA PARA COTAÇÃO
    # ======================================================
    @staticmethod
    def proposta_pronta_para_cotacao(proposta: Proposta) -> bool:
        """
        Retorna True se a proposta já tem peso e cubagem
        suficientes para seguir para cotação.
        """

        return bool(
            proposta.peso_total_kg
            and proposta.cubagem_final_m3()
        )
