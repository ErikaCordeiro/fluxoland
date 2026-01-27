import logging
import os
from typing import Optional

import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from models import Proposta, User, PropostaStatus, ContatoNotificacao, TipoNotificacao

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    Serviço centralizado para notificações via WhatsApp usando BotConversa.
    
    Responsabilidades:
    - Notificar contatos quando proposta muda de status
    - Gerar mensagens formatadas por tipo de notificação
    - Enviar via webhook automático do BotConversa
    """

    # Mapeamento de status para tipo de notificação
    STATUS_TIPO_NOTIFICACAO = {
        PropostaStatus.pendente_simulacao: TipoNotificacao.simulacao,
        PropostaStatus.pendente_cotacao: TipoNotificacao.cotacao,
        PropostaStatus.pendente_envio: TipoNotificacao.envio,
    }

    @staticmethod
    def enviar_notificacao_mudanca_status(
        db: Session,
        proposta: Proposta,
        novo_status: PropostaStatus,
    ) -> bool:
        """
        Notifica contatos relevantes quando proposta muda de status.
        
        Args:
            db: Sessão SQLAlchemy
            proposta: Proposta que mudou de status
            novo_status: Novo status da proposta
            
        Returns:
            True se mensagem foi enviada, False caso contrário
        """
        load_dotenv()
        bot_token = os.getenv("WHATSAPP_BOT_CONVERSA_TOKEN")
        
        if not bot_token:
            logger.error("WHATSAPP_BOT_CONVERSA_TOKEN não configurado em .env")
            return False

        # Para pendente_envio, notifica APENAS o vendedor responsável da proposta
        if novo_status == PropostaStatus.pendente_envio:
            if not proposta.responsavel_telefone:
                msg = f"⚠️ Proposta {proposta.id} sem vendedor responsável - notificação de envio não será enviada"
                logger.warning(msg)
                print(f"[WHATSAPP] Proposta {proposta.id} sem vendedor responsavel")
                return False
            
            telefones = [proposta.responsavel_telefone]
            msg = f"📤 Enviando notificação de ENVIO para vendedor: {proposta.responsavel_telefone}"
            logger.info(msg)
            print(f"[WHATSAPP] Notificacao ENVIO para: {proposta.responsavel_telefone}")
        else:
            # Para outros status, obtém contatos cadastrados no tipo de notificação
            tipo_notificacao = WhatsAppService.STATUS_TIPO_NOTIFICACAO.get(novo_status)
            if not tipo_notificacao:
                msg = f"⚠️ Nenhuma notificação configurada para status {novo_status}"
                logger.warning(msg)
                print(f"[WHATSAPP] Nenhuma notificacao configurada para status {novo_status}")
                return False

            contatos = db.query(ContatoNotificacao).filter(
                ContatoNotificacao.tipo == tipo_notificacao,
                ContatoNotificacao.ativo == True
            ).all()

            telefones = [c.telefone for c in contatos]
            msg = f"📋 Encontrados {len(contatos)} contatos para tipo {tipo_notificacao}: {[c.nome for c in contatos]}"
            logger.info(msg)
            print(f"[WHATSAPP] Encontrados {len(contatos)} contatos para {tipo_notificacao}: {[c.nome for c in contatos]}")
            
            if not telefones:
                msg = f"⚠️ Nenhum contato ativo para notificação tipo {tipo_notificacao}"
                logger.warning(msg)
                print(f"[WHATSAPP] Nenhum contato ativo para {tipo_notificacao}")
                return False

        # Gera mensagem
        mensagem = WhatsAppService._gerar_mensagem(novo_status, proposta)
        if not mensagem:
            msg = f"❌ Falha ao gerar mensagem para status {novo_status}"
            logger.error(msg)
            print(f"[WHATSAPP] ERRO: Falha ao gerar mensagem")
            return False

        msg = f"📨 Enviando mensagem para {len(telefones)} telefone(s): {telefones}"
        logger.info(msg)
        print(f"[WHATSAPP] Enviando para {len(telefones)} telefone(s): {telefones}")
        
        # Envia para todos os contatos
        resultados = [
            WhatsAppService._enviar_mensagem(bot_token, tel, mensagem)
            for tel in telefones
        ]
        
        sucesso = all(resultados)
        if sucesso:
            msg = f"✅ Todas as {len(telefones)} mensagens enviadas com sucesso"
            logger.info(msg)
            print(f"[WHATSAPP] SUCESSO: Todas as {len(telefones)} mensagens enviadas")
        else:
            falhas = sum(1 for r in resultados if not r)
            msg = f"❌ {falhas} de {len(telefones)} mensagens falharam"
            logger.error(msg)
            print(f"[WHATSAPP] ERRO: {falhas} de {len(telefones)} falharam")
        
        return sucesso
        
        return sucesso
    
    @staticmethod
    def _gerar_mensagem(status: PropostaStatus, proposta: Proposta) -> Optional[str]:
        """Gera mensagem formatada baseada no status."""
        cliente = proposta.cliente.nome if proposta.cliente else "N/A"
        valor = proposta.valor_total or 0
        numero = proposta.display_numero if hasattr(proposta, "display_numero") else str(proposta.id)

        if status == PropostaStatus.pendente_simulacao:
            return (
                f"🆕 *Nova Proposta #{numero}*\n"
                f"Cliente: {cliente}\n"
                f"Valor: R$ {valor:,.2f}\n"
                f"Status: Aguardando simulação"
            )

        elif status == PropostaStatus.pendente_cotacao:
            cubagem = f"{proposta.cubagem_m3:.4f} m³" if proposta.cubagem_m3 else "N/A"
            peso = f"{proposta.peso_total_kg} kg" if proposta.peso_total_kg else "N/A"
            return (
                f"📦 *Proposta #{numero} pronta para cotação*\n"
                f"Cliente: {cliente}\n"
                f"Valor: R$ {valor:,.2f}\n"
                f"Cubagem: {cubagem} | Peso: {peso}"
            )

        elif status == PropostaStatus.pendente_envio:
            return (
                f"📤 *Proposta #{numero} pronta para envio*\n"
                f"Cliente: {cliente}\n"
                f"Valor: R$ {valor:,.2f}\n"
                f"Cotação finalizada, aguarda envio ao cliente"
            )

        return None
    
    @staticmethod
    def _enviar_mensagem(bot_token: str, telefone: str, mensagem: str) -> bool:
        """
        Envia mensagem via webhook BotConversa.
        
        Args:
            bot_token: Token do webhook (ID/SECRET)
            telefone: Número WhatsApp destinatário
            mensagem: Texto da mensagem
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        try:
            url = f"https://new-backend.botconversa.com.br/api/v1/webhooks-automation/catch/{bot_token}/"
            payload = {"phone": telefone, "text": mensagem}
            
            msg = f"🔄 Enviando para BotConversa: {telefone}"
            logger.info(msg)
            print(f"[WHATSAPP] >> Enviando para {telefone}")
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code in [200, 201, 204]:
                msg = f"✅ WhatsApp enviado com sucesso para {telefone} (status {response.status_code})"
                logger.info(msg)
                print(f"[WHATSAPP] >> OK {telefone} (HTTP {response.status_code})")
                return True
            
            msg = f"❌ Falha ao enviar WhatsApp para {telefone}: HTTP {response.status_code} - {response.text}"
            logger.error(msg)
            print(f"[WHATSAPP] >> FALHA {telefone}: HTTP {response.status_code}")
            return False
                
        except Exception as e:
            msg = f"❌ Erro ao enviar WhatsApp para {telefone}: {e}"
            logger.exception(msg)
            print(f"[WHATSAPP] >> ERRO {telefone}: {e}")
            return False
