BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_lote_enum') THEN
        CREATE TYPE status_lote_enum AS ENUM ('EM_ANALISE', 'LIBERADO', 'BLOQUEADO');
    END IF;
END $$;

ALTER TABLE lote ADD COLUMN IF NOT EXISTS status status_lote_enum NOT NULL DEFAULT 'LIBERADO';

COMMIT;
