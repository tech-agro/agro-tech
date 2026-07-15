BEGIN;

CREATE TABLE IF NOT EXISTS tipo_maquina (
    id_tipo_maquina BIGSERIAL PRIMARY KEY,
    descricao VARCHAR(120) NOT NULL
);

CREATE TABLE IF NOT EXISTS prestador_servico (
    id_prestador BIGSERIAL PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    cnpj VARCHAR(30) UNIQUE,
    especialidade VARCHAR(120),
    telefone VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS maquina (
    id_maquina BIGSERIAL PRIMARY KEY,
    id_tipo_maquina BIGINT NOT NULL REFERENCES tipo_maquina(id_tipo_maquina),
    id_fazenda BIGINT NOT NULL REFERENCES fazenda(id_fazenda),
    nome VARCHAR(120),
    status status_maquina_enum NOT NULL
);

CREATE TABLE IF NOT EXISTS uso_maquina (
    id_uso BIGSERIAL PRIMARY KEY,
    id_maquina BIGINT NOT NULL REFERENCES maquina(id_maquina),
    id_atividade BIGINT NOT NULL REFERENCES atividade_agricola(id_atividade),
    id_operacao BIGINT NOT NULL REFERENCES operacao_agricola(id_operacao),
    dt_inicio TIMESTAMP,
    dt_fim TIMESTAMP,
    horas_trabalhadas NUMERIC(10, 2),
    CONSTRAINT chk_uso_maquina_periodo CHECK (dt_fim IS NULL OR dt_inicio IS NULL OR dt_fim >= dt_inicio)
);

CREATE TABLE IF NOT EXISTS abastecimento (
    id_abastecimento BIGSERIAL PRIMARY KEY,
    id_maquina BIGINT NOT NULL REFERENCES maquina(id_maquina),
    combustivel VARCHAR(80),
    litros NUMERIC(10, 2),
    valor NUMERIC(14, 2),
    horimetro NUMERIC(12, 2),
    dt_abastecimento TIMESTAMP,
    CONSTRAINT chk_abastecimento_litros_pos CHECK (litros IS NULL OR litros > 0),
    CONSTRAINT chk_abastecimento_valor_pos CHECK (valor IS NULL OR valor >= 0)
);

CREATE TABLE IF NOT EXISTS plano_manutencao (
    id_plano BIGSERIAL PRIMARY KEY,
    id_maquina BIGINT NOT NULL REFERENCES maquina(id_maquina),
    periodicidade VARCHAR(80),
    proxima_execucao DATE
);

CREATE TABLE IF NOT EXISTS manutencao (
    id_manutencao BIGSERIAL PRIMARY KEY,
    id_maquina BIGINT NOT NULL REFERENCES maquina(id_maquina),
    id_funcionario BIGINT REFERENCES funcionario(id_funcionario),
    id_prestador BIGINT REFERENCES prestador_servico(id_prestador),
    tipo VARCHAR(50),
    custo NUMERIC(14, 2),
    status status_manutencao_enum NOT NULL,
    dt_inicio DATE,
    dt_fim DATE,
    CONSTRAINT chk_manutencao_periodo CHECK (dt_fim IS NULL OR dt_inicio IS NULL OR dt_fim >= dt_inicio),
    CONSTRAINT chk_manutencao_custo_pos CHECK (custo IS NULL OR custo >= 0)
);

CREATE TABLE IF NOT EXISTS manutencao_preventiva (
    id_manutencao BIGINT PRIMARY KEY REFERENCES manutencao(id_manutencao),
    id_plano BIGINT NOT NULL REFERENCES plano_manutencao(id_plano),
    hodometro_execucao NUMERIC(12, 2),
    proxima_hodometro NUMERIC(12, 2)
);

CREATE TABLE IF NOT EXISTS manutencao_corretiva (
    id_manutencao BIGINT PRIMARY KEY REFERENCES manutencao(id_manutencao),
    defeito_relatado TEXT,
    causa_raiz TEXT,
    solucao_aplicada TEXT
);

CREATE TABLE IF NOT EXISTS ordem_servico (
    id_ordem_servico BIGSERIAL PRIMARY KEY,
    id_manutencao BIGINT NOT NULL REFERENCES manutencao(id_manutencao),
    descricao TEXT,
    status status_ordem_servico_enum NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_maquina_tipo ON maquina(id_tipo_maquina);
CREATE INDEX IF NOT EXISTS idx_maquina_fazenda ON maquina(id_fazenda);
CREATE INDEX IF NOT EXISTS idx_uso_maquina_maquina ON uso_maquina(id_maquina);
CREATE INDEX IF NOT EXISTS idx_manutencao_maquina ON manutencao(id_maquina);
CREATE INDEX IF NOT EXISTS idx_manutencao_prestador ON manutencao(id_prestador);

COMMIT;
