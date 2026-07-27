BEGIN;

-- -----------------------------------------------------------------------------
-- Despesas de operação logística (origem de contas a pagar)
-- -----------------------------------------------------------------------------
INSERT INTO despesa_operacao_logistica (
    id_operacao, descricao, tipo, valor, data_despesa
)
SELECT
    o.id_operacao,
    'Despesa Logistica ' || g.n,
    (ARRAY[
        'COMBUSTIVEL', 'PEDAGIO', 'FRETE', 'ALIMENTACAO', 'MANUTENCAO_ROTA',
        'COMBUSTIVEL', 'PEDAGIO', 'FRETE', 'ESTACIONAMENTO', 'OUTROS'
    ])[g.n],
    150.00 * g.n,
    CURRENT_DATE - g.n
FROM generate_series(1, 10) AS g(n)
JOIN operacao_logistica o
  ON o.id_operacao = (
      SELECT o2.id_operacao
      FROM operacao_logistica o2
      ORDER BY o2.id_operacao
      OFFSET (g.n - 1) % GREATEST((SELECT COUNT(*) FROM operacao_logistica), 1)
      LIMIT 1
  )
WHERE EXISTS (SELECT 1 FROM operacao_logistica)
  AND NOT EXISTS (
      SELECT 1
      FROM despesa_operacao_logistica d
      WHERE d.descricao = 'Despesa Logistica ' || g.n
  );

-- -----------------------------------------------------------------------------
-- Contas a pagar — origem compra
-- -----------------------------------------------------------------------------
INSERT INTO conta_pagar (id_compra, valor, vencimento, status)
SELECT
    c.id_compra,
    c.valor_total,
    CURRENT_DATE + ((g.n % 5) - 2),
    (ARRAY[
        'ABERTA', 'PARCIALMENTE_PAGA', 'PAGA', 'VENCIDA', 'ABERTA', 'CANCELADA'
    ])[g.n]::status_conta_pagar_enum
FROM generate_series(1, 6) AS g(n)
JOIN compra c
  ON c.id_compra = (
      SELECT c2.id_compra
      FROM compra c2
      ORDER BY c2.id_compra
      OFFSET g.n - 1
      LIMIT 1
  )
WHERE NOT EXISTS (
    SELECT 1 FROM conta_pagar cp WHERE cp.id_compra = c.id_compra
);

-- -----------------------------------------------------------------------------
-- Contas a pagar — origem manutenção
-- -----------------------------------------------------------------------------
INSERT INTO conta_pagar (id_manutencao, valor, vencimento, status)
SELECT
    m.id_manutencao,
    COALESCE(m.custo, 1000.00),
    CURRENT_DATE + ((g.n % 4) - 1),
    (ARRAY[
        'ABERTA', 'PARCIALMENTE_PAGA', 'PAGA', 'VENCIDA', 'ABERTA', 'ABERTA'
    ])[g.n]::status_conta_pagar_enum
FROM generate_series(1, 6) AS g(n)
JOIN manutencao m
  ON m.id_manutencao = (
      SELECT m2.id_manutencao
      FROM manutencao m2
      ORDER BY m2.id_manutencao
      OFFSET g.n - 1
      LIMIT 1
  )
WHERE NOT EXISTS (
    SELECT 1 FROM conta_pagar cp WHERE cp.id_manutencao = m.id_manutencao
);

-- -----------------------------------------------------------------------------
-- Contas a pagar — origem despesa logística
-- -----------------------------------------------------------------------------
INSERT INTO conta_pagar (id_despesa_logistica, valor, vencimento, status)
SELECT
    d.id_despesa,
    d.valor,
    d.data_despesa + 7,
    (ARRAY[
        'ABERTA', 'PARCIALMENTE_PAGA', 'PAGA', 'ABERTA'
    ])[g.n]::status_conta_pagar_enum
FROM generate_series(1, 4) AS g(n)
JOIN despesa_operacao_logistica d
  ON d.descricao = 'Despesa Logistica ' || g.n
WHERE NOT EXISTS (
    SELECT 1 FROM conta_pagar cp WHERE cp.id_despesa_logistica = d.id_despesa
);

