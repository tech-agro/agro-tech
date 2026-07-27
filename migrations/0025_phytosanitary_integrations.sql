BEGIN;

-- Equipment used in the spray + warehouse/lot used for stock debit (reversal).
ALTER TABLE aplicacao_defensivo
    ADD COLUMN IF NOT EXISTS id_maquina BIGINT REFERENCES maquina(id_maquina),
    ADD COLUMN IF NOT EXISTS id_estoque_saida BIGINT REFERENCES estoque(id_estoque),
    ADD COLUMN IF NOT EXISTS id_lote_saida BIGINT REFERENCES lote(id_lote);

CREATE INDEX IF NOT EXISTS idx_aplicacao_defensivo_maquina
    ON aplicacao_defensivo(id_maquina);

-- Block harvest while a pesticide withdrawal period is still active on the planting.
CREATE OR REPLACE FUNCTION fn_bloquear_colheita_carencia()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_carencia DATE;
BEGIN
    SELECT MAX(ad.dt_carencia)
      INTO v_carencia
      FROM aplicacao_defensivo ad
      JOIN controle_fitossanitario cf ON cf.id_controle = ad.id_controle
     WHERE cf.id_plantio = NEW.id_plantio
       AND ad.dt_carencia IS NOT NULL;

    IF v_carencia IS NOT NULL
       AND COALESCE(NEW.dt_inicio, CURRENT_DATE) < v_carencia THEN
        RAISE EXCEPTION
            'Harvest blocked: phytosanitary withdrawal period active until %',
            v_carencia
            USING ERRCODE = 'check_violation';
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_colheita_carencia ON colheita;
CREATE TRIGGER trg_colheita_carencia
    BEFORE INSERT OR UPDATE OF dt_inicio, id_plantio ON colheita
    FOR EACH ROW
    EXECUTE PROCEDURE fn_bloquear_colheita_carencia();

COMMIT;
