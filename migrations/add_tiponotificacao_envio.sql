-- Migration: adiciona valor 'envio' ao enum tiponotificacao
-- Data: 2026-01-27
-- Descrição: habilita notificações WhatsApp na etapa de envio

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        JOIN pg_enum e ON t.oid = e.enumtypid
        WHERE t.typname = 'tiponotificacao'
          AND e.enumlabel = 'envio'
    ) THEN
        ALTER TYPE tiponotificacao ADD VALUE 'envio';
    END IF;
END $$;
