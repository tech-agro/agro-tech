ENTIDADES E ATRIBUTOS

CONVENCOES DDL (POSTGRES)

- Evitar `status: STRING`; usar ENUM especifico por agregado.
- Definir `NOT NULL` para PK, FK e atributos obrigatorios de negocio.
- Definir precisao/escala para `DECIMAL` conforme dominio (ex.: `DECIMAL(12,2)` para valores monetarios).
- Criar `CHECK` para regras basicas (ex.: `dt_fim >= dt_inicio`, `quantidade > 0`, `preco >= 0`).
- Criar indices para FKs e colunas de busca frequente.

ENUMS DE STATUS SUGERIDOS

- status_cliente_enum: ATIVO, INATIVO, BLOQUEADO
- status_safra_enum: PLANEJADA, EM_ANDAMENTO, FINALIZADA, CANCELADA
- status_planejamento_safra_enum: RASCUNHO, APROVADO, EM_EXECUCAO, CONCLUIDO, CANCELADO
- status_ordem_producao_enum: ABERTA, EM_EXECUCAO, CONCLUIDA, CANCELADA
- status_certificacao_enum: VIGENTE, VENCIDA, SUSPENSA, CANCELADA
- status_plantio_enum: PLANEJADO, EM_ANDAMENTO, CONCLUIDO, CANCELADO
- status_operacao_agricola_enum: ABERTA, EM_ANDAMENTO, CONCLUIDA, CANCELADA
- status_atividade_agricola_enum: PENDENTE, EM_ANDAMENTO, CONCLUIDA, CANCELADA
- status_colheita_enum: ABERTA, EM_ANDAMENTO, CONCLUIDA, CANCELADA
- status_pedido_compra_enum: ABERTO, APROVADO, PARCIALMENTE_ATENDIDO, ATENDIDO, CANCELADO
- status_maquina_enum: DISPONIVEL, EM_USO, EM_MANUTENCAO, INATIVA
- status_manutencao_enum: ABERTA, EM_EXECUCAO, CONCLUIDA, CANCELADA
- status_ordem_servico_enum: ABERTA, EM_EXECUCAO, CONCLUIDA, CANCELADA
- status_operacao_logistica_enum: PLANEJADA, EM_TRANSITO, FINALIZADA, CANCELADA
- status_expedicao_enum: PENDENTE, EM_PREPARACAO, EXPEDIDA, ENTREGUE, CANCELADA
- status_conta_pagar_enum: ABERTA, PARCIALMENTE_PAGA, PAGA, VENCIDA, CANCELADA
- status_conta_receber_enum: ABERTA, PARCIALMENTE_RECEBIDA, RECEBIDA, VENCIDA, CANCELADA

PESSOA (
    id_pessoa: INT [PK]
    nome: STRING
    documento: STRING [UNIQUE]
)

EMAIL (
    id_email: INT [PK]
    id_pessoa: INT [FK]
    email: STRING [UNIQUE]
)

TELEFONE (
    id_telefone: INT [PK]
    id_pessoa: INT [FK]
    telefone: STRING
)

USUARIO (
    id_usuario: INT [PK]
    id_pessoa: INT [FK][UNIQUE]
    senha_hash: STRING
    ativo: BOOLEAN
)

FUNCIONARIO (
    id_funcionario: INT [PK]
    id_pessoa: INT [FK]
    cargo: STRING
    setor: STRING
    data_admissao: DATE
)

CLIENTE (
    id_cliente: INT [PK]
    id_pessoa: INT [FK]
    status: status_cliente_enum
)

FORNECEDOR (
    id_fornecedor: INT [PK]
    id_pessoa: INT [FK]
    categoria: STRING
)

PERFIL_ACESSO (
    id_perfil: INT [PK]
    nome: STRING
)

PERMISSAO (
    id_permissao: INT [PK]
    descricao: STRING
)

USUARIO_PERFIL (
    id_usuario: INT [FK]
    id_perfil: INT [FK]
    PK(id_usuario, id_perfil)
)

