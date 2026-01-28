import logging
import os
from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from models import (
    Cliente,
    Produto,
    Proposta,
    PropostaProduto,
    PropostaStatus,
    PropostaOrigem,
    Simulacao,
    TipoSimulacao,
)

from services.proposta_service import PropostaService

from utils.medidas import format_dimensoes_m


DEBUG_ENV_VAR = "DEBUG_BLING_IMPORT"


VENDEDOR_TELEFONE_MAP: dict[str, str] = {
    "AMARILDO MONTIBELER": "5547991316330",
    "ANDERSON ADAMI": "5547992277405",
    "CARLOS HENRIQUE GUIMARAES DELUCHI": "5547991022964",
    "JOÃO PEDRO DE SOUZA": "5547992268504",
    "LUCAS DOGNINI SOARES": "5547991707963",
    "MARCOS LUIS DA CONCEIÇÃO": "554791917906",
    "RODRIGO BOAVENTURA": "5547991791978",
    "TARNIE RICARDO MONTIBELER": "5547991917907",
    "VICTOR HUGO DE MELLO": "5547991695494",
}


logger = logging.getLogger(__name__)


class BlingImportService:
    """
    Importa propostas vindas do Bling seguindo o fluxo do FluxoLand.

    REGRAS:
    - Toda proposta do Bling entra como PENDENTE_SIMULACAO
        - Só avança automaticamente para cotação quando existe proposta de referência
            com SKUs e quantidades iguais (ordem irrelevante)
    """

    @staticmethod
    def _debug(msg: str) -> None:
        if os.getenv(DEBUG_ENV_VAR, "").lower() in {"1", "true", "yes"}:
            logger.info(msg)

    @staticmethod
    def _mapear_itens_por_sku(itens: list[PropostaProduto] | None) -> dict[str, int]:
        produtos: dict[str, int] = {}
        for item in itens or []:
            if not item.produto or not item.produto.sku:
                continue
            sku = item.produto.sku.strip()
            if not sku:
                continue
            produtos[sku] = produtos.get(sku, 0) + int(item.quantidade or 0)
        return produtos

    @staticmethod
    def _score_referencia(candidata: Proposta) -> tuple:
        tem_peso = 1 if candidata.peso_total_kg else 0
        tem_cubagem_manual = 1 if candidata.cubagem_manual_m3 else 0
        tem_cubagem = 1 if candidata.cubagem_m3 else 0
        simulacao_manual = 1 if (candidata.simulacao and not candidata.simulacao.automatica) else 0
        return (
            tem_peso,
            tem_cubagem_manual,
            tem_cubagem,
            simulacao_manual,
            candidata.criado_em,
        )

    @staticmethod
    def _buscar_proposta_referencia(
        db: Session,
        *,
        proposta_id_excluir: int,
        produtos_importados: dict[str, int],
    ) -> Proposta | None:
        if not produtos_importados:
            return None

        candidatas = (
            db.query(Proposta)
            .options(
                joinedload(Proposta.simulacao),
                joinedload(Proposta.itens).joinedload(PropostaProduto.produto),
            )
            .filter(
                Proposta.id != proposta_id_excluir,
                Proposta.simulacao.has(),
                Proposta.status != PropostaStatus.pendente_simulacao,
            )
            .order_by(Proposta.criado_em.desc())
            .all()
        )

        iguais = [
            c
            for c in candidatas
            if BlingImportService._mapear_itens_por_sku(c.itens) == produtos_importados
        ]
        if not iguais:
            return None

        iguais.sort(key=BlingImportService._score_referencia, reverse=True)
        return iguais[0]

    @staticmethod
    def _substituir_simulacao(
        db: Session,
        *,
        proposta: Proposta,
        nova_simulacao: Simulacao | None,
    ) -> None:
        if getattr(proposta, "simulacao", None) is not None:
            db.delete(proposta.simulacao)
            db.flush()
        if nova_simulacao is not None:
            db.add(nova_simulacao)

    @staticmethod
    def _limpar_calculos(proposta: Proposta) -> None:
        proposta.cubagem_m3 = None
        proposta.cubagem_manual_m3 = None
        proposta.cubagem_ajustada = False
        proposta.peso_total_kg = None

    @staticmethod
    def _merge_cliente_fields(
        cliente_db: Cliente,
        cliente_data: dict,
        *,
        overwrite: bool = False,
    ) -> None:
        """Atualiza campos do cliente com valores do Bling.

        - overwrite=False (padrão): só preenche quando o campo no banco está vazio.
        - overwrite=True: se o Bling trouxer valor não-vazio e diferente, sobrescreve.
        """

        def _clean(v: object) -> str | None:
            if v is None:
                return None
            if isinstance(v, str):
                s = v.strip()
                return s or None
            s = str(v).strip()
            return s or None

        for field in ("documento", "endereco", "cidade", "telefone", "email"):
            new_value = _clean(cliente_data.get(field))
            if not new_value:
                continue
            current = _clean(getattr(cliente_db, field, None))
            if not current or (overwrite and current != new_value):
                setattr(cliente_db, field, new_value)

    @staticmethod
    def _aplicar_simulacao_de_referencia(
        db: Session,
        *,
        proposta_destino: Proposta,
        proposta_referencia: Proposta,
    ) -> str | None:
        """Tenta aplicar simulação usando uma proposta referência.

        Retorna a observação de histórico se conseguiu; caso contrário retorna None.
        """

        simulacao_ref = getattr(proposta_referencia, "simulacao", None)
        if not simulacao_ref:
            return None

        # 1) Se a referência é MANUAL, copia.
        if not simulacao_ref.automatica:
            nova_sim = Simulacao(
                proposta_id=proposta_destino.id,
                tipo=simulacao_ref.tipo,
                descricao=simulacao_ref.descricao,
                automatica=True,
            )
            BlingImportService._substituir_simulacao(db, proposta=proposta_destino, nova_simulacao=nova_sim)

            proposta_destino.cubagem_m3 = proposta_referencia.cubagem_m3
            proposta_destino.cubagem_manual_m3 = proposta_referencia.cubagem_manual_m3
            proposta_destino.cubagem_ajustada = proposta_referencia.cubagem_ajustada
            proposta_destino.peso_total_kg = proposta_referencia.peso_total_kg
            return (
                f"Simulação manual copiada da proposta #{proposta_referencia.id} "
                f"(mesmos produtos)"
            )

        # 2) Referência automática: tenta recalcular a partir das medidas atuais.
        peso_total_kg, cubagem_m3, descricao = BlingImportService._calcular_automatico_volumes(proposta_destino)
        if cubagem_m3 and descricao:
            nova_sim = Simulacao(
                proposta_id=proposta_destino.id,
                tipo=TipoSimulacao.volumes,
                descricao=descricao,
                automatica=True,
            )
            BlingImportService._substituir_simulacao(db, proposta=proposta_destino, nova_simulacao=nova_sim)
            proposta_destino.cubagem_m3 = cubagem_m3
            proposta_destino.cubagem_manual_m3 = None
            proposta_destino.cubagem_ajustada = False
            proposta_destino.peso_total_kg = peso_total_kg
            return (
                f"Simulação recalculada automaticamente (referência #{proposta_referencia.id} "
                f"ignorada por ser automática)"
            )

        # 3) Fallback: sem medidas suficientes. Copia a simulação automática se tiver pronta.
        if proposta_referencia.cubagem_m3 and simulacao_ref.descricao:
            nova_sim = Simulacao(
                proposta_id=proposta_destino.id,
                tipo=simulacao_ref.tipo,
                descricao=simulacao_ref.descricao,
                automatica=True,
            )
            BlingImportService._substituir_simulacao(db, proposta=proposta_destino, nova_simulacao=nova_sim)
            proposta_destino.cubagem_m3 = proposta_referencia.cubagem_m3
            proposta_destino.cubagem_manual_m3 = proposta_referencia.cubagem_manual_m3
            proposta_destino.cubagem_ajustada = proposta_referencia.cubagem_ajustada
            proposta_destino.peso_total_kg = proposta_referencia.peso_total_kg
            return (
                f"Simulação automática copiada da proposta #{proposta_referencia.id} "
                f"(itens/quantidades iguais; sem medidas para recalcular)"
            )

        return None

    @staticmethod
    def _montar_observacao_importacao(
        *,
        observacao: str | None,
        pedido: dict | None,
    ) -> tuple[str, str | None, str | None]:
        obs = (observacao or "").strip()
        vendedor_nome = None
        vendedor_telefone = None

        if pedido and pedido.get("numero"):
            obs = f"bling_numero:{pedido.get('numero')}; {obs}".strip()
        if pedido and pedido.get("vendedor"):
            vendedor_nome = str(pedido.get("vendedor") or "").strip() or None
            if vendedor_nome:
                obs = f"bling_vendedor:{vendedor_nome}; {obs}".strip()
                vendedor_telefone = VENDEDOR_TELEFONE_MAP.get(vendedor_nome.upper())

        return obs, vendedor_nome, vendedor_telefone

    @staticmethod
    def _calcular_automatico_volumes(
        proposta: Proposta,
    ) -> tuple[float | None, float | None, str]:
        """Calcula peso, cubagem e descrição no padrão 'QTDx Nome (dimensões m)'.

        Não faz commit; apenas retorna os valores calculados.
        """

        peso_total = 0.0
        cubagem_total_cm3 = 0.0
        descricao_linhas: list[str] = []

        for item_prop in (proposta.itens or []):
            produto = item_prop.produto
            if not produto:
                continue

            quantidade = int(item_prop.quantidade or 0)
            if quantidade <= 0:
                continue

            if produto.peso_unitario_kg is not None:
                peso_total += (produto.peso_unitario_kg or 0) * quantidade

            if (
                produto.comprimento_cm is not None
                and produto.largura_cm is not None
                and produto.altura_cm is not None
            ):
                volume_unitario = (
                    (produto.comprimento_cm or 0)
                    * (produto.largura_cm or 0)
                    * (produto.altura_cm or 0)
                )
                cubagem_total_cm3 += volume_unitario * quantidade

                descricao_linhas.append(
                    f"{quantidade}x {produto.nome} "
                    f"({format_dimensoes_m(produto.comprimento_cm, produto.largura_cm, produto.altura_cm)} m)"
                )

        peso_final = round(peso_total, 3) if peso_total > 0 else None
        cubagem_m3 = round(cubagem_total_cm3 / 1_000_000, 4) if cubagem_total_cm3 > 0 else None
        return peso_final, cubagem_m3, "\n".join(descricao_linhas)

    @staticmethod
    def _sincronizar_calculos_se_automatico_volumes(proposta: Proposta) -> None:
        """Mantém peso/cubagem/descrição consistentes quando a simulação é automática por volumes."""

        try:
            if not getattr(proposta, "simulacao", None):
                return
            if not proposta.simulacao.automatica:
                return
            if proposta.simulacao.tipo != TipoSimulacao.volumes:
                return
            if proposta.cubagem_ajustada:
                return

            peso_total_kg, cubagem_m3, descricao = BlingImportService._calcular_automatico_volumes(proposta)
            if peso_total_kg is not None:
                proposta.peso_total_kg = peso_total_kg
            if cubagem_m3 is not None:
                proposta.cubagem_m3 = cubagem_m3
            if descricao:
                proposta.simulacao.descricao = descricao
        except Exception:
            # Em caso de falha de sincronização, não bloqueia a importação.
            return

    @staticmethod
    def importar_proposta_bling(
        db: Session,
        id_bling: str,
        cliente: dict,
        itens: list[dict],
        vendedor_id: int,
        observacao: str | None = None,
        pedido: dict | None = None,
    ) -> Proposta:
        """
        cliente = {
            "nome": "...",
            "documento": "...",
            "endereco": "...",
            "cidade": "...",
            "telefone": "...",
            "email": "..."
        }

        itens = [
            {
                "sku": "ABC123",
                "codigo": "ABC123",
                "nome": "Produto X",
                "quantidade": 2,
                "preco_unitario": 10.5,
                "preco_total": 21.0,
                "imagem_url": "..."
            }
        ]
        """

        # ==================================================
        # 0. EVITA DUPLICIDADE (ID BLING)
        # ==================================================
        proposta_existente = (
            db.query(Proposta)
            .options(
                joinedload(Proposta.simulacao),
                joinedload(Proposta.itens).joinedload(PropostaProduto.produto)
            )
            .filter(
                Proposta.origem == PropostaOrigem.bling,
                Proposta.id_bling == id_bling,
            )
            .first()
        )

        # Se encontrou uma proposta existente:
        # SEMPRE permite reimportação para atualizar dados do Bling
        if proposta_existente:
            simulacao_anterior = proposta_existente.simulacao
            tinha_simulacao = simulacao_anterior is not None
            cubagem_anterior = proposta_existente.cubagem_m3
            cubagem_ajustada_anterior = proposta_existente.cubagem_ajustada

            status_anterior = proposta_existente.status.value
            status_era_finalizado = proposta_existente.status in {
                PropostaStatus.cancelada,
                PropostaStatus.concluida,
            }
                
            # ==================================================
            # ATUALIZA DADOS DO CLIENTE
            # ==================================================
            cliente_nome = (cliente.get("nome") or "").strip() or "Cliente Bling"
            # Sempre tenta enriquecer o cliente atual com dados do Bling
            if proposta_existente.cliente is not None:
                # Reimportação: sincroniza (se mudou no Bling, atualiza)
                BlingImportService._merge_cliente_fields(proposta_existente.cliente, cliente, overwrite=True)

            cliente_doc = (cliente.get("documento") or "").strip() or None

            if proposta_existente.cliente.nome != cliente_nome:
                # Busca por documento (quando existe) antes de cair em nome
                cliente_db = None
                if cliente_doc:
                    cliente_db = (
                        db.query(Cliente)
                        .filter(Cliente.documento == cliente_doc)
                        .first()
                    )

                if not cliente_db:
                    cliente_db = (
                        db.query(Cliente)
                        .filter(Cliente.nome == cliente_nome)
                        .first()
                    )

                if not cliente_db:
                    cliente_db = Cliente(
                        nome=cliente_nome,
                        documento=cliente.get("documento"),
                        endereco=cliente.get("endereco"),
                        cidade=cliente.get("cidade"),
                        telefone=cliente.get("telefone"),
                        email=cliente.get("email"),
                    )
                    db.add(cliente_db)
                    db.flush()
                else:
                    BlingImportService._merge_cliente_fields(cliente_db, cliente, overwrite=True)

                proposta_existente.cliente_id = cliente_db.id
            
            # ==================================================
            # ATUALIZA OBSERVAÇÃO / DESCONTO
            # ==================================================
            obs, _, _ = BlingImportService._montar_observacao_importacao(
                observacao=observacao,
                pedido=pedido,
            )
            proposta_existente.observacao_importacao = obs
            
            # ==================================================
            # ATUALIZA DESCONTO
            # ==================================================
            if pedido:
                proposta_existente.desconto = pedido.get("desconto")
            
            proposta_existente.atualizado_em = datetime.utcnow()
            
            # ==================================================
            # ATUALIZA ITENS DA PROPOSTA
            # ==================================================
            produtos_anteriores = BlingImportService._mapear_itens_por_sku(proposta_existente.itens)

            # Remove todos os itens antigos
            for item_antigo in proposta_existente.itens:
                db.delete(item_antigo)
            db.flush()
            
            # Recria itens com dados atualizados do Bling
            for item in itens or []:
                nome = (item.get("nome") or "").strip()
                if not nome:
                    continue

                sku = (item.get("sku") or item.get("codigo") or "").strip() or None
                quantidade = int(item.get("quantidade") or 1)
                if quantidade <= 0:
                    quantidade = 1

                produto = None
                if sku:
                    produto = (
                        db.query(Produto)
                        .filter(Produto.sku == sku)
                        .first()
                    )

                if not produto:
                    produto = Produto(
                        sku=sku,
                        nome=nome,
                    )
                    db.add(produto)
                    db.flush()

                proposta_item = PropostaProduto(
                    proposta_id=proposta_existente.id,
                    produto_id=produto.id,
                    quantidade=quantidade,
                    codigo=item.get("codigo"),
                    ncm=item.get("ncm"),
                    preco_unitario=item.get("preco_unitario"),
                    preco_total=item.get("preco_total"),
                    imagem_url=item.get("imagem_url"),
                )
                db.add(proposta_item)
            
            db.flush()
            
            # Recarrega a proposta com itens e produtos para verificação de medidas
            proposta_existente = (
                db.query(Proposta)
                .options(joinedload(Proposta.itens).joinedload(PropostaProduto.produto))
                .filter(Proposta.id == proposta_existente.id)
                .populate_existing()
                .first()
            )

            produtos_importados = BlingImportService._mapear_itens_por_sku(proposta_existente.itens)
            proposta_referencia = BlingImportService._buscar_proposta_referencia(
                db,
                proposta_id_excluir=proposta_existente.id,
                produtos_importados=produtos_importados,
            )

            if proposta_referencia:
                obs_ref = BlingImportService._aplicar_simulacao_de_referencia(
                    db,
                    proposta_destino=proposta_existente,
                    proposta_referencia=proposta_referencia,
                )
                if obs_ref:
                    PropostaService._atualizar_status(
                        db=db,
                        proposta=proposta_existente,
                        novo_status=PropostaStatus.pendente_cotacao,
                        observacao=f"Proposta reimportada: {obs_ref}",
                        forcar_notificacao=True,
                    )

                    BlingImportService._sincronizar_calculos_se_automatico_volumes(proposta_existente)
                    db.commit()
                    db.refresh(proposta_existente)
                    return proposta_existente

                BlingImportService._limpar_calculos(proposta_existente)
                PropostaService._atualizar_status(
                    db=db,
                    proposta=proposta_existente,
                    novo_status=PropostaStatus.pendente_simulacao,
                    observacao=(
                        "Proposta reimportada do Bling - necessário recalcular simulação "
                        "(sem referência útil e sem medidas completas)"
                    ),
                    forcar_notificacao=True,
                )
                db.commit()
                db.refresh(proposta_existente)
                return proposta_existente
            
            itens_iguais = produtos_anteriores == produtos_importados

            # ==================================================
            # SEM REFERÊNCIA: NÃO AVANÇA AUTOMATICAMENTE PARA COTAÇÃO
            # ==================================================
            # Regra: só vai para pendente_cotacao se existir referência com SKUs/quantidades iguais.
            # Aqui, preservamos simulação MANUAL quando os itens não mudaram; caso contrário,
            # limpamos simulação/cálculos e voltamos para pendente_simulacao.
            if itens_iguais and simulacao_anterior and not simulacao_anterior.automatica:
                # Mantém simulação manual existente.
                PropostaService._atualizar_status(
                    db=db,
                    proposta=proposta_existente,
                    novo_status=PropostaStatus.pendente_cotacao,
                    observacao="Proposta reimportada do Bling - simulação manual preservada",
                    forcar_notificacao=True,
                )
            else:
                # Remove simulação automática (ou qualquer simulação inválida após mudança de itens)
                BlingImportService._substituir_simulacao(
                    db,
                    proposta=proposta_existente,
                    nova_simulacao=None,
                )
                BlingImportService._limpar_calculos(proposta_existente)

                PropostaService._atualizar_status(
                    db=db,
                    proposta=proposta_existente,
                    novo_status=PropostaStatus.pendente_simulacao,
                    observacao=(
                        "Proposta reimportada do Bling - necessário simulação "
                        "(sem referência com SKUs/quantidades iguais)"
                    ),
                    forcar_notificacao=True,
                )
            
            BlingImportService._sincronizar_calculos_se_automatico_volumes(proposta_existente)
            db.commit()
            db.refresh(proposta_existente)
            return proposta_existente

        # ==================================================
        # 1. CLIENTE (CRIA OU REAPROVEITA)
        # ==================================================
        cliente_nome = (cliente.get("nome") or "").strip() or "Cliente Bling"

        cliente_doc = (cliente.get("documento") or "").strip() or None

        cliente_db = None
        if cliente_doc:
            cliente_db = (
                db.query(Cliente)
                .filter(Cliente.documento == cliente_doc)
                .first()
            )

        if not cliente_db:
            cliente_db = (
                db.query(Cliente)
                .filter(Cliente.nome == cliente_nome)
                .first()
            )

        if not cliente_db:
            cliente_db = Cliente(
                nome=cliente_nome,
                documento=cliente.get("documento"),
                endereco=cliente.get("endereco"),
                cidade=cliente.get("cidade"),
                telefone=cliente.get("telefone"),
                email=cliente.get("email"),
            )
            db.add(cliente_db)
            db.flush()  # garante cliente_db.id
        else:
            BlingImportService._merge_cliente_fields(cliente_db, cliente)

        # ==================================================
        # 2. CRIA PROPOSTA
        # ==================================================
        obs, vendedor_bling_nome, vendedor_bling_telefone = (
            BlingImportService._montar_observacao_importacao(
                observacao=observacao,
                pedido=pedido,
            )
        )

        proposta = Proposta(
            origem=PropostaOrigem.bling,
            id_bling=id_bling,
            cliente_id=cliente_db.id,
            vendedor_id=vendedor_id,
            responsavel_vendedor=vendedor_bling_nome,
            responsavel_telefone=vendedor_bling_telefone,
            observacao_importacao=obs,
            status=PropostaStatus.pendente_simulacao,
            desconto=pedido.get("desconto") if pedido else None,
        )

        db.add(proposta)
        db.flush()  # garante proposta.id

        # ==================================================
        # 3. ITENS / PRODUTOS
        # ==================================================
        for item in itens or []:
            nome = (item.get("nome") or "").strip()
            if not nome:
                continue

            sku = (item.get("sku") or item.get("codigo") or "").strip() or None
            quantidade = int(item.get("quantidade") or 1)
            if quantidade <= 0:
                quantidade = 1

            produto = None
            if sku:
                produto = (
                    db.query(Produto)
                    .filter(Produto.sku == sku)
                    .first()
                )

            if not produto:
                produto = Produto(
                    sku=sku,
                    nome=nome,
                )
                db.add(produto)
                db.flush()

            proposta_item = PropostaProduto(
                proposta_id=proposta.id,
                produto_id=produto.id,
                quantidade=quantidade,
                codigo=item.get("codigo"),
                ncm=item.get("ncm"),
                preco_unitario=item.get("preco_unitario"),
                preco_total=item.get("preco_total"),
                imagem_url=item.get("imagem_url"),
            )

            db.add(proposta_item)

        db.flush()  # Garante que os itens foram criados
        
        # ==================================================
        # 4. BUSCA PROPOSTA ANTERIOR COM MESMOS PRODUTOS E QUANTIDADES
        # ==================================================
        # Recarrega a proposta com itens e produtos para comparação confiável
        proposta_com_itens = (
            db.query(Proposta)
            .options(joinedload(Proposta.itens).joinedload(PropostaProduto.produto))
            .filter(Proposta.id == proposta.id)
            .one()
        )

        # Extrai SKUs e quantidades da proposta atual (ordem irrelevante)
        produtos_importados = BlingImportService._mapear_itens_por_sku(proposta_com_itens.itens)
        
        proposta_referencia = None
        simulacao_referencia = None
        
        if produtos_importados and len(proposta_com_itens.itens) > 0:
            proposta_referencia = BlingImportService._buscar_proposta_referencia(
                db,
                proposta_id_excluir=proposta.id,
                produtos_importados=produtos_importados,
            )
            simulacao_referencia = proposta_referencia.simulacao if proposta_referencia else None
        
        # ==================================================
        # 5. COPIA SIMULAÇÃO DA PROPOSTA ANTERIOR (SE ENCONTROU)
        # ==================================================
        BlingImportService._debug(
            f"[BLING IMPORT] Proposta {proposta.id} com referência: {bool(simulacao_referencia and proposta_referencia)}"
        )
        if simulacao_referencia and proposta_referencia:
            BlingImportService._debug(
                f"[BLING IMPORT] Copiando simulação da proposta #{proposta_referencia.id}"
            )
            obs_sim = BlingImportService._aplicar_simulacao_de_referencia(
                db,
                proposta_destino=proposta,
                proposta_referencia=proposta_referencia,
            )
            if not obs_sim:
                obs_sim = "Importado do Bling: necessário simulação (sem medidas completas)"
                PropostaService._atualizar_status(
                    db=db,
                    proposta=proposta,
                    novo_status=PropostaStatus.pendente_simulacao,
                    observacao=obs_sim,
                    forcar_notificacao=True,
                )
                db.commit()
                db.refresh(proposta)
                return proposta
            
            # Avança direto para cotação
            PropostaService._atualizar_status(
                db=db,
                proposta=proposta,
                novo_status=PropostaStatus.pendente_cotacao,
                observacao=obs_sim,
                forcar_notificacao=True,
            )
        else:
            # Sem proposta de referência: mantém pendente_simulacao.
            BlingImportService._debug(f"[BLING IMPORT] Proposta {proposta.id} sem referência")
            PropostaService._atualizar_status(
                db=db,
                proposta=proposta,
                novo_status=PropostaStatus.pendente_simulacao,
                observacao="Proposta importada do Bling - necessário simulação (sem referência com SKUs/quantidades iguais)",
                forcar_notificacao=True,
            )

        db.commit()
        db.refresh(proposta)

        return proposta
