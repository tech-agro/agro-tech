BEGIN;

-- Conta a pagar originada por aplicacao de defensivo (fitossanidade).
ALTER TABLE conta_pagar
    ADD COLUMN IF NOT EXISTS id_aplicacao BIGINT
        REFERENCES aplicacao_defensivo(id_aplicacao);

CREATE INDEX IF NOT EXISTS idx_conta_pagar_aplicacao
    ON conta_pagar(id_aplicacao);

ALTER TABLE conta_pagar
    DROP CONSTRAINT IF EXISTS chk_conta_pagar_origem;

ALTER TABLE conta_pagar
    ADD CONSTRAINT chk_conta_pagar_origem
    CHECK (
        (
            (CASE WHEN id_compra IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN id_manutencao IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN id_despesa_logistica IS NOT NULL THEN 1 ELSE 0 END) +
            (CASE WHEN id_aplicacao IS NOT NULL THEN 1 ELSE 0 END)
        ) = 1
    );

-- Seed: contas a pagar para aplicacoes existentes sem conta.
INSERT INTO conta_pagar (id_aplicacao, valor, vencimento, status)
SELECT
    ad.id_aplicacao,
    ROUND(
        COALESCE(p.preco, 0) * COALESCE(ad.volume_aplicado, 0),
        2
    ),
    COALESCE(ad.dt_aplicacao, CURRENT_DATE) + 7,
    'ABERTA'::status_conta_pagar_enum
FROM aplicacao_defensivo ad
JOIN produto p ON p.id_produto = ad.id_insumo
WHERE COALESCE(p.preco, 0) * COALESCE(ad.volume_aplicado, 0) > 0
  AND NOT EXISTS (
      SELECT 1 FROM conta_pagar cp WHERE cp.id_aplicacao = ad.id_aplicacao
  );

COMMIT;
