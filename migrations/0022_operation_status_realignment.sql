BEGIN;

-- =============================================================================
-- status_operacao_logistica_enum:
--   PLANEJADA/EM_TRANSITO/FINALIZADA → ABERTA/EM_ANDAMENTO/CONCLUIDA
-- Operacao = visao gerencial; Expedicao = visao operacional (complementares).
-- =============================================================================

ALTER TYPE status_operacao_logistica_enum RENAME TO status_operacao_logistica_enum_old;

CREATE TYPE status_operacao_logistica_enum AS ENUM (
    'ABERTA',
    'EM_ANDAMENTO',
    'CONCLUIDA',
    'CANCELADA'
);

ALTER TABLE operacao_logistica
    ALTER COLUMN status TYPE status_operacao_logistica_enum
    USING (
        CASE status::text
            WHEN 'PLANEJADA' THEN 'ABERTA'
            WHEN 'EM_TRANSITO' THEN 'EM_ANDAMENTO'
            WHEN 'FINALIZADA' THEN 'CONCLUIDA'
            WHEN 'CANCELADA' THEN 'CANCELADA'
            WHEN 'ABERTA' THEN 'ABERTA'
            WHEN 'EM_ANDAMENTO' THEN 'EM_ANDAMENTO'
            WHEN 'CONCLUIDA' THEN 'CONCLUIDA'
            ELSE 'ABERTA'
        END
    )::status_operacao_logistica_enum;

DROP TYPE status_operacao_logistica_enum_old;

COMMIT;
