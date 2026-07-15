BEGIN;

CREATE TABLE IF NOT EXISTS pessoa (
    id_pessoa BIGSERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    documento VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS email (
    id_email BIGSERIAL PRIMARY KEY,
    id_pessoa BIGINT NOT NULL REFERENCES pessoa(id_pessoa),
    email VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS telefone (
    id_telefone BIGSERIAL PRIMARY KEY,
    id_pessoa BIGINT NOT NULL REFERENCES pessoa(id_pessoa),
    telefone VARCHAR(30) NOT NULL
);

CREATE TABLE IF NOT EXISTS usuario (
    id_usuario BIGSERIAL PRIMARY KEY,
    id_pessoa BIGINT NOT NULL UNIQUE REFERENCES pessoa(id_pessoa),
    senha_hash VARCHAR(255) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS funcionario (
    id_funcionario BIGSERIAL PRIMARY KEY,
    id_pessoa BIGINT NOT NULL REFERENCES pessoa(id_pessoa),
    cargo VARCHAR(100),
    setor VARCHAR(100),
    data_admissao DATE
);

CREATE TABLE IF NOT EXISTS cliente (
    id_cliente BIGSERIAL PRIMARY KEY,
    id_pessoa BIGINT NOT NULL REFERENCES pessoa(id_pessoa),
    status status_cliente_enum NOT NULL
);

CREATE TABLE IF NOT EXISTS fornecedor (
    id_fornecedor BIGSERIAL PRIMARY KEY,
    id_pessoa BIGINT NOT NULL REFERENCES pessoa(id_pessoa),
    categoria VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS perfil_acesso (
    id_perfil BIGSERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS permissao (
    id_permissao BIGSERIAL PRIMARY KEY,
    descricao VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS usuario_perfil (
    id_usuario BIGINT NOT NULL REFERENCES usuario(id_usuario),
    id_perfil BIGINT NOT NULL REFERENCES perfil_acesso(id_perfil),
    PRIMARY KEY (id_usuario, id_perfil)
);

CREATE TABLE IF NOT EXISTS perfil_permissao (
    id_perfil BIGINT NOT NULL REFERENCES perfil_acesso(id_perfil),
    id_permissao BIGINT NOT NULL REFERENCES permissao(id_permissao),
    PRIMARY KEY (id_perfil, id_permissao)
);

CREATE TABLE IF NOT EXISTS auditoria_log (
    id_log BIGSERIAL PRIMARY KEY,
    id_usuario BIGINT NOT NULL REFERENCES usuario(id_usuario),
    acao VARCHAR(255) NOT NULL,
    data_evento TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS notificacao (
    id_notificacao BIGSERIAL PRIMARY KEY,
    id_usuario BIGINT NOT NULL REFERENCES usuario(id_usuario),
    mensagem TEXT NOT NULL,
    data_envio TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS centro_custo (
    id_centro_custo BIGSERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_email_id_pessoa ON email(id_pessoa);
CREATE INDEX IF NOT EXISTS idx_telefone_id_pessoa ON telefone(id_pessoa);
CREATE INDEX IF NOT EXISTS idx_funcionario_id_pessoa ON funcionario(id_pessoa);
CREATE INDEX IF NOT EXISTS idx_cliente_id_pessoa ON cliente(id_pessoa);
CREATE INDEX IF NOT EXISTS idx_fornecedor_id_pessoa ON fornecedor(id_pessoa);

COMMIT;
