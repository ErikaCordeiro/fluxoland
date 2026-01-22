import enum
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    ForeignKey,
    Boolean,
    Text,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from database import Base


# ======================================================
# ENUMS
# ======================================================

class UserRole(str, enum.Enum):
    lider = "lider"
    usuario = "usuario"


class PropostaStatus(str, enum.Enum):
    pendente_simulacao = "pendente_simulacao"
    pendente_cotacao = "pendente_cotacao"
    pendente_envio = "pendente_envio"
    concluida = "concluida"
    cancelada = "cancelada"


class TipoSimulacao(str, enum.Enum):
    manual = "manual"
    volumes = "volumes"


class PropostaOrigem(str, enum.Enum):
    manual = "MANUAL"
    bling = "BLING"


# ======================================================
# USUÁRIO
# ======================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)

    role = Column(Enum(UserRole), default=UserRole.usuario, nullable=False)
    ativo = Column(Boolean, default=True)

    criado_em = Column(DateTime, default=datetime.utcnow)

    propostas = relationship("Proposta", back_populates="vendedor")


# ======================================================
# CLIENTE
# ======================================================

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)

    documento = Column(String(50))
    endereco = Column(String(250))
    cidade = Column(String(120))
    telefone = Column(String(50))
    email = Column(String(120))

    criado_em = Column(DateTime, default=datetime.utcnow)

    propostas = relationship("Proposta", back_populates="cliente")


# ======================================================
# PRODUTO
# ======================================================

class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(80), unique=True, index=True)
    nome = Column(String(200), nullable=False)

    comprimento_cm = Column(Float)
    largura_cm = Column(Float)
    altura_cm = Column(Float)
    peso_unitario_kg = Column(Float)

    data_atualizacao = Column(DateTime, default=datetime.utcnow)

    itens_proposta = relationship(
        "PropostaProduto",
        back_populates="produto",
        cascade="all, delete-orphan",
    )

    def possui_medidas_completas(self) -> bool:
        return all(
            v is not None
            for v in (
                self.comprimento_cm,
                self.largura_cm,
                self.altura_cm,
                self.peso_unitario_kg,
            )
        )


# ======================================================
# PROPOSTA
# ======================================================

class Proposta(Base):
    __tablename__ = "propostas"

    id = Column(Integer, primary_key=True, index=True)

    origem = Column(Enum(PropostaOrigem), nullable=False)
    id_bling = Column(String(80), index=True)

    status = Column(
        Enum(PropostaStatus),
        default=PropostaStatus.pendente_simulacao,
        nullable=False,
    )

    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # CLIENTE
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    cliente = relationship("Cliente", back_populates="propostas")

    # VENDEDOR
    vendedor_id = Column(Integer, ForeignKey("users.id"))
    vendedor = relationship("User", back_populates="propostas")

    # CÁLCULOS
    peso_total_kg = Column(Float)
    comprimento_total_cm = Column(Float)
    largura_total_cm = Column(Float)
    altura_total_cm = Column(Float)

    cubagem_m3 = Column(Float)
    cubagem_manual_m3 = Column(Float)
    cubagem_ajustada = Column(Boolean, default=False)

    # VALORES FINANCEIROS
    desconto = Column(Float)  # desconto aplicado

    observacao_importacao = Column(Text)

    # RELACIONAMENTOS
    itens = relationship(
        "PropostaProduto",
        back_populates="proposta",
        cascade="all, delete-orphan",
    )

    simulacao = relationship(
        "Simulacao",
        uselist=False,
        back_populates="proposta",
        cascade="all, delete-orphan",
    )

    cotacoes = relationship(
        "CotacaoFrete",
        back_populates="proposta",
        cascade="all, delete-orphan",
    )

    envio = relationship(
        "EnvioProposta",
        uselist=False,
        back_populates="proposta",
        cascade="all, delete-orphan",
    )

    historico = relationship(
        "PropostaHistorico",
        back_populates="proposta",
        cascade="all, delete-orphan",
        order_by="PropostaHistorico.criado_em",
    )

    def todos_produtos_possuem_medidas(self) -> bool:
        return all(item.produto.possui_medidas_completas() for item in self.itens)

    def cubagem_final_m3(self) -> float | None:
        if self.cubagem_ajustada and self.cubagem_manual_m3 is not None:
            return self.cubagem_manual_m3
        return self.cubagem_m3

    @hybrid_property
    def valor_total(self) -> float:
        total = 0.0
        for item in self.itens:
            if item.preco_total is not None:
                total += item.preco_total
            else:
                # fallback para quantidade * preco_unitario quando preco_total não está preenchido
                if item.preco_unitario is not None and item.quantidade is not None:
                    total += item.preco_unitario * item.quantidade
        
        # Aplica desconto se existir
        if self.desconto is not None and self.desconto > 0:
            total -= self.desconto
        
        return total
    
    @property
    def display_numero(self) -> str:
        """Retorna o número da proposta para exibição (número do Bling se disponível, senão ID interno)"""
        if self.observacao_importacao and "bling_numero:" in self.observacao_importacao:
            try:
                numero_parte = self.observacao_importacao.split("bling_numero:")[1].split(";")[0].strip()
                return numero_parte
            except IndexError:
                return str(self.id)
        return str(self.id)
    
    @property
    def vendedor_bling(self) -> str | None:
        """Retorna o nome do vendedor do Bling (se disponível na observação)"""
        if self.observacao_importacao and "bling_vendedor:" in self.observacao_importacao:
            try:
                vendedor_parte = self.observacao_importacao.split("bling_vendedor:")[1].split(";")[0].strip()
                return vendedor_parte
            except IndexError:
                return None
        return None
    
    @property
    def tempo_atualizado(self) -> str:
        """Retorna tempo relativo desde a última atualização"""
        from utils.time import time_ago
        return time_ago(self.atualizado_em) if self.atualizado_em else time_ago(self.criado_em)