PERFIL_PERMISSAO (
    id_perfil: INT [FK]
    id_permissao: INT [FK]
    PK(id_perfil, id_permissao)
)

AUDITORIA_LOG (
    id_log: INT [PK]
    id_usuario: INT [FK]
    acao: STRING
    data_evento: DATETIME
)

NOTIFICACAO (
    id_notificacao: INT [PK]
    id_usuario: INT [FK]
    mensagem: STRING
    data_envio: DATETIME
)

CENTRO_CUSTO (
    id_centro_custo: INT [PK]
    nome: STRING
)

FAZENDA (
    id_fazenda: INT [PK]
    nome: STRING
    localizacao: STRING
)

SAFRA (
    id_safra: INT [PK]
    nome: STRING
    ano: INT
    dt_inicio: DATE
    dt_fim: DATE
    status: status_safra_enum
)

CULTURA (
    id_cultura: INT [PK]
    nome: STRING
    nome_cientifico: STRING
    variedade: STRING
    ciclo_dias: INT
    tipo_cultura: STRING
)

TALHAO (
    id_talhao: INT [PK]
    id_fazenda: INT [FK]
    id_safra: INT [FK]
    nome: STRING
    area_hectares: DECIMAL
)

SOLO (
    id_solo: INT [PK]
    id_talhao: INT [FK][UNIQUE]
    tipo_solo: STRING
    textura: STRING
    profundidade_cm: DECIMAL
)

ANALISE_SOLO (
    id_analise: INT [PK]
    id_solo: INT [FK]
    id_safra: INT [FK]
    id_funcionario: INT [FK]
    dt_coleta: DATE
    dt_resultado: DATE
    ph: DECIMAL
    materia_organica: DECIMAL
    fosforo: DECIMAL
    potassio: DECIMAL
    calcio: DECIMAL
    magnesio: DECIMAL
    saturacao_bases: DECIMAL
    observacao: STRING
)

CONDICAO_CLIMATICA (
    id_condicao: INT [PK]
    id_talhao: INT [FK]
    dt_registro: DATETIME
    temperatura_min: DECIMAL
    temperatura_max: DECIMAL
    umidade_relativa: DECIMAL
    precipitacao_mm: DECIMAL
    velocidade_vento: DECIMAL
    direcao_vento: STRING
    radiacao_solar: DECIMAL
)

PLANEJAMENTO_SAFRA (
    id_planejamento: INT [PK]
    id_safra: INT [FK]
    id_talhao: INT [FK]
    id_cultura: INT [FK]
    meta_produtividade: DECIMAL
    area_planejada: DECIMAL
    dt_plantio_previsto: DATE
    dt_colheita_previsto: DATE
    status: status_planejamento_safra_enum
)

ORDEM_PRODUCAO (
    id_ordem: INT [PK]
    id_safra: INT [FK]
    data_abertura: DATE
    status: status_ordem_producao_enum
)

CATEGORIA_PRODUTO (
    id_categoria: INT [PK]
    nome: STRING
)

UNIDADE_MEDIDA (
    id_unidade: INT [PK]
    sigla: unidade_sigla_enum  -- KG | L | UN | SC | HA | T (nao e texto livre)
    descricao: STRING
)

PRODUTO (
    id_produto: INT [PK]
    id_categoria: INT [FK]
    id_unidade: INT [FK]
    nome: STRING
    tipo: STRING
    preco: DECIMAL
)

INSUMO (
    id_produto: INT [FK][PK]
    classe_agronomica: STRING
    principio_ativo: STRING
    periodo_carencia_dias: INT
    registro_mapa: STRING
)

GRAO (
    id_produto: INT [FK][PK]
    umidade_maxima: DECIMAL
    impureza_maxima: DECIMAL
    classificacao_tipo: STRING
)

COTACAO_GRAO (
    id_cotacao: INT [PK]
    id_produto: INT [FK]
    data_cotacao: DATE
    preco: DECIMAL
)

PRODUTO_COMERCIAL (
    id_produto: INT [FK][PK]
    codigo_comercial: STRING
    marca: STRING
    descricao_comercial: STRING
)

