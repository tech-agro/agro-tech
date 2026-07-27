BEGIN;

-- Sale lifecycle continues after confirmation: shipped / delivered
ALTER TYPE status_venda_enum ADD VALUE IF NOT EXISTS 'EXPEDIDA';
ALTER TYPE status_venda_enum ADD VALUE IF NOT EXISTS 'ENTREGUE';

-- Optional planned logistics cost on the operation (feeds Financeiro)
ALTER TABLE operacao_logistica
    ADD COLUMN IF NOT EXISTS custo_previsto NUMERIC(14, 2);

ALTER TABLE operacao_logistica
    DROP CONSTRAINT IF EXISTS chk_operacao_custo_previsto_pos;

ALTER TABLE operacao_logistica
    ADD CONSTRAINT chk_operacao_custo_previsto_pos
    CHECK (custo_previsto IS NULL OR custo_previsto >= 0);

-- Intelligence measurements may be recorded without a crop season
ALTER TABLE medicao_indicador
    ALTER COLUMN id_safra DROP NOT NULL;

-- Seed logistics KPIs (idempotent)
INSERT INTO indicador (nome, unidade)
SELECT v.nome, v.unidade
FROM (
    VALUES
        ('Entregas logisticas concluidas', 'UN'),
        ('Expedicoes iniciadas', 'UN'),
        ('Custo logistico acumulado', 'BRL')
) AS v(nome, unidade)
WHERE NOT EXISTS (
    SELECT 1 FROM indicador i WHERE i.nome = v.nome
);

COMMIT;
