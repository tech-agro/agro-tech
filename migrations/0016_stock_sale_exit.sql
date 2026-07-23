BEGIN;

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

COMMIT;