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


class BlingImportService:
    """
    Importa propostas vindas do Bling seguindo o fluxo do FluxoLand.

    REGRAS:
    - Toda proposta do Bling entra como PENDENTE_SIMULACAO
    - Nunca pula direto para cotação
    """

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
        # Verifica se já existe uma proposta com este ID do Bling
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
            # Captura dados da simulação anterior (se existia)
            simulacao_anterior = proposta_existente.simulacao
            tinha_simulacao = simulacao_anterior is not None
            cubagem_anterior = proposta_existente.cubagem_m3
            cubagem_ajustada_anterior = proposta_existente.cubagem_ajustada
            
            status_anterior = proposta_existente.status.value
            status_era_finalizado = proposta_existente.status in [PropostaStatus.cancelada, PropostaStatus.concluida]
                
            # ==================================================
            # ATUALIZA DADOS DO CLIENTE
            # ==================================================
            cliente_nome = (cliente.get("nome") or "").strip() or "Cliente Bling"
            if proposta_existente.cliente.nome != cliente_nome:
                # Busca ou cria novo cliente
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
                proposta_existente.cliente_id = cliente_db.id
            
            # ==================================================
            # ATUALIZA OBSERVAÇÃO (inclui número e vendedor do Bling)
            # ==================================================
            obs = observacao or ""
            if pedido and pedido.get("numero"):
                obs = f"bling_numero:{pedido.get('numero')}; {obs}".strip()
            if pedido and pedido.get("vendedor"):
                vendedor_bling = pedido.get("vendedor")
                if "bling_vendedor:" not in obs:
                    obs = f"bling_vendedor:{vendedor_bling}; {obs}".strip()
            proposta_existente.observacao_importacao = obs
            
            # ==================================================
            # ATUALIZA ITENS DA PROPOSTA
            # ==================================================
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
                .first()
            )
            
            # ==================================================
            # RESTAURA SIMULAÇÃO E AJUSTA STATUS
            # ==================================================
            # IMPORTANTE: Verifica primeiro se todos os produtos têm medidas
            # mesmo que tenha simulação anterior, produtos novos podem não ter
            produtos_com_medidas_completas = all(
                item.produto.possui_medidas_completas()
                for item in proposta_existente.itens
                if item.produto
            )
            
            # Se tinha simulação, recria automaticamente
            if tinha_simulacao and produtos_com_medidas_completas:
                # Deleta a simulação existente primeiro (por causa da constraint UNIQUE)
                db.delete(simulacao_anterior)
                db.flush()
                
                # Recria a simulação com os mesmos dados
                nova_simulacao = Simulacao(
                    proposta_id=proposta_existente.id,
                    tipo=simulacao_anterior.tipo,
                    descricao=simulacao_anterior.descricao,
                )
                db.add(nova_simulacao)
                
                # Restaura cubagem
                proposta_existente.cubagem_m3 = cubagem_anterior
                proposta_existente.cubagem_ajustada = cubagem_ajustada_anterior
                
                # Se estava finalizada (cancelada/concluída), reativa para cotação
                # Se já estava em outro status, mantém apenas atualizando dados
                if status_era_finalizado:
                    PropostaService._atualizar_status(
                        db=db,
                        proposta=proposta_existente,
                        novo_status=PropostaStatus.pendente_cotacao,
                        observacao=f"Proposta reimportada (anteriormente {status_anterior}) - dados e simulação atualizados do Bling",
                    )
                else:
                    # Mantém no status atual, apenas registra a atualização
                    PropostaService._registrar_historico(
                        db=db,
                        proposta=proposta_existente,
                        status=proposta_existente.status,
                        observacao="Dados e simulação atualizados do Bling",
                    )
            elif tinha_simulacao and not produtos_com_medidas_completas:
                # Tinha simulação MAS agora tem produtos sem medidas
                # DEVE voltar para pendente_simulacao
                db.delete(simulacao_anterior)
                db.flush()
                
                # Limpa cubagem
                proposta_existente.cubagem_m3 = None
                proposta_existente.cubagem_ajustada = False
                
                # Volta para simulação
                PropostaService._atualizar_status(
                    db=db,
                    proposta=proposta_existente,
                    novo_status=PropostaStatus.pendente_simulacao,
                    observacao=f"Proposta reimportada com produtos novos sem medidas - necessária nova simulação",
                )
            else:
                # ==================================================
                # SEM SIMULAÇÃO ANTERIOR - VERIFICA SE TEM MEDIDAS
                # ==================================================
                # Verifica se os produtos têm medidas para criar simulação automática
                produtos_com_medidas_completas = all(
                    item.produto.possui_medidas_completas()
                    for item in proposta_existente.itens
                    if item.produto
                )
                
                if produtos_com_medidas_completas and len(proposta_existente.itens) > 0:
                    # Calcula cubagem total baseado nas medidas dos produtos
                    cubagem_total_cm3 = 0.0
                    descricao_linhas = []
                    
                    for item_prop in proposta_existente.itens:
                        produto = item_prop.produto
                        if produto.possui_medidas_completas():
                            volume_unitario = (
                                produto.comprimento_cm *
                                produto.largura_cm *
                                produto.altura_cm
                            )
                            volume_total_item = volume_unitario * item_prop.quantidade
                            cubagem_total_cm3 += volume_total_item
                            
                            descricao_linhas.append(
                                f"{item_prop.quantidade}x {produto.nome} "
                                f"({produto.comprimento_cm}x{produto.largura_cm}x{produto.altura_cm} cm)"
                            )
                    
                    if cubagem_total_cm3 > 0:
                        # Converte para m³
                        cubagem_m3 = cubagem_total_cm3 / 1_000_000
                        
                        # Cria simulação automática
                        simulacao = Simulacao(
                            proposta_id=proposta_existente.id,
                            tipo=TipoSimulacao.volumes,
                            descricao="\n".join(descricao_linhas),
                        )
                        db.add(simulacao)
                        
                        # Atualiza cubagem da proposta
                        proposta_existente.cubagem_m3 = round(cubagem_m3, 4)
                        proposta_existente.cubagem_ajustada = False
                        
                        # Avança para COTAÇÃO com simulação automática
                        PropostaService._atualizar_status(
                            db=db,
                            proposta=proposta_existente,
                            novo_status=PropostaStatus.pendente_cotacao,
                            observacao=f"Proposta reimportada (anteriormente {status_anterior}) - simulação criada automaticamente (produtos com medidas conhecidas)",
                        )
                    else:
                        # Não conseguiu calcular cubagem
                        if status_era_finalizado:
                            PropostaService._atualizar_status(
                                db=db,
                                proposta=proposta_existente,
                                novo_status=PropostaStatus.pendente_simulacao,
                                observacao=f"Proposta reimportada do Bling (anteriormente {status_anterior}) - dados atualizados",
                            )
                        else:
                            PropostaService._registrar_historico(
                                db=db,
                                proposta=proposta_existente,
                                status=proposta_existente.status,
                                observacao="Dados atualizados do Bling",
                            )
                else:
                    # Sem medidas completas
                    if status_era_finalizado:
                        # Volta para pendente_simulacao
                        PropostaService._atualizar_status(
                            db=db,
                            proposta=proposta_existente,
                            novo_status=PropostaStatus.pendente_simulacao,
                            observacao=f"Proposta reimportada do Bling (anteriormente {status_anterior}) - dados atualizados",
                        )
                    else:
                        # Mantém no status atual, apenas registra a atualização
                        PropostaService._registrar_historico(
                            db=db,
                            proposta=proposta_existente,
                            status=proposta_existente.status,
                            observacao="Dados atualizados do Bling",
                        )
            
            db.commit()
            db.refresh(proposta_existente)
            return proposta_existente

        # ==================================================
        # 1. CLIENTE (CRIA OU REAPROVEITA)
        # ==================================================
        cliente_nome = (cliente.get("nome") or "").strip() or "Cliente Bling"

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

        # ==================================================
        # 2. CRIA PROPOSTA
        # ==================================================
        # monta observação incluindo número e vendedor do Bling quando disponível
        obs = observacao or ""
        if pedido and pedido.get("numero"):
            obs = f"bling_numero:{pedido.get('numero')}; {obs}".strip()
        if pedido and pedido.get("vendedor"):
            vendedor_bling = pedido.get("vendedor")
            obs = f"bling_vendedor:{vendedor_bling}; {obs}".strip()

        proposta = Proposta(
            origem=PropostaOrigem.bling,
            id_bling=id_bling,
            cliente_id=cliente_db.id,
            vendedor_id=vendedor_id,
            observacao_importacao=obs,
            status=PropostaStatus.pendente_simulacao,
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
        # Extrai SKUs e quantidades da proposta atual
        produtos_importados = {}  # {sku: quantidade}
        for item in proposta.itens:
            if item.produto and item.produto.sku:
                produtos_importados[item.produto.sku] = item.quantidade
        
        proposta_referencia = None
        simulacao_referencia = None
        
        if produtos_importados and len(proposta.itens) > 0:
            # Busca propostas anteriores que:
            # 1. Tenham simulação concluída (status != pendente_simulacao)
            # 2. Tenham os mesmos produtos com as mesmas quantidades
            propostas_candidatas = (
                db.query(Proposta)
                .options(
                    joinedload(Proposta.simulacao),
                    joinedload(Proposta.itens).joinedload(PropostaProduto.produto)
                )
                .filter(
                    Proposta.id != proposta.id,  # Não a própria proposta
                    Proposta.simulacao.has(),  # Tem simulação
                    Proposta.status != PropostaStatus.pendente_simulacao  # Já passou da simulação
                )
                .order_by(Proposta.criado_em.desc())  # Mais recentes primeiro
                .all()
            )
            
            # Verifica qual proposta tem exatamente os mesmos produtos E quantidades
            for candidata in propostas_candidatas:
                produtos_candidata = {}  # {sku: quantidade}
                for item in candidata.itens:
                    if item.produto and item.produto.sku:
                        produtos_candidata[item.produto.sku] = item.quantidade
                
                # Se os produtos E quantidades são exatamente os mesmos
                if produtos_candidata == produtos_importados:
                    proposta_referencia = candidata
                    simulacao_referencia = candidata.simulacao
                    break
        
        # ==================================================
        # 5. COPIA SIMULAÇÃO DA PROPOSTA ANTERIOR (SE ENCONTROU)
        # ==================================================
        if simulacao_referencia and proposta_referencia:
            # Copia a simulação da proposta anterior
            nova_simulacao = Simulacao(
                proposta_id=proposta.id,
                tipo=simulacao_referencia.tipo,
                descricao=simulacao_referencia.descricao,
            )
            db.add(nova_simulacao)
            
            # Copia cubagem
            proposta.cubagem_m3 = proposta_referencia.cubagem_m3
            proposta.cubagem_ajustada = proposta_referencia.cubagem_ajustada
            
            # Avança direto para cotação
            PropostaService._atualizar_status(
                db=db,
                proposta=proposta,
                novo_status=PropostaStatus.pendente_cotacao,
                observacao=f"Simulação copiada da proposta #{proposta_referencia.id} (mesmos produtos)",
            )
        else:
            # Sem proposta de referência - verifica se produtos têm medidas cadastradas
            produtos_com_medidas_completas = all(
                item.produto and item.produto.possui_medidas_completas()
                for item in proposta.itens
            )
            
            if produtos_com_medidas_completas and len(proposta.itens) > 0:
                # Calcula cubagem total baseado nas medidas dos produtos
                cubagem_total_cm3 = 0.0
                descricao_linhas = []
                
                for item_prop in proposta.itens:
                    produto = item_prop.produto
                    if produto.possui_medidas_completas():
                        volume_unitario = (
                            produto.comprimento_cm *
                            produto.largura_cm *
                            produto.altura_cm
                        )
                        volume_total_item = volume_unitario * item_prop.quantidade
                        cubagem_total_cm3 += volume_total_item
                        
                        descricao_linhas.append(
                            f"{item_prop.quantidade}x {produto.nome} "
                        f"({produto.comprimento_cm}x{produto.largura_cm}x{produto.altura_cm} cm)"
                    )
                
                if cubagem_total_cm3 > 0:
                    # Converte para m³
                    cubagem_m3 = cubagem_total_cm3 / 1_000_000
                    
                    # Cria simulação
                    simulacao = Simulacao(
                        proposta_id=proposta.id,
                        tipo=TipoSimulacao.volumes,
                        descricao="\n".join(descricao_linhas),
                    )
                    db.add(simulacao)
                    
                    # Atualiza cubagem da proposta
                    proposta.cubagem_m3 = round(cubagem_m3, 4)
                    proposta.cubagem_ajustada = False
                    
                    # Avança direto para COTAÇÃO
                    PropostaService._atualizar_status(
                        db=db,
                        proposta=proposta,
                        novo_status=PropostaStatus.pendente_cotacao,
                        observacao="Proposta importada do Bling - simulação criada automaticamente (produtos com medidas conhecidas)",
                    )
                else:
                    # Tem produtos mas não conseguiu calcular cubagem
                    PropostaService._atualizar_status(
                        db=db,
                        proposta=proposta,
                        novo_status=PropostaStatus.pendente_simulacao,
                        observacao="Proposta importada automaticamente do Bling",
                    )
            else:
                # Sem medidas conhecidas, vai para simulação manual
                PropostaService._atualizar_status(
                    db=db,
                    proposta=proposta,
                    novo_status=PropostaStatus.pendente_simulacao,
                    observacao="Proposta importada automaticamente do Bling",
                )

        db.commit()
        db.refresh(proposta)

        return proposta
