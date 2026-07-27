BEGIN;

CREATE TABLE IF NOT EXISTS historico_manutencao (
    id_historico BIGSERIAL PRIMARY KEY,
    id_manutencao BIGINT NOT NULL REFERENCES manutencao(id_manutencao),
    observacao TEXT NOT NULL,
    dt_registro TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_historico_manutencao
    ON historico_manutencao(id_manutencao);

COMMIT;
