BEGIN;

-- =============================================================================
-- Extra purchases so the Compras Sankey has real many-to-one flows.
-- High-volume inputs (Ureia, Diesel, MAP) get 2-3 competing suppliers.
-- Niche products from 0026 stay single-supplier.
-- Dates skip CURRENT_DATE-1..10 (used by 0026) and stay inside a 90-day window.
-- Idempotent via (fornecedor, data_pedido).
-- =============================================================================

INSERT INTO pedido (id_fornecedor, data_pedido, status, tipo_compra)
SELECT
    f.id_fornecedor,
    CURRENT_DATE - spec.dias,
    'ATENDIDO'::status_pedido_compra_enum,
    'INSUMO'::tipo_compra_enum
FROM (
    VALUES
        (1, 12),
        (2, 14),
        (5, 16),
        (1, 18),
        (3, 20),
        (8, 22),
        (2, 24),
        (4, 28),
        (7, 32)
) AS spec(forn_n, dias)
JOIN pessoa pe ON pe.documento = 'DOC-FORN-' || lpad(spec.forn_n::text, 3, '0')
JOIN fornecedor f ON f.id_pessoa = pe.id_pessoa
WHERE NOT EXISTS (
    SELECT 1
    FROM pedido p
    WHERE p.id_fornecedor = f.id_fornecedor
      AND p.data_pedido = CURRENT_DATE - spec.dias
);

INSERT INTO item_pedido (id_pedido, id_produto, quantidade, valor_unitario)
SELECT
    ped.id_pedido,
    prod.id_produto,
    spec.quantidade,
    spec.valor_unitario
FROM (
    VALUES
        (1, 12, 'Ureia 45%',          140.00, 172.00),
        (2, 14, 'Ureia 45%',           95.00, 180.00),
        (5, 16, 'Ureia 45%',           80.00, 188.00),
        (1, 18, 'Oleo diesel S10',    300.00,   6.40),
        (3, 20, 'Oleo diesel S10',    180.00,   6.70),
        (8, 22, 'Oleo diesel S10',    210.00,   6.55),
        (2, 24, 'MAP 11-52-00',        70.00, 205.00),
        (4, 28, 'MAP 11-52-00',        55.00, 218.00),
        (7, 32, 'MAP 11-52-00',        65.00, 212.00)
) AS spec(forn_n, dias, produto, quantidade, valor_unitario)
JOIN pessoa pe ON pe.documento = 'DOC-FORN-' || lpad(spec.forn_n::text, 3, '0')
JOIN fornecedor f ON f.id_pessoa = pe.id_pessoa
JOIN pedido ped
    ON ped.id_fornecedor = f.id_fornecedor
   AND ped.data_pedido = CURRENT_DATE - spec.dias
JOIN produto prod ON prod.nome = spec.produto
WHERE NOT EXISTS (
    SELECT 1 FROM item_pedido i WHERE i.id_pedido = ped.id_pedido
);

INSERT INTO compra (id_pedido, id_centro_custo, valor_total, data_compra)
SELECT
    ped.id_pedido,
    cc.id_centro_custo,
    spec.quantidade * spec.valor_unitario,
    CURRENT_DATE - spec.dias
FROM (
    VALUES
        (1, 12, 'Ureia 45%',          140.00, 172.00),
        (2, 14, 'Ureia 45%',           95.00, 180.00),
        (5, 16, 'Ureia 45%',           80.00, 188.00),
        (1, 18, 'Oleo diesel S10',    300.00,   6.40),
        (3, 20, 'Oleo diesel S10',    180.00,   6.70),
        (8, 22, 'Oleo diesel S10',    210.00,   6.55),
        (2, 24, 'MAP 11-52-00',        70.00, 205.00),
        (4, 28, 'MAP 11-52-00',        55.00, 218.00),
        (7, 32, 'MAP 11-52-00',        65.00, 212.00)
) AS spec(forn_n, dias, produto, quantidade, valor_unitario)
JOIN pessoa pe ON pe.documento = 'DOC-FORN-' || lpad(spec.forn_n::text, 3, '0')
JOIN fornecedor f ON f.id_pessoa = pe.id_pessoa
JOIN pedido ped
    ON ped.id_fornecedor = f.id_fornecedor
   AND ped.data_pedido = CURRENT_DATE - spec.dias
JOIN centro_custo cc ON cc.nome = 'Centro de Custo 1'
WHERE NOT EXISTS (
    SELECT 1 FROM compra c WHERE c.id_pedido = ped.id_pedido
);

COMMIT;