CERTIFICACAO (
    id_certificacao: INT [PK]
    nome: STRING
    orgao_emissor: STRING
    tipo: STRING
)

CERTIFICACAO_FAZENDA (
    id_cert_fazenda: INT [PK]
    id_certificacao: INT [FK]
    id_fazenda: INT [FK]
    dt_emissao: DATE
    dt_validade: DATE
    numero_certificado: STRING [UNIQUE]
    status: status_certificacao_enum
)

CERTIFICACAO_LOTE (
    id_cert_lote: INT [PK]
    id_certificacao: INT [FK]
    id_lote: INT [FK]
    dt_emissao: DATE
    dt_validade: DATE
    numero_certificado: STRING [UNIQUE]
    status: status_certificacao_enum
)

PLANTIO (
    id_plantio: INT [PK]
    id_ordem: INT [FK]
    id_talhao: INT [FK]
    id_produto: INT [FK]
    id_cultura: INT [FK]
    id_planejamento: INT [FK]
    dt_plantio: DATE
    status: status_plantio_enum
)

OPERACAO_AGRICOLA (
    id_operacao: INT [PK]
    id_plantio: INT [FK]
    id_funcionario: INT [FK]
    tipo_operacao: STRING
    descricao: STRING
    dt_inicio: DATETIME
    dt_fim: DATETIME
    status: status_operacao_agricola_enum
)

ATIVIDADE_AGRICOLA (
    id_atividade: INT [PK]
    id_operacao: INT [FK]
    descricao: STRING
    dt_inicio: DATETIME
    dt_fim: DATETIME
    status: status_atividade_agricola_enum
)

FUNCIONARIO_ATIVIDADE (
    id_funcionario: INT [FK]
    id_atividade: INT [FK]
    PK(id_funcionario, id_atividade)
)

PULVERIZACAO (
    id_atividade: INT [FK][PK]
    id_insumo: INT [FK]
    volume_calda: DECIMAL
    vazao: DECIMAL
    condicao_climatica: STRING
)

ADUBACAO (
    id_atividade: INT [FK][PK]
    id_insumo: INT [FK]
    tipo_adubacao: STRING
    dose_hectare: DECIMAL
    metodo_aplicacao: STRING
)

IRRIGACAO (
    id_atividade: INT [FK][PK]
    lamina_agua: DECIMAL
    metodo_irrigacao: STRING
    duracao_horas: DECIMAL
)

AGENTE_NOCIVO (
    id_agente: INT [PK]
    nome_comum: STRING
    nome_cientifico: STRING
)

PRAGA (
    id_agente: INT [FK][PK]
    tipo_praga: STRING
    habito_alimentar: STRING
)

DOENCA (
    id_agente: INT [FK][PK]
    agente_causador: STRING
    sintomas: STRING
    condicao_favoravel: STRING
)

CONTROLE_FITOSSANITARIO (
    id_controle: INT [PK]
    id_plantio: INT [FK]
    id_funcionario: INT [FK]
    dt_identificacao: DATE
    nivel_severidade: STRING
    area_afetada_hectares: DECIMAL
    recomendacao: STRING
)

OCORRENCIA_AGENTE (
    id_ocorrencia: INT [PK]
    id_controle: INT [FK]
    id_agente: INT [FK]
    nivel_infestacao: STRING
    metodo_controle: STRING
)

APLICACAO_DEFENSIVO (
    id_aplicacao: INT [PK]
    id_controle: INT [FK]
    id_insumo: INT [FK]
    dose_hectare: DECIMAL
    volume_aplicado: DECIMAL
    dt_aplicacao: DATE
    dt_carencia: DATE
)

MONITORAMENTO_SAFRA (
    id_monitoramento: INT [PK]
    id_safra: INT [FK]
    id_talhao: INT [FK]
    id_funcionario: INT [FK]
    dt_monitoramento: DATETIME
    estagio_fenologico: STRING
    observacao: STRING
)

PARAMETRO_MONITORAMENTO (
    id_parametro: INT [PK]
    id_monitoramento: INT [FK]
    nome_parametro: STRING
    valor: DECIMAL
    unidade: STRING
)

