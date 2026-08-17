BEGIN;

-- =============================================================================
-- Mock data for purchase requests, quotations, invoices and equipment detail.
-- Idempotent via observacao / unique keys. Requires 0026 + 0029.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Solicitacoes (10): mix of status and tipo
-- -----------------------------------------------------------------------------
INSERT INTO solicitacao_compra (
    data_solicitacao, status, tipo_compra, observacao,
    id_tipo_maquina, patrimonio, id_fazenda
)
SELECT
    CURRENT_DATE - g.n,
    (ARRAY[
        'RASCUNHO',
        'RASCUNHO',
        'ENVIADA',
        'APROVADA',
        'APROVADA',
        'REJEITADA',
        'CANCELADA',
        'APROVADA',
        'ENVIADA',
        'RASCUNHO'
    ])[g.n]::status_solicitacao_compra_enum,
    (ARRAY[
        'INSUMO',
        'INSUMO',
        'INSUMO',
        'INSUMO',
        'INSUMO',
        'INSUMO',
        'INSUMO',
        'EQUIPAMENTO',
        'EQUIPAMENTO',
        'EQUIPAMENTO'
    ])[g.n]::tipo_compra_enum,
    'SEED-SOL-' || lpad(g.n::text, 2, '0'),
    CASE WHEN g.n >= 8 THEN tm.id_tipo_maquina END,
    CASE WHEN g.n >= 8 THEN 'PAT-SEED-' || lpad(g.n::text, 3, '0') END,
    CASE WHEN g.n >= 8 THEN f.id_fazenda END
FROM generate_series(1, 10) AS g(n)
LEFT JOIN tipo_maquina tm ON tm.descricao = 'Tipo Maquina ' || ((g.n - 1) % 12 + 1)
LEFT JOIN fazenda f ON f.nome = 'Fazenda ' || ((g.n - 1) % 12 + 1)
WHERE NOT EXISTS (
    SELECT 1
    FROM solicitacao_compra s
    WHERE s.observacao = 'SEED-SOL-' || lpad(g.n::text, 2, '0')
);

INSERT INTO item_solicitacao_compra (id_solicitacao, id_produto, quantidade)
SELECT
    s.id_solicitacao,
    p.id_produto,
    10 + g.n
FROM generate_series(1, 10) AS g(n)
JOIN solicitacao_compra s
    ON s.observacao = 'SEED-SOL-' || lpad(g.n::text, 2, '0')
JOIN produto p ON p.nome = (ARRAY[
    'Glifosato 480',
    'Oleo diesel S10',
    'Ureia 45%',
    'Inseticida lambda-cialotrina',
    'Fungicida tebuconazol',
    'MAP 11-52-00',
    'KCl 60%',
    'Semente de milho hibrido',
    'Semente de soja',
    'Herbicida atrazina'
])[g.n]
WHERE NOT EXISTS (
    SELECT 1
    FROM item_solicitacao_compra i
    WHERE i.id_solicitacao = s.id_solicitacao
);

-- Segundo item nas solicitacoes de insumo para a grade nao ficar com uma linha so.
INSERT INTO item_solicitacao_compra (id_solicitacao, id_produto, quantidade)
SELECT
    s.id_solicitacao,
    p.id_produto,
    5 + g.n
FROM generate_series(1, 7) AS g(n)
JOIN solicitacao_compra s
    ON s.observacao = 'SEED-SOL-' || lpad(g.n::text, 2, '0')
JOIN produto p ON p.nome = (ARRAY[
    'Ureia 45%',
    'KCl 60%',
    'Glifosato 480',
    'Oleo diesel S10',
    'MAP 11-52-00',
    'Herbicida atrazina',
    'Semente de soja'
])[g.n]
WHERE NOT EXISTS (
    SELECT 1
    FROM item_solicitacao_compra i
    WHERE i.id_solicitacao = s.id_solicitacao AND i.id_produto = p.id_produto
);

-- -----------------------------------------------------------------------------
-- Cotacoes para solicitacoes APROVADAS de insumo (04 e 05)
-- -----------------------------------------------------------------------------
INSERT INTO cotacao_compra (
    id_solicitacao, id_fornecedor, status, prazo_entrega_dias, observacao
)
SELECT
    s.id_solicitacao,
    f.id_fornecedor,
    v.status::status_cotacao_compra_enum,
    v.prazo,
    v.obs
FROM (VALUES
    (4, 1, 'ENVIADA', 7, 'SEED-COT-04-A'),
    (4, 2, 'ENVIADA', 10, 'SEED-COT-04-B'),
    (5, 3, 'VENCEDORA', 5, 'SEED-COT-05-A'),
    (5, 4, 'DESCARTADA', 12, 'SEED-COT-05-B')
) AS v(sol_n, forn_n, status, prazo, obs)
JOIN solicitacao_compra s
    ON s.observacao = 'SEED-SOL-' || lpad(v.sol_n::text, 2, '0')
