BEGIN;

CREATE TABLE IF NOT EXISTS lote (
    id_lote BIGSERIAL PRIMARY KEY,
    id_colheita BIGINT NOT NULL REFERENCES colheita(id_colheita),
    id_produto BIGINT NOT NULL REFERENCES produto(id_produto),
    codigo_lote VARCHAR(120) NOT NULL UNIQUE,
    validade DATE,
    qualidade VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS certificacao_lote (
    id_cert_lote BIGSERIAL PRIMARY KEY,
    id_certificacao BIGINT NOT NULL REFERENCES certificacao(id_certificacao),
    id_lote BIGINT NOT NULL REFERENCES lote(id_lote),
    dt_emissao DATE,
    dt_validade DATE,
    numero_certificado VARCHAR(120) UNIQUE,
    status status_certificacao_enum NOT NULL,
    CONSTRAINT chk_certificacao_lote_periodo CHECK (dt_validade IS NULL OR dt_emissao IS NULL OR dt_validade >= dt_emissao)
);

CREATE TABLE IF NOT EXISTS local_armazenamento (
    id_local BIGSERIAL PRIMARY KEY,
    descricao VARCHAR(255) NOT NULL,
    capacidade NUMERIC(14, 2),
    CONSTRAINT chk_local_capacidade_pos CHECK (capacidade IS NULL OR capacidade > 0)
);

CREATE TABLE IF NOT EXISTS estoque (
    id_estoque BIGSERIAL PRIMARY KEY,
    id_local BIGINT NOT NULL REFERENCES local_armazenamento(id_local)
);

CREATE TABLE IF NOT EXISTS saldo_estoque (
    id_saldo BIGSERIAL PRIMARY KEY,
    id_estoque BIGINT NOT NULL REFERENCES estoque(id_estoque),
    id_produto BIGINT NOT NULL REFERENCES produto(id_produto),
    quantidade_atual NUMERIC(14, 2) NOT NULL,
    UNIQUE (id_estoque, id_produto),
    CONSTRAINT chk_saldo_quantidade_pos CHECK (quantidade_atual >= 0)
);

CREATE TABLE IF NOT EXISTS movimentacao_estoque (
    id_movimentacao BIGSERIAL PRIMARY KEY,
    id_estoque BIGINT NOT NULL REFERENCES estoque(id_estoque),
    id_produto BIGINT NOT NULL REFERENCES produto(id_produto),
    id_lote BIGINT REFERENCES lote(id_lote),
    tipo_movimentacao VARCHAR(50) NOT NULL,
    quantidade NUMERIC(14, 2) NOT NULL,
    data_movimentacao TIMESTAMP NOT NULL,
    CONSTRAINT chk_movimentacao_quantidade_pos CHECK (quantidade > 0)
);

CREATE TABLE IF NOT EXISTS entrada_estoque (
    id_entrada BIGSERIAL PRIMARY KEY,
    id_compra BIGINT NOT NULL REFERENCES compra(id_compra),
    id_movimentacao BIGINT NOT NULL REFERENCES movimentacao_estoque(id_movimentacao)
);

CREATE TABLE IF NOT EXISTS saida_estoque (
    id_saida BIGSERIAL PRIMARY KEY,
    id_movimentacao BIGINT NOT NULL REFERENCES movimentacao_estoque(id_movimentacao),
    id_atividade BIGINT NOT NULL REFERENCES atividade_agricola(id_atividade)
);

CREATE TABLE IF NOT EXISTS consumo_insumo (
    id_atividade BIGINT NOT NULL REFERENCES atividade_agricola(id_atividade),
    id_insumo BIGINT NOT NULL REFERENCES insumo(id_produto),
    id_lote BIGINT NOT NULL REFERENCES lote(id_lote),
    quantidade NUMERIC(14, 2) NOT NULL,
    PRIMARY KEY (id_atividade, id_insumo, id_lote),
    CONSTRAINT chk_consumo_insumo_quantidade_pos CHECK (quantidade > 0)
);

CREATE INDEX IF NOT EXISTS idx_lote_colheita ON lote(id_colheita);
CREATE INDEX IF NOT EXISTS idx_lote_produto ON lote(id_produto);
CREATE INDEX IF NOT EXISTS idx_mov_estoque ON movimentacao_estoque(id_estoque);
CREATE INDEX IF NOT EXISTS idx_mov_produto ON movimentacao_estoque(id_produto);

COMMIT;
