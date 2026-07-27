BEGIN;

-- Sale status
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_venda_enum') THEN
        CREATE TYPE status_venda_enum AS ENUM (
            'RASCUNHO',
            'CONFIRMADA',
            'CANCELADA'
        );
    END IF;
END $$;

ALTER TABLE venda
    ADD COLUMN IF NOT EXISTS status status_venda_enum NOT NULL DEFAULT 'CONFIRMADA';

-- Lot origin typing
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_origem_lote_enum') THEN
        CREATE TYPE tipo_origem_lote_enum AS ENUM (
            'COLHEITA',
            'COMPRA',
            'AJUSTE',
            'TRANSFERENCIA'
        );
    END IF;
END $$;

ALTER TABLE lote
    ADD COLUMN IF NOT EXISTS tipo_origem tipo_origem_lote_enum;

ALTER TABLE lote
    ADD COLUMN IF NOT EXISTS quantidade_inicial NUMERIC(14, 2);

UPDATE lote
SET tipo_origem = 'COLHEITA'
WHERE id_colheita IS NOT NULL AND tipo_origem IS NULL;

UPDATE lote
SET tipo_origem = 'COMPRA'
WHERE id_colheita IS NULL AND tipo_origem IS NULL;

ALTER TABLE lote
    ALTER COLUMN tipo_origem SET DEFAULT 'COMPRA';

ALTER TABLE lote
    ALTER COLUMN tipo_origem SET NOT NULL;

-- Balance per lot (traceability)
CREATE TABLE IF NOT EXISTS saldo_lote (
    id_saldo_lote BIGSERIAL PRIMARY KEY,
    id_estoque BIGINT NOT NULL REFERENCES estoque(id_estoque),
    id_lote BIGINT NOT NULL REFERENCES lote(id_lote),
    quantidade_atual NUMERIC(14, 2) NOT NULL DEFAULT 0,
    quantidade_reservada NUMERIC(14, 2) NOT NULL DEFAULT 0,
    UNIQUE (id_estoque, id_lote),
    CONSTRAINT chk_saldo_lote_quantidade_pos CHECK (quantidade_atual >= 0),
    CONSTRAINT chk_saldo_lote_reservada_pos CHECK (quantidade_reservada >= 0),
    CONSTRAINT chk_saldo_lote_reservada_lte_atual CHECK (quantidade_reservada <= quantidade_atual)
);

CREATE INDEX IF NOT EXISTS idx_saldo_lote_lote ON saldo_lote(id_lote);
CREATE INDEX IF NOT EXISTS idx_saldo_lote_estoque ON saldo_lote(id_estoque);

-- Backfill lot balances from existing movements (net qty per estoque+lote)
INSERT INTO saldo_lote (id_estoque, id_lote, quantidade_atual, quantidade_reservada)
SELECT
    m.id_estoque,
    m.id_lote,
    GREATEST(
        SUM(
            CASE
                WHEN m.tipo_movimentacao LIKE 'entrada%' THEN m.quantidade
                WHEN m.tipo_movimentacao LIKE 'saida%' THEN -m.quantidade
                ELSE 0
            END
        ),
        0
    ),
    0
FROM movimentacao_estoque m
WHERE m.id_lote IS NOT NULL
GROUP BY m.id_estoque, m.id_lote
ON CONFLICT (id_estoque, id_lote) DO NOTHING;

-- Multi-lot allocation on sale items
CREATE TABLE IF NOT EXISTS item_venda_lote (
    id_alocacao BIGSERIAL PRIMARY KEY,
    id_item_venda BIGINT NOT NULL REFERENCES item_venda(id_item_venda),
    id_lote BIGINT NOT NULL REFERENCES lote(id_lote),
    id_estoque BIGINT NOT NULL REFERENCES estoque(id_estoque),
    quantidade NUMERIC(14, 2) NOT NULL,
    UNIQUE (id_item_venda, id_lote, id_estoque),
    CONSTRAINT chk_item_venda_lote_qtd_pos CHECK (quantidade > 0)
);

CREATE INDEX IF NOT EXISTS idx_item_venda_lote_item ON item_venda_lote(id_item_venda);
CREATE INDEX IF NOT EXISTS idx_item_venda_lote_lote ON item_venda_lote(id_lote);

-- Backfill allocations from legacy item_venda.id_lote when present
INSERT INTO item_venda_lote (id_item_venda, id_lote, id_estoque, quantidade)
SELECT
    iv.id_item_venda,
    iv.id_lote,
    COALESCE(
        (
            SELECT se.id_estoque
            FROM saldo_estoque se
            WHERE se.id_produto = iv.id_produto
            ORDER BY se.quantidade_atual DESC
            LIMIT 1
        ),
        (SELECT e.id_estoque FROM estoque e ORDER BY e.id_estoque LIMIT 1)
    ),
    iv.quantidade
FROM item_venda iv
WHERE iv.id_lote IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM item_venda_lote ivl WHERE ivl.id_item_venda = iv.id_item_venda
  )
  AND EXISTS (SELECT 1 FROM estoque LIMIT 1);

-- Logistics: operation type + optional sale
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_operacao_logistica_enum') THEN
        CREATE TYPE tipo_operacao_logistica_enum AS ENUM (
            'VENDA',
            'COMPRA',
            'TRANSFERENCIA',
            'SERVICO'
        );
    END IF;
END $$;

ALTER TABLE operacao_logistica
    ADD COLUMN IF NOT EXISTS tipo tipo_operacao_logistica_enum NOT NULL DEFAULT 'VENDA';

ALTER TABLE operacao_logistica
    ALTER COLUMN id_venda DROP NOT NULL;

-- Load may reference the sale item that originated the picking
ALTER TABLE carga
    ADD COLUMN IF NOT EXISTS id_item_venda BIGINT REFERENCES item_venda(id_item_venda);

CREATE INDEX IF NOT EXISTS idx_carga_item_venda ON carga(id_item_venda);

-- Link logistic location to warehouse location (optional)
ALTER TABLE local_logistico
    ADD COLUMN IF NOT EXISTS id_local_armazenamento BIGINT
        REFERENCES local_armazenamento(id_local);

-- Typed movement kinds (column stays VARCHAR for compatibility; enum available)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_movimentacao_estoque_enum') THEN
        CREATE TYPE tipo_movimentacao_estoque_enum AS ENUM (
            'entrada_compra',
            'entrada_colheita',
            'saida_venda',
            'saida_atividade',
            'ajuste',
            'transferencia'
        );
    END IF;
END $$;

COMMIT;
