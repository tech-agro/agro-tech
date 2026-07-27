BEGIN;

-- =============================================================================
-- Enriquecimento de expedicao (agrupa dados operacionais da saida).
-- Status continua automatico conforme eventos (carga / saida / entrega / cancelamento).
-- =============================================================================

ALTER TABLE expedicao
    ADD COLUMN IF NOT EXISTS data_chegada_prevista TIMESTAMP,
    ADD COLUMN IF NOT EXISTS data_entrega TIMESTAMP,
    ADD COLUMN IF NOT EXISTS motorista VARCHAR(120),
    ADD COLUMN IF NOT EXISTS observacoes TEXT;

COMMIT;