# ======================================================
# ITEM DA PROPOSTA
# ======================================================

class PropostaProduto(Base):
    __tablename__ = "propostas_produtos"

    id = Column(Integer, primary_key=True, index=True)

    proposta_id = Column(Integer, ForeignKey("propostas.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)

    quantidade = Column(Integer, nullable=False)

    codigo = Column(String(80))
    ncm = Column(String(20))
    preco_unitario = Column(Float)
    preco_total = Column(Float)
    imagem_url = Column(Text)

    proposta = relationship("Proposta", back_populates="itens")
    produto = relationship("Produto", back_populates="itens_proposta")


# ======================================================
# HISTÓRICO
# ======================================================

class PropostaHistorico(Base):
    __tablename__ = "propostas_historico"

    id = Column(Integer, primary_key=True, index=True)
    proposta_id = Column(Integer, ForeignKey("propostas.id"), nullable=False)

    status = Column(Enum(PropostaStatus), nullable=False)
    observacao = Column(Text)

    criado_em = Column(DateTime, default=datetime.utcnow)

    proposta = relationship("Proposta", back_populates="historico")


# ======================================================
# SIMULAÇÃO
# ======================================================

class Simulacao(Base):
    __tablename__ = "simulacoes"

    id = Column(Integer, primary_key=True, index=True)
    proposta_id = Column(Integer, ForeignKey("propostas.id"), unique=True)

    tipo = Column(Enum(TipoSimulacao), nullable=False)
    descricao = Column(Text)
    automatica = Column(Boolean, default=False)

    criado_em = Column(DateTime, default=datetime.utcnow)

    proposta = relationship("Proposta", back_populates="simulacao")


# ======================================================
# COTAÇÃO FRETE
# ======================================================

class CotacaoFrete(Base):
    __tablename__ = "cotacoes_frete"

    id = Column(Integer, primary_key=True, index=True)

    proposta_id = Column(Integer, ForeignKey("propostas.id"), nullable=False)
    transportadora_id = Column(Integer, ForeignKey("transportadoras.id"), nullable=False)

    numero_cotacao = Column(String, nullable=True)
    preco = Column(Float, nullable=False)
    prazo_dias = Column(Integer, nullable=False)

    selecionada = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)

    proposta = relationship("Proposta", back_populates="cotacoes")
    transportadora = relationship("Transportadora", back_populates="cotacoes")


# ======================================================
# TRANSPORTADORA
# ======================================================

class Transportadora(Base):
    __tablename__ = "transportadoras"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), unique=True, nullable=False)

    cotacoes = relationship("CotacaoFrete", back_populates="transportadora")


# ======================================================
# CAIXA
# ======================================================

class Caixa(Base):
    __tablename__ = "caixas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)

    altura_cm = Column(Float, nullable=False)
    largura_cm = Column(Float, nullable=False)
    comprimento_cm = Column(Float, nullable=False)

    criado_em = Column(DateTime, default=datetime.utcnow)

    @property
    def volume_cm3(self) -> float:
        return self.altura_cm * self.largura_cm * self.comprimento_cm


# ======================================================
# ENVIO
# ======================================================

class EnvioProposta(Base):
    __tablename__ = "envios_proposta"

    id = Column(Integer, primary_key=True, index=True)
    proposta_id = Column(Integer, ForeignKey("propostas.id"), unique=True)

    resumo_envio = Column(Text)
    meio_envio = Column(String(50))

    enviado = Column(Boolean, default=False)
    enviado_em = Column(DateTime)

    proposta = relationship("Proposta", back_populates="envio")
