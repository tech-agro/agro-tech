BEGIN;

CREATE TABLE IF NOT EXISTS talhao (
    id_talhao BIGSERIAL PRIMARY KEY,
    id_fazenda BIGINT NOT NULL REFERENCES fazenda(id_fazenda),
    id_safra BIGINT NOT NULL REFERENCES safra(id_safra),
    nome VARCHAR(120) NOT NULL,
    area_hectares NUMERIC(12, 2) NOT NULL,
    CONSTRAINT chk_talhao_area_pos CHECK (area_hectares > 0)
);

CREATE TABLE IF NOT EXISTS solo (
    id_solo BIGSERIAL PRIMARY KEY,
    id_talhao BIGINT NOT NULL UNIQUE REFERENCES talhao(id_talhao),
    tipo_solo VARCHAR(80),
    textura VARCHAR(80),
    profundidade_cm NUMERIC(12, 2)
);

CREATE TABLE IF NOT EXISTS analise_solo (
    id_analise BIGSERIAL PRIMARY KEY,
    id_solo BIGINT NOT NULL REFERENCES solo(id_solo),
    id_safra BIGINT NOT NULL REFERENCES safra(id_safra),
    id_funcionario BIGINT NOT NULL REFERENCES funcionario(id_funcionario),
    dt_coleta DATE,
    dt_resultado DATE,
    ph NUMERIC(8, 2),
    materia_organica NUMERIC(8, 2),
    fosforo NUMERIC(8, 2),
    potassio NUMERIC(8, 2),
    calcio NUMERIC(8, 2),
    magnesio NUMERIC(8, 2),
    saturacao_bases NUMERIC(8, 2),
    observacao TEXT,
    CONSTRAINT chk_analise_solo_periodo CHECK (dt_resultado IS NULL OR dt_coleta IS NULL OR dt_resultado >= dt_coleta)
);

CREATE TABLE IF NOT EXISTS condicao_climatica (
    id_condicao BIGSERIAL PRIMARY KEY,
    id_talhao BIGINT NOT NULL REFERENCES talhao(id_talhao),
    dt_registro TIMESTAMP NOT NULL,
    temperatura_min NUMERIC(8, 2),
    temperatura_max NUMERIC(8, 2),
    umidade_relativa NUMERIC(8, 2),
    precipitacao_mm NUMERIC(8, 2),
    velocidade_vento NUMERIC(8, 2),
    direcao_vento VARCHAR(30),
    radiacao_solar NUMERIC(8, 2)
);

CREATE TABLE IF NOT EXISTS planejamento_safra (
    id_planejamento BIGSERIAL PRIMARY KEY,
    id_safra BIGINT NOT NULL REFERENCES safra(id_safra),
    id_talhao BIGINT NOT NULL REFERENCES talhao(id_talhao),
    id_cultura BIGINT NOT NULL REFERENCES cultura(id_cultura),
    meta_produtividade NUMERIC(12, 2),
    area_planejada NUMERIC(12, 2),
    dt_plantio_previsto DATE,
    dt_colheita_previsto DATE,
    status status_planejamento_safra_enum NOT NULL,
    CONSTRAINT chk_planejamento_periodo CHECK (
        dt_colheita_previsto IS NULL
        OR dt_plantio_previsto IS NULL
        OR dt_colheita_previsto >= dt_plantio_previsto
    ),
    CONSTRAINT chk_planejamento_area_pos CHECK (area_planejada IS NULL OR area_planejada > 0)
);

CREATE TABLE IF NOT EXISTS ordem_producao (
    id_ordem BIGSERIAL PRIMARY KEY,
    id_safra BIGINT NOT NULL REFERENCES safra(id_safra),
    data_abertura DATE,
    status status_ordem_producao_enum NOT NULL
);

CREATE TABLE IF NOT EXISTS plantio (
    id_plantio BIGSERIAL PRIMARY KEY,
    id_ordem BIGINT NOT NULL REFERENCES ordem_producao(id_ordem),
    id_talhao BIGINT NOT NULL REFERENCES talhao(id_talhao),
    id_produto BIGINT NOT NULL REFERENCES produto(id_produto),
    id_cultura BIGINT NOT NULL REFERENCES cultura(id_cultura),
    id_planejamento BIGINT NOT NULL REFERENCES planejamento_safra(id_planejamento),
    dt_plantio DATE,
    status status_plantio_enum NOT NULL
);

