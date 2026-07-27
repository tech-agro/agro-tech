from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.producao.enum import (
    StatusAtividadeAgricola,
    StatusColheita,
    StatusOperacaoAgricola,
    StatusOrdemProducao,
    StatusPlanejamentoSafra,
    StatusPlantio,
    StatusSafra,
)


# Propriedade rural onde a producao acontece
class FazendaModel(BaseModel):
    id_fazenda: int
    nome: str
    localizacao: str | None = None


# Campo de plantio dentro de uma fazenda, com area delimitada e caracteristicas do solo
# Está associado a uma safra e a uma cultura
class TalhaoModel(BaseModel):
    id_talhao: int
    id_fazenda: int
    id_safra: int
    nome: str
    area_hectares: Decimal


# Caracteristicas fisicas do solo de um talhao (tipo, textura, profundidade)
class SoloModel(BaseModel):
    id_solo: int
    id_talhao: int
    tipo_solo: str | None = None
    textura: str | None = None
    profundidade_cm: Decimal | None = None


# Registro de condicoes climaticas observadas em um talhao (temperatura, umidade, precipitacao, vento, radiacao)
class CondicaoClimaticaModel(BaseModel):
    id_condicao: int
    id_talhao: int
    dt_registro: datetime
    temperatura_min: Decimal | None = None
    temperatura_max: Decimal | None = None
    umidade_relativa: Decimal | None = None
    precipitacao_mm: Decimal | None = None
    velocidade_vento: Decimal | None = None
    direcao_vento: str | None = None
    radiacao_solar: Decimal | None = None


# Tipo de cultura agricola que pode ser plantada
class CulturaModel(BaseModel):
    id_cultura: int
    nome: str
    nome_cientifico: str | None = None
    variedade: str | None = None
    ciclo_dias: int | None = None
    tipo_cultura: str | None = None


# Ciclo de producao agricola de um ano/periodo (planejada, em andamento, finalizada, cancelada).
class SafraModel(BaseModel):
    id_safra: int
    nome: str
    ano: int
    dt_inicio: date | None = None
    dt_fim: date | None = None
    status: StatusSafra


# Plano de metas para uma safra em um talhao
class PlanejamentoSafraModel(BaseModel):
    id_planejamento: int
    id_safra: int
    id_talhao: int
    id_cultura: int
    meta_produtividade: Decimal | None = None
    area_planejada: Decimal | None = None
    dt_plantio_previsto: date | None = None
    dt_colheita_previsto: date | None = None
    status: StatusPlanejamentoSafra


# Resultado de analise laboratorial do solo (ph, nutrientes, materia organica) coletada em uma safra
class AnaliseSoloModel(BaseModel):
    id_analise: int
    id_solo: int
    id_safra: int
    id_funcionario: int
    dt_coleta: date | None = None
    dt_resultado: date | None = None
    ph: Decimal | None = None
    materia_organica: Decimal | None = None
    fosforo: Decimal | None = None
    potassio: Decimal | None = None
    calcio: Decimal | None = None
    magnesio: Decimal | None = None
    saturacao_bases: Decimal | None = None
    observacao: str | None = None


# Acompanhamento periodico de uma safra em um talhao (estagio fenologico, observacoes)
class MonitoramentoSafraModel(BaseModel):
    id_monitoramento: int
    id_safra: int
    id_talhao: int
    id_funcionario: int
    dt_monitoramento: datetime
    estagio_fenologico: str | None = None
    observacao: str | None = None


# Parametro especifico coletado em um monitoramento de safra (nome, valor, unidade)
class ParametroMonitoramentoModel(BaseModel):
    id_parametro: int
    id_monitoramento: int
    nome_parametro: str
    valor: Decimal | None = None
    unidade: str | None = None


# Ordem formal que abre a execucao da producao de uma safra
class OrdemProducaoModel(BaseModel):
    id_ordem: int
    id_safra: int
    data_abertura: date | None = None
    status: StatusOrdemProducao


# Registro do plantio efetivo, ligando ordem de producao, talhao, cultura e produto usado
class PlantioModel(BaseModel):
    id_plantio: int
    id_ordem: int
    id_talhao: int
    id_produto: int
    id_cultura: int
    id_planejamento: int
    dt_plantio: date | None = None
    status: StatusPlantio


# Operacao de campo realizada durante um plantio (responsavel, periodo, status)
class OperacaoAgricolaModel(BaseModel):
    id_operacao: int
    id_plantio: int
    id_funcionario: int
    tipo_operacao: str | None = None
    descricao: str | None = None
    dt_inicio: datetime | None = None
    dt_fim: datetime | None = None
    status: StatusOperacaoAgricola


# Atividade especifica executada dentro de uma operacao agricola (descricao, periodo, status)
class AtividadeAgricolaModel(BaseModel):
    id_atividade: int
    id_operacao: int
    descricao: str | None = None
    dt_inicio: datetime | None = None
    dt_fim: datetime | None = None
    status: StatusAtividadeAgricola


# Associacao entre um funcionario e uma atividade agricola que ele executou
class FuncionarioAtividadeModel(BaseModel):
    id_funcionario: int
    id_atividade: int