CONSUMO_INSUMO (
    id_atividade: INT [FK]
    id_insumo: INT [FK]
    id_lote: INT [FK]
    quantidade: DECIMAL
    PK(id_atividade, id_insumo, id_lote)
)

COLHEITA (
    id_colheita: INT [PK]
    id_plantio: INT [FK]
    quantidade_colhida: DECIMAL
    dt_inicio: DATE
    dt_fim: DATE
    status: status_colheita_enum
)

LOTE (
    id_lote: INT [PK]
    id_colheita: INT [FK]
    id_produto: INT [FK]
    codigo_lote: STRING [UNIQUE]
    validade: DATE
    qualidade: STRING
)

LOCAL_ARMAZENAMENTO (
    id_local: INT [PK]
    descricao: STRING
    capacidade: DECIMAL
)

ESTOQUE (
    id_estoque: INT [PK]
    id_local: INT [FK]
)

SALDO_ESTOQUE (
    id_saldo: INT [PK]
    id_estoque: INT [FK]
    id_produto: INT [FK]
    quantidade_atual: DECIMAL
    UNIQUE(id_estoque, id_produto)
)

MOVIMENTACAO_ESTOQUE (
    id_movimentacao: INT [PK]
    id_estoque: INT [FK]
    id_produto: INT [FK]
    id_lote: INT [FK]
    tipo_movimentacao: STRING
    quantidade: DECIMAL
    data_movimentacao: DATETIME
)

ENTRADA_ESTOQUE (
    id_entrada: INT [PK]
    id_compra: INT [FK]
    id_movimentacao: INT [FK]
)

SAIDA_ESTOQUE (
    id_saida: INT [PK]
    id_movimentacao: INT [FK]
    id_atividade: INT [FK]
)

PEDIDO_COMPRA (
    id_pedido: INT [PK]
    id_fornecedor: INT [FK]
    data_pedido: DATE
    status: status_pedido_compra_enum
)

ITEM_PEDIDO_COMPRA (
    id_item: INT [PK]
    id_pedido: INT [FK]
    id_produto: INT [FK]
    quantidade: DECIMAL
    valor_unitario: DECIMAL
)

FORNECEDOR_PRODUTO (
    id_fornecedor: INT [FK]
    id_produto: INT [FK]
    preco_referencia: DECIMAL
    prazo_entrega_dias: INT
    PK(id_fornecedor, id_produto)
)

COMPRA (
    id_compra: INT [PK]
    id_pedido: INT [FK]
    id_centro_custo: INT [FK]
    valor_total: DECIMAL
    data_compra: DATE
)

TIPO_MAQUINA (
    id_tipo_maquina: INT [PK]
    descricao: STRING
)

PRESTADOR_SERVICO (
    id_prestador: INT [PK]
    nome: STRING
    cnpj: STRING [UNIQUE]
    especialidade: STRING
    telefone: STRING
)

MAQUINA (
    id_maquina: INT [PK]
    id_tipo_maquina: INT [FK]
    id_fazenda: INT [FK]
    nome: STRING
    status: status_maquina_enum
)

USO_MAQUINA (
    id_uso: INT [PK]
    id_maquina: INT [FK]
    id_atividade: INT [FK]
    id_operacao: INT [FK]
    dt_inicio: DATETIME
    dt_fim: DATETIME
    horas_trabalhadas: DECIMAL
)

ABASTECIMENTO (
    id_abastecimento: INT [PK]
    id_maquina: INT [FK]
    combustivel: STRING
    litros: DECIMAL
    valor: DECIMAL
    horimetro: DECIMAL
    dt_abastecimento: DATETIME
)

MANUTENCAO (
    id_manutencao: INT [PK]
    id_maquina: INT [FK]
    id_funcionario: INT [FK]
    id_prestador: INT [FK]
    tipo: STRING
    custo: DECIMAL
    status: status_manutencao_enum
    dt_inicio: DATE
    dt_fim: DATE
)

