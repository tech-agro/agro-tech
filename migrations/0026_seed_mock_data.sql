BEGIN;

-- =============================================================================
-- Seed mock data for local/dev POC demos.
--
-- Naming:
--   - Generic labels (logic-neutral): "Fornecedor 1", "Cliente 2", "Maquina 3"
--   - Domain names when the label matters: products, cultures, pests, lots, KPIs
--
-- Idempotent: every insert is guarded with WHERE NOT EXISTS / NOT EXISTS join.
-- Requires migrations through 0025 (schema) + 0014 (units/catalog base).
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Identity: Funcionario / Fornecedor / Cliente / Motorista (10+ each)
-- -----------------------------------------------------------------------------
INSERT INTO pessoa (nome, documento)
SELECT
    'Funcionario ' || g.n,
    'DOC-FUNC-' || lpad(g.n::text, 3, '0')
FROM generate_series(1, 12) AS g(n)
WHERE NOT EXISTS (
    SELECT 1 FROM pessoa p
    WHERE p.documento = 'DOC-FUNC-' || lpad(g.n::text, 3, '0')
);

INSERT INTO pessoa (nome, documento)
SELECT
    'Fornecedor ' || g.n,
    'DOC-FORN-' || lpad(g.n::text, 3, '0')
FROM generate_series(1, 12) AS g(n)
WHERE NOT EXISTS (
    SELECT 1 FROM pessoa p
    WHERE p.documento = 'DOC-FORN-' || lpad(g.n::text, 3, '0')
);

INSERT INTO pessoa (nome, documento)
SELECT
    'Cliente ' || g.n,
    'DOC-CLI-' || lpad(g.n::text, 3, '0')
FROM generate_series(1, 12) AS g(n)
WHERE NOT EXISTS (
    SELECT 1 FROM pessoa p
    WHERE p.documento = 'DOC-CLI-' || lpad(g.n::text, 3, '0')
);

INSERT INTO pessoa (nome, documento)
SELECT
    'Motorista ' || g.n,
    'DOC-MOT-' || lpad(g.n::text, 3, '0')
FROM generate_series(1, 12) AS g(n)
WHERE NOT EXISTS (
    SELECT 1 FROM pessoa p
    WHERE p.documento = 'DOC-MOT-' || lpad(g.n::text, 3, '0')
);

INSERT INTO funcionario (id_pessoa, cargo, setor, data_admissao)
SELECT
    p.id_pessoa,
    CASE (g.n % 4)
        WHEN 0 THEN 'Agronomo'
        WHEN 1 THEN 'Operador de campo'
        WHEN 2 THEN 'Tecnico de manutencao'
        ELSE 'Auxiliar administrativo'
    END,
    CASE (g.n % 3)
        WHEN 0 THEN 'Producao'
        WHEN 1 THEN 'Manutencao'
        ELSE 'Administrativo'
    END,
    DATE '2024-01-01' + ((g.n - 1) * 15)
FROM generate_series(1, 12) AS g(n)
JOIN pessoa p ON p.documento = 'DOC-FUNC-' || lpad(g.n::text, 3, '0')
WHERE NOT EXISTS (
    SELECT 1 FROM funcionario f WHERE f.id_pessoa = p.id_pessoa
);

INSERT INTO funcionario (id_pessoa, cargo, setor, data_admissao)
SELECT
    p.id_pessoa,
    'Motorista',
    'Logistica',
    DATE '2024-02-01' + ((g.n - 1) * 7)
FROM generate_series(1, 12) AS g(n)
JOIN pessoa p ON p.documento = 'DOC-MOT-' || lpad(g.n::text, 3, '0')
WHERE NOT EXISTS (
    SELECT 1 FROM funcionario f WHERE f.id_pessoa = p.id_pessoa
);

INSERT INTO fornecedor (id_pessoa, categoria)
SELECT
    p.id_pessoa,
    CASE (g.n % 4)
        WHEN 0 THEN 'Insumos'
        WHEN 1 THEN 'Combustiveis'
        WHEN 2 THEN 'Pecas'
        ELSE 'Servicos'
    END
FROM generate_series(1, 12) AS g(n)
JOIN pessoa p ON p.documento = 'DOC-FORN-' || lpad(g.n::text, 3, '0')
WHERE NOT EXISTS (
    SELECT 1 FROM fornecedor f WHERE f.id_pessoa = p.id_pessoa
);

INSERT INTO cliente (id_pessoa, status)
SELECT
    p.id_pessoa,
    CASE
        WHEN g.n = 12 THEN 'BLOQUEADO'::status_cliente_enum
        WHEN g.n = 11 THEN 'INATIVO'::status_cliente_enum
        ELSE 'ATIVO'::status_cliente_enum
    END
FROM generate_series(1, 12) AS g(n)
JOIN pessoa p ON p.documento = 'DOC-CLI-' || lpad(g.n::text, 3, '0')
WHERE NOT EXISTS (
    SELECT 1 FROM cliente c WHERE c.id_pessoa = p.id_pessoa
);

INSERT INTO centro_custo (nome)
SELECT 'Centro de Custo ' || g.n
FROM generate_series(1, 12) AS g(n)
WHERE NOT EXISTS (
    SELECT 1 FROM centro_custo cc WHERE cc.nome = 'Centro de Custo ' || g.n
);

-- -----------------------------------------------------------------------------
-- Catalog: categories + domain products (names matter)
-- -----------------------------------------------------------------------------
INSERT INTO categoria_produto (nome)
SELECT v.nome
FROM (VALUES ('Graos'), ('Defensivos'), ('Sementes'), ('Fertilizantes')) AS v(nome)
WHERE NOT EXISTS (SELECT 1 FROM categoria_produto c WHERE c.nome = v.nome);

INSERT INTO produto (id_categoria, id_unidade, nome, tipo, preco)
SELECT
    (SELECT id_categoria FROM categoria_produto WHERE nome = 'Graos' LIMIT 1),
    (SELECT id_unidade FROM unidade_medida WHERE sigla = 'SC' LIMIT 1),
    v.nome,
    'grao',
    v.preco
FROM (VALUES
    ('Milho', 85.00),
    ('Soja', 150.00),
    ('Sorgo', 70.00),
    ('Trigo', 95.00)
) AS v(nome, preco)
WHERE NOT EXISTS (SELECT 1 FROM produto p WHERE p.nome = v.nome);

