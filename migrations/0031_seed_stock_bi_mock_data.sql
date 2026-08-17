BEGIN;

-- =============================================================================
-- Mock data for the Estoque BI dashboard.
-- Idempotent via codigo_lote / movement timestamp fingerprint (08:17:00).
-- Requires 0026 (lotes, saldos, locais).
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Lotes: validade proxima + um bloqueado (itens criticos / vencendo)
-- -----------------------------------------------------------------------------
UPDATE lote
SET validade = CURRENT_DATE + 7
WHERE codigo_lote = 'LOTE-MILHO-001';

UPDATE lote
SET validade = CURRENT_DATE + 15
WHERE codigo_lote = 'LOTE-SOJA-002';

UPDATE lote
SET validade = CURRENT_DATE + 25
WHERE codigo_lote = 'LOTE-SORGO-003';

UPDATE lote
SET
    validade = CURRENT_DATE + 10,
    status = 'BLOQUEADO'::status_lote_enum
WHERE codigo_lote = 'LOTE-COMPRA-001';

-- Saldo baixo de ureia para aparecer como item critico (cobertura < 15 dias).
UPDATE saldo_lote sl
SET quantidade_atual = 18
FROM lote l
WHERE sl.id_lote = l.id_lote
  AND l.codigo_lote = 'LOTE-COMPRA-005';

UPDATE saldo_estoque se
SET quantidade_atual = 18
FROM produto p, estoque e, local_armazenamento la
WHERE se.id_produto = p.id_produto
  AND se.id_estoque = e.id_estoque
  AND e.id_local = la.id_local
  AND p.nome = 'Ureia 45%'
  AND la.descricao = 'Local Armazenamento 1';

-- -----------------------------------------------------------------------------
-- Movimentacoes: entradas e saidas nas ultimas ~12 semanas
-- Timestamp 08:17:00 marca o seed (nao colide com horario "cheio" da API).
-- -----------------------------------------------------------------------------
INSERT INTO movimentacao_estoque (
    id_estoque, id_produto, id_lote, tipo_movimentacao, quantidade, data_movimentacao
)
SELECT
    e.id_estoque,
    l.id_produto,
    l.id_lote,
    spec.tipo,
    spec.quantidade,
    ((CURRENT_DATE - (semana.n * 7) - spec.dias_offset)::timestamp + TIME '08:17:00')
FROM generate_series(1, 12) AS semana(n)
CROSS JOIN (
    VALUES
        ('LOTE-MILHO-001',  'entrada_colheita', 80.00, 2),
        ('LOTE-MILHO-001',  'saida_venda',      45.00, 0),
        ('LOTE-SOJA-002',   'entrada_colheita', 70.00, 2),
        ('LOTE-SOJA-002',   'saida_venda',      38.00, 0),
        ('LOTE-SORGO-003',  'entrada_colheita', 55.00, 2),
        ('LOTE-SORGO-003',  'saida_venda',      22.00, 0),
        ('LOTE-TRIGO-004',  'entrada_colheita', 60.00, 2),
        ('LOTE-TRIGO-004',  'saida_venda',      30.00, 0),
        ('LOTE-COMPRA-001', 'entrada_compra',   40.00, 3),
        ('LOTE-COMPRA-001', 'saida_atividade',  12.00, 1),
        ('LOTE-COMPRA-002', 'entrada_compra',   35.00, 3),
        ('LOTE-COMPRA-002', 'saida_atividade',  18.00, 1),
        ('LOTE-COMPRA-005', 'entrada_compra',   25.00, 3),
        ('LOTE-COMPRA-005', 'saida_atividade',  20.00, 1),
        ('LOTE-COMPRA-008', 'entrada_compra',   50.00, 3),
        ('LOTE-COMPRA-008', 'saida_atividade',  28.00, 1)
) AS spec(codigo_lote, tipo, quantidade, dias_offset)
JOIN lote l ON l.codigo_lote = spec.codigo_lote
JOIN local_armazenamento la ON la.descricao = 'Local Armazenamento 1'
JOIN estoque e ON e.id_local = la.id_local
WHERE ((CURRENT_DATE - (semana.n * 7) - spec.dias_offset)::timestamp + TIME '08:17:00')
        <= CURRENT_TIMESTAMP
  AND NOT EXISTS (
        SELECT 1
        FROM movimentacao_estoque m
        WHERE m.id_lote = l.id_lote
          AND m.tipo_movimentacao = spec.tipo
          AND m.data_movimentacao
              = ((CURRENT_DATE - (semana.n * 7) - spec.dias_offset)::timestamp
                 + TIME '08:17:00')
    );

COMMIT;
