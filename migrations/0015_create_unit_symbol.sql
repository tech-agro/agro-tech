BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'unidade_sigla_enum') THEN
        CREATE TYPE unidade_sigla_enum AS ENUM ('KG', 'L', 'UN', 'SC', 'HA', 'T');
    END IF;
END $$;

COMMIT;
