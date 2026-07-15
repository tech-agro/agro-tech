BEGIN;

CREATE TABLE IF NOT EXISTS tipo_veiculo (
    id_tipo_veiculo BIGSERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL
);

CREATE TABLE IF NOT EXISTS veiculo (
    id_veiculo BIGSERIAL PRIMARY KEY,
    id_tipo_veiculo BIGINT NOT NULL REFERENCES tipo_veiculo(id_tipo_veiculo),
    placa VARCHAR(15) NOT NULL UNIQUE,
    capacidade NUMERIC(12, 2)
);

CREATE TABLE IF NOT EXISTS rota (
    id_rota BIGSERIAL PRIMARY KEY,
    origem VARCHAR(255) NOT NULL,
    destino VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS operacao_logistica (
    id_operacao BIGSERIAL PRIMARY KEY,
    id_veiculo BIGINT NOT NULL REFERENCES veiculo(id_veiculo),
    id_rota BIGINT NOT NULL REFERENCES rota(id_rota),
    id_venda BIGINT NOT NULL REFERENCES venda(id_venda),
    data_inicio TIMESTAMP,
    data_fim TIMESTAMP,
    status status_operacao_logistica_enum NOT NULL,
    CONSTRAINT chk_operacao_logistica_periodo CHECK (data_fim IS NULL OR data_inicio IS NULL OR data_fim >= data_inicio)
);

CREATE TABLE IF NOT EXISTS carga (
    id_carga BIGSERIAL PRIMARY KEY,
    id_operacao BIGINT NOT NULL REFERENCES operacao_logistica(id_operacao),
    id_lote BIGINT NOT NULL REFERENCES lote(id_lote),
    quantidade NUMERIC(12, 2),
    peso_previsto NUMERIC(12, 2),
    CONSTRAINT chk_carga_quantidade_pos CHECK (quantidade IS NULL OR quantidade > 0),
    CONSTRAINT chk_carga_peso_previsto_pos CHECK (peso_previsto IS NULL OR peso_previsto >= 0)
);

CREATE TABLE IF NOT EXISTS pesagem (
    id_pesagem BIGSERIAL PRIMARY KEY,
    id_carga BIGINT NOT NULL REFERENCES carga(id_carga),
    peso_registrado NUMERIC(12, 2),
    data_pesagem TIMESTAMP
);

CREATE TABLE IF NOT EXISTS expedicao (
    id_expedicao BIGSERIAL PRIMARY KEY,
    id_carga BIGINT NOT NULL UNIQUE REFERENCES carga(id_carga),
    data_saida TIMESTAMP,
    status status_expedicao_enum NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_operacao_logistica_venda ON operacao_logistica(id_venda);
CREATE INDEX IF NOT EXISTS idx_operacao_logistica_veiculo ON operacao_logistica(id_veiculo);
CREATE INDEX IF NOT EXISTS idx_carga_operacao ON carga(id_operacao);
CREATE INDEX IF NOT EXISTS idx_pesagem_carga ON pesagem(id_carga);

COMMIT;