-- -----------------------------------------------------------------------------
-- Contas a receber — a partir de vendas (exceto rascunho/cancelada)
-- -----------------------------------------------------------------------------
INSERT INTO conta_receber (id_venda, valor, vencimento, status)
SELECT
    v.id_venda,
    v.valor_total,
    COALESCE(v.data_venda, CURRENT_DATE) + 15,
    CASE
        WHEN v.status::text = 'ENTREGUE' THEN 'RECEBIDA'::status_conta_receber_enum
        WHEN v.status::text = 'EXPEDIDA' THEN 'PARCIALMENTE_RECEBIDA'::status_conta_receber_enum
        WHEN COALESCE(v.data_venda, CURRENT_DATE) < CURRENT_DATE - 20
            THEN 'VENCIDA'::status_conta_receber_enum
        ELSE 'ABERTA'::status_conta_receber_enum
    END
FROM venda v
WHERE v.status::text NOT IN ('RASCUNHO', 'CANCELADA')
  AND NOT EXISTS (
      SELECT 1 FROM conta_receber cr WHERE cr.id_venda = v.id_venda
  );

-- -----------------------------------------------------------------------------
-- Pagamentos (parcial/total) + fluxo de caixa de saída
-- -----------------------------------------------------------------------------
INSERT INTO pagamento (
    id_conta_pagar, valor_pago, data_pagamento, forma_pagamento
)
SELECT
    cp.id_conta_pagar,
    CASE
        WHEN cp.status = 'PAGA' THEN cp.valor
        WHEN cp.status = 'PARCIALMENTE_PAGA' THEN ROUND(cp.valor * 0.5, 2)
        ELSE ROUND(cp.valor * 0.3, 2)
    END,
    CURRENT_DATE - 3,
    (ARRAY['PIX', 'TED', 'BOLETO', 'DINHEIRO', 'CARTAO'])[
        ((cp.id_conta_pagar - 1) % 5) + 1
    ]
FROM conta_pagar cp
WHERE cp.status IN ('PAGA', 'PARCIALMENTE_PAGA')
  AND NOT EXISTS (
      SELECT 1 FROM pagamento p WHERE p.id_conta_pagar = cp.id_conta_pagar
  );

INSERT INTO fluxo_caixa (
    id_conta_pagar,
    id_conta_receber,
    id_pagamento,
    id_recebimento,
    valor,
    tipo,
    data_movimento
)
SELECT
    p.id_conta_pagar,
    NULL,
    p.id_pagamento,
    NULL,
    p.valor_pago,
    'SAIDA',
    COALESCE(p.data_pagamento, CURRENT_DATE)
FROM pagamento p
WHERE NOT EXISTS (
    SELECT 1 FROM fluxo_caixa f WHERE f.id_pagamento = p.id_pagamento
);

-- -----------------------------------------------------------------------------
-- Recebimentos (parcial/total) + fluxo de caixa de entrada
-- -----------------------------------------------------------------------------
INSERT INTO recebimento (
    id_conta_receber, valor_recebido, data_recebimento, forma_pagamento
)
SELECT
    cr.id_conta_receber,
    CASE
        WHEN cr.status = 'RECEBIDA' THEN cr.valor
        WHEN cr.status = 'PARCIALMENTE_RECEBIDA' THEN ROUND(cr.valor * 0.4, 2)
        ELSE ROUND(cr.valor * 0.25, 2)
    END,
    CURRENT_DATE - 2,
    (ARRAY['PIX', 'TED', 'BOLETO', 'DINHEIRO', 'CARTAO'])[
        ((cr.id_conta_receber - 1) % 5) + 1
    ]
FROM conta_receber cr
WHERE cr.status IN ('RECEBIDA', 'PARCIALMENTE_RECEBIDA')
  AND NOT EXISTS (
      SELECT 1 FROM recebimento r WHERE r.id_conta_receber = cr.id_conta_receber
  );

INSERT INTO fluxo_caixa (
    id_conta_pagar,
    id_conta_receber,
    id_pagamento,
    id_recebimento,
    valor,
    tipo,
    data_movimento
)
SELECT
    NULL,
    r.id_conta_receber,
    NULL,
    r.id_recebimento,
    r.valor_recebido,
    'ENTRADA',
    COALESCE(r.data_recebimento, CURRENT_DATE)
FROM recebimento r
WHERE NOT EXISTS (
    SELECT 1 FROM fluxo_caixa f WHERE f.id_recebimento = r.id_recebimento
);

COMMIT;
