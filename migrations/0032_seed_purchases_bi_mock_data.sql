BEGIN;

-- =============================================================================
-- Mock purchases spread across safras so the Compras BI dashboard has volume,
-- supplier ranking and cost-by-harvest charts. Idempotent via (fornecedor, data).
-- Requires 0026 (fornecedor, produto, centro_custo, safra).
-- =============================================================================

INSERT INTO pedido (id_fornecedor, data_pedido, status, tipo_compra)
SELECT
    f.id_fornecedor,
    spec.data_pedido,
    'ATENDIDO'::status_pedido_compra_enum,
    'INSUMO'::tipo_compra_enum
FROM (
    VALUES
        (1, DATE '2024-10-12'),
        (2, DATE '2024-12-05'),
        (3, DATE '2025-02-18'),
        (5, DATE '2025-03-22'),
        (1, DATE '2025-10-08'),
        (6, DATE '2025-11-20'),
        (4, DATE '2026-01-15'),
        (8, DATE '2026-03-10'),
        (1, DATE '2026-09-10'),
        (7, DATE '2026-10-05'),
        (3, DATE '2026-11-12'),
        (2, DATE '2026-12-01')
) AS spec(forn_n, data_pedido)
JOIN pessoa pe ON pe.documento = 'DOC-FORN-' || lpad(spec.forn_n::text, 3, '0')
JOIN fornecedor f ON f.id_pessoa = pe.id_pessoa
WHERE NOT EXISTS (
    SELECT 1
    FROM pedido p
    WHERE p.id_fornecedor = f.id_fornecedor
      AND p.data_pedido = spec.data_pedido
);

INSERT INTO item_pedido (id_pedido, id_produto, quantidade, valor_unitario)
SELECT
    ped.id_pedido,
    prod.id_produto,
    spec.quantidade,
    spec.valor_unitario
FROM (
    VALUES
        (1, DATE '2024-10-12', 'Glifosato 480',                80.00,  32.00),
        (2, DATE '2024-12-05', 'Ureia 45%',                   120.00, 175.00),
        (3, DATE '2025-02-18', 'Semente de milho hibrido',     60.00,  45.00),
        (5, DATE '2025-03-22', 'MAP 11-52-00',                 50.00, 210.00),
        (1, DATE '2025-10-08', 'Oleo diesel S10',             220.00,   6.50),
        (6, DATE '2025-11-20', 'Herbicida atrazina',           40.00,  42.00),
        (4, DATE '2026-01-15', 'Inseticida lambda-cialotrina', 35.00,  95.00),
        (8, DATE '2026-03-10', 'KCl 60%',                      70.00, 165.00),
        (1, DATE '2026-09-10', 'Glifosato 480',                90.00,  34.00),
        (7, DATE '2026-10-05', 'Fungicida tebuconazol',        25.00,  78.00),
        (3, DATE '2026-11-12', 'Ureia 45%',                   110.00, 185.00),
        (2, DATE '2026-12-01', 'Semente de soja',              55.00,  38.00)
) AS spec(forn_n, data_pedido, produto, quantidade, valor_unitario)
JOIN pessoa pe ON pe.documento = 'DOC-FORN-' || lpad(spec.forn_n::text, 3, '0')
JOIN fornecedor f ON f.id_pessoa = pe.id_pessoa
JOIN pedido ped
    ON ped.id_fornecedor = f.id_fornecedor
   AND ped.data_pedido = spec.data_pedido
JOIN produto prod ON prod.nome = spec.produto
WHERE NOT EXISTS (
    SELECT 1 FROM item_pedido i WHERE i.id_pedido = ped.id_pedido
);

INSERT INTO compra (id_pedido, id_centro_custo, valor_total, data_compra)
SELECT
    ped.id_pedido,
    cc.id_centro_custo,
    spec.quantidade * spec.valor_unitario,
    spec.data_pedido
FROM (
    VALUES
        (1, DATE '2024-10-12', 'Glifosato 480',                80.00,  32.00),
        (2, DATE '2024-12-05', 'Ureia 45%',                   120.00, 175.00),
        (3, DATE '2025-02-18', 'Semente de milho hibrido',     60.00,  45.00),
        (5, DATE '2025-03-22', 'MAP 11-52-00',                 50.00, 210.00),
        (1, DATE '2025-10-08', 'Oleo diesel S10',             220.00,   6.50),
        (6, DATE '2025-11-20', 'Herbicida atrazina',           40.00,  42.00),
        (4, DATE '2026-01-15', 'Inseticida lambda-cialotrina', 35.00,  95.00),
        (8, DATE '2026-03-10', 'KCl 60%',                      70.00, 165.00),
        (1, DATE '2026-09-10', 'Glifosato 480',                90.00,  34.00),
        (7, DATE '2026-10-05', 'Fungicida tebuconazol',        25.00,  78.00),
        (3, DATE '2026-11-12', 'Ureia 45%',                   110.00, 185.00),
        (2, DATE '2026-12-01', 'Semente de soja',              55.00,  38.00)
) AS spec(forn_n, data_pedido, produto, quantidade, valor_unitario)
JOIN pessoa pe ON pe.documento = 'DOC-FORN-' || lpad(spec.forn_n::text, 3, '0')
JOIN fornecedor f ON f.id_pessoa = pe.id_pessoa
JOIN pedido ped
    ON ped.id_fornecedor = f.id_fornecedor
   AND ped.data_pedido = spec.data_pedido
JOIN centro_custo cc ON cc.nome = 'Centro de Custo 1'
WHERE NOT EXISTS (
    SELECT 1 FROM compra c WHERE c.id_pedido = ped.id_pedido
);

COMMIT;