# Insumo/nutriente aplicado em uma atividade agricola
class AdubacaoModel(BaseModel):
    id_atividade: int
    id_insumo: int
    tipo_adubacao: str | None = None
    dose_hectare: Decimal | None = None
    metodo_aplicacao: str | None = None


# Detalhe de irrigacao aplicada em uma atividade
class IrrigacaoModel(BaseModel):
    id_atividade: int
    lamina_agua: Decimal | None = None
    metodo_irrigacao: str | None = None
    duracao_horas: Decimal | None = None


# Detalhe de pulverizacao de insumo em uma atividade (volume de calda, vazao)
class PulverizacaoModel(BaseModel):
    id_atividade: int
    id_insumo: int
    volume_calda: Decimal | None = None
    vazao: Decimal | None = None


# Registro da colheita de um plantio
class ColheitaModel(BaseModel):
    id_colheita: int
    id_plantio: int
    quantidade_colhida: Decimal | None = None
    dt_inicio: date | None = None
    dt_fim: date | None = None
    status: StatusColheita


# ----------------------------------------------------------------------
# Contratos de entrada da API (sem id, preenchido pelo banco na criacao)
# ----------------------------------------------------------------------
class NovaFazenda(BaseModel):
    nome: str
    localizacao: str | None = None


class NovoTalhao(BaseModel):
    id_fazenda: int
    id_safra: int
    nome: str
    area_hectares: Decimal


class NovoSolo(BaseModel):
    id_talhao: int
    tipo_solo: str | None = None
    textura: str | None = None
    profundidade_cm: Decimal | None = None


class NovaCondicaoClimatica(BaseModel):
    id_talhao: int
    dt_registro: datetime
    temperatura_min: Decimal | None = None
    temperatura_max: Decimal | None = None
    umidade_relativa: Decimal | None = None
    precipitacao_mm: Decimal | None = None
    velocidade_vento: Decimal | None = None
    direcao_vento: str | None = None
    radiacao_solar: Decimal | None = None


class NovaCultura(BaseModel):
    nome: str
    nome_cientifico: str | None = None
    variedade: str | None = None
    ciclo_dias: int | None = None
    tipo_cultura: str | None = None


class NovaSafra(BaseModel):
    nome: str
    ano: int
    status: StatusSafra
    dt_inicio: date | None = None
    dt_fim: date | None = None


class NovoPlanejamentoSafra(BaseModel):
    id_safra: int
    id_talhao: int
    id_cultura: int
    status: StatusPlanejamentoSafra
    meta_produtividade: Decimal | None = None
    area_planejada: Decimal | None = None
    dt_plantio_previsto: date | None = None
    dt_colheita_previsto: date | None = None


class NovaAnaliseSolo(BaseModel):
    id_solo: int
    id_safra: int
    id_funcionario: int
    dt_coleta: date | None = None
    dt_resultado: date | None = None
    ph: Decimal | None = None
    materia_organica: Decimal | None = None
    fosforo: Decimal | None = None
    potassio: Decimal | None = None
    calcio: Decimal | None = None
    magnesio: Decimal | None = None
    saturacao_bases: Decimal | None = None
    observacao: str | None = None


class NovoMonitoramentoSafra(BaseModel):
    id_safra: int
    id_talhao: int
    id_funcionario: int
    dt_monitoramento: datetime
    estagio_fenologico: str | None = None
    observacao: str | None = None


class NovoParametroMonitoramento(BaseModel):
    nome_parametro: str
    valor: Decimal | None = None
    unidade: str | None = None


class NovaOrdemProducao(BaseModel):
    id_safra: int
    status: StatusOrdemProducao
    data_abertura: date | None = None


class NovoPlantio(BaseModel):
    id_ordem: int
    id_talhao: int
    id_produto: int
    id_cultura: int
    id_planejamento: int
    status: StatusPlantio
    dt_plantio: date | None = None


class NovaOperacaoAgricola(BaseModel):
    id_plantio: int
    id_funcionario: int
    status: StatusOperacaoAgricola
    tipo_operacao: str | None = None
    descricao: str | None = None
    dt_inicio: datetime | None = None
    dt_fim: datetime | None = None


class NovaAtividadeAgricola(BaseModel):
    id_operacao: int
    status: StatusAtividadeAgricola
    descricao: str | None = None
    dt_inicio: datetime | None = None
    dt_fim: datetime | None = None


class NovaAdubacao(BaseModel):
    id_insumo: int
    tipo_adubacao: str | None = None
    dose_hectare: Decimal | None = None
    metodo_aplicacao: str | None = None


class NovaIrrigacao(BaseModel):
    lamina_agua: Decimal | None = None
    metodo_irrigacao: str | None = None
    duracao_horas: Decimal | None = None


class NovaPulverizacao(BaseModel):
    id_insumo: int
    volume_calda: Decimal | None = None
    vazao: Decimal | None = None


# Corpo da operacao "colher plantio": id_plantio e status vem da URL/da propria
# operacao (abre a colheita como ABERTA e encerra o plantio automaticamente).
class RegistroColheitaPlantio(BaseModel):
    quantidade_colhida: Decimal | None = None
    dt_inicio: date | None = None
    dt_fim: date | None = None