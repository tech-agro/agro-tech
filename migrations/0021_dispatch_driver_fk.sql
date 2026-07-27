BEGIN;

-- =============================================================================
-- Motoristas como funcionarios (padrao de nome: "Motorista 1", "Motorista 2")
-- e FK em expedicao no lugar do texto livre.
-- =============================================================================

INSERT INTO pessoa (nome, documento)
SELECT 'Motorista 1', 'DOC-MOT-001'
WHERE NOT EXISTS (SELECT 1 FROM pessoa WHERE documento = 'DOC-MOT-001');

INSERT INTO pessoa (nome, documento)
SELECT 'Motorista 2', 'DOC-MOT-002'
WHERE NOT EXISTS (SELECT 1 FROM pessoa WHERE documento = 'DOC-MOT-002');

INSERT INTO funcionario (id_pessoa, cargo, setor, data_admissao)
SELECT p.id_pessoa, 'Motorista', 'Logistica', DATE '2024-02-01'
FROM pessoa p
WHERE p.documento = 'DOC-MOT-001'
  AND NOT EXISTS (
      SELECT 1 FROM funcionario f WHERE f.id_pessoa = p.id_pessoa
  );

INSERT INTO funcionario (id_pessoa, cargo, setor, data_admissao)
SELECT p.id_pessoa, 'Motorista', 'Logistica', DATE '2024-02-15'
FROM pessoa p
WHERE p.documento = 'DOC-MOT-002'
  AND NOT EXISTS (
      SELECT 1 FROM funcionario f WHERE f.id_pessoa = p.id_pessoa
  );

ALTER TABLE expedicao
    ADD COLUMN IF NOT EXISTS id_funcionario BIGINT REFERENCES funcionario(id_funcionario);

UPDATE expedicao e
SET id_funcionario = f.id_funcionario
FROM funcionario f
JOIN pessoa p ON p.id_pessoa = f.id_pessoa
WHERE e.id_funcionario IS NULL
  AND e.motorista IS NOT NULL
  AND p.nome = e.motorista;

ALTER TABLE expedicao
    DROP COLUMN IF EXISTS motorista;

CREATE INDEX IF NOT EXISTS idx_expedicao_funcionario ON expedicao(id_funcionario);

COMMIT;