INSERT INTO produto (id_categoria, id_unidade, nome, tipo, preco)
SELECT
    (SELECT id_categoria FROM categoria_produto WHERE nome = 'Sementes' LIMIT 1),
    (SELECT id_unidade FROM unidade_medida WHERE sigla = 'KG' LIMIT 1),
    v.nome,
    'insumo',
    v.preco
FROM (VALUES
    ('Semente de milho hibrido', 45.00),
    ('Semente de soja', 38.00),
    ('Semente de sorgo', 28.00)
) AS v(nome, preco)
WHERE NOT EXISTS (SELECT 1 FROM produto p WHERE p.nome = v.nome);

INSERT INTO produto (id_categoria, id_unidade, nome, tipo, preco)
SELECT
    (SELECT id_categoria FROM categoria_produto WHERE nome = 'Defensivos' LIMIT 1),
    (SELECT id_unidade FROM unidade_medida WHERE sigla = 'L' LIMIT 1),
    v.nome,
    'insumo',
    v.preco
FROM (VALUES
    ('Glifosato 480', 32.00),
    ('Inseticida lambda-cialotrina', 95.00),
    ('Fungicida tebuconazol', 78.00),
    ('Herbicida atrazina', 42.00)
) AS v(nome, preco)
WHERE NOT EXISTS (SELECT 1 FROM produto p WHERE p.nome = v.nome);

INSERT INTO produto (id_categoria, id_unidade, nome, tipo, preco)
SELECT
    (SELECT id_categoria FROM categoria_produto WHERE nome = 'Fertilizantes' LIMIT 1),
    (SELECT id_unidade FROM unidade_medida WHERE sigla = 'KG' LIMIT 1),
    v.nome,
    'insumo',
    v.preco
FROM (VALUES
    ('MAP 11-52-00', 210.00),
    ('KCl 60%', 165.00)
) AS v(nome, preco)
WHERE NOT EXISTS (SELECT 1 FROM produto p WHERE p.nome = v.nome);

INSERT INTO grao (id_produto, umidade_maxima, impureza_maxima, classificacao_tipo)
SELECT p.id_produto, 14.00, 1.00, 'Tipo 1'
FROM produto p
WHERE p.nome IN ('Milho', 'Soja', 'Sorgo', 'Trigo')
  AND NOT EXISTS (SELECT 1 FROM grao g WHERE g.id_produto = p.id_produto);

INSERT INTO insumo (id_produto, classe_agronomica, principio_ativo, periodo_carencia_dias, registro_mapa)
SELECT p.id_produto, v.classe, v.principio, v.carencia, v.mapa
FROM (VALUES
    ('Glifosato 480', 'Herbicida', 'Glifosato', 7, 'MAPA-HERB-001'),
    ('Inseticida lambda-cialotrina', 'Inseticida', 'Lambda-cialotrina', 14, 'MAPA-INS-001'),
    ('Fungicida tebuconazol', 'Fungicida', 'Tebuconazol', 21, 'MAPA-FUNG-001'),
    ('Herbicida atrazina', 'Herbicida', 'Atrazina', 10, 'MAPA-HERB-002'),
    ('Ureia 45%', 'Fertilizante', 'Ureia', NULL, NULL),
    ('MAP 11-52-00', 'Fertilizante', 'Fosfato monoamonico', NULL, NULL),
    ('KCl 60%', 'Fertilizante', 'Cloreto de potassio', NULL, NULL),
    ('Semente de milho hibrido', 'Semente', NULL, NULL, NULL),
    ('Semente de soja', 'Semente', NULL, NULL, NULL),
    ('Semente de sorgo', 'Semente', NULL, NULL, NULL),
    ('Saco de sementes', 'Semente', NULL, NULL, NULL)
) AS v(nome, classe, principio, carencia, mapa)
JOIN produto p ON p.nome = v.nome
WHERE NOT EXISTS (SELECT 1 FROM insumo i WHERE i.id_produto = p.id_produto);

INSERT INTO produto_comercial (id_produto, codigo_comercial, marca, descricao_comercial)
SELECT
    p.id_produto,
    'SKU-' || lpad(g.n::text, 3, '0'),
    'Marca ' || g.n,
    'Produto comercial ' || g.n
FROM generate_series(1, 12) AS g(n)
JOIN produto p ON p.nome = CASE
    WHEN g.n <= 4 THEN (ARRAY['Milho', 'Soja', 'Sorgo', 'Trigo'])[g.n]
    WHEN g.n <= 8 THEN (ARRAY['Glifosato 480', 'Inseticida lambda-cialotrina', 'Fungicida tebuconazol', 'Herbicida atrazina'])[g.n - 4]
    ELSE (ARRAY['Semente de milho hibrido', 'Semente de soja', 'Ureia 45%', 'Oleo diesel S10'])[g.n - 8]
END
WHERE NOT EXISTS (SELECT 1 FROM produto_comercial pc WHERE pc.id_produto = p.id_produto);

-- -----------------------------------------------------------------------------
-- Farm / production chain
-- -----------------------------------------------------------------------------
INSERT INTO fazenda (nome, localizacao)
SELECT 'Fazenda ' || g.n, 'Zona rural ' || g.n
FROM generate_series(1, 12) AS g(n)
WHERE NOT EXISTS (SELECT 1 FROM fazenda f WHERE f.nome = 'Fazenda ' || g.n);

INSERT INTO safra (nome, ano, dt_inicio, dt_fim, status)
SELECT v.nome, v.ano, v.inicio, v.fim, v.status::status_safra_enum
FROM (VALUES
    ('Safra 2024/2025', 2024, DATE '2024-09-01', DATE '2025-04-30', 'FINALIZADA'),
    ('Safra 2025/2026', 2025, DATE '2025-09-01', DATE '2026-04-30', 'EM_ANDAMENTO'),
    ('Safra 2026/2027', 2026, DATE '2026-09-01', DATE '2027-04-30', 'PLANEJADA')
) AS v(nome, ano, inicio, fim, status)
WHERE NOT EXISTS (SELECT 1 FROM safra s WHERE s.nome = v.nome);

