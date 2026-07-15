BEGIN;

CREATE TABLE IF NOT EXISTS conta_pagar (
    id_conta_pagar BIGSERIAL PRIMARY KEY,
    id_compra BIGINT NOT NULL REFERENCES compra(id_compra),
    valor NUMERIC(14, 2) NOT NULL,
    vencimento DATE,
    status status_conta_pagar_enum NOT NULL,
    CONSTRAINT chk_conta_pagar_valor_pos CHECK (valor >= 0)
);

CREATE TABLE IF NOT EXISTS pagamento (
    id_pagamento BIGSERIAL PRIMARY KEY,
    id_conta_pagar BIGINT NOT NULL REFERENCES conta_pagar(id_conta_pagar),
    valor_pago NUMERIC(14, 2) NOT NULL,
    data_pagamento DATE,
    forma_pagamento VARCHAR(80),
    CONSTRAINT chk_pagamento_valor_pos CHECK (valor_pago >= 0)
);

CREATE TABLE IF NOT EXISTS conta_receber (
    id_conta_receber BIGSERIAL PRIMARY KEY,
    id_venda BIGINT NOT NULL REFERENCES venda(id_venda),
    valor NUMERIC(14, 2) NOT NULL,
    vencimento DATE,
    status status_conta_receber_enum NOT NULL,
    CONSTRAINT chk_conta_receber_valor_pos CHECK (valor >= 0)
);

CREATE TABLE IF NOT EXISTS recebimento (
    id_recebimento BIGSERIAL PRIMARY KEY,
    id_conta_receber BIGINT NOT NULL REFERENCES conta_receber(id_conta_receber),
    valor_recebido NUMERIC(14, 2) NOT NULL,
    data_recebimento DATE,
    forma_pagamento VARCHAR(80),
    CONSTRAINT chk_recebimento_valor_pos CHECK (valor_recebido >= 0)
);

CREATE TABLE IF NOT EXISTS fluxo_caixa (
    id_fluxo BIGSERIAL PRIMARY KEY,
    id_conta_pagar BIGINT REFERENCES conta_pagar(id_conta_pagar),
    id_conta_receber BIGINT REFERENCES conta_receber(id_conta_receber),
    valor NUMERIC(14, 2) NOT NULL,
    tipo VARCHAR(50),
    data_movimento DATE,
    CONSTRAINT chk_fluxo_caixa_valor_pos CHECK (valor >= 0)
);

CREATE INDEX IF NOT EXISTS idx_conta_pagar_compra ON conta_pagar(id_compra);
CREATE INDEX IF NOT EXISTS idx_pagamento_conta_pagar ON pagamento(id_conta_pagar);
CREATE INDEX IF NOT EXISTS idx_conta_receber_venda ON conta_receber(id_venda);
CREATE INDEX IF NOT EXISTS idx_recebimento_conta_receber ON recebimento(id_conta_receber);

COMMIT;
