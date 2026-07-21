BEGIN;

-- Rename legacy procurement tables to shorter domain names.

ALTER TABLE IF EXISTS pedido_compra RENAME TO pedido;
ALTER TABLE IF EXISTS item_pedido_compra RENAME TO item_pedido;

ALTER INDEX IF EXISTS idx_pedido_fornecedor RENAME TO idx_pedido_id_fornecedor;
ALTER INDEX IF EXISTS idx_item_pedido RENAME TO idx_item_pedido_id_pedido;
ALTER INDEX IF EXISTS idx_item_pedido_produto RENAME TO idx_item_pedido_id_produto;

ALTER SEQUENCE IF EXISTS pedido_compra_id_pedido_seq RENAME TO pedido_id_pedido_seq;
ALTER SEQUENCE IF EXISTS item_pedido_compra_id_item_seq RENAME TO item_pedido_id_item_seq;

COMMIT;