INSERT INTO cultura (nome, nome_cientifico, variedade, ciclo_dias, tipo_cultura)
SELECT v.nome, v.cientifico, v.variedade, v.ciclo, v.tipo
FROM (VALUES
    ('Milho', 'Zea mays', 'Hibrido AG 8088', 130, 'Grao'),
    ('Soja', 'Glycine max', 'Cultivar 63I64RSF', 120, 'Grao'),
    ('Sorgo', 'Sorghum bicolor', 'Variedade 1', 110, 'Grao'),
    ('Trigo', 'Triticum aestivum', 'Variedade 1', 125, 'Grao')
) AS v(nome, cientifico, variedade, ciclo, tipo)
WHERE NOT EXISTS (
    SELECT 1 FROM cultura c WHERE c.nome = v.nome AND c.variedade = v.variedade
);

INSERT INTO talhao (id_fazenda, id_safra, nome, area_hectares)
SELECT
    f.id_fazenda,
    s.id_safra,
    'Talhao ' || g.n,
    20.00 + (g.n * 2.5)
FROM generate_series(1, 12) AS g(n)
JOIN fazenda f ON f.nome = 'Fazenda ' || ((g.n - 1) % 12 + 1)
JOIN safra s ON s.nome = 'Safra 2025/2026'
WHERE NOT EXISTS (SELECT 1 FROM talhao t WHERE t.nome = 'Talhao ' || g.n);

INSERT INTO planejamento_safra (
    id_safra, id_talhao, id_cultura, meta_produtividade, area_planejada,
    dt_plantio_previsto, dt_colheita_previsto, status
)
SELECT
    s.id_safra,
    t.id_talhao,
    c.id_cultura,
    50.00 + g.n,
    t.area_hectares,
    DATE '2025-10-01' + ((g.n - 1) * 3),
    DATE '2026-02-15' + ((g.n - 1) * 3),
    CASE
        WHEN g.n <= 6 THEN 'EM_EXECUCAO'::status_planejamento_safra_enum
        ELSE 'APROVADO'::status_planejamento_safra_enum
    END
FROM generate_series(1, 12) AS g(n)
JOIN talhao t ON t.nome = 'Talhao ' || g.n
JOIN safra s ON s.nome = 'Safra 2025/2026'
JOIN cultura c ON c.nome = (ARRAY['Milho', 'Soja', 'Sorgo', 'Trigo'])[((g.n - 1) % 4) + 1]
WHERE NOT EXISTS (
    SELECT 1
    FROM planejamento_safra ps
    WHERE ps.id_talhao = t.id_talhao AND ps.id_cultura = c.id_cultura
);

INSERT INTO ordem_producao (id_safra, data_abertura, status)
SELECT s.id_safra, DATE '2025-09-15', 'EM_EXECUCAO'::status_ordem_producao_enum
FROM safra s
WHERE s.nome = 'Safra 2025/2026'
  AND NOT EXISTS (SELECT 1 FROM ordem_producao o WHERE o.id_safra = s.id_safra);

INSERT INTO plantio (
    id_ordem, id_talhao, id_produto, id_cultura, id_planejamento, dt_plantio, status
)
SELECT
    o.id_ordem,
    t.id_talhao,
    p.id_produto,
    c.id_cultura,
    ps.id_planejamento,
    DATE '2025-10-05' + ((g.n - 1) * 2),
    CASE
        WHEN g.n <= 4 THEN 'CONCLUIDO'::status_plantio_enum
        WHEN g.n <= 8 THEN 'EM_ANDAMENTO'::status_plantio_enum
        ELSE 'PLANEJADO'::status_plantio_enum
    END
FROM generate_series(1, 12) AS g(n)
JOIN ordem_producao o
    ON o.id_safra = (SELECT id_safra FROM safra WHERE nome = 'Safra 2025/2026' LIMIT 1)
JOIN talhao t ON t.nome = 'Talhao ' || g.n
JOIN cultura c ON c.id_cultura = (
    SELECT ps2.id_cultura FROM planejamento_safra ps2 WHERE ps2.id_talhao = t.id_talhao LIMIT 1
)
JOIN planejamento_safra ps ON ps.id_talhao = t.id_talhao AND ps.id_cultura = c.id_cultura
JOIN produto p ON p.nome = CASE c.nome
    WHEN 'Milho' THEN 'Semente de milho hibrido'
    WHEN 'Soja' THEN 'Semente de soja'
    WHEN 'Sorgo' THEN 'Semente de sorgo'
    ELSE 'Semente de milho hibrido'
END
WHERE NOT EXISTS (
    SELECT 1 FROM plantio pl WHERE pl.id_talhao = t.id_talhao AND pl.id_cultura = c.id_cultura
);

INSERT INTO colheita (id_plantio, quantidade_colhida, dt_inicio, dt_fim, status)
SELECT
    pl.id_plantio,
    800.00 + (g.n * 50),
    DATE '2026-02-01' + g.n,
    DATE '2026-02-05' + g.n,
    'CONCLUIDA'::status_colheita_enum
FROM generate_series(1, 4) AS g(n)
JOIN talhao t ON t.nome = 'Talhao ' || g.n
JOIN plantio pl ON pl.id_talhao = t.id_talhao
WHERE NOT EXISTS (SELECT 1 FROM colheita c WHERE c.id_plantio = pl.id_plantio);

INSERT INTO lote (
    id_colheita, id_produto, codigo_lote, validade, qualidade, tipo_origem, quantidade_inicial, status
)
SELECT
    c.id_colheita,
    prod.id_produto,
    'LOTE-' || upper(left(prod.nome, 5)) || '-' || lpad(g.n::text, 3, '0'),
    DATE '2027-02-14',
    'Tipo ' || ((g.n % 2) + 1),
    'COLHEITA'::tipo_origem_lote_enum,
    c.quantidade_colhida,
    'LIBERADO'::status_lote_enum
FROM generate_series(1, 4) AS g(n)
JOIN talhao t ON t.nome = 'Talhao ' || g.n
JOIN plantio pl ON pl.id_talhao = t.id_talhao
JOIN colheita c ON c.id_plantio = pl.id_plantio
JOIN produto prod ON prod.nome = (ARRAY['Milho', 'Soja', 'Sorgo', 'Trigo'])[g.n]
WHERE NOT EXISTS (
    SELECT 1 FROM lote l
    WHERE l.codigo_lote = 'LOTE-' || upper(left(prod.nome, 5)) || '-' || lpad(g.n::text, 3, '0')
);

