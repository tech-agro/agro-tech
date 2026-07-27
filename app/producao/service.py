import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.core.database import pg_connector
from app.producao.enum import (
    StatusAtividadeAgricola,
    StatusColheita,
    StatusOperacaoAgricola,
    StatusOrdemProducao,
    StatusPlanejamentoSafra,
    StatusPlantio,
    StatusSafra,
)
from app.producao.models import (
    AdubacaoModel,
    AnaliseSoloModel,
    AtividadeAgricolaModel,
    ColheitaModel,
    CondicaoClimaticaModel,
    CulturaModel,
    FazendaModel,
    FuncionarioAtividadeModel,
    IrrigacaoModel,
    MonitoramentoSafraModel,
    OperacaoAgricolaModel,
    OrdemProducaoModel,
    ParametroMonitoramentoModel,
    PlanejamentoSafraModel,
    PlantioModel,
    PulverizacaoModel,
    SafraModel,
    SoloModel,
    TalhaoModel,
)
from app.producao.repository import ProducaoRepository

logger = logging.getLogger(__name__)

_TRANSICOES_SAFRA = {
    StatusSafra.PLANEJADA: {StatusSafra.EM_ANDAMENTO, StatusSafra.CANCELADA},
    StatusSafra.EM_ANDAMENTO: {StatusSafra.FINALIZADA, StatusSafra.CANCELADA},
    StatusSafra.FINALIZADA: set(),
    StatusSafra.CANCELADA: set(),
}

_TRANSICOES_PLANEJAMENTO_SAFRA = {
    StatusPlanejamentoSafra.RASCUNHO: {StatusPlanejamentoSafra.APROVADO, StatusPlanejamentoSafra.CANCELADO},
    StatusPlanejamentoSafra.APROVADO: {StatusPlanejamentoSafra.EM_EXECUCAO, StatusPlanejamentoSafra.CANCELADO},
    StatusPlanejamentoSafra.EM_EXECUCAO: {StatusPlanejamentoSafra.CONCLUIDO, StatusPlanejamentoSafra.CANCELADO},
    StatusPlanejamentoSafra.CONCLUIDO: set(),
    StatusPlanejamentoSafra.CANCELADO: set(),
}

_TRANSICOES_ORDEM_PRODUCAO = {
    StatusOrdemProducao.ABERTA: {StatusOrdemProducao.EM_EXECUCAO, StatusOrdemProducao.CANCELADA},
    StatusOrdemProducao.EM_EXECUCAO: {StatusOrdemProducao.CONCLUIDA, StatusOrdemProducao.CANCELADA},
    StatusOrdemProducao.CONCLUIDA: set(),
    StatusOrdemProducao.CANCELADA: set(),
}

_TRANSICOES_PLANTIO = {
    StatusPlantio.PLANEJADO: {StatusPlantio.EM_ANDAMENTO, StatusPlantio.CANCELADO},
    StatusPlantio.EM_ANDAMENTO: {StatusPlantio.CONCLUIDO, StatusPlantio.CANCELADO},
    StatusPlantio.CONCLUIDO: set(),
    StatusPlantio.CANCELADO: set(),
}

_TRANSICOES_OPERACAO_AGRICOLA = {
    StatusOperacaoAgricola.ABERTA: {StatusOperacaoAgricola.EM_ANDAMENTO, StatusOperacaoAgricola.CANCELADA},
    StatusOperacaoAgricola.EM_ANDAMENTO: {StatusOperacaoAgricola.CONCLUIDA, StatusOperacaoAgricola.CANCELADA},
    StatusOperacaoAgricola.CONCLUIDA: set(),
    StatusOperacaoAgricola.CANCELADA: set(),
}

_TRANSICOES_ATIVIDADE_AGRICOLA = {
    StatusAtividadeAgricola.PENDENTE: {StatusAtividadeAgricola.EM_ANDAMENTO, StatusAtividadeAgricola.CANCELADA},
    StatusAtividadeAgricola.EM_ANDAMENTO: {StatusAtividadeAgricola.CONCLUIDA, StatusAtividadeAgricola.CANCELADA},
    StatusAtividadeAgricola.CONCLUIDA: set(),
    StatusAtividadeAgricola.CANCELADA: set(),
}

_TRANSICOES_COLHEITA = {
    StatusColheita.ABERTA: {StatusColheita.EM_ANDAMENTO, StatusColheita.CANCELADA},
    StatusColheita.EM_ANDAMENTO: {StatusColheita.CONCLUIDA, StatusColheita.CANCELADA},
    StatusColheita.CONCLUIDA: set(),
    StatusColheita.CANCELADA: set(),
}


