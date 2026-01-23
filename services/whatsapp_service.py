import os
import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from models import Proposta, User, PropostaStatus, ContatoNotificacao, TipoNotificacao


class WhatsAppService:
    """Serviço para envio de notificações via WhatsApp usando Bot Conversa."""

    @staticmethod
    def enviar_notificacao_mudanca_status(
        db: Session,
        proposta: Proposta,
        novo_status: PropostaStatus,
    ) -> bool:
        """
        Envia notificação via WhatsApp baseado na mudança de status.
        
        Regras:
        - pendente_simulacao → contatos tipo "simulacao"
        - pendente_cotacao → contatos tipo "cotacao"
        - pendente_envio → vendedor responsável
        """
        load_dotenv()
        
        bot_token = os.getenv("WHATSAPP_BOT_CONVERSA_TOKEN")
        if not bot_token:
            return False
        
        telefones_destino = []
        mensagem = None
        
        if novo_status == PropostaStatus.pendente_simulacao:
            contatos = db.query(ContatoNotificacao).filter(
                ContatoNotificacao.tipo == TipoNotificacao.simulacao,
                ContatoNotificacao.ativo == True
            ).all()
            telefones_destino = [c.telefone for c in contatos]
            mensagem = WhatsAppService._mensagem_pendente_simulacao(proposta)
            
        elif novo_status == PropostaStatus.pendente_cotacao:
            contatos = db.query(ContatoNotificacao).filter(
                ContatoNotificacao.tipo == TipoNotificacao.cotacao,
                ContatoNotificacao.ativo == True
            ).all()
            telefones_destino = [c.telefone for c in contatos]
            mensagem = WhatsAppService._mensagem_pendente_cotacao(proposta)
            
        elif novo_status == PropostaStatus.pendente_envio:
            vendedor = db.query(User).filter(User.id == proposta.vendedor_id).first()
            if vendedor and vendedor.telefone:
                telefones_destino = [vendedor.telefone]
                mensagem = WhatsAppService._mensagem_pendente_envio(proposta, vendedor)
        
        if not telefones_destino or not mensagem:
            return False
        
        sucesso = True
        for telefone in telefones_destino:
            if not WhatsAppService._enviar_mensagem(bot_token, telefone, mensagem):
                sucesso = False
        
        return sucesso
    
    @staticmethod
    def _mensagem_pendente_simulacao(proposta: Proposta) -> str:
        cliente = proposta.cliente.nome if proposta.cliente else 'N/A'
        valor = proposta.valor_total or 0
        
        return f"""🔔 *Nova Proposta para Simulação*

📋 *Proposta #{proposta.id}*
👤 Cliente: {cliente}
💰 Valor: R$ {valor:,.2f}

⏰ Aguardando simulação de volumes."""
    
    @staticmethod
    def _mensagem_pendente_cotacao(proposta: Proposta) -> str:
        cliente = proposta.cliente.nome if proposta.cliente else 'N/A'
        valor = proposta.valor_total or 0
        cubagem = f"{proposta.cubagem_m3:.4f} m³" if proposta.cubagem_m3 else "N/A"
        peso = f"{proposta.peso_total_kg} kg" if proposta.peso_total_kg else "N/A"
        
        return f"""🔔 *Proposta Pronta para Cotação*

📋 *Proposta #{proposta.id}*
👤 Cliente: {cliente}
💰 Valor: R$ {valor:,.2f}

📦 Cubagem: {cubagem}
⚖️ Peso: {peso}

⏰ Aguardando cotação de frete."""
    
    @staticmethod
    def _mensagem_pendente_envio(proposta: Proposta, vendedor: User) -> str:
        cliente = proposta.cliente.nome if proposta.cliente else 'N/A'
        valor = proposta.valor_total or 0
        
        return f"""🔔 *Cotação Finalizada - Pronta para Envio*

Olá {vendedor.nome}! 👋

📋 *Proposta #{proposta.id}*
👤 Cliente: {cliente}
💰 Valor: R$ {valor:,.2f}

✅ A cotação está pronta para ser enviada ao cliente."""
    
    @staticmethod
    def _enviar_mensagem(bot_token: str, telefone: str, mensagem: str) -> bool:
        try:
            url = f"https://backend.botconversa.com.br/api/v1/webhooks-automation/catch/{bot_token}/"
            
            response = requests.post(
                url,
                json={"phone": telefone, "text": mensagem},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ WhatsApp enviado: {telefone}")
                return True
            
            print(f"❌ Erro WhatsApp ({response.status_code}): {response.text}")
            return False
                
        except Exception as e:
            print(f"❌ Erro ao enviar WhatsApp: {e}")
            return False