-- Extra purchase lots (no harvest)
INSERT INTO lote (
    id_colheita, id_produto, codigo_lote, validade, qualidade, tipo_origem, quantidade_inicial, status
)
SELECT
    NULL,
    p.id_produto,
    'LOTE-COMPRA-' || lpad(g.n::text, 3, '0'),
    DATE '2027-06-01',
    'Padrao',
    'COMPRA'::tipo_origem_lote_enum,
    100.00 * g.n,
    'LIBERADO'::status_lote_enum
FROM generate_series(1, 8) AS g(n)
JOIN produto p ON p.nome = (ARRAY[
    'Glifosato 480',
    'Inseticida lambda-cialotrina',
    'Fungicida tebuconazol',
    'Herbicida atrazina',
    'Ureia 45%',
    'MAP 11-52-00',
    'KCl 60%',
    'Oleo diesel S10'
])[g.n]
WHERE NOT EXISTS (
    SELECT 1 FROM lote l WHERE l.codigo_lote = 'LOTE-COMPRA-' || lpad(g.n::text, 3, '0')
);

-- -----------------------------------------------------------------------------
-- Inventory
-- -----------------------------------------------------------------------------
INSERT INTO local_armazenamento (descricao, capacidade)
SELECT 'Local Armazenamento ' || g.n, 1000.00 * g.n
FROM generate_series(1, 12) AS g(n)
WHERE NOT EXISTS (
    SELECT 1 FROM local_armazenamento la WHERE la.descricao = 'Local Armazenamento ' || g.n
);

INSERT INTO estoque (id_local)
SELECT la.id_local
FROM generate_series(1, 12) AS g(n)
JOIN local_armazenamento la ON la.descricao = 'Local Armazenamento ' || g.n
WHERE NOT EXISTS (SELECT 1 FROM estoque e WHERE e.id_local = la.id_local);

INSERT INTO saldo_estoque (id_estoque, id_produto, quantidade_atual)
SELECT
    e.id_estoque,
    p.id_produto,
    200.00 + (g.n * 10)
FROM generate_series(1, 12) AS g(n)
JOIN local_armazenamento la ON la.descricao = 'Local Armazenamento ' || ((g.n - 1) % 12 + 1)
JOIN estoque e ON e.id_local = la.id_local
JOIN produto p ON p.nome = (ARRAY[
    'Milho', 'Soja', 'Sorgo', 'Trigo',
    'Glifosato 480', 'Inseticida lambda-cialotrina', 'Fungicida tebuconazol', 'Herbicida atrazina',
    'Ureia 45%', 'MAP 11-52-00', 'KCl 60%', 'Oleo diesel S10'
])[g.n]
WHERE NOT EXISTS (
    SELECT 1
    FROM saldo_estoque se
    WHERE se.id_estoque = e.id_estoque AND se.id_produto = p.id_produto
);

INSERT INTO saldo_lote (id_estoque, id_lote, quantidade_atual, quantidade_reservada)
SELECT
    e.id_estoque,
    l.id_lote,
    COALESCE(l.quantidade_inicial, 100),
    0
FROM lote l
JOIN produto p ON p.id_produto = l.id_produto
JOIN local_armazenamento la ON la.descricao = 'Local Armazenamento 1'
JOIN estoque e ON e.id_local = la.id_local
WHERE NOT EXISTS (
    SELECT 1 FROM saldo_lote sl WHERE sl.id_estoque = e.id_estoque AND sl.id_lote = l.id_lote
);

-- -----------------------------------------------------------------------------
-- Procurement samples (spread across first suppliers)
-- -----------------------------------------------------------------------------
INSERT INTO pedido (id_fornecedor, data_pedido, status)
SELECT
    f.id_fornecedor,
    CURRENT_DATE - g.n,
    (ARRAY[
        'ABERTO',
        'APROVADO',
        'PARCIALMENTE_ATENDIDO',
        'ATENDIDO',
        'ABERTO',
        'APROVADO',
        'ATENDIDO',
        'ABERTO',
        'APROVADO',
        'CANCELADO'
    ])[g.n]::status_pedido_compra_enum
FROM generate_series(1, 10) AS g(n)
JOIN pessoa pe ON pe.documento = 'DOC-FORN-' || lpad(g.n::text, 3, '0')
JOIN fornecedor f ON f.id_pessoa = pe.id_pessoa
WHERE NOT EXISTS (
    SELECT 1
    FROM pedido ped
    WHERE ped.id_fornecedor = f.id_fornecedor
      AND ped.data_pedido = CURRENT_DATE - g.n
);

INSERT INTO item_pedido (id_pedido, id_produto, quantidade, valor_unitario)
SELECT
    ped.id_pedido,
    p.id_produto,
    20 + g.n,
    COALESCE(p.preco, 10.00)
FROM generate_series(1, 10) AS g(n)
JOIN pessoa pe ON pe.documento = 'DOC-FORN-' || lpad(g.n::text, 3, '0')
JOIN fornecedor f ON f.id_pessoa = pe.id_pessoa
JOIN pedido ped ON ped.id_fornecedor = f.id_fornecedor AND ped.data_pedido = CURRENT_DATE - g.n
JOIN produto p ON p.nome = (ARRAY[
    'Glifosato 480',
    'Oleo diesel S10',
    'Ureia 45%',
    'Inseticida lambda-cialotrina',
    'Fungicida tebuconazol',
    'MAP 11-52-00',
    'KCl 60%',
    'Semente de milho hibrido',
    'Semente de soja',
    'Herbicida atrazina'
])[g.n]
WHERE NOT EXISTS (SELECT 1 FROM item_pedido i WHERE i.id_pedido = ped.id_pedido);

INSERT INTO compra (id_pedido, id_centro_custo, valor_total, data_compra)
SELECT
    ped.id_pedido,
    cc.id_centro_custo,
    (20 + g.n) * COALESCE(p.preco, 10.00),
    CURRENT_DATE - g.n + 1
