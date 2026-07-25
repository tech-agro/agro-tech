BEGIN;

ALTER TABLE lote ALTER COLUMN id_colheita DROP NOT NULL;

CREATE TABLE IF NOT EXISTS saida_venda_estoque (
    id_saida_venda BIGSERIAL PRIMARY KEY,
    id_movimentacao BIGINT NOT NULL UNIQUE REFERENCES movimentacao_estoque(id_movimentacao),
    id_item_venda BIGINT NOT NULL REFERENCES item_venda(id_item_venda)
);

CREATE INDEX IF NOT EXISTS idx_saida_venda_item ON saida_venda_estoque(id_item_venda);
CREATE INDEX IF NOT EXISTS idx_mov_lote ON movimentacao_estoque(id_lote);
CREATE INDEX IF NOT EXISTS idx_saldo_produto ON saldo_estoque(id_produto);
CREATE INDEX IF NOT EXISTS idx_cert_lote ON certificacao_lote(id_lote);

ALTER TABLE entrada_estoque ADD CONSTRAINT uq_entrada_movimentacao UNIQUE (id_movimentacao);
ALTER TABLE saida_estoque ADD CONSTRAINT uq_saida_movimentacao UNIQUE (id_movimentacao);

CREATE TABLE IF NOT EXISTS recebimento_compra (
    id_recebimento BIGSERIAL PRIMARY KEY,
    id_item_pedido BIGINT NOT NULL REFERENCES item_pedido(id_item),
    id_estoque BIGINT NOT NULL REFERENCES estoque(id_estoque),
    id_movimentacao BIGINT NOT NULL UNIQUE REFERENCES movimentacao_estoque(id_movimentacao),
    quantidade_recebida NUMERIC(14, 2) NOT NULL,
    data_recebimento TIMESTAMP NOT NULL,
    CONSTRAINT chk_recebimento_quantidade_pos CHECK (quantidade_recebida > 0)
);

CREATE INDEX IF NOT EXISTS idx_recebimento_item ON recebimento_compra(id_item_pedido);
CREATE INDEX IF NOT EXISTS idx_recebimento_estoque ON recebimento_compra(id_estoque);

CREATE TABLE IF NOT EXISTS entrada_colheita_estoque (
    id_entrada_colheita BIGSERIAL PRIMARY KEY,
    id_colheita BIGINT NOT NULL REFERENCES colheita(id_colheita),
    id_movimentacao BIGINT NOT NULL UNIQUE REFERENCES movimentacao_estoque(id_movimentacao)
);

CREATE INDEX IF NOT EXISTS idx_entrada_colheita_colheita ON entrada_colheita_estoque(id_colheita);

COMMIT;