MANUTENCAO_PREVENTIVA (
    id_manutencao: INT [FK][PK]
    id_plano: INT [FK]
    hodometro_execucao: DECIMAL
    proxima_hodometro: DECIMAL
)

MANUTENCAO_CORRETIVA (
    id_manutencao: INT [FK][PK]
    defeito_relatado: STRING
    causa_raiz: STRING
    solucao_aplicada: STRING
)

ORDEM_SERVICO (
    id_ordem_servico: INT [PK]
    id_manutencao: INT [FK]
    descricao: STRING
    status: status_ordem_servico_enum
)

PLANO_MANUTENCAO (
    id_plano: INT [PK]
    id_maquina: INT [FK]
    periodicidade: STRING
    proxima_execucao: DATE
)

TIPO_VEICULO (
    id_tipo_veiculo: INT [PK]
    nome: STRING
)

VEICULO (
    id_veiculo: INT [PK]
    id_tipo_veiculo: INT [FK]
    placa: STRING [UNIQUE]
    capacidade: DECIMAL
)

ROTA (
    id_rota: INT [PK]
    origem: STRING
    destino: STRING
)

VENDA (
    id_venda: INT [PK]
    id_cliente: INT [FK]
    id_centro_custo: INT [FK]
    valor_total: DECIMAL
    data_venda: DATE
)

OPERACAO_LOGISTICA (
    id_operacao: INT [PK]
    id_veiculo: INT [FK]
    id_rota: INT [FK]
    id_venda: INT [FK]
    data_inicio: DATETIME
    data_fim: DATETIME
    status: status_operacao_logistica_enum
)

CARGA (
    id_carga: INT [PK]
    id_operacao: INT [FK]
    id_lote: INT [FK]
    quantidade: DECIMAL
    peso_previsto: DECIMAL
)

PESAGEM (
    id_pesagem: INT [PK]
    id_carga: INT [FK]
    peso_registrado: DECIMAL
    data_pesagem: DATETIME
)

EXPEDICAO (
    id_expedicao: INT [PK]
    id_carga: INT [FK]
    data_saida: DATETIME
    status: status_expedicao_enum
)

ITEM_VENDA (
    id_item_venda: INT [PK]
    id_venda: INT [FK]
    id_produto: INT [FK]
    id_lote: INT [FK]
    quantidade: DECIMAL
    valor_unitario: DECIMAL
)

CONTA_PAGAR (
    id_conta_pagar: INT [PK]
    id_compra: INT [FK]
    valor: DECIMAL
    vencimento: DATE
    status: status_conta_pagar_enum
)

PAGAMENTO (
    id_pagamento: INT [PK]
    id_conta_pagar: INT [FK]
    valor_pago: DECIMAL
    data_pagamento: DATE
    forma_pagamento: STRING
)

CONTA_RECEBER (
    id_conta_receber: INT [PK]
    id_venda: INT [FK]
    valor: DECIMAL
    vencimento: DATE
    status: status_conta_receber_enum
)

RECEBIMENTO (
    id_recebimento: INT [PK]
    id_conta_receber: INT [FK]
    valor_recebido: DECIMAL
    data_recebimento: DATE
    forma_pagamento: STRING
)

FLUXO_CAIXA (
    id_fluxo: INT [PK]
    id_conta_pagar: INT [FK]
    id_conta_receber: INT [FK]
    valor: DECIMAL
    tipo: STRING
    data_movimento: DATE
)

INDICADOR (
    id_indicador: INT [PK]
    nome: STRING
    unidade: STRING
)

MEDICAO_INDICADOR (
    id_medicao: INT [PK]
    id_indicador: INT [FK]
    id_safra: INT [FK]
    valor: DECIMAL
    data_referencia: DATE
)

RELACIONAMENTOS

PESSOA (1) —— (N) EMAIL
PESSOA (1) —— (N) TELEFONE
PESSOA (1) —— (0..1) USUARIO
PESSOA (1) —— (0..1) CLIENTE
PESSOA (1) —— (0..1) FORNECEDOR
PESSOA (1) —— (0..1) FUNCIONARIO

