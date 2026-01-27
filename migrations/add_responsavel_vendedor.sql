-- Migration: Adiciona campos de vendedor responsável para notificações
-- Data: 2026-01-27
-- Descrição: Permite enviar mensagens de pendente_envio para o vendedor responsável de cada proposta

ALTER TABLE propostas
ADD COLUMN IF NOT EXISTS responsavel_vendedor VARCHAR(200),
ADD COLUMN IF NOT EXISTS responsavel_telefone VARCHAR(20);

COMMENT ON COLUMN propostas.responsavel_vendedor IS 'Nome do vendedor responsável (extraído do Bling)';
COMMENT ON COLUMN propostas.responsavel_telefone IS 'Telefone do vendedor responsável para notificações';