FROM generate_series(1, 10) AS g(n)
JOIN pessoa pe ON pe.documento = 'DOC-FORN-' || lpad(g.n::text, 3, '0')
JOIN fornecedor f ON f.id_pessoa = pe.id_pessoa
JOIN pedido ped ON ped.id_fornecedor = f.id_fornecedor
    AND ped.data_pedido = CURRENT_DATE - g.n
    AND ped.status IN (
        'APROVADO'::status_pedido_compra_enum,
        'PARCIALMENTE_ATENDIDO'::status_pedido_compra_enum,
        'ATENDIDO'::status_pedido_compra_enum
    )
JOIN centro_custo cc ON cc.nome = 'Centro de Custo ' || ((g.n - 1) % 12 + 1)
JOIN item_pedido ip ON ip.id_pedido = ped.id_pedido
JOIN produto p ON p.id_produto = ip.id_produto
WHERE NOT EXISTS (SELECT 1 FROM compra c WHERE c.id_pedido = ped.id_pedido);

-- -----------------------------------------------------------------------------
-- Phytosanitary
-- -----------------------------------------------------------------------------
INSERT INTO agente_nocivo (nome_comum, nome_cientifico)
SELECT v.comum, v.cientifico
FROM (VALUES
    ('Lagarta-do-cartucho', 'Spodoptera frugiperda'),
    ('Ferrugem asiatica', 'Phakopsora pachyrhizi'),
    ('Percevejo-marrom', 'Euschistus heros'),
    ('Mosca-branca', 'Bemisia tabaci'),
    ('Cigarrinha-do-milho', 'Dalbulus maidis'),
    ('Helmintosporiose', 'Exserohilum turcicum'),
    ('Antracnose', 'Colletotrichum truncatum'),
    ('Mofo-branco', 'Sclerotinia sclerotiorum'),
    ('Lagarta-da-soja', 'Anticarsia gemmatalis'),
    ('Pulgão', 'Aphis glycines'),
    ('Tripes', 'Frankliniella schultzei'),
    ('Oidio', 'Erysiphe diffusa')
) AS v(comum, cientifico)
WHERE NOT EXISTS (SELECT 1 FROM agente_nocivo a WHERE a.nome_comum = v.comum);

INSERT INTO praga (id_agente, tipo_praga, habito_alimentar)
SELECT a.id_agente, 'Inseto', 'Folhas e graos'
FROM agente_nocivo a
WHERE a.nome_comum IN (
    'Lagarta-do-cartucho', 'Percevejo-marrom', 'Mosca-branca', 'Cigarrinha-do-milho',
    'Lagarta-da-soja', 'Pulgão', 'Tripes'
)
  AND NOT EXISTS (SELECT 1 FROM praga p WHERE p.id_agente = a.id_agente);

INSERT INTO doenca (id_agente, agente_causador, sintomas, condicao_favoravel)
SELECT
    a.id_agente,
    'Fungo',
    'Sintomas tipicos da doenca',
    'Alta umidade'
FROM agente_nocivo a
WHERE a.nome_comum IN (
    'Ferrugem asiatica', 'Helmintosporiose', 'Antracnose', 'Mofo-branco', 'Oidio'
)
  AND NOT EXISTS (SELECT 1 FROM doenca d WHERE d.id_agente = a.id_agente);

INSERT INTO controle_fitossanitario (
    id_plantio, id_funcionario, dt_identificacao, nivel_severidade,
    area_afetada_hectares, recomendacao
)
SELECT
    pl.id_plantio,
    f.id_funcionario,
    CURRENT_DATE - g.n,
    (ARRAY['Baixo', 'Medio', 'Alto', 'Critico'])[((g.n - 1) % 4) + 1],
    1.00 + g.n,
    'Recomendacao ' || g.n
FROM generate_series(1, 10) AS g(n)
JOIN talhao t ON t.nome = 'Talhao ' || g.n
JOIN plantio pl ON pl.id_talhao = t.id_talhao
JOIN pessoa pe ON pe.documento = 'DOC-FUNC-' || lpad(((g.n - 1) % 12 + 1)::text, 3, '0')
JOIN funcionario f ON f.id_pessoa = pe.id_pessoa
WHERE NOT EXISTS (
    SELECT 1 FROM controle_fitossanitario cf WHERE cf.id_plantio = pl.id_plantio
);

INSERT INTO ocorrencia_agente (id_controle, id_agente, nivel_infestacao, metodo_controle)
SELECT
    cf.id_controle,
    a.id_agente,
    (ARRAY['Baixo', 'Medio', 'Alto'])[((g.n - 1) % 3) + 1],
    'Controle quimico'
FROM generate_series(1, 10) AS g(n)
JOIN talhao t ON t.nome = 'Talhao ' || g.n
JOIN plantio pl ON pl.id_talhao = t.id_talhao
JOIN controle_fitossanitario cf ON cf.id_plantio = pl.id_plantio
JOIN agente_nocivo a ON a.nome_comum = (ARRAY[
    'Lagarta-do-cartucho', 'Ferrugem asiatica', 'Percevejo-marrom', 'Mosca-branca',
    'Cigarrinha-do-milho', 'Helmintosporiose', 'Antracnose', 'Mofo-branco',
    'Lagarta-da-soja', 'Pulgão'
])[g.n]
WHERE NOT EXISTS (
    SELECT 1
    FROM ocorrencia_agente oa
    WHERE oa.id_controle = cf.id_controle AND oa.id_agente = a.id_agente
);

INSERT INTO aplicacao_defensivo (
    id_controle, id_insumo, dose_hectare, volume_aplicado, dt_aplicacao, dt_carencia
)
SELECT
    cf.id_controle,
    i.id_produto,
    0.20 + (g.n * 0.05),
    100.00 + (g.n * 10),
    CURRENT_DATE - g.n + 1,
    CURRENT_DATE - g.n + 1 + COALESCE(i.periodo_carencia_dias, 7)
FROM generate_series(1, 10) AS g(n)
JOIN talhao t ON t.nome = 'Talhao ' || g.n
JOIN plantio pl ON pl.id_talhao = t.id_talhao
JOIN controle_fitossanitario cf ON cf.id_plantio = pl.id_plantio
JOIN produto prod ON prod.nome = (ARRAY[
    'Inseticida lambda-cialotrina',
    'Fungicida tebuconazol',
    'Glifosato 480',
    'Herbicida atrazina',
    'Inseticida lambda-cialotrina',
    'Fungicida tebuconazol',
    'Glifosato 480',
    'Herbicida atrazina',
    'Inseticida lambda-cialotrina',
    'Fungicida tebuconazol'
])[g.n]
JOIN insumo i ON i.id_produto = prod.id_produto
WHERE NOT EXISTS (
    SELECT 1
    FROM aplicacao_defensivo ad
    WHERE ad.id_controle = cf.id_controle AND ad.id_insumo = i.id_produto
);