USUARIO (N) —— (N) PERFIL_ACESSO
PERFIL_ACESSO (N) —— (N) PERMISSAO
USUARIO (1) —— (N) USUARIO_PERFIL
PERFIL_ACESSO (1) —— (N) USUARIO_PERFIL
PERFIL_ACESSO (1) —— (N) PERFIL_PERMISSAO
PERMISSAO (1) —— (N) PERFIL_PERMISSAO

USUARIO (1) —— (N) AUDITORIA_LOG
USUARIO (1) —— (N) NOTIFICACAO

FAZENDA (1) —— (N) TALHAO
FAZENDA (1) —— (N) MAQUINA
FAZENDA (1) —— (N) CERTIFICACAO_FAZENDA

SAFRA (1) —— (N) TALHAO
SAFRA (1) —— (N) ORDEM_PRODUCAO
SAFRA (1) —— (N) MEDICAO_INDICADOR
SAFRA (1) —— (N) PLANEJAMENTO_SAFRA
SAFRA (1) —— (N) MONITORAMENTO_SAFRA
SAFRA (1) —— (N) ANALISE_SOLO

CULTURA (1) —— (N) PLANEJAMENTO_SAFRA
CULTURA (1) —— (N) PLANTIO

TALHAO (1) —— (N) PLANEJAMENTO_SAFRA
TALHAO (1) —— (N) MONITORAMENTO_SAFRA
TALHAO (1) —— (1) SOLO
TALHAO (1) —— (N) CONDICAO_CLIMATICA

SOLO (1) —— (N) ANALISE_SOLO

MONITORAMENTO_SAFRA (1) —— (N) PARAMETRO_MONITORAMENTO

PLANEJAMENTO_SAFRA (1) —— (N) PLANTIO

CERTIFICACAO (1) —— (N) CERTIFICACAO_FAZENDA
CERTIFICACAO (1) —— (N) CERTIFICACAO_LOTE

LOTE (1) —— (N) CERTIFICACAO_LOTE
LOTE (1) —— (N) MOVIMENTACAO_ESTOQUE
LOTE (1) —— (N) ITEM_VENDA
LOTE (1) —— (N) CARGA

GRAO (1) —— (N) COTACAO_GRAO

CATEGORIA_PRODUTO (1) —— (N) PRODUTO
UNIDADE_MEDIDA (1) —— (N) PRODUTO

PRODUTO (1) —— (N) ITEM_PEDIDO_COMPRA
PRODUTO (1) —— (N) ITEM_VENDA
PRODUTO (1) —— (N) SALDO_ESTOQUE
PRODUTO (1) —— (N) MOVIMENTACAO_ESTOQUE
PRODUTO (1) —— (N) LOTE

ORDEM_PRODUCAO (1) —— (N) PLANTIO

PLANTIO (1) —— (N) OPERACAO_AGRICOLA

OPERACAO_AGRICOLA (1) —— (N) ATIVIDADE_AGRICOLA
OPERACAO_AGRICOLA (1) —— (N) USO_MAQUINA

PLANTIO (1) —— (N) CONTROLE_FITOSSANITARIO

CONTROLE_FITOSSANITARIO (1) —— (N) OCORRENCIA_AGENTE
CONTROLE_FITOSSANITARIO (1) —— (N) APLICACAO_DEFENSIVO

AGENTE_NOCIVO (1) —— (N) OCORRENCIA_AGENTE

INSUMO (1) —— (N) APLICACAO_DEFENSIVO
INSUMO (1) —— (N) PULVERIZACAO
INSUMO (1) —— (N) ADUBACAO
INSUMO (1) —— (N) CONSUMO_INSUMO

FUNCIONARIO (1) —— (N) MONITORAMENTO_SAFRA
FUNCIONARIO (1) —— (N) CONTROLE_FITOSSANITARIO
FUNCIONARIO (1) —— (N) ANALISE_SOLO

