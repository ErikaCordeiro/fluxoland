-- Migration: Dashboard e WhatsApp Features
-- Data: 2026-01-23
-- Descrição: Adiciona suporte para dashboard e notificações WhatsApp

-- ==========================================
-- 1. ADICIONAR TELEFONE AOS USUÁRIOS
-- ==========================================
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS telefone VARCHAR(20);

COMMENT ON COLUMN users.telefone IS 'Telefone para notificações WhatsApp (formato: 5547999999999)';


-- ==========================================
-- 2. CRIAR ENUM PARA TIPO DE NOTIFICAÇÃO
-- ==========================================
DO $$ BEGIN
    CREATE TYPE tiponotificacao AS ENUM ('simulacao', 'cotacao');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;


-- ==========================================
-- 3. CRIAR TABELA DE CONTATOS NOTIFICAÇÃO
-- ==========================================
CREATE TABLE IF NOT EXISTS contatos_notificacao (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    tipo tiponotificacao NOT NULL,
    ativo BOOLEAN DEFAULT true
);

COMMENT ON TABLE contatos_notificacao IS 'Contatos que recebem notificações WhatsApp automáticas';
COMMENT ON COLUMN contatos_notificacao.tipo IS 'simulacao = notificado quando vai para pendente_simulacao, cotacao = notificado quando vai para pendente_cotacao';


-- ==========================================
-- 4. VERIFICAR ESTRUTURA EXISTENTE
-- ==========================================
-- Nada é deletado, apenas adicionado
-- Todas as tabelas e dados existentes são preservados
-- Dashboard usa apenas queries em tabelas existentes (propostas, clientes)


-- ==========================================
-- ROLLBACK (se necessário)
-- ==========================================
-- Para desfazer esta migração:
/*
DROP TABLE IF EXISTS contatos_notificacao;
DROP TYPE IF EXISTS tiponotificacao;
ALTER TABLE users DROP COLUMN IF EXISTS telefone;
*/
