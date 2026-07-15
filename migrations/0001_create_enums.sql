BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_cliente_enum') THEN
        CREATE TYPE status_cliente_enum AS ENUM ('ATIVO', 'INATIVO', 'BLOQUEADO');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_safra_enum') THEN
        CREATE TYPE status_safra_enum AS ENUM ('PLANEJADA', 'EM_ANDAMENTO', 'FINALIZADA', 'CANCELADA');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_planejamento_safra_enum') THEN
        CREATE TYPE status_planejamento_safra_enum AS ENUM ('RASCUNHO', 'APROVADO', 'EM_EXECUCAO', 'CONCLUIDO', 'CANCELADO');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_ordem_producao_enum') THEN
        CREATE TYPE status_ordem_producao_enum AS ENUM ('ABERTA', 'EM_EXECUCAO', 'CONCLUIDA', 'CANCELADA');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_certificacao_enum') THEN
        CREATE TYPE status_certificacao_enum AS ENUM ('VIGENTE', 'VENCIDA', 'SUSPENSA', 'CANCELADA');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_plantio_enum') THEN
        CREATE TYPE status_plantio_enum AS ENUM ('PLANEJADO', 'EM_ANDAMENTO', 'CONCLUIDO', 'CANCELADO');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_operacao_agricola_enum') THEN
        CREATE TYPE status_operacao_agricola_enum AS ENUM ('ABERTA', 'EM_ANDAMENTO', 'CONCLUIDA', 'CANCELADA');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_atividade_agricola_enum') THEN
        CREATE TYPE status_atividade_agricola_enum AS ENUM ('PENDENTE', 'EM_ANDAMENTO', 'CONCLUIDA', 'CANCELADA');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_colheita_enum') THEN
        CREATE TYPE status_colheita_enum AS ENUM ('ABERTA', 'EM_ANDAMENTO', 'CONCLUIDA', 'CANCELADA');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_pedido_compra_enum') THEN
        CREATE TYPE status_pedido_compra_enum AS ENUM ('ABERTO', 'APROVADO', 'PARCIALMENTE_ATENDIDO', 'ATENDIDO', 'CANCELADO');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_maquina_enum') THEN
        CREATE TYPE status_maquina_enum AS ENUM ('DISPONIVEL', 'EM_USO', 'EM_MANUTENCAO', 'INATIVA');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_manutencao_enum') THEN
        CREATE TYPE status_manutencao_enum AS ENUM ('ABERTA', 'EM_EXECUCAO', 'CONCLUIDA', 'CANCELADA');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_ordem_servico_enum') THEN
        CREATE TYPE status_ordem_servico_enum AS ENUM ('ABERTA', 'EM_EXECUCAO', 'CONCLUIDA', 'CANCELADA');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_operacao_logistica_enum') THEN
        CREATE TYPE status_operacao_logistica_enum AS ENUM ('PLANEJADA', 'EM_TRANSITO', 'FINALIZADA', 'CANCELADA');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_expedicao_enum') THEN
        CREATE TYPE status_expedicao_enum AS ENUM ('PENDENTE', 'EM_PREPARACAO', 'EXPEDIDA', 'ENTREGUE', 'CANCELADA');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_conta_pagar_enum') THEN
        CREATE TYPE status_conta_pagar_enum AS ENUM ('ABERTA', 'PARCIALMENTE_PAGA', 'PAGA', 'VENCIDA', 'CANCELADA');
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_conta_receber_enum') THEN
        CREATE TYPE status_conta_receber_enum AS ENUM ('ABERTA', 'PARCIALMENTE_RECEBIDA', 'RECEBIDA', 'VENCIDA', 'CANCELADA');
    END IF;
END $$;

COMMIT;