ATIVIDADE_AGRICOLA (N) —— (N) PRODUTO
ATIVIDADE_AGRICOLA (1) —— (N) CONSUMO_INSUMO
ATIVIDADE_AGRICOLA (1) —— (N) FUNCIONARIO_ATIVIDADE
FUNCIONARIO (1) —— (N) FUNCIONARIO_ATIVIDADE

LOTE (1) —— (N) CONSUMO_INSUMO

PLANTIO (1) —— (N) COLHEITA
COLHEITA (1) —— (N) LOTE

LOCAL_ARMAZENAMENTO (1) —— (N) ESTOQUE

ESTOQUE (1) —— (N) SALDO_ESTOQUE
ESTOQUE (1) —— (N) MOVIMENTACAO_ESTOQUE

COMPRA (1) —— (N) ENTRADA_ESTOQUE

ATIVIDADE_AGRICOLA (1) —— (N) SAIDA_ESTOQUE

FORNECEDOR (1) —— (N) PEDIDO_COMPRA
FORNECEDOR (1) —— (N) FORNECEDOR_PRODUTO
PRODUTO (1) —— (N) FORNECEDOR_PRODUTO

PEDIDO_COMPRA (1) —— (0..1) COMPRA

CENTRO_CUSTO (1) —— (N) COMPRA
CENTRO_CUSTO (1) —— (N) VENDA

TIPO_MAQUINA (1) —— (N) MAQUINA

MAQUINA (1) —— (N) USO_MAQUINA
MAQUINA (1) —— (N) MANUTENCAO
MAQUINA (1) —— (N) PLANO_MANUTENCAO
MAQUINA (1) —— (N) ABASTECIMENTO

PLANO_MANUTENCAO (1) —— (N) MANUTENCAO_PREVENTIVA

MANUTENCAO (1) —— (N) ORDEM_SERVICO
PRESTADOR_SERVICO (1) —— (N) MANUTENCAO

TIPO_VEICULO (1) —— (N) VEICULO

VEICULO (1) —— (N) OPERACAO_LOGISTICA

ROTA (1) —— (N) OPERACAO_LOGISTICA

VENDA (1) —— (N) OPERACAO_LOGISTICA

OPERACAO_LOGISTICA (1) —— (N) CARGA

CARGA (1) —— (N) PESAGEM
CARGA (1) —— (1) EXPEDICAO

CLIENTE (1) —— (N) VENDA

VENDA (1) —— (N) ITEM_VENDA

COMPRA (1) —— (N) CONTA_PAGAR

VENDA (1) —— (N) CONTA_RECEBER

CONTA_PAGAR (1) —— (N) PAGAMENTO
CONTA_PAGAR (1) —— (N) FLUXO_CAIXA

CONTA_RECEBER (1) —— (N) RECEBIMENTO
CONTA_RECEBER (1) —— (N) FLUXO_CAIXA

INDICADOR (1) —— (N) MEDICAO_INDICADOR

EER

PESSOA
    △ PARCIAL + SOBREPOSTA
    ├── USUARIO
    ├── FUNCIONARIO
    ├── CLIENTE
    └── FORNECEDOR

PRODUTO
    △ PARCIAL + DISJUNTA
    ├── INSUMO
    ├── GRAO
    └── PRODUTO_COMERCIAL

ATIVIDADE_AGRICOLA
    △ PARCIAL + DISJUNTA
    ├── PULVERIZACAO
    ├── ADUBACAO
    └── IRRIGACAO

MANUTENCAO
    △ TOTAL + DISJUNTA
    ├── MANUTENCAO_PREVENTIVA
    └── MANUTENCAO_CORRETIVA

AGENTE_NOCIVO
    △ TOTAL + DISJUNTA
    ├── PRAGA
    └── DOENCA

AGREGACAO — CONTROLE_FITOSSANITARIO
    └── agrega o relacionamento entre PLANTIO e OCORRENCIA_AGENTE
    └── sobre essa agregação incide APLICACAO_DEFENSIVO

AGREGACAO — OPERACAO_AGRICOLA
    └── agrega o relacionamento entre PLANTIO e ATIVIDADE_AGRICOLA
    └── sobre essa agregação incide USO_MAQUINA

