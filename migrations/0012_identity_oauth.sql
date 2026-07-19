BEGIN;

ALTER TABLE usuario DROP COLUMN senha_hash;

CREATE TABLE IF NOT EXISTS identidade_externa (
    id_identidade_externa BIGSERIAL PRIMARY KEY,
    id_usuario BIGINT NOT NULL REFERENCES usuario(id_usuario),
    provedor VARCHAR(30) NOT NULL,
    provedor_user_id VARCHAR(255) NOT NULL,
    email_provedor VARCHAR(255) NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE (provedor, provedor_user_id)
);

CREATE INDEX IF NOT EXISTS idx_identidade_externa_id_usuario ON identidade_externa(id_usuario);
CREATE INDEX IF NOT EXISTS idx_auditoria_log_id_usuario ON auditoria_log(id_usuario);
CREATE INDEX IF NOT EXISTS idx_notificacao_id_usuario ON notificacao(id_usuario);

ALTER TABLE perfil_acesso ADD CONSTRAINT uq_perfil_acesso_nome UNIQUE (nome);
ALTER TABLE permissao ADD CONSTRAINT uq_permissao_descricao UNIQUE (descricao);

INSERT INTO perfil_acesso (nome) VALUES ('admin'), ('usuario')
    ON CONFLICT (nome) DO NOTHING;

COMMIT;
