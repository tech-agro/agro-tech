BEGIN;

CREATE TABLE IF NOT EXISTS pedido_compra (
    id_pedido BIGSERIAL PRIMARY KEY,
    id_fornecedor BIGINT NOT NULL REFERENCES fornecedor(id_fornecedor),
    data_pedido DATE,
    status status_pedido_compra_enum NOT NULL
);

CREATE TABLE IF NOT EXISTS item_pedido_compra (
    id_item BIGSERIAL PRIMARY KEY,
    id_pedido BIGINT NOT NULL REFERENCES pedido_compra(id_pedido),
    id_produto BIGINT NOT NULL REFERENCES produto(id_produto),
    quantidade NUMERIC(12, 2) NOT NULL,
    valor_unitario NUMERIC(14, 2) NOT NULL,
    CONSTRAINT chk_item_pedido_quantidade_pos CHECK (quantidade > 0),
    CONSTRAINT chk_item_pedido_valor_pos CHECK (valor_unitario >= 0)
);

CREATE TABLE IF NOT EXISTS fornecedor_produto (
    id_fornecedor BIGINT NOT NULL REFERENCES fornecedor(id_fornecedor),
    id_produto BIGINT NOT NULL REFERENCES produto(id_produto),
    preco_referencia NUMERIC(14, 2),
    prazo_entrega_dias INTEGER,
    PRIMARY KEY (id_fornecedor, id_produto),
    CONSTRAINT chk_fornecedor_produto_preco_pos CHECK (preco_referencia IS NULL OR preco_referencia >= 0)
);

CREATE TABLE IF NOT EXISTS compra (
    id_compra BIGSERIAL PRIMARY KEY,
    id_pedido BIGINT NOT NULL REFERENCES pedido_compra(id_pedido),
    id_centro_custo BIGINT NOT NULL REFERENCES centro_custo(id_centro_custo),
    valor_total NUMERIC(14, 2) NOT NULL,
    data_compra DATE,
    CONSTRAINT chk_compra_valor_total_pos CHECK (valor_total >= 0)
);

CREATE INDEX IF NOT EXISTS idx_pedido_fornecedor ON pedido_compra(id_fornecedor);
CREATE INDEX IF NOT EXISTS idx_item_pedido ON item_pedido_compra(id_pedido);
CREATE INDEX IF NOT EXISTS idx_item_pedido_produto ON item_pedido_compra(id_produto);
CREATE INDEX IF NOT EXISTS idx_compra_centro_custo ON compra(id_centro_custo);

COMMIT;