-- -----------------------------------------------------------------------------
-- Maintenance
-- -----------------------------------------------------------------------------
INSERT INTO tipo_maquina (descricao)
SELECT 'Tipo Maquina ' || g.n
FROM generate_series(1, 12) AS g(n)
WHERE NOT EXISTS (
    SELECT 1 FROM tipo_maquina tm WHERE tm.descricao = 'Tipo Maquina ' || g.n
);

INSERT INTO prestador_servico (nome, cnpj, especialidade, telefone)
SELECT
    'Prestador ' || g.n,
    lpad(g.n::text, 14, '0'),
    CASE (g.n % 3)
        WHEN 0 THEN 'Mecanica'
        WHEN 1 THEN 'Eletrica'
        ELSE 'Hidraulica'
    END,
    '8199' || lpad(g.n::text, 7, '0')
FROM generate_series(1, 12) AS g(n)
WHERE NOT EXISTS (
    SELECT 1 FROM prestador_servico ps WHERE ps.nome = 'Prestador ' || g.n
);

INSERT INTO maquina (id_tipo_maquina, id_fazenda, nome, status)
SELECT
    tm.id_tipo_maquina,
    f.id_fazenda,
    'Maquina ' || g.n,
    (ARRAY[
        'DISPONIVEL', 'EM_USO', 'EM_MANUTENCAO', 'INATIVA',
        'DISPONIVEL', 'EM_USO', 'DISPONIVEL', 'EM_MANUTENCAO',
        'DISPONIVEL', 'EM_USO', 'DISPONIVEL', 'DISPONIVEL'
    ])[g.n]::status_maquina_enum
FROM generate_series(1, 12) AS g(n)
JOIN tipo_maquina tm ON tm.descricao = 'Tipo Maquina ' || g.n
JOIN fazenda f ON f.nome = 'Fazenda ' || g.n
WHERE NOT EXISTS (SELECT 1 FROM maquina m WHERE m.nome = 'Maquina ' || g.n);

INSERT INTO plano_manutencao (id_maquina, periodicidade, proxima_execucao)
SELECT
    m.id_maquina,
    (g.n * 30) || ' dias',
    CURRENT_DATE + (g.n * 7)
FROM generate_series(1, 12) AS g(n)
JOIN maquina m ON m.nome = 'Maquina ' || g.n
WHERE NOT EXISTS (SELECT 1 FROM plano_manutencao pm WHERE pm.id_maquina = m.id_maquina);

INSERT INTO manutencao (
    id_maquina, id_funcionario, id_prestador, tipo, custo, status, dt_inicio, dt_fim
)
SELECT
    m.id_maquina,
    f.id_funcionario,
    ps.id_prestador,
    CASE WHEN g.n % 2 = 0 THEN 'Preventiva' ELSE 'Corretiva' END,
    500.00 * g.n,
    (ARRAY[
        'ABERTA', 'EM_EXECUCAO', 'CONCLUIDA', 'CANCELADA',
        'ABERTA', 'EM_EXECUCAO', 'CONCLUIDA', 'ABERTA',
        'EM_EXECUCAO', 'CONCLUIDA', 'ABERTA', 'CONCLUIDA'
    ])[g.n]::status_manutencao_enum,
    CURRENT_DATE - g.n,
    CASE WHEN g.n % 3 = 0 THEN CURRENT_DATE - g.n + 2 ELSE NULL END
FROM generate_series(1, 12) AS g(n)
JOIN maquina m ON m.nome = 'Maquina ' || g.n
JOIN pessoa pe ON pe.documento = 'DOC-FUNC-' || lpad(((g.n - 1) % 12 + 1)::text, 3, '0')
JOIN funcionario f ON f.id_pessoa = pe.id_pessoa
JOIN prestador_servico ps ON ps.nome = 'Prestador ' || g.n
WHERE NOT EXISTS (
    SELECT 1 FROM manutencao mt WHERE mt.id_maquina = m.id_maquina AND mt.tipo IS NOT NULL
      AND mt.dt_inicio = CURRENT_DATE - g.n
);

INSERT INTO ordem_servico (id_manutencao, descricao, status)
SELECT
    mt.id_manutencao,
    'Ordem Servico ' || g.n,
    (ARRAY[
        'ABERTA', 'EM_EXECUCAO', 'CONCLUIDA', 'CANCELADA',
        'ABERTA', 'EM_EXECUCAO', 'CONCLUIDA', 'ABERTA',
        'EM_EXECUCAO', 'CONCLUIDA', 'ABERTA', 'CONCLUIDA'
    ])[g.n]::status_ordem_servico_enum
FROM generate_series(1, 12) AS g(n)
JOIN maquina m ON m.nome = 'Maquina ' || g.n
JOIN manutencao mt ON mt.id_maquina = m.id_maquina AND mt.dt_inicio = CURRENT_DATE - g.n
WHERE NOT EXISTS (
    SELECT 1 FROM ordem_servico os WHERE os.id_manutencao = mt.id_manutencao
);

-- -----------------------------------------------------------------------------
-- Sales
-- -----------------------------------------------------------------------------
INSERT INTO venda (id_cliente, id_centro_custo, valor_total, data_venda, status)
SELECT
    c.id_cliente,
    cc.id_centro_custo,
    1000.00 * g.n,
    CURRENT_DATE - g.n,
    (ARRAY[
        'CONFIRMADA', 'CONFIRMADA', 'EXPEDIDA', 'ENTREGUE', 'CONFIRMADA',
        'RASCUNHO', 'CONFIRMADA', 'CANCELADA', 'CONFIRMADA', 'ENTREGUE',
        'CONFIRMADA', 'CONFIRMADA'
    ])[g.n]::status_venda_enum
