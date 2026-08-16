BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_solicitacao_compra_enum') THEN
        CREATE TYPE status_solicitacao_compra_enum AS ENUM (
            'RASCUNHO', 'ENVIADA', 'APROVADA', 'REJEITADA', 'CANCELADA'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_compra_enum') THEN
        CREATE TYPE tipo_compra_enum AS ENUM ('INSUMO', 'EQUIPAMENTO');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_cotacao_compra_enum') THEN
        CREATE TYPE status_cotacao_compra_enum AS ENUM (
            'RASCUNHO', 'ENVIADA', 'VENCEDORA', 'DESCARTADA'
        );
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS solicitacao_compra (
    id_solicitacao BIGSERIAL PRIMARY KEY,
    data_solicitacao DATE NOT NULL DEFAULT CURRENT_DATE,
    status status_solicitacao_compra_enum NOT NULL DEFAULT 'RASCUNHO',
    tipo_compra tipo_compra_enum NOT NULL DEFAULT 'INSUMO',
    observacao TEXT,
    id_tipo_maquina BIGINT REFERENCES tipo_maquina(id_tipo_maquina),
    patrimonio VARCHAR(80),
    id_fazenda BIGINT REFERENCES fazenda(id_fazenda)
);

CREATE TABLE IF NOT EXISTS item_solicitacao_compra (
    id_item BIGSERIAL PRIMARY KEY,
    id_solicitacao BIGINT NOT NULL REFERENCES solicitacao_compra(id_solicitacao) ON DELETE CASCADE,
    id_produto BIGINT NOT NULL REFERENCES produto(id_produto),
    quantidade NUMERIC(12, 2) NOT NULL,
    CONSTRAINT chk_item_solicitacao_quantidade_pos CHECK (quantidade > 0)
);

ALTER TABLE pedido
    ADD COLUMN IF NOT EXISTS id_solicitacao BIGINT REFERENCES solicitacao_compra(id_solicitacao),
    ADD COLUMN IF NOT EXISTS tipo_compra tipo_compra_enum NOT NULL DEFAULT 'INSUMO';

CREATE TABLE IF NOT EXISTS cotacao_compra (
    id_cotacao BIGSERIAL PRIMARY KEY,
    id_solicitacao BIGINT NOT NULL REFERENCES solicitacao_compra(id_solicitacao) ON DELETE CASCADE,
    id_fornecedor BIGINT NOT NULL REFERENCES fornecedor(id_fornecedor),
    status status_cotacao_compra_enum NOT NULL DEFAULT 'RASCUNHO',
    prazo_entrega_dias INTEGER,
    observacao TEXT,
    CONSTRAINT chk_cotacao_prazo_pos CHECK (prazo_entrega_dias IS NULL OR prazo_entrega_dias >= 0)
);

CREATE TABLE IF NOT EXISTS item_cotacao_compra (
    id_item_cotacao BIGSERIAL PRIMARY KEY,
    id_cotacao BIGINT NOT NULL REFERENCES cotacao_compra(id_cotacao) ON DELETE CASCADE,
    id_produto BIGINT NOT NULL REFERENCES produto(id_produto),
    quantidade NUMERIC(12, 2) NOT NULL,
    preco_unitario NUMERIC(14, 2) NOT NULL,
    CONSTRAINT chk_item_cotacao_quantidade_pos CHECK (quantidade > 0),
    CONSTRAINT chk_item_cotacao_preco_pos CHECK (preco_unitario >= 0)
);

CREATE TABLE IF NOT EXISTS nota_fiscal_compra (
    id_nota_fiscal BIGSERIAL PRIMARY KEY,
    id_pedido BIGINT NOT NULL REFERENCES pedido(id_pedido) ON DELETE CASCADE,
    id_fornecedor BIGINT NOT NULL REFERENCES fornecedor(id_fornecedor),
    numero VARCHAR(30) NOT NULL,
    serie VARCHAR(10) NOT NULL,
    data_emissao DATE NOT NULL,
    valor_total NUMERIC(14, 2) NOT NULL,
    chave_acesso VARCHAR(44),
    CONSTRAINT chk_nota_fiscal_valor_pos CHECK (valor_total > 0),
    CONSTRAINT uq_nota_fiscal_numero_serie_fornecedor UNIQUE (numero, serie, id_fornecedor)
);

CREATE TABLE IF NOT EXISTS detalhe_compra_equipamento (
    id_pedido BIGINT PRIMARY KEY REFERENCES pedido(id_pedido) ON DELETE CASCADE,
    id_tipo_maquina BIGINT NOT NULL REFERENCES tipo_maquina(id_tipo_maquina),
    patrimonio VARCHAR(80),
    id_fazenda BIGINT NOT NULL REFERENCES fazenda(id_fazenda),
    id_maquina BIGINT REFERENCES maquina(id_maquina)
);

CREATE INDEX IF NOT EXISTS idx_solicitacao_status ON solicitacao_compra(status);
CREATE INDEX IF NOT EXISTS idx_item_solicitacao ON item_solicitacao_compra(id_solicitacao);
CREATE INDEX IF NOT EXISTS idx_pedido_solicitacao ON pedido(id_solicitacao);
CREATE INDEX IF NOT EXISTS idx_cotacao_solicitacao ON cotacao_compra(id_solicitacao);
CREATE INDEX IF NOT EXISTS idx_item_cotacao ON item_cotacao_compra(id_cotacao);
CREATE INDEX IF NOT EXISTS idx_nota_fiscal_pedido ON nota_fiscal_compra(id_pedido);

COMMIT;
