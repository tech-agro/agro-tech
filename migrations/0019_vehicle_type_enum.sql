BEGIN;

-- =============================================================================
-- Tipo de veiculo como ENUM (fixo tipo_veiculo + FK).
-- Motivo: conjunto fechado de categorias; evita cadastro ad-hoc com poucos tipos.
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_veiculo_enum') THEN
        CREATE TYPE tipo_veiculo_enum AS ENUM (
            'CAMINHAO_GRANELEIRO',
            'CAMINHAO_BASCULANTE',
            'CAMINHAO_BAU',
            'CAMINHAO_TANQUE',
            'CARRETA_BASCULANTE',
            'BITREM',
            'RODOTREM',
            'TOCO',
            'TRUCK',
            'CAMIONETE',
            'UTILITARIO',
            'VAN',
            'TRATOR',
            'OUTRO'
        );
    END IF;
END $$;

ALTER TABLE veiculo
    ADD COLUMN IF NOT EXISTS tipo tipo_veiculo_enum;

UPDATE veiculo v
SET tipo = CASE
    WHEN lower(tv.nome) LIKE '%graneleiro%' THEN 'CAMINHAO_GRANELEIRO'::tipo_veiculo_enum
    WHEN lower(tv.nome) LIKE '%basculante%' AND lower(tv.nome) LIKE '%carreta%'
        THEN 'CARRETA_BASCULANTE'::tipo_veiculo_enum
    WHEN lower(tv.nome) LIKE '%basculante%' THEN 'CAMINHAO_BASCULANTE'::tipo_veiculo_enum
    WHEN lower(tv.nome) LIKE '%bau%' OR lower(tv.nome) LIKE '%baú%'
        THEN 'CAMINHAO_BAU'::tipo_veiculo_enum
    WHEN lower(tv.nome) LIKE '%tanque%' THEN 'CAMINHAO_TANQUE'::tipo_veiculo_enum
    WHEN lower(tv.nome) LIKE '%bitrem%' THEN 'BITREM'::tipo_veiculo_enum
    WHEN lower(tv.nome) LIKE '%rodotrem%' THEN 'RODOTREM'::tipo_veiculo_enum
    WHEN lower(tv.nome) LIKE '%toco%' THEN 'TOCO'::tipo_veiculo_enum
    WHEN lower(tv.nome) LIKE '%truck%' THEN 'TRUCK'::tipo_veiculo_enum
    WHEN lower(tv.nome) LIKE '%camionete%' OR lower(tv.nome) LIKE '%pickup%'
        THEN 'CAMIONETE'::tipo_veiculo_enum
    WHEN lower(tv.nome) LIKE '%utilitario%' OR lower(tv.nome) LIKE '%utilitário%'
        THEN 'UTILITARIO'::tipo_veiculo_enum
    WHEN lower(tv.nome) LIKE '%van%' THEN 'VAN'::tipo_veiculo_enum
    WHEN lower(tv.nome) LIKE '%trator%' THEN 'TRATOR'::tipo_veiculo_enum
    ELSE 'OUTRO'::tipo_veiculo_enum
END
FROM tipo_veiculo tv
WHERE v.id_tipo_veiculo = tv.id_tipo_veiculo
  AND v.tipo IS NULL;

UPDATE veiculo
SET tipo = 'OUTRO'::tipo_veiculo_enum
WHERE tipo IS NULL;

ALTER TABLE veiculo
    ALTER COLUMN tipo SET NOT NULL;

ALTER TABLE veiculo
    DROP CONSTRAINT IF EXISTS veiculo_id_tipo_veiculo_fkey;

ALTER TABLE veiculo
    DROP COLUMN IF EXISTS id_tipo_veiculo;

DROP TABLE IF EXISTS tipo_veiculo;

CREATE INDEX IF NOT EXISTS idx_veiculo_tipo ON veiculo(tipo);

COMMIT;