FROM generate_series(1, 12) AS g(n)
JOIN pessoa pe ON pe.documento = 'DOC-CLI-' || lpad(g.n::text, 3, '0')
JOIN cliente c ON c.id_pessoa = pe.id_pessoa
JOIN centro_custo cc ON cc.nome = 'Centro de Custo ' || g.n
WHERE NOT EXISTS (
    SELECT 1
    FROM venda v
    WHERE v.id_cliente = c.id_cliente AND v.valor_total = 1000.00 * g.n
);

INSERT INTO item_venda (id_venda, id_produto, id_lote, quantidade, valor_unitario)
SELECT
    v.id_venda,
    p.id_produto,
    l.id_lote,
    10 * g.n,
    COALESCE(p.preco, 85.00)
FROM generate_series(1, 10) AS g(n)
JOIN pessoa pe ON pe.documento = 'DOC-CLI-' || lpad(g.n::text, 3, '0')
JOIN cliente c ON c.id_pessoa = pe.id_pessoa
JOIN venda v ON v.id_cliente = c.id_cliente AND v.valor_total = 1000.00 * g.n
JOIN produto p ON p.nome = (ARRAY[
    'Milho', 'Soja', 'Sorgo', 'Trigo', 'Milho',
    'Soja', 'Milho', 'Soja', 'Trigo', 'Sorgo'
])[g.n]
LEFT JOIN lote l ON l.codigo_lote = (
    SELECT l2.codigo_lote
    FROM lote l2
    WHERE l2.id_produto = p.id_produto
    ORDER BY l2.id_lote
    LIMIT 1
)
WHERE NOT EXISTS (SELECT 1 FROM item_venda iv WHERE iv.id_venda = v.id_venda);

-- -----------------------------------------------------------------------------
-- Logistics
-- -----------------------------------------------------------------------------
INSERT INTO endereco (logradouro, numero, cidade, estado, cep)
SELECT
    'Rua ' || g.n,
    g.n::text,
    'Cidade ' || g.n,
    (ARRAY['PE', 'PB', 'AL', 'BA', 'SE', 'RN', 'CE', 'PI', 'MA', 'SP', 'MG', 'PR'])[g.n],
    lpad((50000000 + g.n)::text, 8, '0')
FROM generate_series(1, 12) AS g(n)
WHERE NOT EXISTS (
    SELECT 1 FROM endereco e
    WHERE e.logradouro = 'Rua ' || g.n AND e.numero = g.n::text
);

INSERT INTO local_logistico (nome, tipo, id_endereco)
SELECT
    CASE
        WHEN g.n <= 4 THEN 'Fazenda ' || g.n
        WHEN g.n <= 7 THEN 'Armazem ' || (g.n - 4)
        WHEN g.n <= 9 THEN 'Porto ' || (g.n - 7)
        ELSE 'Cliente Destino ' || (g.n - 9)
    END,
    CASE
        WHEN g.n <= 4 THEN 'FAZENDA'::tipo_local_logistico_enum
        WHEN g.n <= 7 THEN 'ARMAZEM'::tipo_local_logistico_enum
        WHEN g.n <= 9 THEN 'PORTO'::tipo_local_logistico_enum
        ELSE 'CLIENTE'::tipo_local_logistico_enum
    END,
    e.id_endereco
FROM generate_series(1, 12) AS g(n)
JOIN endereco e ON e.logradouro = 'Rua ' || g.n AND e.numero = g.n::text
WHERE NOT EXISTS (
    SELECT 1
    FROM local_logistico ll
    WHERE ll.nome = CASE
        WHEN g.n <= 4 THEN 'Fazenda ' || g.n
        WHEN g.n <= 7 THEN 'Armazem ' || (g.n - 4)
        WHEN g.n <= 9 THEN 'Porto ' || (g.n - 7)
        ELSE 'Cliente Destino ' || (g.n - 9)
    END
);

INSERT INTO veiculo (tipo, placa, capacidade)
SELECT
    (ARRAY[
        'CAMINHAO_GRANELEIRO',
        'CAMINHAO_BASCULANTE',
        'CARRETA_BASCULANTE',
        'BITREM',
        'RODOTREM',
        'TRUCK',
        'TOCO',
        'CAMINHAO_BAU',
        'CAMIONETE',
        'UTILITARIO',
        'VAN',
        'TRATOR'
    ])[g.n]::tipo_veiculo_enum,
    'AAA1A' || lpad(g.n::text, 2, '0'),
    10.00 + (g.n * 2)
FROM generate_series(1, 12) AS g(n)
WHERE NOT EXISTS (
    SELECT 1 FROM veiculo v WHERE v.placa = 'AAA1A' || lpad(g.n::text, 2, '0')
);

INSERT INTO operacao_logistica (
    id_veiculo, id_venda, id_origem, id_destino, tipo, data_inicio, data_fim, status, custo_previsto
)
SELECT
    v.id_veiculo,
    vd.id_venda,
    lo.id_local_logistico,
    ld.id_local_logistico,
    'VENDA'::tipo_operacao_logistica_enum,
    CURRENT_TIMESTAMP - ((g.n || ' days')::interval),
    CASE WHEN g.n % 3 = 0 THEN CURRENT_TIMESTAMP - ((g.n - 1) || ' days')::interval ELSE NULL END,
    (ARRAY[
        'ABERTA', 'EM_ANDAMENTO', 'CONCLUIDA', 'CANCELADA',
        'ABERTA', 'EM_ANDAMENTO', 'CONCLUIDA', 'ABERTA',
        'EM_ANDAMENTO', 'CONCLUIDA'
    ])[g.n]::status_operacao_logistica_enum,
    250.00 * g.n
FROM generate_series(1, 10) AS g(n)
JOIN veiculo v ON v.placa = 'AAA1A' || lpad(g.n::text, 2, '0')
JOIN pessoa pe ON pe.documento = 'DOC-CLI-' || lpad(g.n::text, 3, '0')
JOIN cliente c ON c.id_pessoa = pe.id_pessoa
JOIN venda vd ON vd.id_cliente = c.id_cliente AND vd.valor_total = 1000.00 * g.n
JOIN local_logistico lo ON lo.nome = 'Fazenda ' || ((g.n - 1) % 4 + 1)
JOIN local_logistico ld ON ld.nome = CASE
    WHEN g.n % 2 = 0 THEN 'Armazem ' || ((g.n - 1) % 3 + 1)
    ELSE 'Porto ' || ((g.n - 1) % 2 + 1)
