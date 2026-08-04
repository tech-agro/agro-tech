BEGIN;

-- ============================================================
-- CONFIGURAÇÃO FINANCEIRA
-- ============================================================
-- Armazena parâmetros globais do módulo financeiro.
-- Inicialmente é utilizado apenas o limite para aprovação
-- automática de compras, mas a tabela pode receber outras
-- configurações futuramente.

CREATE TABLE IF NOT EXISTS configuracao_financeira (
    id_configuracao SMALLINT PRIMARY KEY DEFAULT 1,
    limite_aprovacao_automatica NUMERIC(14,2) NOT NULL,
    atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_configuracao_financeira_unica
        CHECK (id_configuracao = 1),

    CONSTRAINT chk_limite_aprovacao_pos
        CHECK (limite_aprovacao_automatica >= 0)
);

-- Configuração inicial do sistema.
INSERT INTO configuracao_financeira (
    id_configuracao,
    limite_aprovacao_automatica
)
SELECT
    1,
    10000.00
WHERE NOT EXISTS (
    SELECT 1
    FROM configuracao_financeira
);

-- ============================================================
-- DESPESAS DA OPERAÇÃO LOGÍSTICA
-- ============================================================
-- Cada operação logística pode gerar diversas despesas
-- (combustível, pedágio, frete, alimentação, etc.).
-- Essas despesas posteriormente poderão originar contas
-- a pagar no módulo financeiro.

CREATE TABLE IF NOT EXISTS despesa_operacao_logistica (
    id_despesa BIGSERIAL PRIMARY KEY,
    id_operacao BIGINT NOT NULL REFERENCES operacao_logistica(id_operacao),

    descricao VARCHAR(120) NOT NULL,
    tipo VARCHAR(50),
    valor NUMERIC(14,2) NOT NULL,
    data_despesa DATE NOT NULL DEFAULT CURRENT_DATE,

    CONSTRAINT chk_despesa_logistica_valor_pos
        CHECK (valor >= 0)
);

CREATE INDEX IF NOT EXISTS idx_despesa_operacao_logistica_operacao
ON despesa_operacao_logistica(id_operacao);

-- ============================================================
-- CONTA A PAGAR
-- ============================================================
-- Uma conta a pagar pode ser originada por diferentes módulos
-- do sistema. Apenas uma origem deve ser informada para cada
-- registro.

ALTER TABLE conta_pagar
    ALTER COLUMN id_compra DROP NOT NULL;

ALTER TABLE conta_pagar
    ADD COLUMN id_manutencao BIGINT REFERENCES manutencao(id_manutencao);

ALTER TABLE conta_pagar
    ADD COLUMN id_despesa_logistica BIGINT
        REFERENCES despesa_operacao_logistica(id_despesa);

ALTER TABLE conta_pagar
ADD CONSTRAINT chk_conta_pagar_origem
CHECK (
    (
        (CASE WHEN id_compra IS NOT NULL THEN 1 ELSE 0 END) +
        (CASE WHEN id_manutencao IS NOT NULL THEN 1 ELSE 0 END) +
        (CASE WHEN id_despesa_logistica IS NOT NULL THEN 1 ELSE 0 END)
    ) = 1
);

CREATE INDEX IF NOT EXISTS idx_conta_pagar_manutencao
ON conta_pagar(id_manutencao);

CREATE INDEX IF NOT EXISTS idx_conta_pagar_despesa_logistica
ON conta_pagar(id_despesa_logistica);

-- Apenas uma origem deve ser informada para cada registro de fluxo de caixa.
ALTER TABLE fluxo_caixa
ADD CONSTRAINT chk_fluxo_caixa_origem
CHECK (
    (
        (CASE WHEN id_conta_pagar IS NOT NULL THEN 1 ELSE 0 END) +
        (CASE WHEN id_conta_receber IS NOT NULL THEN 1 ELSE 0 END)
    ) = 1
);

-- ============================================================
-- FLUXO DE CAIXA — vínculo direto com pagamento/recebimento
-- ============================================================
-- Além da origem (conta a pagar / conta a receber), passamos a
-- guardar também qual pagamento ou recebimento específico gerou
-- o lançamento. Isso é necessário porque uma mesma conta pode ter
-- vários pagamentos/recebimentos ao longo do tempo, e sem esse
-- vínculo não é possível saber com certeza qual lançamento de
-- fluxo_caixa remover quando um pagamento/recebimento é excluído.
--
-- Nullable porque lançamentos criados antes desta migration não
-- possuem essa informação retroativamente.

ALTER TABLE fluxo_caixa
    ADD COLUMN id_pagamento BIGINT REFERENCES pagamento(id_pagamento);

ALTER TABLE fluxo_caixa
    ADD COLUMN id_recebimento BIGINT REFERENCES recebimento(id_recebimento);

CREATE INDEX IF NOT EXISTS idx_fluxo_caixa_pagamento
ON fluxo_caixa(id_pagamento);

CREATE INDEX IF NOT EXISTS idx_fluxo_caixa_recebimento
ON fluxo_caixa(id_recebimento);

-- Garante consistência: se id_pagamento estiver preenchido, o
-- lançamento deve ser de saída vinculado a conta_pagar; se
-- id_recebimento estiver preenchido, deve ser de entrada vinculado
-- a conta_receber.
ALTER TABLE fluxo_caixa
ADD CONSTRAINT chk_fluxo_caixa_pagamento_consistente
CHECK (
    id_pagamento IS NULL OR id_conta_pagar IS NOT NULL
);

ALTER TABLE fluxo_caixa
ADD CONSTRAINT chk_fluxo_caixa_recebimento_consistente
CHECK (
    id_recebimento IS NULL OR id_conta_receber IS NOT NULL
);

-- Cada pagamento/recebimento gera exatamente um lançamento de fluxo de caixa.
ALTER TABLE fluxo_caixa
ADD CONSTRAINT uq_fluxo_caixa_pagamento UNIQUE (id_pagamento);

ALTER TABLE fluxo_caixa
ADD CONSTRAINT uq_fluxo_caixa_recebimento UNIQUE (id_recebimento);

COMMIT;