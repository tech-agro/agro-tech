BEGIN;

CREATE TABLE IF NOT EXISTS fazenda (
    id_fazenda BIGSERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    localizacao VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS safra (
    id_safra BIGSERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    ano INTEGER NOT NULL,
    dt_inicio DATE,
    dt_fim DATE,
    status status_safra_enum NOT NULL,
    CONSTRAINT chk_safra_periodo CHECK (dt_fim IS NULL OR dt_inicio IS NULL OR dt_fim >= dt_inicio)
);

CREATE TABLE IF NOT EXISTS cultura (
    id_cultura BIGSERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    nome_cientifico VARCHAR(120),
    variedade VARCHAR(120),
    ciclo_dias INTEGER,
    tipo_cultura VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS categoria_produto (
    id_categoria BIGSERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL
);

CREATE TABLE IF NOT EXISTS unidade_medida (
    id_unidade BIGSERIAL PRIMARY KEY,
    sigla VARCHAR(20) NOT NULL,
    descricao VARCHAR(120) NOT NULL
);

CREATE TABLE IF NOT EXISTS produto (
    id_produto BIGSERIAL PRIMARY KEY,
    id_categoria BIGINT NOT NULL REFERENCES categoria_produto(id_categoria),
    id_unidade BIGINT NOT NULL REFERENCES unidade_medida(id_unidade),
    nome VARCHAR(255) NOT NULL,
    tipo VARCHAR(80),
    preco NUMERIC(14, 2),
    CONSTRAINT chk_produto_preco_pos CHECK (preco IS NULL OR preco >= 0)
);

CREATE TABLE IF NOT EXISTS insumo (
    id_produto BIGINT PRIMARY KEY REFERENCES produto(id_produto),
    classe_agronomica VARCHAR(120),
    principio_ativo VARCHAR(120),
    periodo_carencia_dias INTEGER,
    registro_mapa VARCHAR(120)
);

CREATE TABLE IF NOT EXISTS grao (
    id_produto BIGINT PRIMARY KEY REFERENCES produto(id_produto),
    umidade_maxima NUMERIC(8, 2),
    impureza_maxima NUMERIC(8, 2),
    classificacao_tipo VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS cotacao_grao (
    id_cotacao BIGSERIAL PRIMARY KEY,
    id_produto BIGINT NOT NULL REFERENCES produto(id_produto),
    data_cotacao DATE NOT NULL,
    preco NUMERIC(14, 2) NOT NULL,
    CONSTRAINT chk_cotacao_grao_preco_pos CHECK (preco >= 0)
);

CREATE TABLE IF NOT EXISTS produto_comercial (
    id_produto BIGINT PRIMARY KEY REFERENCES produto(id_produto),
    codigo_comercial VARCHAR(80),
    marca VARCHAR(120),
    descricao_comercial TEXT
);

CREATE TABLE IF NOT EXISTS certificacao (
    id_certificacao BIGSERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    orgao_emissor VARCHAR(120),
    tipo VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS certificacao_fazenda (
    id_cert_fazenda BIGSERIAL PRIMARY KEY,
    id_certificacao BIGINT NOT NULL REFERENCES certificacao(id_certificacao),
    id_fazenda BIGINT NOT NULL REFERENCES fazenda(id_fazenda),
    dt_emissao DATE,
    dt_validade DATE,
    numero_certificado VARCHAR(120) UNIQUE,
    status status_certificacao_enum NOT NULL,
    CONSTRAINT chk_certificacao_fazenda_periodo CHECK (dt_validade IS NULL OR dt_emissao IS NULL OR dt_validade >= dt_emissao)
);

CREATE INDEX IF NOT EXISTS idx_produto_categoria ON produto(id_categoria);
CREATE INDEX IF NOT EXISTS idx_produto_unidade ON produto(id_unidade);
CREATE INDEX IF NOT EXISTS idx_cotacao_produto ON cotacao_grao(id_produto);
CREATE INDEX IF NOT EXISTS idx_cert_fazenda_certificacao ON certificacao_fazenda(id_certificacao);
CREATE INDEX IF NOT EXISTS idx_cert_fazenda_fazenda ON certificacao_fazenda(id_fazenda);

COMMIT;
