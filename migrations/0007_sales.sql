BEGIN;

CREATE TABLE IF NOT EXISTS venda (
    id_venda BIGSERIAL PRIMARY KEY,
    id_cliente BIGINT NOT NULL REFERENCES cliente(id_cliente),
    id_centro_custo BIGINT NOT NULL REFERENCES centro_custo(id_centro_custo),
    valor_total NUMERIC(14, 2) NOT NULL,
    data_venda DATE,
    CONSTRAINT chk_venda_valor_total_pos CHECK (valor_total >= 0)
);

CREATE TABLE IF NOT EXISTS item_venda (
    id_item_venda BIGSERIAL PRIMARY KEY,
    id_venda BIGINT NOT NULL REFERENCES venda(id_venda),
    id_produto BIGINT NOT NULL REFERENCES produto(id_produto),
    id_lote BIGINT REFERENCES lote(id_lote),
    quantidade NUMERIC(14, 2) NOT NULL,
    valor_unitario NUMERIC(14, 2) NOT NULL,
    CONSTRAINT chk_item_venda_quantidade_pos CHECK (quantidade > 0),
    CONSTRAINT chk_item_venda_valor_pos CHECK (valor_unitario >= 0)
);

CREATE INDEX IF NOT EXISTS idx_venda_cliente ON venda(id_cliente);
CREATE INDEX IF NOT EXISTS idx_venda_centro_custo ON venda(id_centro_custo);
CREATE INDEX IF NOT EXISTS idx_item_venda_venda ON item_venda(id_venda);
CREATE INDEX IF NOT EXISTS idx_item_venda_produto ON item_venda(id_produto);

COMMIT;
