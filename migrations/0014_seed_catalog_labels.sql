BEGIN;

INSERT INTO unidade_medida (sigla, descricao)
SELECT 'KG', 'Quilograma'
WHERE NOT EXISTS (SELECT 1 FROM unidade_medida WHERE sigla = 'KG');

INSERT INTO unidade_medida (sigla, descricao)
SELECT 'L', 'Litro'
WHERE NOT EXISTS (SELECT 1 FROM unidade_medida WHERE sigla = 'L');

INSERT INTO unidade_medida (sigla, descricao)
SELECT 'UN', 'Unidade'
WHERE NOT EXISTS (SELECT 1 FROM unidade_medida WHERE sigla = 'UN');

INSERT INTO unidade_medida (sigla, descricao)
SELECT 'SC', 'Saca'
WHERE NOT EXISTS (SELECT 1 FROM unidade_medida WHERE sigla = 'SC');

INSERT INTO unidade_medida (sigla, descricao)
SELECT 'HA', 'Hectare'
WHERE NOT EXISTS (SELECT 1 FROM unidade_medida WHERE sigla = 'HA');

INSERT INTO unidade_medida (sigla, descricao)
SELECT 'T', 'Tonelada'
WHERE NOT EXISTS (SELECT 1 FROM unidade_medida WHERE sigla = 'T');

INSERT INTO categoria_produto (nome)
SELECT 'Insumos'
WHERE NOT EXISTS (SELECT 1 FROM categoria_produto WHERE nome = 'Insumos');

INSERT INTO categoria_produto (nome)
SELECT 'Combustiveis'
WHERE NOT EXISTS (SELECT 1 FROM categoria_produto WHERE nome = 'Combustiveis');

INSERT INTO produto (id_categoria, id_unidade, nome, tipo, preco)
SELECT
    (SELECT id_categoria FROM categoria_produto WHERE nome = 'Insumos' LIMIT 1),
    (SELECT id_unidade FROM unidade_medida WHERE sigla = 'KG' LIMIT 1),
    'Ureia 45%',
    'insumo',
    180.00
WHERE NOT EXISTS (SELECT 1 FROM produto WHERE nome = 'Ureia 45%');

INSERT INTO produto (id_categoria, id_unidade, nome, tipo, preco)
SELECT
    (SELECT id_categoria FROM categoria_produto WHERE nome = 'Combustiveis' LIMIT 1),
    (SELECT id_unidade FROM unidade_medida WHERE sigla = 'L' LIMIT 1),
    'Oleo diesel S10',
    'combustivel',
    6.50
WHERE NOT EXISTS (SELECT 1 FROM produto WHERE nome = 'Oleo diesel S10');

INSERT INTO produto (id_categoria, id_unidade, nome, tipo, preco)
SELECT
    (SELECT id_categoria FROM categoria_produto WHERE nome = 'Insumos' LIMIT 1),
    (SELECT id_unidade FROM unidade_medida WHERE sigla = 'UN' LIMIT 1),
    'Saco de sementes',
    'insumo',
    120.00
WHERE NOT EXISTS (SELECT 1 FROM produto WHERE nome = 'Saco de sementes');

COMMIT;