CREATE TABLE IF NOT EXISTS operacao_agricola (
    id_operacao BIGSERIAL PRIMARY KEY,
    id_plantio BIGINT NOT NULL REFERENCES plantio(id_plantio),
    id_funcionario BIGINT NOT NULL REFERENCES funcionario(id_funcionario),
    tipo_operacao VARCHAR(80),
    descricao TEXT,
    dt_inicio TIMESTAMP,
    dt_fim TIMESTAMP,
    status status_operacao_agricola_enum NOT NULL,
    CONSTRAINT chk_operacao_agricola_periodo CHECK (dt_fim IS NULL OR dt_inicio IS NULL OR dt_fim >= dt_inicio)
);

CREATE TABLE IF NOT EXISTS atividade_agricola (
    id_atividade BIGSERIAL PRIMARY KEY,
    id_operacao BIGINT NOT NULL REFERENCES operacao_agricola(id_operacao),
    descricao TEXT,
    dt_inicio TIMESTAMP,
    dt_fim TIMESTAMP,
    status status_atividade_agricola_enum NOT NULL,
    CONSTRAINT chk_atividade_agricola_periodo CHECK (dt_fim IS NULL OR dt_inicio IS NULL OR dt_fim >= dt_inicio)
);

CREATE TABLE IF NOT EXISTS funcionario_atividade (
    id_funcionario BIGINT NOT NULL REFERENCES funcionario(id_funcionario),
    id_atividade BIGINT NOT NULL REFERENCES atividade_agricola(id_atividade),
    PRIMARY KEY (id_funcionario, id_atividade)
);

CREATE TABLE IF NOT EXISTS pulverizacao (
    id_atividade BIGINT PRIMARY KEY REFERENCES atividade_agricola(id_atividade),
    id_insumo BIGINT NOT NULL REFERENCES insumo(id_produto),
    volume_calda NUMERIC(12, 2),
    vazao NUMERIC(12, 2)
);

CREATE TABLE IF NOT EXISTS adubacao (
    id_atividade BIGINT PRIMARY KEY REFERENCES atividade_agricola(id_atividade),
    id_insumo BIGINT NOT NULL REFERENCES insumo(id_produto),
    tipo_adubacao VARCHAR(80),
    dose_hectare NUMERIC(12, 2),
    metodo_aplicacao VARCHAR(120)
);

CREATE TABLE IF NOT EXISTS irrigacao (
    id_atividade BIGINT PRIMARY KEY REFERENCES atividade_agricola(id_atividade),
    lamina_agua NUMERIC(12, 2),
    metodo_irrigacao VARCHAR(80),
    duracao_horas NUMERIC(10, 2)
);

CREATE TABLE IF NOT EXISTS monitoramento_safra (
    id_monitoramento BIGSERIAL PRIMARY KEY,
    id_safra BIGINT NOT NULL REFERENCES safra(id_safra),
    id_talhao BIGINT NOT NULL REFERENCES talhao(id_talhao),
    id_funcionario BIGINT NOT NULL REFERENCES funcionario(id_funcionario),
    dt_monitoramento TIMESTAMP NOT NULL,
    estagio_fenologico VARCHAR(120),
    observacao TEXT
);

CREATE TABLE IF NOT EXISTS parametro_monitoramento (
    id_parametro BIGSERIAL PRIMARY KEY,
    id_monitoramento BIGINT NOT NULL REFERENCES monitoramento_safra(id_monitoramento),
    nome_parametro VARCHAR(120) NOT NULL,
    valor NUMERIC(12, 2),
    unidade VARCHAR(40)
);