JOIN pessoa pe ON pe.documento = 'DOC-FORN-' || lpad(v.forn_n::text, 3, '0')
JOIN fornecedor f ON f.id_pessoa = pe.id_pessoa
WHERE NOT EXISTS (
    SELECT 1 FROM cotacao_compra c WHERE c.observacao = v.obs
);

INSERT INTO item_cotacao_compra (id_cotacao, id_produto, quantidade, preco_unitario)
SELECT
    c.id_cotacao,
    isi.id_produto,
    isi.quantidade,
    COALESCE(p.preco, 10.00) * CASE
        WHEN c.observacao LIKE '%-A' THEN 1.00
        ELSE 1.12
    END
FROM cotacao_compra c
JOIN item_solicitacao_compra isi ON isi.id_solicitacao = c.id_solicitacao
JOIN produto p ON p.id_produto = isi.id_produto
WHERE c.observacao LIKE 'SEED-COT-%'
  AND NOT EXISTS (
      SELECT 1
      FROM item_cotacao_compra ic
      WHERE ic.id_cotacao = c.id_cotacao AND ic.id_produto = isi.id_produto
  );

-- Pedido gerado a partir da solicitacao 05 (vencedora).
INSERT INTO pedido (
    id_fornecedor, data_pedido, status, id_solicitacao, tipo_compra
)
SELECT
    f.id_fornecedor,
    CURRENT_DATE - 5,
    'ABERTO'::status_pedido_compra_enum,
    s.id_solicitacao,
    'INSUMO'::tipo_compra_enum
FROM solicitacao_compra s
JOIN cotacao_compra c ON c.id_solicitacao = s.id_solicitacao
    AND c.status = 'VENCEDORA'::status_cotacao_compra_enum
    AND c.observacao = 'SEED-COT-05-A'
JOIN fornecedor f ON f.id_fornecedor = c.id_fornecedor
WHERE s.observacao = 'SEED-SOL-05'
  AND NOT EXISTS (
      SELECT 1 FROM pedido ped WHERE ped.id_solicitacao = s.id_solicitacao
  );

INSERT INTO item_pedido (id_pedido, id_produto, quantidade, valor_unitario)
SELECT
    ped.id_pedido,
    ic.id_produto,
    ic.quantidade,
    ic.preco_unitario
FROM solicitacao_compra s
JOIN pedido ped ON ped.id_solicitacao = s.id_solicitacao
JOIN cotacao_compra c ON c.id_solicitacao = s.id_solicitacao
    AND c.status = 'VENCEDORA'::status_cotacao_compra_enum
JOIN item_cotacao_compra ic ON ic.id_cotacao = c.id_cotacao
WHERE s.observacao = 'SEED-SOL-05'
  AND NOT EXISTS (
      SELECT 1 FROM item_pedido i WHERE i.id_pedido = ped.id_pedido
  );

-- Detalhe de equipamento nas solicitacoes 08-10 (ainda sem pedido).
-- Nada a inserir em detalhe_compra_equipamento ate nascer pedido.

-- -----------------------------------------------------------------------------
-- Notas fiscais em pedidos ja existentes (aprovados/atendidos)
-- -----------------------------------------------------------------------------
INSERT INTO nota_fiscal_compra (
    id_pedido, id_fornecedor, numero, serie, data_emissao, valor_total, chave_acesso
)
SELECT
    ped.id_pedido,
    ped.id_fornecedor,
    'NF-SEED-' || lpad(row_n::text, 4, '0'),
    '1',
    COALESCE(ped.data_pedido, CURRENT_DATE) + 2,
    GREATEST(COALESCE(c.valor_total, 100.00), 0.01),
    NULL
FROM (
    SELECT
        p.id_pedido,
        p.id_fornecedor,
        p.data_pedido,
        ROW_NUMBER() OVER (ORDER BY p.id_pedido) AS row_n
    FROM pedido p
    WHERE p.status IN (
        'APROVADO'::status_pedido_compra_enum,
        'PARCIALMENTE_ATENDIDO'::status_pedido_compra_enum,
        'ATENDIDO'::status_pedido_compra_enum
    )
) ped
LEFT JOIN compra c ON c.id_pedido = ped.id_pedido
WHERE ped.row_n <= 4
  AND NOT EXISTS (
      SELECT 1
      FROM nota_fiscal_compra nf
      WHERE nf.numero = 'NF-SEED-' || lpad(ped.row_n::text, 4, '0')
        AND nf.serie = '1'
        AND nf.id_fornecedor = ped.id_fornecedor
  );

COMMIT;