class ProducaoService:
    """Camada de orquestracao das regras de negocio."""

    def __init__(self, repository: ProducaoRepository | None = None) -> None:
        self.repository = repository or ProducaoRepository(pg_connector, logger)

    @staticmethod
    def _validar_transicao(transicoes: dict, atual, novo, nome_entidade: str) -> None:
        if novo not in transicoes.get(atual, set()):
            raise ValueError(f"Transicao de {atual.value} para {novo.value} nao e permitida para {nome_entidade}.")

    # CRUD de Fazenda
    def create_fazenda(self, nome: str, localizacao: str | None = None) -> FazendaModel | None:
        return self.repository.create_fazenda(nome, localizacao)

    def get_fazenda_by_id(self, id_fazenda: int) -> FazendaModel | None:
        return self.repository.get_fazenda_by_id(id_fazenda)

    def list_fazendas(self, filters: dict | None = None) -> list[FazendaModel]:
        return self.repository.list_fazendas(filters)

    def update_fazenda(self, id_fazenda: int, nome: str | None = None, localizacao: str | None = None) -> bool:
        return self.repository.update_fazenda(id_fazenda, nome, localizacao)

    def delete_fazenda(self, id_fazenda: int) -> bool:
        return self.repository.delete_fazenda(id_fazenda)

    # CRUD de Talhao
    def create_talhao(self, id_fazenda: int, id_safra: int, nome: str, area_hectares: Decimal) -> TalhaoModel | None:
        if self.repository.get_fazenda_by_id(id_fazenda) is None:
            raise ValueError("Fazenda nao encontrada.")
        if self.repository.get_safra_by_id(id_safra) is None:
            raise ValueError("Safra nao encontrada.")
        if area_hectares <= 0:
            raise ValueError("A area do talhao deve ser maior que zero.")
        return self.repository.create_talhao(id_fazenda, id_safra, nome, area_hectares)

    def get_talhao_by_id(self, id_talhao: int) -> TalhaoModel | None:
        return self.repository.get_talhao_by_id(id_talhao)

    def list_talhoes(self, filters: dict | None = None) -> list[TalhaoModel]:
        return self.repository.list_talhoes(filters)

    def update_talhao(self, id_talhao: int, nome: str | None = None, area_hectares: Decimal | None = None) -> bool:
        if self.repository.get_talhao_by_id(id_talhao) is None:
            return False
        if area_hectares is not None and area_hectares <= 0:
            raise ValueError("A area do talhao deve ser maior que zero.")
        return self.repository.update_talhao(id_talhao, nome, area_hectares)

    def delete_talhao(self, id_talhao: int) -> bool:
        return self.repository.delete_talhao(id_talhao)

    # CRUD de Solo (1:1 com Talhao)
    def create_solo(
        self,
        id_talhao: int,
        tipo_solo: str | None = None,
        textura: str | None = None,
        profundidade_cm: Decimal | None = None,
    ) -> SoloModel | None:
        if self.repository.get_talhao_by_id(id_talhao) is None:
            raise ValueError("Talhao nao encontrado.")
        return self.repository.create_solo(id_talhao, tipo_solo, textura, profundidade_cm)

    def get_solo_by_talhao(self, id_talhao: int) -> SoloModel | None:
        return self.repository.get_solo_by_talhao(id_talhao)

    def list_solos(self, filters: dict | None = None) -> list[SoloModel]:
        return self.repository.list_solos(filters)

    def update_solo(
        self,
        id_solo: int,
        tipo_solo: str | None = None,
        textura: str | None = None,
        profundidade_cm: Decimal | None = None,
    ) -> bool:
        return self.repository.update_solo(id_solo, tipo_solo, textura, profundidade_cm)

    def delete_solo(self, id_solo: int) -> bool:
        return self.repository.delete_solo(id_solo)

    # CRUD de CondicaoClimatica
    def create_condicao_climatica(
        self,
        id_talhao: int,
        dt_registro: datetime,
        temperatura_min: Decimal | None = None,
        temperatura_max: Decimal | None = None,
        umidade_relativa: Decimal | None = None,
        precipitacao_mm: Decimal | None = None,
        velocidade_vento: Decimal | None = None,
        direcao_vento: str | None = None,
        radiacao_solar: Decimal | None = None,
    ) -> CondicaoClimaticaModel | None:
        if self.repository.get_talhao_by_id(id_talhao) is None:
            raise ValueError("Talhao nao encontrado.")
        return self.repository.create_condicao_climatica(
            id_talhao,
            dt_registro,
            temperatura_min,
            temperatura_max,
            umidade_relativa,
            precipitacao_mm,
            velocidade_vento,
            direcao_vento,
            radiacao_solar,
        )

    def get_condicao_climatica_by_id(self, id_condicao: int) -> CondicaoClimaticaModel | None:
        return self.repository.get_condicao_climatica_by_id(id_condicao)

    def list_condicoes_climaticas(self, filters: dict | None = None) -> list[CondicaoClimaticaModel]:
        return self.repository.list_condicoes_climaticas(filters)

    def delete_condicao_climatica(self, id_condicao: int) -> bool:
        return self.repository.delete_condicao_climatica(id_condicao)

    # CRUD de Cultura
    def create_cultura(
        self,
        nome: str,
        nome_cientifico: str | None = None,
        variedade: str | None = None,
        ciclo_dias: int | None = None,
        tipo_cultura: str | None = None,
    ) -> CulturaModel | None:
        return self.repository.create_cultura(nome, nome_cientifico, variedade, ciclo_dias, tipo_cultura)

    def get_cultura_by_id(self, id_cultura: int) -> CulturaModel | None:
        return self.repository.get_cultura_by_id(id_cultura)

    def list_culturas(self, filters: dict | None = None) -> list[CulturaModel]:
        return self.repository.list_culturas(filters)

    def update_cultura(
        self,
        id_cultura: int,
        nome: str | None = None,
        nome_cientifico: str | None = None,
        variedade: str | None = None,
        ciclo_dias: int | None = None,
        tipo_cultura: str | None = None,
    ) -> bool:
        return self.repository.update_cultura(id_cultura, nome, nome_cientifico, variedade, ciclo_dias, tipo_cultura)

    def delete_cultura(self, id_cultura: int) -> bool:
        return self.repository.delete_cultura(id_cultura)

    # CRUD de Safra
    def create_safra(
        self,
        nome: str,
        ano: int,
        status: StatusSafra,
        dt_inicio: date | None = None,
        dt_fim: date | None = None,
    ) -> SafraModel | None:
        if dt_inicio is not None and dt_fim is not None and dt_fim < dt_inicio:
            raise ValueError("A data de fim da safra nao pode ser anterior a data de inicio.")
        return self.repository.create_safra(nome, ano, status, dt_inicio, dt_fim)

    def get_safra_by_id(self, id_safra: int) -> SafraModel | None:
        return self.repository.get_safra_by_id(id_safra)

    def list_safras(self, filters: dict | None = None) -> list[SafraModel]:
        return self.repository.list_safras(filters)

    def update_safra(
        self,
        id_safra: int,
        nome: str | None = None,
        ano: int | None = None,
        dt_inicio: date | None = None,
        dt_fim: date | None = None,
    ) -> bool:
        atual = self.repository.get_safra_by_id(id_safra)
        if atual is None:
            return False
        novo_inicio = dt_inicio if dt_inicio is not None else atual.dt_inicio
        novo_fim = dt_fim if dt_fim is not None else atual.dt_fim
        if novo_inicio is not None and novo_fim is not None and novo_fim < novo_inicio:
            raise ValueError("A data de fim da safra nao pode ser anterior a data de inicio.")
        return self.repository.update_safra(id_safra, nome, ano, dt_inicio, dt_fim)

    def update_status_safra(self, id_safra: int, status: StatusSafra) -> bool:
        atual = self.repository.get_safra_by_id(id_safra)
        if atual is None:
            return False
        self._validar_transicao(_TRANSICOES_SAFRA, atual.status, status, "safra")
        return self.repository.update_status_safra(id_safra, status)

    def iniciar_safra(self, id_safra: int) -> bool:
        return self.update_status_safra(id_safra, StatusSafra.EM_ANDAMENTO)

    def finalizar_safra(self, id_safra: int) -> bool:
        return self.update_status_safra(id_safra, StatusSafra.FINALIZADA)

    def cancelar_safra(self, id_safra: int) -> bool:
        return self.update_status_safra(id_safra, StatusSafra.CANCELADA)

    def delete_safra(self, id_safra: int) -> bool:
        return self.repository.delete_safra(id_safra)

    # CRUD de PlanejamentoSafra
    def create_planejamento_safra(
        self,
        id_safra: int,
        id_talhao: int,
        id_cultura: int,
        status: StatusPlanejamentoSafra,
        meta_produtividade: Decimal | None = None,
        area_planejada: Decimal | None = None,
        dt_plantio_previsto: date | None = None,
        dt_colheita_previsto: date | None = None,
    ) -> PlanejamentoSafraModel | None:
        safra = self.repository.get_safra_by_id(id_safra)
        if safra is None:
            raise ValueError("Safra nao encontrada.")
        if safra.status in (StatusSafra.FINALIZADA, StatusSafra.CANCELADA):
            raise ValueError("Nao e possivel planejar em uma safra finalizada ou cancelada.")
        if self.repository.get_talhao_by_id(id_talhao) is None:
            raise ValueError("Talhao nao encontrado.")
        cultura = self.repository.get_cultura_by_id(id_cultura)
        if cultura is None:
            raise ValueError("Cultura nao encontrada.")
        if area_planejada is not None and area_planejada <= 0:
            raise ValueError("A area planejada deve ser maior que zero.")
        self._validar_sazonalidade_planejamento(cultura, dt_plantio_previsto, dt_colheita_previsto)
        return self.repository.create_planejamento_safra(
            id_safra,
            id_talhao,
            id_cultura,
            status,
            meta_produtividade,
            area_planejada,
            dt_plantio_previsto,
            dt_colheita_previsto,
        )

    @staticmethod
    def _validar_sazonalidade_planejamento(
        cultura: CulturaModel, dt_plantio_previsto: date | None, dt_colheita_previsto: date | None
    ) -> None:
        if dt_plantio_previsto is None or dt_colheita_previsto is None:
            return
        if dt_colheita_previsto < dt_plantio_previsto:
            raise ValueError("A data de colheita prevista nao pode ser anterior a data de plantio prevista.")
        if cultura.ciclo_dias is not None and dt_colheita_previsto < dt_plantio_previsto + timedelta(
            days=cultura.ciclo_dias
        ):
            raise ValueError("A colheita prevista e anterior ao ciclo minimo da cultura, desrespeitando a sazonalidade.")

    def get_planejamento_safra_by_id(self, id_planejamento: int) -> PlanejamentoSafraModel | None:
        return self.repository.get_planejamento_safra_by_id(id_planejamento)

    def list_planejamentos_safra(self, filters: dict | None = None) -> list[PlanejamentoSafraModel]:
        return self.repository.list_planejamentos_safra(filters)

    def update_planejamento_safra(
        self,
        id_planejamento: int,
        meta_produtividade: Decimal | None = None,
        area_planejada: Decimal | None = None,
        dt_plantio_previsto: date | None = None,
        dt_colheita_previsto: date | None = None,
    ) -> bool:
        atual = self.repository.get_planejamento_safra_by_id(id_planejamento)
        if atual is None:
            return False
        novo_area = area_planejada if area_planejada is not None else atual.area_planejada
        novo_plantio = dt_plantio_previsto if dt_plantio_previsto is not None else atual.dt_plantio_previsto
        novo_colheita = dt_colheita_previsto if dt_colheita_previsto is not None else atual.dt_colheita_previsto
        if novo_area is not None and novo_area <= 0:
            raise ValueError("A area planejada deve ser maior que zero.")
        cultura = self.repository.get_cultura_by_id(atual.id_cultura)
        if cultura is not None:
            self._validar_sazonalidade_planejamento(cultura, novo_plantio, novo_colheita)
        return self.repository.update_planejamento_safra(
            id_planejamento, meta_produtividade, area_planejada, dt_plantio_previsto, dt_colheita_previsto
        )

    def update_status_planejamento_safra(self, id_planejamento: int, status: StatusPlanejamentoSafra) -> bool:
        atual = self.repository.get_planejamento_safra_by_id(id_planejamento)
        if atual is None:
            return False
        self._validar_transicao(_TRANSICOES_PLANEJAMENTO_SAFRA, atual.status, status, "planejamento de safra")
        return self.repository.update_status_planejamento_safra(id_planejamento, status)

    def aprovar_planejamento_safra(self, id_planejamento: int) -> bool:
        return self.update_status_planejamento_safra(id_planejamento, StatusPlanejamentoSafra.APROVADO)

    def iniciar_execucao_planejamento_safra(self, id_planejamento: int) -> bool:
        return self.update_status_planejamento_safra(id_planejamento, StatusPlanejamentoSafra.EM_EXECUCAO)

    def concluir_planejamento_safra(self, id_planejamento: int) -> bool:
        return self.update_status_planejamento_safra(id_planejamento, StatusPlanejamentoSafra.CONCLUIDO)

    def cancelar_planejamento_safra(self, id_planejamento: int) -> bool:
        return self.update_status_planejamento_safra(id_planejamento, StatusPlanejamentoSafra.CANCELADO)

    def delete_planejamento_safra(self, id_planejamento: int) -> bool:
        return self.repository.delete_planejamento_safra(id_planejamento)

    # CRUD de AnaliseSolo
    def create_analise_solo(
        self,
        id_solo: int,
        id_safra: int,
        id_funcionario: int,
        dt_coleta: date | None = None,
        dt_resultado: date | None = None,
        ph: Decimal | None = None,
        materia_organica: Decimal | None = None,
        fosforo: Decimal | None = None,
        potassio: Decimal | None = None,
        calcio: Decimal | None = None,
        magnesio: Decimal | None = None,
        saturacao_bases: Decimal | None = None,
        observacao: str | None = None,
    ) -> AnaliseSoloModel | None:
        if self.repository.get_safra_by_id(id_safra) is None:
            raise ValueError("Safra nao encontrada.")
        if dt_coleta is not None and dt_resultado is not None and dt_resultado < dt_coleta:
            raise ValueError("A data de resultado nao pode ser anterior a data de coleta.")
        return self.repository.create_analise_solo(
            id_solo,
            id_safra,
            id_funcionario,
            dt_coleta,
            dt_resultado,
            ph,
            materia_organica,
            fosforo,
            potassio,
            calcio,
            magnesio,
            saturacao_bases,
            observacao,
        )

    def get_analise_solo_by_id(self, id_analise: int) -> AnaliseSoloModel | None:
        return self.repository.get_analise_solo_by_id(id_analise)

    def list_analises_solo(self, filters: dict | None = None) -> list[AnaliseSoloModel]:
        return self.repository.list_analises_solo(filters)

    def delete_analise_solo(self, id_analise: int) -> bool:
        return self.repository.delete_analise_solo(id_analise)

    # CRUD de MonitoramentoSafra
    def create_monitoramento_safra(
        self,
        id_safra: int,
        id_talhao: int,
        id_funcionario: int,
        dt_monitoramento: datetime,
        estagio_fenologico: str | None = None,
        observacao: str | None = None,
    ) -> MonitoramentoSafraModel | None:
        if self.repository.get_safra_by_id(id_safra) is None:
            raise ValueError("Safra nao encontrada.")
        if self.repository.get_talhao_by_id(id_talhao) is None:
            raise ValueError("Talhao nao encontrado.")
        return self.repository.create_monitoramento_safra(
            id_safra, id_talhao, id_funcionario, dt_monitoramento, estagio_fenologico, observacao
        )

    def get_monitoramento_safra_by_id(self, id_monitoramento: int) -> MonitoramentoSafraModel | None:
        return self.repository.get_monitoramento_safra_by_id(id_monitoramento)

    def list_monitoramentos_safra(self, filters: dict | None = None) -> list[MonitoramentoSafraModel]:
        return self.repository.list_monitoramentos_safra(filters)

    def delete_monitoramento_safra(self, id_monitoramento: int) -> bool:
        return self.repository.delete_monitoramento_safra(id_monitoramento)

    # CRUD de ParametroMonitoramento
    def create_parametro_monitoramento(
        self, id_monitoramento: int, nome_parametro: str, valor: Decimal | None = None, unidade: str | None = None
    ) -> ParametroMonitoramentoModel | None:
        if self.repository.get_monitoramento_safra_by_id(id_monitoramento) is None:
            raise ValueError("Monitoramento de safra nao encontrado.")
        return self.repository.create_parametro_monitoramento(id_monitoramento, nome_parametro, valor, unidade)

    def list_parametros_por_monitoramento(self, id_monitoramento: int) -> list[ParametroMonitoramentoModel]:
        return self.repository.list_parametros_por_monitoramento(id_monitoramento)

    def delete_parametro_monitoramento(self, id_parametro: int) -> bool:
        return self.repository.delete_parametro_monitoramento(id_parametro)

    # CRUD de OrdemProducao
    def create_ordem_producao(
        self, id_safra: int, status: StatusOrdemProducao, data_abertura: date | None = None
    ) -> OrdemProducaoModel | None:
        safra = self.repository.get_safra_by_id(id_safra)
        if safra is None:
            raise ValueError("Safra nao encontrada.")
        if safra.status in (StatusSafra.FINALIZADA, StatusSafra.CANCELADA):
            raise ValueError("Nao e possivel abrir ordem de producao para uma safra finalizada ou cancelada.")
        return self.repository.create_ordem_producao(id_safra, status, data_abertura)

    def get_ordem_producao_by_id(self, id_ordem: int) -> OrdemProducaoModel | None:
        return self.repository.get_ordem_producao_by_id(id_ordem)

    def list_ordens_producao(self, filters: dict | None = None) -> list[OrdemProducaoModel]:
        return self.repository.list_ordens_producao(filters)

    def update_status_ordem_producao(self, id_ordem: int, status: StatusOrdemProducao) -> bool:
        atual = self.repository.get_ordem_producao_by_id(id_ordem)
        if atual is None:
            return False
        self._validar_transicao(_TRANSICOES_ORDEM_PRODUCAO, atual.status, status, "ordem de producao")
        return self.repository.update_status_ordem_producao(id_ordem, status)

    def iniciar_ordem_producao(self, id_ordem: int) -> bool:
        return self.update_status_ordem_producao(id_ordem, StatusOrdemProducao.EM_EXECUCAO)

    def concluir_ordem_producao(self, id_ordem: int) -> bool:
        return self.update_status_ordem_producao(id_ordem, StatusOrdemProducao.CONCLUIDA)

    def cancelar_ordem_producao(self, id_ordem: int) -> bool:
        return self.update_status_ordem_producao(id_ordem, StatusOrdemProducao.CANCELADA)

    def delete_ordem_producao(self, id_ordem: int) -> bool:
        return self.repository.delete_ordem_producao(id_ordem)

    # CRUD de Plantio
    def create_plantio(
        self,
        id_ordem: int,
        id_talhao: int,
        id_produto: int,
        id_cultura: int,
        id_planejamento: int,
        status: StatusPlantio,
        dt_plantio: date | None = None,
    ) -> PlantioModel | None:
        ordem = self.repository.get_ordem_producao_by_id(id_ordem)
        if ordem is None:
            raise ValueError("Ordem de producao nao encontrada.")
        if ordem.status in (StatusOrdemProducao.CONCLUIDA, StatusOrdemProducao.CANCELADA):
            raise ValueError("Nao e possivel criar plantio em uma ordem de producao concluida ou cancelada.")
        talhao = self.repository.get_talhao_by_id(id_talhao)
        if talhao is None:
            raise ValueError("Talhao nao encontrado.")
        if self.repository.get_cultura_by_id(id_cultura) is None:
            raise ValueError("Cultura nao encontrada.")
        planejamento = self.repository.get_planejamento_safra_by_id(id_planejamento)
        if planejamento is None:
            raise ValueError("Planejamento de safra nao encontrado.")
        if planejamento.status == StatusPlanejamentoSafra.CANCELADO:
            raise ValueError("Nao e possivel criar plantio a partir de um planejamento cancelado.")
        if talhao.id_safra != planejamento.id_safra:
            raise ValueError("O talhao informado nao pertence a mesma safra do planejamento.")
        if dt_plantio is not None:
            safra = self.repository.get_safra_by_id(planejamento.id_safra)
            fora_do_periodo = safra is not None and (
                (safra.dt_inicio is not None and dt_plantio < safra.dt_inicio)
                or (safra.dt_fim is not None and dt_plantio > safra.dt_fim)
            )
            if fora_do_periodo:
                raise ValueError("A data de plantio esta fora do periodo da safra.")
        return self.repository.create_plantio(id_ordem, id_talhao, id_produto, id_cultura, id_planejamento, status, dt_plantio)

    def get_plantio_by_id(self, id_plantio: int) -> PlantioModel | None:
        return self.repository.get_plantio_by_id(id_plantio)

    def list_plantios(self, filters: dict | None = None) -> list[PlantioModel]:
        return self.repository.list_plantios(filters)

    def update_status_plantio(self, id_plantio: int, status: StatusPlantio) -> bool:
        atual = self.repository.get_plantio_by_id(id_plantio)
        if atual is None:
            return False
        self._validar_transicao(_TRANSICOES_PLANTIO, atual.status, status, "plantio")
        return self.repository.update_status_plantio(id_plantio, status)

    def iniciar_plantio(self, id_plantio: int) -> bool:
        return self.update_status_plantio(id_plantio, StatusPlantio.EM_ANDAMENTO)

    def cancelar_plantio(self, id_plantio: int) -> bool:
        return self.update_status_plantio(id_plantio, StatusPlantio.CANCELADO)

    def delete_plantio(self, id_plantio: int) -> bool:
        return self.repository.delete_plantio(id_plantio)

    # CRUD de OperacaoAgricola
    def create_operacao_agricola(
        self,
        id_plantio: int,
        id_funcionario: int,
        status: StatusOperacaoAgricola,
        tipo_operacao: str | None = None,
        descricao: str | None = None,
        dt_inicio: datetime | None = None,
        dt_fim: datetime | None = None,
    ) -> OperacaoAgricolaModel | None:
        plantio = self.repository.get_plantio_by_id(id_plantio)
        if plantio is None:
            raise ValueError("Plantio nao encontrado.")
        if plantio.status in (StatusPlantio.CONCLUIDO, StatusPlantio.CANCELADO):
            raise ValueError("Nao e possivel registrar operacao para um plantio concluido ou cancelado.")
        if dt_inicio is not None and dt_fim is not None and dt_fim < dt_inicio:
            raise ValueError("A data de fim da operacao nao pode ser anterior a data de inicio.")
        if dt_inicio is not None and plantio.dt_plantio is not None and dt_inicio.date() < plantio.dt_plantio:
            raise ValueError("A operacao nao pode iniciar antes do plantio.")
        return self.repository.create_operacao_agricola(
            id_plantio, id_funcionario, status, tipo_operacao, descricao, dt_inicio, dt_fim
        )

    def get_operacao_agricola_by_id(self, id_operacao: int) -> OperacaoAgricolaModel | None:
        return self.repository.get_operacao_agricola_by_id(id_operacao)

    def list_operacoes_agricolas(self, filters: dict | None = None) -> list[OperacaoAgricolaModel]:
        return self.repository.list_operacoes_agricolas(filters)

    def update_status_operacao_agricola(self, id_operacao: int, status: StatusOperacaoAgricola) -> bool:
        atual = self.repository.get_operacao_agricola_by_id(id_operacao)
        if atual is None:
            return False
        self._validar_transicao(_TRANSICOES_OPERACAO_AGRICOLA, atual.status, status, "operacao agricola")
        return self.repository.update_status_operacao_agricola(id_operacao, status)

    def iniciar_operacao_agricola(self, id_operacao: int) -> bool:
        return self.update_status_operacao_agricola(id_operacao, StatusOperacaoAgricola.EM_ANDAMENTO)

    def concluir_operacao_agricola(self, id_operacao: int) -> bool:
        return self.update_status_operacao_agricola(id_operacao, StatusOperacaoAgricola.CONCLUIDA)

    def cancelar_operacao_agricola(self, id_operacao: int) -> bool:
        return self.update_status_operacao_agricola(id_operacao, StatusOperacaoAgricola.CANCELADA)

    def delete_operacao_agricola(self, id_operacao: int) -> bool:
        return self.repository.delete_operacao_agricola(id_operacao)

    # CRUD de AtividadeAgricola (detalhes abaixo)
    def create_atividade_agricola(
        self,
        id_operacao: int,
        status: StatusAtividadeAgricola,
        descricao: str | None = None,
        dt_inicio: datetime | None = None,
        dt_fim: datetime | None = None,
    ) -> AtividadeAgricolaModel | None:
        operacao = self.repository.get_operacao_agricola_by_id(id_operacao)
        if operacao is None:
            raise ValueError("Operacao agricola nao encontrada.")
        if operacao.status in (StatusOperacaoAgricola.CONCLUIDA, StatusOperacaoAgricola.CANCELADA):
            raise ValueError("Nao e possivel registrar atividade para uma operacao concluida ou cancelada.")
        if dt_inicio is not None and dt_fim is not None and dt_fim < dt_inicio:
            raise ValueError("A data de fim da atividade nao pode ser anterior a data de inicio.")
        if dt_inicio is not None and operacao.dt_inicio is not None and dt_inicio < operacao.dt_inicio:
            raise ValueError("A atividade nao pode iniciar antes da operacao.")
        return self.repository.create_atividade_agricola(id_operacao, status, descricao, dt_inicio, dt_fim)

    def get_atividade_agricola_by_id(self, id_atividade: int) -> AtividadeAgricolaModel | None:
        return self.repository.get_atividade_agricola_by_id(id_atividade)

    def list_atividades_agricolas(self, filters: dict | None = None) -> list[AtividadeAgricolaModel]:
        return self.repository.list_atividades_agricolas(filters)

    def update_status_atividade_agricola(self, id_atividade: int, status: StatusAtividadeAgricola) -> bool:
        atual = self.repository.get_atividade_agricola_by_id(id_atividade)
        if atual is None:
            return False
        self._validar_transicao(_TRANSICOES_ATIVIDADE_AGRICOLA, atual.status, status, "atividade agricola")
        return self.repository.update_status_atividade_agricola(id_atividade, status)

    def iniciar_atividade_agricola(self, id_atividade: int) -> bool:
        return self.update_status_atividade_agricola(id_atividade, StatusAtividadeAgricola.EM_ANDAMENTO)

    def concluir_atividade_agricola(self, id_atividade: int) -> bool:
        return self.update_status_atividade_agricola(id_atividade, StatusAtividadeAgricola.CONCLUIDA)

    def cancelar_atividade_agricola(self, id_atividade: int) -> bool:
        return self.update_status_atividade_agricola(id_atividade, StatusAtividadeAgricola.CANCELADA)

    def delete_atividade_agricola(self, id_atividade: int) -> bool:
        return self.repository.delete_atividade_agricola(id_atividade)


    # CRUD de FuncionarioAtividade
    def link_funcionario_atividade(self, id_funcionario: int, id_atividade: int) -> bool:
        if self.repository.get_atividade_agricola_by_id(id_atividade) is None:
            raise ValueError("Atividade nao encontrada.")
        return self.repository.link_funcionario_atividade(id_funcionario, id_atividade)

    def unlink_funcionario_atividade(self, id_funcionario: int, id_atividade: int) -> bool:
        return self.repository.unlink_funcionario_atividade(id_funcionario, id_atividade)

    def list_funcionarios_por_atividade(self, id_atividade: int) -> list[FuncionarioAtividadeModel]:
        return self.repository.list_funcionarios_por_atividade(id_atividade)

    def list_atividades_por_funcionario(self, id_funcionario: int) -> list[FuncionarioAtividadeModel]:
        return self.repository.list_atividades_por_funcionario(id_funcionario)

    # Adubacao (AtividadeAgricola)
    def upsert_adubacao(
        self,
        id_atividade: int,
        id_insumo: int,
        tipo_adubacao: str | None = None,
        dose_hectare: Decimal | None = None,
        metodo_aplicacao: str | None = None,
    ) -> AdubacaoModel | None:
        if self.repository.get_atividade_agricola_by_id(id_atividade) is None:
            raise ValueError("Atividade nao encontrada.")
        return self.repository.upsert_adubacao(id_atividade, id_insumo, tipo_adubacao, dose_hectare, metodo_aplicacao)

    def get_adubacao_by_atividade(self, id_atividade: int) -> AdubacaoModel | None:
        return self.repository.get_adubacao_by_atividade(id_atividade)

    def delete_adubacao(self, id_atividade: int) -> bool:
        return self.repository.delete_adubacao(id_atividade)

    # Irrigacao (AtividadeAgricola)
    def upsert_irrigacao(
        self,
        id_atividade: int,
        lamina_agua: Decimal | None = None,
        metodo_irrigacao: str | None = None,
        duracao_horas: Decimal | None = None,
    ) -> IrrigacaoModel | None:
        if self.repository.get_atividade_agricola_by_id(id_atividade) is None:
            raise ValueError("Atividade nao encontrada.")
        return self.repository.upsert_irrigacao(id_atividade, lamina_agua, metodo_irrigacao, duracao_horas)

    def get_irrigacao_by_atividade(self, id_atividade: int) -> IrrigacaoModel | None:
        return self.repository.get_irrigacao_by_atividade(id_atividade)

    def delete_irrigacao(self, id_atividade: int) -> bool:
        return self.repository.delete_irrigacao(id_atividade)

    # Pulverizacao (AtividadeAgricola)
    def upsert_pulverizacao(
        self, id_atividade: int, id_insumo: int, volume_calda: Decimal | None = None, vazao: Decimal | None = None
    ) -> PulverizacaoModel | None:
        if self.repository.get_atividade_agricola_by_id(id_atividade) is None:
            raise ValueError("Atividade nao encontrada.")
        return self.repository.upsert_pulverizacao(id_atividade, id_insumo, volume_calda, vazao)

    def get_pulverizacao_by_atividade(self, id_atividade: int) -> PulverizacaoModel | None:
        return self.repository.get_pulverizacao_by_atividade(id_atividade)

    def delete_pulverizacao(self, id_atividade: int) -> bool:
        return self.repository.delete_pulverizacao(id_atividade)

    # CRUD de Colheita
    def create_colheita(
        self,
        id_plantio: int,
        status: StatusColheita,
        quantidade_colhida: Decimal | None = None,
        dt_inicio: date | None = None,
        dt_fim: date | None = None,
    ) -> ColheitaModel | None:
        plantio = self.repository.get_plantio_by_id(id_plantio)
        if plantio is None:
            raise ValueError("Plantio nao encontrado.")
        if plantio.status in (StatusPlantio.PLANEJADO, StatusPlantio.CANCELADO):
            raise ValueError("Nao e possivel registrar colheita para um plantio ainda nao iniciado ou cancelado.")
        if quantidade_colhida is not None and quantidade_colhida <= 0:
            raise ValueError("A quantidade colhida deve ser maior que zero.")
        if dt_inicio is not None and dt_fim is not None and dt_fim < dt_inicio:
            raise ValueError("A data de fim da colheita nao pode ser anterior a data de inicio.")
        if dt_inicio is not None and plantio.dt_plantio is not None and dt_inicio < plantio.dt_plantio:
            raise ValueError("A colheita nao pode iniciar antes do plantio.")
        self._assert_carencia_respeitada(id_plantio, dt_inicio)
        return self.repository.create_colheita(id_plantio, status, quantidade_colhida, dt_inicio, dt_fim)

    def _assert_carencia_respeitada(
        self, id_plantio: int, dt_inicio: date | None
    ) -> None:
        """Bloqueia colheita enquanto houver carencia de defensivo ativa no plantio."""
        from sqlalchemy import text

        from app.core.database import get_session

        referencia = dt_inicio or date.today()
        with get_session() as session:
            row = session.execute(
                text(
                    """
                    SELECT MAX(ad.dt_carencia) AS dt_carencia
                    FROM aplicacao_defensivo ad
                    JOIN controle_fitossanitario cf
                      ON cf.id_controle = ad.id_controle
                    WHERE cf.id_plantio = :id_plantio
                      AND ad.dt_carencia IS NOT NULL
                    """
                ),
                {"id_plantio": id_plantio},
            ).first()
        if row is None or row[0] is None:
            return
        dt_carencia = row[0]
        if referencia < dt_carencia:
            raise ValueError(
                f"Nao e possivel colher: periodo de carencia ativo ate {dt_carencia.isoformat()} "
                "devido a aplicacao de defensivo no plantio."
            )

    def colher_plantio(
        self,
        id_plantio: int,
        quantidade_colhida: Decimal | None = None,
        dt_inicio: date | None = None,
        dt_fim: date | None = None,
    ) -> ColheitaModel | None:
        """Operacao composta: abre a colheita do plantio e encerra o plantio (EM_ANDAMENTO -> CONCLUIDO)."""
        colheita = self.create_colheita(id_plantio, StatusColheita.ABERTA, quantidade_colhida, dt_inicio, dt_fim)
        if colheita is None:
            return None
        plantio_atual = self.repository.get_plantio_by_id(id_plantio)
        if plantio_atual is not None and plantio_atual.status == StatusPlantio.EM_ANDAMENTO:
            self.repository.update_status_plantio(id_plantio, StatusPlantio.CONCLUIDO)
        return colheita

    def get_colheita_by_id(self, id_colheita: int) -> ColheitaModel | None:
        return self.repository.get_colheita_by_id(id_colheita)

    def list_colheitas(self, filters: dict | None = None) -> list[ColheitaModel]:
        return self.repository.list_colheitas(filters)

    def update_status_colheita(self, id_colheita: int, status: StatusColheita) -> bool:
        atual = self.repository.get_colheita_by_id(id_colheita)
        if atual is None:
            return False
        self._validar_transicao(_TRANSICOES_COLHEITA, atual.status, status, "colheita")
        return self.repository.update_status_colheita(id_colheita, status)

    def iniciar_colheita(self, id_colheita: int) -> bool:
        atual = self.repository.get_colheita_by_id(id_colheita)
        if atual is None:
            return False
        self._assert_carencia_respeitada(atual.id_plantio, atual.dt_inicio)
        return self.update_status_colheita(id_colheita, StatusColheita.EM_ANDAMENTO)

    def concluir_colheita(
        self,
        id_colheita: int,
        id_estoque: int | None = None,
        id_produto: int | None = None,
    ) -> bool:
        ok = self.update_status_colheita(id_colheita, StatusColheita.CONCLUIDA)
        if not ok:
            return False
        try:
            from app.estoque.service import EstoqueService

            EstoqueService().register_entry_from_harvest(
                id_colheita,
                id_estoque=id_estoque,
                id_produto=id_produto,
            )
        except Exception:
            # Harvest status already persisted; stock entry may be retried manually.
            pass
        return True

    def cancelar_colheita(self, id_colheita: int) -> bool:
        return self.update_status_colheita(id_colheita, StatusColheita.CANCELADA)

    def delete_colheita(self, id_colheita: int) -> bool:
        return self.repository.delete_colheita(id_colheita)
