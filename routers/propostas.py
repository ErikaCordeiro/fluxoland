from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload
from starlette.status import HTTP_303_SEE_OTHER
from datetime import datetime

from database import get_db
from dependencies import get_current_user_html
from templates import templates

from models import (
    Proposta,
    PropostaProduto,
    PropostaStatus,
    TipoSimulacao,
    Simulacao,
    Caixa,
    Transportadora,
    User,
    Cliente,
    CotacaoFrete,
    PropostaHistorico,
    EnvioProposta,
)

from services.galpao_service import GalpaoService
from services.bling_parser_service import BlingParserService
from services.bling_import_service import BlingImportService
from services.proposta_service import PropostaService

router = APIRouter(prefix="/propostas", tags=["propostas"])


# ======================================================
# KANBAN
# ======================================================
@router.get("/")
def kanban_propostas(
    request: Request,
    cliente: str | None = None,
    vendedor: int | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    if isinstance(user, RedirectResponse):
        return user

    def aplicar_filtros(query):
        if cliente:
            query = query.filter(
                Proposta.cliente.has(Cliente.nome.ilike(f"%{cliente}%"))
            )
        if vendedor:
            query = query.filter(Proposta.vendedor_id == vendedor)
        return query

    pend_sim = aplicar_filtros(
        db.query(Proposta)
        .options(
            joinedload(Proposta.cliente),
            joinedload(Proposta.vendedor),
            joinedload(Proposta.itens).joinedload(PropostaProduto.produto)
        )
        .filter(Proposta.status == PropostaStatus.pendente_simulacao)
    ).all()

    pend_cot = aplicar_filtros(
        db.query(Proposta)
        .options(
            joinedload(Proposta.cliente),
            joinedload(Proposta.vendedor),
            joinedload(Proposta.itens).joinedload(PropostaProduto.produto)
        )
        .filter(Proposta.status == PropostaStatus.pendente_cotacao)
    ).all()

    pend_env = aplicar_filtros(
        db.query(Proposta)
        .options(
            joinedload(Proposta.cliente),
            joinedload(Proposta.vendedor),
            joinedload(Proposta.itens).joinedload(PropostaProduto.produto)
        )
        .filter(Proposta.status == PropostaStatus.pendente_envio)
    ).all()

    for p in pend_sim + pend_cot + pend_env:
        # nome do cliente para facilitar templates
        p.cliente_nome = p.cliente.nome if p.cliente else ""

    vendedores = db.query(User).order_by(User.nome).all()

    return templates.TemplateResponse(
        "propostas_kanban.html",
        {
            "request": request,
            "user": user,
            "pendentes_simulacao": pend_sim,
            "pendentes_cotacao": pend_cot,
            "pendentes_envio": pend_env,
            "vendedores": vendedores,
        },
    )


# ======================================================
# NOVA PROPOSTA (IMPORTAÇÃO BLING)
# ======================================================
@router.get("/nova")
def nova_proposta(request: Request, user=Depends(get_current_user_html)):
    if isinstance(user, RedirectResponse):
        return user

    return templates.TemplateResponse(
        "proposta_nova.html",
        {"request": request, "user": user},
    )


@router.post("/nova")
def importar_proposta_bling(
    link_bling: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    if isinstance(user, RedirectResponse):
        return user

    dados = BlingParserService.parse_doc_view(link_bling)

    cliente = dados.get("cliente")
    if not cliente or not cliente.get("nome"):
        raise ValueError("Cliente não encontrado no documento do Bling")

    # Busca ou cria vendedor baseado no nome do Bling
    vendedor_id = user.id  # Padrão: usuário logado
    pedido = dados.get("pedido", {})
    nome_vendedor_bling = pedido.get("vendedor")
    
    if nome_vendedor_bling:
        vendedor = db.query(User).filter(User.nome == nome_vendedor_bling).first()
        if vendedor:
            vendedor_id = vendedor.id

    BlingImportService.importar_proposta_bling(
        db=db,
        id_bling=dados["id_bling"],
        cliente=cliente,
        itens=dados.get("itens", []),
        vendedor_id=vendedor_id,
        observacao="Importado via Bling",
        pedido=pedido,
    )

    return RedirectResponse("/propostas", status_code=HTTP_303_SEE_OTHER)


# ======================================================
# HISTÓRICO DE PROPOSTAS
# ======================================================
@router.get("/historico")
def historico_propostas(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    if isinstance(user, RedirectResponse):
        return user

    historico = (
        db.query(PropostaHistorico)
        .options(joinedload(PropostaHistorico.proposta))
        .order_by(PropostaHistorico.criado_em.desc())
        .all()
    )

    vendedores = db.query(User).order_by(User.nome).all()

    return templates.TemplateResponse(
        "propostas_historico.html",
        {
            "request": request,
            "user": user,
            "historico": historico,
            "vendedores": vendedores,
        },
    )


# ======================================================
# DETALHE DA PROPOSTA
# ======================================================
@router.get("/{proposta_id}")
def detalhe_proposta(
    proposta_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    if isinstance(user, RedirectResponse):
        return user

    proposta = (
        db.query(Proposta)
        .options(
            joinedload(Proposta.cliente),
            joinedload(Proposta.vendedor),
            joinedload(Proposta.itens).joinedload(PropostaProduto.produto),
            joinedload(Proposta.cotacoes).joinedload(CotacaoFrete.transportadora),
            joinedload(Proposta.simulacao),
            joinedload(Proposta.envio),
        )
        .filter(Proposta.id == proposta_id)
        .first()
    )

    if not proposta:
        return RedirectResponse("/propostas", HTTP_303_SEE_OTHER)

    transportadoras = db.query(Transportadora).order_by(Transportadora.nome).all()

    # garantir itens como lista explícita para o template (evita problemas de lazy-loading)
    itens = (
        db.query(PropostaProduto)
        .filter(PropostaProduto.proposta_id == proposta.id)
        .all()
    )

    # serializar dados essenciais para debug/visualização no template
    cliente_data = None
    if proposta.cliente:
        cliente_data = {
            "id": proposta.cliente.id,
            "nome": proposta.cliente.nome,
            "documento": proposta.cliente.documento,
            "endereco": proposta.cliente.endereco,
            "cidade": proposta.cliente.cidade,
            "telefone": proposta.cliente.telefone,
            "email": proposta.cliente.email,
        }

    itens_data = []
    for it in itens:
        itens_data.append(
            {
                "id": it.id,
                "produto_id": it.produto_id,
                "produto_nome": (it.produto.nome if it.produto else None),
                "produto_sku": (it.produto.sku if it.produto else None),
                "codigo": it.codigo,
                "ncm": it.ncm,
                "quantidade": it.quantidade,
                "preco_unitario": it.preco_unitario,
                "preco_total": it.preco_total,
                "imagem_url": it.imagem_url,
            }
        )

    return templates.TemplateResponse(
        "proposta_detail.html",
        {
            "request": request,
            "user": user,
            "proposta": proposta,
            "itens": itens,
            "itens_data": itens_data,
            "cliente_data": cliente_data,
            "transportadoras": transportadoras,
            "caixas": db.query(Caixa).order_by(Caixa.nome).all(),
        },
    )


@router.post("/{proposta_id}/simulacao-volumes")
async def simular_por_volumes(
    proposta_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    if isinstance(user, RedirectResponse):
        return user

    proposta = db.get(Proposta, proposta_id)
    if not proposta:
        return RedirectResponse("/propostas", HTTP_303_SEE_OTHER)

    form = await request.form()
    action = form.get("action", "").strip()

    # 1) Collect selected caixa rows (volume_select[index] and volume_qtd[index])
    caixas_payload = []
    peso_total = 0.0
    index = 0
    while f"volume_select[{index}]" in form:
        sel = form.get(f"volume_select[{index}]")
        try:
            qtd = int(form.get(f"volume_qtd[{index}]") or 0)
            peso = float(form.get(f"volume_peso[{index}]") or 0)
        except (TypeError, ValueError):
            qtd = 0
            peso = 0

        if sel and sel != "manual":
            try:
                cid = int(sel)
                if qtd > 0:
                    caixas_payload.append({"caixa_id": cid, "quantidade": qtd})
                    peso_total += peso
            except (TypeError, ValueError):
                continue

        index += 1

    # 2) Collect manual volumes (manual_volumes[index][comprimento], largura, altura, quantidade)
    manual_volumes = []
    mindex = 0
    while f"manual_volumes[{mindex}][comprimento]" in form:
        try:
            c = float(form.get(f"manual_volumes[{mindex}][comprimento]") or 0)
            l = float(form.get(f"manual_volumes[{mindex}][largura]") or 0)
            h = float(form.get(f"manual_volumes[{mindex}][altura]") or 0)
            q = int(form.get(f"manual_volumes[{mindex}][quantidade]") or 1)
        except (TypeError, ValueError):
            mindex += 1
            continue

        if c > 0 and l > 0 and h > 0 and q > 0:
            manual_volumes.append({
                "comprimento": c,
                "largura": l,
                "altura": h,
                "quantidade": q,
            })

        mindex += 1

    # 3) If nothing provided, show error
    if not caixas_payload and not manual_volumes:
        return RedirectResponse(f"/propostas/{proposta_id}?erro=sem_volumes", status_code=HTTP_303_SEE_OTHER)

    # 4) Compute total volume and description, then save Simulacao (logic similar to SimulacaoVolumesService)
    volume_total_cm3 = 0.0
    descricao_linhas = []

    # process caixas payload
    for item in caixas_payload:
        caixa = db.get(Caixa, int(item.get("caixa_id")))
        quantidade = int(item.get("quantidade", 0))
        if not caixa or quantidade <= 0:
            continue
        volume_unitario_cm3 = caixa.volume_cm3
        volume_total_cm3 += volume_unitario_cm3 * quantidade
        descricao_linhas.append(
            f"{quantidade}x {caixa.nome} ({caixa.altura_cm}x{caixa.largura_cm}x{caixa.comprimento_cm} cm)"
        )

    # process manual volumes
    for mv in manual_volumes:
        c = mv["comprimento"]
        l = mv["largura"]
        h = mv["altura"]
        q = mv["quantidade"]
        vol_unit = c * l * h
        volume_total_cm3 += vol_unit * q
        descricao_linhas.append(f"{q}x Manual ({c}x{l}x{h} cm)")

    if volume_total_cm3 <= 0:
        return RedirectResponse(f"/propostas/{proposta_id}", status_code=HTTP_303_SEE_OTHER)

    volume_total_m3 = volume_total_cm3 / 1_000_000

    # Remove simulação anterior se existir
    if proposta.simulacao:
        db.delete(proposta.simulacao)
        db.flush()

    simulacao = Simulacao(
        proposta_id=proposta.id,
        tipo=TipoSimulacao.volumes,
        descricao="\n".join(descricao_linhas),
    )

    db.add(simulacao)
    db.flush()

    # Salva peso e cubagem na proposta
    proposta.cubagem_m3 = round(volume_total_m3, 4)
    proposta.cubagem_ajustada = False
    if peso_total > 0:
        proposta.peso_total_kg = peso_total

    db.commit()
    db.refresh(proposta)
    db.refresh(simulacao)

    # Se ação for "concluir", muda status para pendente_cotacao
    if action == "concluir":
        # ==================================================
        # SALVA MEDIDAS NOS PRODUTOS (para futuras simulações automáticas)
        # ==================================================
        # Se a proposta tem apenas 1 item, salva as medidas unitárias no produto
        proposta_com_itens = (
            db.query(Proposta)
            .options(joinedload(Proposta.itens).joinedload(PropostaProduto.produto))
            .filter(Proposta.id == proposta.id)
            .first()
        )
        
        if proposta_com_itens and len(proposta_com_itens.itens) == 1:
            item = proposta_com_itens.itens[0]
            produto = item.produto
            quantidade_produto = item.quantidade
            
            if produto and quantidade_produto > 0:
                # Calcula o volume unitário (volume total / quantidade de produtos)
                # Volume total já foi calculado e armazenado em volume_total_cm3
                volume_unitario_cm3 = volume_total_cm3 / quantidade_produto
                
                # Estimativa de dimensões unitárias (assumindo formato cúbico para simplificar)
                # lado_cm = raiz_cúbica(volume_unitario_cm3)
                lado_cm = round(volume_unitario_cm3 ** (1/3), 2)
                
                # Salva as medidas estimadas no produto
                produto.comprimento_cm = lado_cm
                produto.largura_cm = lado_cm
                produto.altura_cm = lado_cm
                produto.peso_unitario_kg = 1.0  # Peso padrão - pode ser ajustado depois
                produto.data_atualizacao = datetime.utcnow()
        
        # Atualizar timestamp da proposta
        proposta.atualizado_em = datetime.utcnow()
        
        db.commit()
        
        PropostaService._atualizar_status(
            db=db,
            proposta=proposta,
            novo_status=PropostaStatus.pendente_cotacao,
            observacao="Simulação por volumes concluída",
        )

    return RedirectResponse(f"/propostas/{proposta_id}", status_code=HTTP_303_SEE_OTHER)


@router.post("/{proposta_id}/simulacao-manual")
async def salvar_simulacao_manual(
    proposta_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    if isinstance(user, RedirectResponse):
        return user

    proposta = db.get(Proposta, proposta_id)
    if not proposta:
        return RedirectResponse("/propostas", HTTP_303_SEE_OTHER)

    form = await request.form()
    descricao = (form.get("simulacao_texto") or "").strip()
    action = form.get("action", "").strip()
    
    if not descricao:
        return RedirectResponse(f"/propostas/{proposta_id}", status_code=HTTP_303_SEE_OTHER)

    # Remove simulação anterior
    if proposta.simulacao:
        db.delete(proposta.simulacao)
        db.flush()

    simulacao = Simulacao(
        proposta_id=proposta.id,
        tipo=TipoSimulacao.manual,
        descricao=descricao,
    )

    db.add(simulacao)
    db.flush()

    # Atualizar timestamp
    proposta.atualizado_em = datetime.utcnow()

    db.commit()
    db.refresh(proposta)
    db.refresh(simulacao)

    # Se ação for "concluir", muda status para pendente_cotacao
    if action == "concluir":
        PropostaService._atualizar_status(
            db=db,
            proposta=proposta,
            novo_status=PropostaStatus.pendente_cotacao,
            observacao="Simulação manual concluída",
        )

    return RedirectResponse(f"/propostas/{proposta_id}", status_code=HTTP_303_SEE_OTHER)


@router.get("/debug/{proposta_id}")
def debug_proposta_json(
    proposta_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    """Retorna JSON com cliente e itens (para diagnóstico)."""
    if isinstance(user, RedirectResponse):
        return user

    proposta = (
        db.query(Proposta)
        .options(
            joinedload(Proposta.cliente),
            joinedload(Proposta.itens).joinedload(PropostaProduto.produto),
        )
        .filter(Proposta.id == proposta_id)
        .first()
    )

    if not proposta:
        return {"error": "Proposta não encontrada"}

    cliente = None
    if proposta.cliente:
        cliente = {
            "id": proposta.cliente.id,
            "nome": proposta.cliente.nome,
            "documento": proposta.cliente.documento,
            "endereco": proposta.cliente.endereco,
            "cidade": proposta.cliente.cidade,
            "telefone": proposta.cliente.telefone,
            "email": proposta.cliente.email,
        }

    itens_out = []
    for it in proposta.itens:
        itens_out.append(
            {
                "id": it.id,
                "produto_id": it.produto_id,
                "produto_nome": (it.produto.nome if it.produto else None),
                "produto_sku": (it.produto.sku if it.produto else None),
                "codigo": it.codigo,
                "ncm": it.ncm,
                "quantidade": it.quantidade,
                "preco_unitario": it.preco_unitario,
                "preco_total": it.preco_total,
                "imagem_url": it.imagem_url,
            }
        )

    return {"proposta_id": proposta.id, "cliente": cliente, "itens": itens_out}


@router.get("/{proposta_id}/abrir")
def abrir_proposta(
    proposta_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    """Página pronta para abrir em nova aba / imprimir."""
    if isinstance(user, RedirectResponse):
        return user

    proposta = (
        db.query(Proposta)
        .options(
            joinedload(Proposta.cliente),
            joinedload(Proposta.vendedor),
            joinedload(Proposta.itens).joinedload(PropostaProduto.produto),
        )
        .filter(Proposta.id == proposta_id)
        .first()
    )

    if not proposta:
        return RedirectResponse("/propostas", HTTP_303_SEE_OTHER)

    itens = (
        db.query(PropostaProduto)
        .filter(PropostaProduto.proposta_id == proposta.id)
        .all()
    )

    return templates.TemplateResponse(
        "proposta_print.html",
        {
            "request": request,
            "user": user,
            "proposta": proposta,
            "itens": itens,
        },
    )


# ======================================================
# CANCELAR PROPOSTA
# ======================================================
@router.post("/{proposta_id}/cancelar")
def cancelar_proposta(
    proposta_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    proposta = db.get(Proposta, proposta_id)
    if not proposta:
        return RedirectResponse("/propostas", HTTP_303_SEE_OTHER)

    proposta.status = PropostaStatus.cancelada
    proposta.atualizado_em = datetime.utcnow()

    db.add(
        PropostaHistorico(
            proposta_id=proposta.id,
            status=PropostaStatus.cancelada,
            observacao="Proposta cancelada pelo usuário",
        )
    )

    db.commit()
    return RedirectResponse("/propostas", HTTP_303_SEE_OTHER)


# ======================================================
# SIMULAÇÃO MANUAL (GALPÃO)
# ======================================================
@router.post("/{proposta_id}/simulacao")
async def salvar_simulacao_galpao(
    proposta_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    if isinstance(user, RedirectResponse):
        return user

    proposta = db.get(Proposta, proposta_id)
    if not proposta:
        return RedirectResponse("/propostas", HTTP_303_SEE_OTHER)

    form = await request.form()
    produtos_payload = []
    index = 0

    while f"produtos[{index}][produto_id]" in form:
        produtos_payload.append(
            {
                "produto_id": int(form[f"produtos[{index}][produto_id]"]),
                "comprimento": float(form[f"produtos[{index}][comprimento]"]),
                "largura": float(form[f"produtos[{index}][largura]"]),
                "altura": float(form[f"produtos[{index}][altura]"]),
                "peso_unitario": float(form[f"produtos[{index}][peso_unitario]"]),
            }
        )
        index += 1

    GalpaoService.salvar_simulacao_galpao(
        db=db,
        proposta=proposta,
        produtos_payload=produtos_payload,
    )

    proposta.status = PropostaStatus.pendente_cotacao
    proposta.atualizado_em = datetime.utcnow()
    db.add(
        PropostaHistorico(
            proposta_id=proposta.id,
            status=PropostaStatus.pendente_cotacao,
            observacao="Simulação logística realizada",
        )
    )

    db.commit()

    return RedirectResponse(
        f"/propostas/{proposta_id}",
        status_code=HTTP_303_SEE_OTHER,
    )


# ======================================================
# SALVAR COTAÇÃO
# ======================================================
@router.post("/{proposta_id}/cotacao")
async def salvar_cotacao(
    proposta_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    if isinstance(user, RedirectResponse):
        return user

    proposta = db.get(Proposta, proposta_id)
    if not proposta:
        return RedirectResponse("/propostas", HTTP_303_SEE_OTHER)

    form = await request.form()
    action = form.get("action", "").strip()

    # Processar múltiplas cotações
    cotacoes_criadas = 0
    index = 0
    while f"transportadora_id[{index}]" in form:
        transportadora_id = form.get(f"transportadora_id[{index}]")
        preco_str = form.get(f"preco[{index}]")
        prazo_str = form.get(f"prazo_dias[{index}]")
        numero_cotacao = form.get(f"numero_cotacao[{index}]", "").strip() or None

        # Validar se campos estão preenchidos
        if transportadora_id and preco_str and prazo_str:
            try:
                transportadora_id = int(transportadora_id)
                preco = float(preco_str)
                prazo_dias = int(prazo_str)

                # Verificar se já existe uma cotação para esta transportadora
                cotacao_existente = db.query(CotacaoFrete).filter(
                    CotacaoFrete.proposta_id == proposta.id,
                    CotacaoFrete.transportadora_id == transportadora_id
                ).first()

                if cotacao_existente:
                    # Atualizar cotação existente
                    cotacao_existente.preco = preco
                    cotacao_existente.prazo_dias = prazo_dias
                    cotacao_existente.numero_cotacao = numero_cotacao
                else:
                    # Criar nova cotação
                    db.add(
                        CotacaoFrete(
                            proposta_id=proposta.id,
                            transportadora_id=transportadora_id,
                            preco=preco,
                            prazo_dias=prazo_dias,
                            numero_cotacao=numero_cotacao,
                        )
                    )
                cotacoes_criadas += 1
            except (TypeError, ValueError):
                continue

        index += 1

    # Se pelo menos uma cotação foi criada
    if cotacoes_criadas > 0:
        # Atualizar timestamp
        proposta.atualizado_em = datetime.utcnow()
        db.commit()

        # Se ação for "concluir", muda status para pendente_envio
        if action == "concluir":
            PropostaService._atualizar_status(
                db=db,
                proposta=proposta,
                novo_status=PropostaStatus.pendente_envio,
                observacao=f"{cotacoes_criadas} cotação(ões) de frete cadastrada(s)",
            )

    return RedirectResponse(
        f"/propostas/{proposta_id}",
        status_code=HTTP_303_SEE_OTHER,
    )


# ======================================================
# ENVIO AO CLIENTE
# ======================================================
@router.post("/{proposta_id}/envio")
def enviar_proposta(
    proposta_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_html),
):
    if isinstance(user, RedirectResponse):
        return user

    proposta = db.get(Proposta, proposta_id)
    if not proposta:
        return RedirectResponse("/propostas", HTTP_303_SEE_OTHER)

    # Criar registro de envio
    envio = EnvioProposta(
        proposta_id=proposta.id,
        resumo_envio="Proposta enviada ao cliente",
        meio_envio="WhatsApp/E-mail",
        enviado=True,
        enviado_em=datetime.utcnow(),
    )
    db.add(envio)
    db.flush()

    # Atualizar timestamp
    proposta.atualizado_em = datetime.utcnow()

    # Atualizar status para concluída
    PropostaService._atualizar_status(
        db=db,
        proposta=proposta,
        novo_status=PropostaStatus.concluida,
        observacao="Proposta enviada ao cliente e concluída",
    )

    return RedirectResponse("/propostas", HTTP_303_SEE_OTHER)