END
WHERE lo.id_local_logistico <> ld.id_local_logistico
  AND NOT EXISTS (
      SELECT 1
      FROM operacao_logistica ol
      WHERE ol.id_venda = vd.id_venda AND ol.id_veiculo = v.id_veiculo
  );

INSERT INTO carga (id_operacao, id_lote, quantidade, peso_previsto, id_item_venda)
SELECT
    ol.id_operacao,
    COALESCE(iv.id_lote, (
        SELECT l.id_lote
        FROM lote l
        WHERE l.id_produto = iv.id_produto
        ORDER BY l.id_lote
        LIMIT 1
    )),
    iv.quantidade,
    iv.quantidade / 50.0,
    iv.id_item_venda
FROM generate_series(1, 10) AS g(n)
JOIN veiculo v ON v.placa = 'AAA1A' || lpad(g.n::text, 2, '0')
JOIN pessoa pe ON pe.documento = 'DOC-CLI-' || lpad(g.n::text, 3, '0')
JOIN cliente c ON c.id_pessoa = pe.id_pessoa
JOIN venda vd ON vd.id_cliente = c.id_cliente AND vd.valor_total = 1000.00 * g.n
JOIN operacao_logistica ol ON ol.id_venda = vd.id_venda AND ol.id_veiculo = v.id_veiculo
JOIN item_venda iv ON iv.id_venda = vd.id_venda
WHERE NOT EXISTS (
    SELECT 1 FROM carga cg WHERE cg.id_operacao = ol.id_operacao
);

INSERT INTO pesagem (id_carga, peso_registrado, data_pesagem)
SELECT
    cg.id_carga,
    COALESCE(cg.peso_previsto, 10) - 0.2,
    CURRENT_TIMESTAMP - ((g.n || ' hours')::interval)
FROM generate_series(1, 10) AS g(n)
JOIN veiculo v ON v.placa = 'AAA1A' || lpad(g.n::text, 2, '0')
JOIN pessoa pe ON pe.documento = 'DOC-CLI-' || lpad(g.n::text, 3, '0')
JOIN cliente c ON c.id_pessoa = pe.id_pessoa
JOIN venda vd ON vd.id_cliente = c.id_cliente AND vd.valor_total = 1000.00 * g.n
JOIN operacao_logistica ol ON ol.id_venda = vd.id_venda AND ol.id_veiculo = v.id_veiculo
JOIN carga cg ON cg.id_operacao = ol.id_operacao
WHERE NOT EXISTS (SELECT 1 FROM pesagem p WHERE p.id_carga = cg.id_carga);

INSERT INTO expedicao (id_carga, data_saida, status, id_funcionario, observacoes)
SELECT
    cg.id_carga,
    CASE WHEN g.n % 2 = 0 THEN CURRENT_TIMESTAMP - ((g.n || ' hours')::interval) ELSE NULL END,
    (ARRAY[
        'PENDENTE', 'EM_PREPARACAO', 'EXPEDIDA', 'ENTREGUE', 'PENDENTE',
        'EM_PREPARACAO', 'EXPEDIDA', 'CANCELADA', 'PENDENTE', 'ENTREGUE'
    ])[g.n]::status_expedicao_enum,
    f.id_funcionario,
    'Expedicao ' || g.n
FROM generate_series(1, 10) AS g(n)
JOIN veiculo v ON v.placa = 'AAA1A' || lpad(g.n::text, 2, '0')
JOIN pessoa pe ON pe.documento = 'DOC-CLI-' || lpad(g.n::text, 3, '0')
JOIN cliente c ON c.id_pessoa = pe.id_pessoa
JOIN venda vd ON vd.id_cliente = c.id_cliente AND vd.valor_total = 1000.00 * g.n
JOIN operacao_logistica ol ON ol.id_venda = vd.id_venda AND ol.id_veiculo = v.id_veiculo
JOIN carga cg ON cg.id_operacao = ol.id_operacao
JOIN pessoa pm ON pm.documento = 'DOC-MOT-' || lpad(g.n::text, 3, '0')
JOIN funcionario f ON f.id_pessoa = pm.id_pessoa
WHERE NOT EXISTS (SELECT 1 FROM expedicao e WHERE e.id_carga = cg.id_carga);

-- -----------------------------------------------------------------------------
-- Intelligence
-- -----------------------------------------------------------------------------
INSERT INTO indicador (nome, unidade)
SELECT v.nome, v.unidade
FROM (VALUES
    ('Produtividade media', 'SC/HA'),
    ('Custo por hectare', 'BRL'),
    ('Perda pos-colheita', '%'),
    ('Consumo de combustivel', 'L'),
    ('Horas de maquina', 'H'),
    ('Ocorrencias fitossanitarias', 'UN'),
    ('Aplicacoes de defensivo', 'UN'),
    ('Pedidos de compra abertos', 'UN'),
    ('Vendas confirmadas', 'UN'),
    ('Saldo de estoque critico', 'UN'),
    ('Indicador 11', 'UN'),
    ('Indicador 12', 'UN')
) AS v(nome, unidade)
WHERE NOT EXISTS (SELECT 1 FROM indicador i WHERE i.nome = v.nome);

INSERT INTO medicao_indicador (id_indicador, id_safra, valor, data_referencia)
SELECT
    i.id_indicador,
    s.id_safra,
    10.00 * g.n,
    CURRENT_DATE - g.n
FROM generate_series(1, 12) AS g(n)
JOIN indicador i ON i.nome = (ARRAY[
    'Produtividade media',
    'Custo por hectare',
    'Perda pos-colheita',
    'Consumo de combustivel',
    'Horas de maquina',
    'Ocorrencias fitossanitarias',
    'Aplicacoes de defensivo',
    'Pedidos de compra abertos',
    'Vendas confirmadas',
    'Saldo de estoque critico',
    'Indicador 11',
    'Indicador 12'
])[g.n]
JOIN safra s ON s.nome = 'Safra 2025/2026'
WHERE NOT EXISTS (
    SELECT 1
    FROM medicao_indicador m
    WHERE m.id_indicador = i.id_indicador
      AND m.id_safra = s.id_safra
      AND m.data_referencia = CURRENT_DATE - g.n
);

COMMIT;