CREATE TABLE IF NOT EXISTS colheita (
    id_colheita BIGSERIAL PRIMARY KEY,
    id_plantio BIGINT NOT NULL REFERENCES plantio(id_plantio),
    quantidade_colhida NUMERIC(12, 2),
    dt_inicio DATE,
    dt_fim DATE,
    status status_colheita_enum NOT NULL,
    CONSTRAINT chk_colheita_periodo CHECK (dt_fim IS NULL OR dt_inicio IS NULL OR dt_fim >= dt_inicio),
    CONSTRAINT chk_colheita_quantidade_pos CHECK (quantidade_colhida IS NULL OR quantidade_colhida > 0)
);

CREATE TABLE IF NOT EXISTS agente_nocivo (
    id_agente BIGSERIAL PRIMARY KEY,
    nome_comum VARCHAR(120),
    nome_cientifico VARCHAR(120)
);

CREATE TABLE IF NOT EXISTS praga (
    id_agente BIGINT PRIMARY KEY REFERENCES agente_nocivo(id_agente),
    tipo_praga VARCHAR(80),
    habito_alimentar VARCHAR(120)
);

CREATE TABLE IF NOT EXISTS doenca (
    id_agente BIGINT PRIMARY KEY REFERENCES agente_nocivo(id_agente),
    agente_causador VARCHAR(120),
    sintomas TEXT,
    condicao_favoravel TEXT
);

CREATE TABLE IF NOT EXISTS controle_fitossanitario (
    id_controle BIGSERIAL PRIMARY KEY,
    id_plantio BIGINT NOT NULL REFERENCES plantio(id_plantio),
    id_funcionario BIGINT NOT NULL REFERENCES funcionario(id_funcionario),
    dt_identificacao DATE,
    nivel_severidade VARCHAR(50),
    area_afetada_hectares NUMERIC(12, 2),
    recomendacao TEXT,
    CONSTRAINT chk_controle_area_pos CHECK (area_afetada_hectares IS NULL OR area_afetada_hectares >= 0)
);

CREATE TABLE IF NOT EXISTS ocorrencia_agente (
    id_ocorrencia BIGSERIAL PRIMARY KEY,
    id_controle BIGINT NOT NULL REFERENCES controle_fitossanitario(id_controle),
    id_agente BIGINT NOT NULL REFERENCES agente_nocivo(id_agente),
    nivel_infestacao VARCHAR(50),
    metodo_controle VARCHAR(120)
);

CREATE TABLE IF NOT EXISTS aplicacao_defensivo (
    id_aplicacao BIGSERIAL PRIMARY KEY,
    id_controle BIGINT NOT NULL REFERENCES controle_fitossanitario(id_controle),
    id_insumo BIGINT NOT NULL REFERENCES insumo(id_produto),
    dose_hectare NUMERIC(12, 2),
    volume_aplicado NUMERIC(12, 2),
    dt_aplicacao DATE,
    dt_carencia DATE,
    CONSTRAINT chk_aplicacao_dose_pos CHECK (dose_hectare IS NULL OR dose_hectare > 0),
    CONSTRAINT chk_aplicacao_volume_pos CHECK (volume_aplicado IS NULL OR volume_aplicado > 0),
    CONSTRAINT chk_aplicacao_datas CHECK (dt_carencia IS NULL OR dt_aplicacao IS NULL OR dt_carencia >= dt_aplicacao)
);

CREATE INDEX IF NOT EXISTS idx_talhao_fazenda ON talhao(id_fazenda);
CREATE INDEX IF NOT EXISTS idx_talhao_safra ON talhao(id_safra);
CREATE INDEX IF NOT EXISTS idx_analise_solo_solo ON analise_solo(id_solo);
CREATE INDEX IF NOT EXISTS idx_analise_solo_safra ON analise_solo(id_safra);
CREATE INDEX IF NOT EXISTS idx_plantio_talhao ON plantio(id_talhao);
CREATE INDEX IF NOT EXISTS idx_operacao_plantio ON operacao_agricola(id_plantio);
CREATE INDEX IF NOT EXISTS idx_atividade_operacao ON atividade_agricola(id_operacao);
CREATE INDEX IF NOT EXISTS idx_monitoramento_safra ON monitoramento_safra(id_safra);
CREATE INDEX IF NOT EXISTS idx_ocorrencia_controle ON ocorrencia_agente(id_controle);

COMMIT;
