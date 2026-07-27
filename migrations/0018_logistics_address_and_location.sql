BEGIN;

-- =============================================================================
-- Endereco (dados geograficos) + Local logistico (ponto de origem/destino).
-- Motivo: origem/destino de operacao pode ser fazenda, porto, armazem, cliente etc.
-- Nao reutiliza local_armazenamento (dominio de estoque) nem fazenda/cliente
-- (nao cobrem todos os tipos de ponto logistico).
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_local_logistico_enum') THEN
        CREATE TYPE tipo_local_logistico_enum AS ENUM (
            'FAZENDA',
            'ARMAZEM',
            'CLIENTE',
            'FORNECEDOR',
            'PORTO',
            'COOPERATIVA',
            'OFICINA',
            'PATIO',
            'CENTRO_DISTRIBUICAO',
            'OUTRO'
        );
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS endereco (
    id_endereco BIGSERIAL PRIMARY KEY,
    logradouro VARCHAR(255) NOT NULL,
    numero VARCHAR(30),
    cidade VARCHAR(120) NOT NULL,
    estado CHAR(2) NOT NULL,
    cep VARCHAR(12),
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    CONSTRAINT chk_endereco_estado_uf CHECK (estado ~ '^[A-Z]{2}$')
);

CREATE TABLE IF NOT EXISTS local_logistico (
    id_local_logistico BIGSERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    tipo tipo_local_logistico_enum NOT NULL,
    id_endereco BIGINT REFERENCES endereco(id_endereco),
    CONSTRAINT uq_local_logistico_nome_tipo UNIQUE (nome, tipo)
);

CREATE INDEX IF NOT EXISTS idx_local_logistico_endereco
    ON local_logistico(id_endereco);
CREATE INDEX IF NOT EXISTS idx_local_logistico_tipo
    ON local_logistico(tipo);

-- -----------------------------------------------------------------------------
-- Migra rotas textuais -> locais e liga operacao a origem/destino
-- -----------------------------------------------------------------------------

ALTER TABLE operacao_logistica
    ADD COLUMN IF NOT EXISTS id_origem BIGINT,
    ADD COLUMN IF NOT EXISTS id_destino BIGINT;

-- Cria locais a partir de textos distintos em rota.origem / rota.destino
INSERT INTO local_logistico (nome, tipo)
SELECT DISTINCT origem, 'OUTRO'::tipo_local_logistico_enum
FROM rota
WHERE origem IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM local_logistico ll
      WHERE ll.nome = rota.origem AND ll.tipo = 'OUTRO'::tipo_local_logistico_enum
  );

INSERT INTO local_logistico (nome, tipo)
SELECT DISTINCT destino, 'OUTRO'::tipo_local_logistico_enum
FROM rota
WHERE destino IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM local_logistico ll
      WHERE ll.nome = rota.destino AND ll.tipo = 'OUTRO'::tipo_local_logistico_enum
  );

UPDATE operacao_logistica ol
SET
    id_origem = lo.id_local_logistico,
    id_destino = ld.id_local_logistico
FROM rota r
JOIN local_logistico lo ON lo.nome = r.origem
JOIN local_logistico ld ON ld.nome = r.destino
WHERE ol.id_rota = r.id_rota
  AND (ol.id_origem IS NULL OR ol.id_destino IS NULL);

-- Operacoes orfas (sem rota resolvida): cria locais placeholder
INSERT INTO local_logistico (nome, tipo)
SELECT 'Local origem pendente', 'OUTRO'::tipo_local_logistico_enum
WHERE NOT EXISTS (
    SELECT 1 FROM local_logistico WHERE nome = 'Local origem pendente'
);

INSERT INTO local_logistico (nome, tipo)
SELECT 'Local destino pendente', 'OUTRO'::tipo_local_logistico_enum
WHERE NOT EXISTS (
    SELECT 1 FROM local_logistico WHERE nome = 'Local destino pendente'
);

UPDATE operacao_logistica
SET id_origem = (
    SELECT id_local_logistico FROM local_logistico WHERE nome = 'Local origem pendente' LIMIT 1
)
WHERE id_origem IS NULL;

UPDATE operacao_logistica
SET id_destino = (
    SELECT id_local_logistico FROM local_logistico WHERE nome = 'Local destino pendente' LIMIT 1
)
WHERE id_destino IS NULL;

ALTER TABLE operacao_logistica
    ALTER COLUMN id_origem SET NOT NULL,
    ALTER COLUMN id_destino SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_operacao_origem'
    ) THEN
        ALTER TABLE operacao_logistica
            ADD CONSTRAINT fk_operacao_origem
            FOREIGN KEY (id_origem) REFERENCES local_logistico(id_local_logistico);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_operacao_destino'
    ) THEN
        ALTER TABLE operacao_logistica
            ADD CONSTRAINT fk_operacao_destino
            FOREIGN KEY (id_destino) REFERENCES local_logistico(id_local_logistico);
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_operacao_origem_destino'
    ) THEN
        ALTER TABLE operacao_logistica
            ADD CONSTRAINT chk_operacao_origem_destino
            CHECK (id_origem <> id_destino);
    END IF;
END $$;

ALTER TABLE operacao_logistica DROP CONSTRAINT IF EXISTS operacao_logistica_id_rota_fkey;
ALTER TABLE operacao_logistica DROP COLUMN IF EXISTS id_rota;

DROP TABLE IF EXISTS rota;

CREATE INDEX IF NOT EXISTS idx_operacao_logistica_origem ON operacao_logistica(id_origem);
CREATE INDEX IF NOT EXISTS idx_operacao_logistica_destino ON operacao_logistica(id_destino);

-- Tipagem dos locais migrados do seed antigo (quando o nome indica o tipo)
UPDATE local_logistico
SET tipo = 'FAZENDA'::tipo_local_logistico_enum
WHERE nome ILIKE 'Fazenda%' AND tipo = 'OUTRO'::tipo_local_logistico_enum;

UPDATE local_logistico
SET tipo = 'ARMAZEM'::tipo_local_logistico_enum
WHERE nome ILIKE 'Armazem%' AND tipo = 'OUTRO'::tipo_local_logistico_enum;

UPDATE local_logistico
SET tipo = 'PORTO'::tipo_local_logistico_enum
WHERE nome ILIKE 'Porto%' AND tipo = 'OUTRO'::tipo_local_logistico_enum;

COMMIT;
