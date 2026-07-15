BEGIN;

CREATE TABLE IF NOT EXISTS indicador (
    id_indicador BIGSERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    unidade VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS medicao_indicador (
    id_medicao BIGSERIAL PRIMARY KEY,
    id_indicador BIGINT NOT NULL REFERENCES indicador(id_indicador),
    id_safra BIGINT NOT NULL REFERENCES safra(id_safra),
    valor NUMERIC(12, 2),
    data_referencia DATE
);

CREATE INDEX IF NOT EXISTS idx_medicao_indicador ON medicao_indicador(id_indicador);
CREATE INDEX IF NOT EXISTS idx_medicao_safra ON medicao_indicador(id_safra);

COMMIT;
