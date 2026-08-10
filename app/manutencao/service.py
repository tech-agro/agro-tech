"""Regras de negocio do dominio manutencao."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from app.core.database import pg_connector

if TYPE_CHECKING:
    from app.financeiro.service import FinanceiroService
from app.manutencao.repository import (
    ManutencaoCorretivaFilters,
    ManutencaoPreventivaFilters,
    ManutencaoRepository,
    MaquinaFilters,
    OrdemServicoFilters,
    PlanoManutencaoFilters,
)
from app.manutencao.schemas.maquina import (
    MaquinaCreateSchema,
    MaquinaReadSchema,
    MaquinaUpdateSchema,
)
from app.manutencao.schemas.manutencao import (
    ManutencaoCreateSchema,
    ManutencaoReadSchema,
    ManutencaoUpdateSchema,
)
from app.manutencao.schemas.manutencao_corretiva import (
    ManutencaoCorretivaDetalheSchema,
    ManutencaoCorretivaReadSchema,
    ManutencaoCorretivaUpdateSchema,
)
from app.manutencao.schemas.manutencao_preventiva import (
    ManutencaoPreventivaDetalheSchema,
    ManutencaoPreventivaReadSchema,
    ManutencaoPreventivaUpdateSchema,
)
from app.manutencao.schemas.ordem_servico import (
    OrdemServicoCreateSchema,
    OrdemServicoDetalheSchema,
    OrdemServicoReadSchema,
    OrdemServicoUpdateSchema,
)
from app.manutencao.schemas.plano_manutencao import (
    PlanoManutencaoCreateSchema,
    PlanoManutencaoDetalheSchema,
    PlanoManutencaoReadSchema,
    PlanoManutencaoUpdateSchema,
)
from app.manutencao.schemas.tipo_maquina import (
    TipoMaquinaCreateSchema,
    TipoMaquinaReadSchema,
    TipoMaquinaUpdateSchema,
)

logger = logging.getLogger(__name__)

TIPO_PREVENTIVA = "PREVENTIVA"
TIPO_CORRETIVA = "CORRETIVA"

STATUS_ABERTA = "ABERTA"
STATUS_EM_EXECUCAO = "EM_EXECUCAO"
STATUS_CONCLUIDA = "CONCLUIDA"
STATUS_CANCELADA = "CANCELADA"

STATUS_MAQUINA_DISPONIVEL = "DISPONIVEL"
STATUS_MAQUINA_EM_MANUTENCAO = "EM_MANUTENCAO"

OPEN_MANUTENCAO_STATUSES = {STATUS_ABERTA, STATUS_EM_EXECUCAO}
FINAL_MANUTENCAO_STATUSES = {STATUS_CONCLUIDA, STATUS_CANCELADA}


class ManutencaoError(Exception):
    """Erro de regra de negocio do dominio manutencao."""


class ManutencaoValidationError(ManutencaoError):
    """Entrada ou transicao de estado invalida."""


class ManutencaoConflictError(ManutencaoError):
    """Conflito com o estado atual do registro."""


class ManutencaoNotFoundError(ManutencaoError):
    """Registro solicitado nao encontrado."""


@dataclass(slots=True)
class ManutencaoPreventivaResult:
    manutencao: ManutencaoReadSchema
    preventiva: ManutencaoPreventivaReadSchema


@dataclass(slots=True)
class ManutencaoCorretivaResult:
    manutencao: ManutencaoReadSchema
    corretiva: ManutencaoCorretivaReadSchema


class ManutencaoService:
    """Camada de orquestracao das regras de negocio."""

    def __init__(
        self,
        repository: ManutencaoRepository | None = None,
        financeiro_service: FinanceiroService | None = None,
    ) -> None:
        self.repository = repository or ManutencaoRepository(pg_connector, logger)
        self._financeiro_service = financeiro_service

    def _financeiro(self) -> FinanceiroService:
        if self._financeiro_service is None:
            from app.financeiro.service import FinanceiroService

            self._financeiro_service = FinanceiroService()
        return self._financeiro_service

    def _request_conta_pagar_from_manutencao(
        self,
        id_manutencao: int,
        valor: Decimal,
        vencimento: date,
    ) -> None:
        """Conclusao de manutencao gera conta a pagar no financeiro."""
        self._financeiro().create_conta_pagar_from_manutencao(
            id_manutencao=id_manutencao,
            valor=valor,
            vencimento=vencimento,
        )

    # ------------------------------------------------------------------
    # Manutencao preventiva / corretiva
    # ------------------------------------------------------------------

    def criar_manutencao_preventiva(
        self,
        payload: ManutencaoCreateSchema,
        *,
        id_plano: int,
        hodometro_execucao: float | None = None,
        proxima_hodometro: float | None = None,
    ) -> ManutencaoPreventivaResult:
        """Registra manutencao preventiva vinculada a um plano da mesma maquina."""
        self._validar_periodo(payload.dt_inicio, payload.dt_fim)
        self._garantir_maquina_existe(payload.id_maquina)

        plano = self.repository.get_plano_by_id(id_plano)
        if plano is None:
            raise ManutencaoNotFoundError(f"Plano {id_plano} nao encontrado.")
        if plano.id_maquina != payload.id_maquina:
            raise ManutencaoValidationError(
                "O plano de manutencao deve pertencer a mesma maquina."
            )

        self._garantir_sem_manutencao_aberta(payload.id_maquina)

        manutencao_payload = payload.model_copy(
            update={
                "tipo": TIPO_PREVENTIVA,
                "status": STATUS_ABERTA,
            }
        )
        result = self.repository.create_manutencao_preventiva(
            manutencao_payload,
            id_plano=id_plano,
            hodometro_execucao=hodometro_execucao,
            proxima_hodometro=proxima_hodometro,
        )
        if result is None:
            raise ManutencaoError("Nao foi possivel registrar a manutencao preventiva.")
        manutencao, preventiva = result
        return ManutencaoPreventivaResult(
            manutencao=manutencao,
            preventiva=preventiva,
        )

    def criar_manutencao_corretiva(
        self,
        payload: ManutencaoCreateSchema,
        *,
        defeito_relatado: str,
        causa_raiz: str | None = None,
        solucao_aplicada: str | None = None,
    ) -> ManutencaoCorretivaResult:
        """Registra manutencao corretiva a partir de um defeito relatado."""
        if not defeito_relatado or not defeito_relatado.strip():
            raise ManutencaoValidationError(
                "Manutencao corretiva exige defeito relatado."
            )

        self._validar_periodo(payload.dt_inicio, payload.dt_fim)
        self._garantir_maquina_existe(payload.id_maquina)
        self._garantir_sem_manutencao_aberta(payload.id_maquina)

        manutencao_payload = payload.model_copy(
            update={
                "tipo": TIPO_CORRETIVA,
                "status": STATUS_ABERTA,
            }
        )
        result = self.repository.create_manutencao_corretiva(
            manutencao_payload,
            defeito_relatado=defeito_relatado.strip(),
            causa_raiz=causa_raiz,
            solucao_aplicada=solucao_aplicada,
        )
        if result is None:
            raise ManutencaoError("Nao foi possivel registrar a manutencao corretiva.")
        manutencao, corretiva = result
        return ManutencaoCorretivaResult(
            manutencao=manutencao,
            corretiva=corretiva,
        )

    def list_manutencoes_corretivas(
        self,
        *,
        id_maquina: int | None = None,
        status: str | None = None,
    ) -> list[ManutencaoCorretivaDetalheSchema]:
        """Lista manutencoes corretivas com filtros opcionais."""
        return self.repository.list_manutencoes_corretivas(
            ManutencaoCorretivaFilters(
                id_maquina=id_maquina,
                status=status,
            )
        )

    def list_manutencoes_preventivas(
        self,
        *,
        id_maquina: int | None = None,
        id_plano: int | None = None,
        status: str | None = None,
    ) -> list[ManutencaoPreventivaDetalheSchema]:
        """Lista manutencoes preventivas com filtros opcionais."""
        return self.repository.list_manutencoes_preventivas(
            ManutencaoPreventivaFilters(
                id_maquina=id_maquina,
                id_plano=id_plano,
                status=status,
            )
        )

    def atualizar_manutencao_preventiva(
        self,
        id_manutencao: int,
        payload: ManutencaoPreventivaUpdateSchema,
    ) -> ManutencaoPreventivaReadSchema:
        """Atualiza detalhes de manutencao preventiva durante a execucao."""
        manutencao = self._obter_manutencao(id_manutencao)
        if manutencao.tipo != TIPO_PREVENTIVA:
            raise ManutencaoValidationError(
                "Somente manutencoes preventivas possuem estes detalhes."
            )
        if manutencao.status in FINAL_MANUTENCAO_STATUSES:
            raise ManutencaoConflictError(
                "Manutencao encerrada nao pode ser alterada."
            )

        if payload.dt_inicio is not None:
            self._validar_periodo(payload.dt_inicio, manutencao.dt_fim)
            updated_manutencao = self.repository.update_manutencao(
                id_manutencao,
                ManutencaoUpdateSchema(dt_inicio=payload.dt_inicio),
            )
            if updated_manutencao is None:
                raise ManutencaoError("Nao foi possivel atualizar a data de execucao.")

        updated = self.repository.update_manutencao_preventiva(
            id_manutencao,
            ManutencaoPreventivaUpdateSchema(
                id_plano=payload.id_plano,
                hodometro_execucao=payload.hodometro_execucao,
                proxima_hodometro=payload.proxima_hodometro,
            ),
        )
        if updated is None:
            raise ManutencaoNotFoundError(
                f"Manutencao preventiva {id_manutencao} nao encontrada."
            )
        return updated

    def iniciar_manutencao(self, id_manutencao: int) -> ManutencaoReadSchema:
        """Transiciona manutencao de ABERTA para EM_EXECUCAO."""
        manutencao = self._obter_manutencao(id_manutencao)
        if manutencao.status != STATUS_ABERTA:
            raise ManutencaoConflictError(
                "Somente manutencoes abertas podem ser iniciadas."
            )

        update = ManutencaoUpdateSchema(
            status=STATUS_EM_EXECUCAO,
            dt_inicio=manutencao.dt_inicio or date.today(),
        )
        updated = self.repository.update_manutencao(id_manutencao, update)
        if updated is None:
            raise ManutencaoError("Nao foi possivel iniciar a manutencao.")
        return updated

    def concluir_manutencao(
        self,
        id_manutencao: int,
        *,
        custo: float | None = None,
        dt_fim: date | None = None,
        proxima_execucao: date | None = None,
    ) -> ManutencaoReadSchema:
        """Conclui manutencao e dispara historico, financeiro e recalculo preventivo."""
        manutencao = self._obter_manutencao(id_manutencao)
        if manutencao.status in FINAL_MANUTENCAO_STATUSES:
            raise ManutencaoConflictError("Manutencao ja encerrada.")
        if manutencao.status not in {STATUS_ABERTA, STATUS_EM_EXECUCAO}:
            raise ManutencaoConflictError("Status atual nao permite conclusao.")

        ordens_abertas = self.repository.count_open_ordens_by_manutencao(id_manutencao)
        if ordens_abertas > 0:
            raise ManutencaoConflictError(
                "Existem ordens de servico abertas vinculadas a esta manutencao."
            )

        dt_fim_efetiva = dt_fim or date.today()
        self._validar_periodo(manutencao.dt_inicio, dt_fim_efetiva)

        corretiva = None
        preventiva = None
        plano = None

        if manutencao.tipo == TIPO_CORRETIVA:
            corretiva = self.repository.get_manutencao_corretiva_by_id(id_manutencao)
            if corretiva is None:
                raise ManutencaoNotFoundError(
                    "Detalhes da manutencao corretiva nao encontrados."
                )
            if not corretiva.solucao_aplicada or not corretiva.solucao_aplicada.strip():
                raise ManutencaoValidationError(
                    "Manutencao corretiva so pode ser concluida com solucao aplicada."
                )

        if manutencao.tipo == TIPO_PREVENTIVA:
            preventiva = self.repository.get_manutencao_preventiva_by_id(id_manutencao)
            if preventiva is not None:
                plano = self.repository.get_plano_by_id(preventiva.id_plano)

        custo_efetivo = custo if custo is not None else manutencao.custo
        if manutencao.tipo in {TIPO_CORRETIVA, TIPO_PREVENTIVA}:
            if custo_efetivo is None or custo_efetivo <= 0:
                raise ManutencaoValidationError(
                    "Manutencao exige custo informado para ser concluida."
                )

        proxima_execucao_calc, proxima_hodometro_calc = self._recalcular_ciclo_preventivo(
            plano,
            preventiva,
            dt_fim_efetiva,
        )
        proxima_execucao_efetiva = proxima_execucao or proxima_execucao_calc
        proxima_hodometro_efetiva = (
            preventiva.proxima_hodometro
            if preventiva is not None and preventiva.proxima_hodometro is not None
            else proxima_hodometro_calc
        )

        observacao = self._montar_observacao_historico(
            manutencao,
            dt_fim=dt_fim_efetiva,
            custo=custo_efetivo,
            corretiva=corretiva,
            preventiva=preventiva,
            proxima_execucao=proxima_execucao_efetiva,
            proxima_hodometro=proxima_hodometro_efetiva,
        )

        updated = self.repository.finalize_manutencao_execution(
            id_manutencao,
            id_maquina=manutencao.id_maquina,
            custo=custo_efetivo,
            dt_fim=dt_fim_efetiva,
            observacao_historico=observacao,
            id_plano=preventiva.id_plano if preventiva is not None else None,
            proxima_execucao=proxima_execucao_efetiva,
            proxima_hodometro=proxima_hodometro_efetiva,
        )
        if updated is None:
            raise ManutencaoError("Nao foi possivel concluir a manutencao.")

        if custo_efetivo is not None and custo_efetivo > 0:
            self._request_conta_pagar_from_manutencao(
                id_manutencao=id_manutencao,
                valor=Decimal(str(custo_efetivo)),
                vencimento=dt_fim_efetiva,
            )

        return updated

    def cancelar_manutencao(self, id_manutencao: int) -> ManutencaoReadSchema:
        """Cancela manutencao em andamento."""
        manutencao = self._obter_manutencao(id_manutencao)
        if manutencao.status == STATUS_CONCLUIDA:
            raise ManutencaoConflictError("Manutencao concluida nao pode ser cancelada.")
        if manutencao.status == STATUS_CANCELADA:
            raise ManutencaoConflictError("Manutencao ja esta cancelada.")

        ordens_abertas = self.repository.count_open_ordens_by_manutencao(id_manutencao)
        if ordens_abertas > 0:
            raise ManutencaoConflictError(
                "Existem ordens de servico abertas vinculadas a esta manutencao."
            )

        updated = self.repository.update_manutencao(
            id_manutencao,
            ManutencaoUpdateSchema(status=STATUS_CANCELADA),
        )
        if updated is None:
            raise ManutencaoError("Nao foi possivel cancelar a manutencao.")

        self._restaurar_disponibilidade_maquina(manutencao.id_maquina)
        return updated

    def atualizar_manutencao_corretiva(
        self,
        id_manutencao: int,
        payload: ManutencaoCorretivaUpdateSchema,
    ) -> ManutencaoCorretivaReadSchema:
        """Atualiza detalhes de manutencao corretiva durante a execucao."""
        manutencao = self._obter_manutencao(id_manutencao)
        if manutencao.tipo != TIPO_CORRETIVA:
            raise ManutencaoValidationError(
                "Somente manutencoes corretivas possuem estes detalhes."
            )
        if manutencao.status in FINAL_MANUTENCAO_STATUSES:
            raise ManutencaoConflictError(
                "Manutencao encerrada nao pode ser alterada."
            )

        if payload.dt_inicio is not None:
            self._validar_periodo(payload.dt_inicio, manutencao.dt_fim)
            updated_manutencao = self.repository.update_manutencao(
                id_manutencao,
                ManutencaoUpdateSchema(dt_inicio=payload.dt_inicio),
            )
            if updated_manutencao is None:
                raise ManutencaoError("Nao foi possivel atualizar a data do defeito.")

        if payload.custo is not None:
            updated_custo = self.repository.update_manutencao(
                id_manutencao,
                ManutencaoUpdateSchema(custo=payload.custo),
            )
            if updated_custo is None:
                raise ManutencaoError("Nao foi possivel atualizar o custo da manutencao.")

        updated = self.repository.update_manutencao_corretiva(
            id_manutencao,
            ManutencaoCorretivaUpdateSchema(
                defeito_relatado=payload.defeito_relatado,
                causa_raiz=payload.causa_raiz,
                solucao_aplicada=payload.solucao_aplicada,
            ),
        )
        if updated is None:
            raise ManutencaoNotFoundError(
                f"Manutencao corretiva {id_manutencao} nao encontrada."
            )
        return updated

    def get_manutencao(self, id_manutencao: int) -> ManutencaoReadSchema:
        return self._obter_manutencao(id_manutencao)

    # ------------------------------------------------------------------
    # Tipo maquina
    # ------------------------------------------------------------------

    def create_tipo_maquina(
        self,
        payload: TipoMaquinaCreateSchema,
    ) -> TipoMaquinaReadSchema:
        tipo = self.repository.create_tipo_maquina(payload)
        if tipo is None:
            raise ManutencaoError("Nao foi possivel criar o tipo de maquina.")
        return tipo

    def list_tipos_maquina(self) -> list[TipoMaquinaReadSchema]:
        return self.repository.list_tipos_maquina()

    def get_tipo_maquina(self, id_tipo_maquina: int) -> TipoMaquinaReadSchema:
        tipo = self.repository.get_tipo_maquina_by_id(id_tipo_maquina)
        if tipo is None:
            raise ManutencaoNotFoundError(
                f"Tipo de maquina {id_tipo_maquina} nao encontrado."
            )
        return tipo

    def update_tipo_maquina(
        self,
        id_tipo_maquina: int,
        payload: TipoMaquinaUpdateSchema,
    ) -> TipoMaquinaReadSchema:
        self.get_tipo_maquina(id_tipo_maquina)
        if payload.descricao is not None and not payload.descricao.strip():
            raise ManutencaoValidationError("Descricao do tipo nao pode ser vazia.")
        updated = self.repository.update_tipo_maquina(id_tipo_maquina, payload)
        if updated is None:
            raise ManutencaoError("Nao foi possivel atualizar o tipo de maquina.")
        return updated

    def delete_tipo_maquina(self, id_tipo_maquina: int) -> bool:
        self.get_tipo_maquina(id_tipo_maquina)
        if self.repository.count_maquinas_by_tipo(id_tipo_maquina) > 0:
            raise ManutencaoConflictError(
                "Tipo de maquina possui maquinas cadastradas e nao pode ser excluido."
            )
        return self.repository.delete_tipo_maquina(id_tipo_maquina)

    # ------------------------------------------------------------------
    # Maquina
    # ------------------------------------------------------------------

    def create_maquina(
        self,
        payload: MaquinaCreateSchema,
        *,
        id_fazenda: int,
    ) -> MaquinaReadSchema:
        maquina = self.repository.create_maquina(payload, id_fazenda=id_fazenda)
        if maquina is None:
            raise ManutencaoError("Nao foi possivel criar a maquina.")
        return maquina

    def get_maquina(self, id_maquina: int) -> MaquinaReadSchema:
        maquina = self.repository.get_maquina_by_id(id_maquina)
        if maquina is None:
            raise ManutencaoNotFoundError(f"Maquina {id_maquina} nao encontrada.")
        return maquina

    def list_maquinas(
        self,
        filters: MaquinaFilters | None = None,
    ) -> list[MaquinaReadSchema]:
        return self.repository.list_maquinas(filters)

    def update_maquina(
        self,
        id_maquina: int,
        payload: MaquinaUpdateSchema,
    ) -> MaquinaReadSchema:
        self.get_maquina(id_maquina)
        updated = self.repository.update_maquina(id_maquina, payload)
        if updated is None:
            raise ManutencaoError("Nao foi possivel atualizar a maquina.")
        return updated

    def delete_maquina(self, id_maquina: int) -> bool:
        self.get_maquina(id_maquina)
        if self.repository.count_open_manutencoes_by_maquina(id_maquina) > 0:
            raise ManutencaoConflictError(
                "Maquina possui manutencao aberta e nao pode ser excluida."
            )
        return self.repository.delete_maquina(id_maquina)

    # ------------------------------------------------------------------
    # Plano manutencao
    # ------------------------------------------------------------------

    def create_plano(self, payload: PlanoManutencaoCreateSchema) -> PlanoManutencaoDetalheSchema:
        self._garantir_maquina_existe(payload.id_maquina)
        self._validar_periodicidade(payload.periodicidade)
        proxima_execucao = payload.proxima_execucao
        if proxima_execucao is None and payload.periodicidade:
            proxima_execucao = self.calcular_proxima_execucao_plano(payload.periodicidade)
        payload_efetivo = payload.model_copy(update={"proxima_execucao": proxima_execucao})
        plano = self.repository.create_plano(payload_efetivo)
        if plano is None:
            raise ManutencaoError("Nao foi possivel criar o plano de manutencao.")
        return plano

    def list_planos(
        self,
        *,
        id_maquina: int | None = None,
    ) -> list[PlanoManutencaoDetalheSchema]:
        return self.repository.list_planos(
            PlanoManutencaoFilters(id_maquina=id_maquina)
        )

    def get_plano(self, id_plano: int) -> PlanoManutencaoReadSchema:
        plano = self.repository.get_plano_by_id(id_plano)
        if plano is None:
            raise ManutencaoNotFoundError(f"Plano {id_plano} nao encontrado.")
        return plano

    def update_plano(
        self,
        id_plano: int,
        payload: PlanoManutencaoUpdateSchema,
    ) -> PlanoManutencaoDetalheSchema:
        atual = self.get_plano(id_plano)
        if payload.id_maquina is not None:
            self._garantir_maquina_existe(payload.id_maquina)
        if payload.periodicidade is not None:
            self._validar_periodicidade(payload.periodicidade)
        elif atual.periodicidade:
            self._validar_periodicidade(atual.periodicidade)

        proxima_execucao = None
        if (
            payload.periodicidade is not None
            and payload.periodicidade != atual.periodicidade
        ):
            proxima_execucao = self.calcular_proxima_execucao_plano(payload.periodicidade)

        update_payload = PlanoManutencaoUpdateSchema(
            id_maquina=payload.id_maquina,
            periodicidade=payload.periodicidade,
            proxima_execucao=proxima_execucao,
        )
        updated = self.repository.update_plano(id_plano, update_payload)
        if updated is None:
            raise ManutencaoError("Nao foi possivel atualizar o plano de manutencao.")
        return updated

    def delete_plano(self, id_plano: int) -> bool:
        self.get_plano(id_plano)
        if self.repository.count_preventivas_by_plano(id_plano) > 0:
            raise ManutencaoConflictError(
                "Plano possui manutencoes preventivas vinculadas e nao pode ser excluido."
            )
        return self.repository.delete_plano(id_plano)

    # ------------------------------------------------------------------
    # Ordem de servico
    # ------------------------------------------------------------------

    def create_ordem_servico(
        self,
        payload: OrdemServicoCreateSchema,
    ) -> OrdemServicoReadSchema:
        manutencao = self._obter_manutencao(payload.id_manutencao)
        if manutencao.status in FINAL_MANUTENCAO_STATUSES:
            raise ManutencaoConflictError(
                "Nao e possivel abrir ordem de servico para manutencao encerrada."
            )

        ordem = self.repository.create_ordem_servico(payload)
        if ordem is None:
            raise ManutencaoError("Nao foi possivel criar a ordem de servico.")
        return ordem

    def get_ordem_servico(self, id_ordem_servico: int) -> OrdemServicoReadSchema:
        ordem = self.repository.get_ordem_servico_by_id(id_ordem_servico)
        if ordem is None:
            raise ManutencaoNotFoundError(
                f"Ordem de servico {id_ordem_servico} nao encontrada."
            )
        return ordem

    def list_ordens_servico(
        self,
        filters: OrdemServicoFilters | None = None,
    ) -> list[OrdemServicoDetalheSchema]:
        return self.repository.list_ordens_servico(filters)

    def update_ordem_servico(
        self,
        id_ordem_servico: int,
        payload: OrdemServicoUpdateSchema,
    ) -> OrdemServicoReadSchema:
        ordem = self.get_ordem_servico(id_ordem_servico)
        if payload.status == STATUS_CONCLUIDA:
            self._validar_conclusao_ordem_servico(ordem)
        if payload.id_manutencao is not None:
            self._obter_manutencao(payload.id_manutencao)

        updated = self.repository.update_ordem_servico(id_ordem_servico, payload)
        if updated is None:
            raise ManutencaoError("Nao foi possivel atualizar a ordem de servico.")
        return updated

    def concluir_ordem_servico(self, id_ordem_servico: int) -> OrdemServicoReadSchema:
        """Finaliza ordem de servico apos validar execucao completa."""
        ordem = self.get_ordem_servico(id_ordem_servico)
        self._validar_conclusao_ordem_servico(ordem)

        updated = self.repository.update_ordem_servico(
            id_ordem_servico,
            OrdemServicoUpdateSchema(status=STATUS_CONCLUIDA),
        )
        if updated is None:
            raise ManutencaoError("Nao foi possivel concluir a ordem de servico.")
        return updated

    def delete_ordem_servico(self, id_ordem_servico: int) -> bool:
        ordem = self.get_ordem_servico(id_ordem_servico)
        if ordem.status == STATUS_CONCLUIDA:
            raise ManutencaoConflictError(
                "Ordem de servico concluida nao pode ser excluida."
            )
        return self.repository.delete_ordem_servico(id_ordem_servico)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _obter_manutencao(self, id_manutencao: int) -> ManutencaoReadSchema:
        manutencao = self.repository.get_manutencao_by_id(id_manutencao)
        if manutencao is None:
            raise ManutencaoNotFoundError(
                f"Manutencao {id_manutencao} nao encontrada."
            )
        return manutencao

    def _garantir_maquina_existe(self, id_maquina: int) -> None:
        if self.repository.get_maquina_by_id(id_maquina) is None:
            raise ManutencaoNotFoundError(f"Maquina {id_maquina} nao encontrada.")

    def _garantir_sem_manutencao_aberta(self, id_maquina: int) -> None:
        if self.repository.count_open_manutencoes_by_maquina(id_maquina) > 0:
            raise ManutencaoConflictError(
                "A maquina ja possui manutencao aberta ou em execucao."
            )

    def _restaurar_disponibilidade_maquina(self, id_maquina: int) -> None:
        if self.repository.count_open_manutencoes_by_maquina(id_maquina) == 0:
            self.repository.set_maquina_status(id_maquina, STATUS_MAQUINA_DISPONIVEL)

    @staticmethod
    def _validar_periodo(dt_inicio: date | None, dt_fim: date | None) -> None:
        if dt_inicio is not None and dt_fim is not None and dt_fim < dt_inicio:
            raise ManutencaoValidationError(
                "Data fim nao pode ser anterior a data inicio."
            )

    @staticmethod
    def _validar_periodicidade(periodicidade: str | None) -> None:
        if periodicidade is None or not periodicidade.strip():
            raise ManutencaoValidationError("Informe a periodicidade do plano.")
        if ManutencaoService._parse_periodicidade(periodicidade) is None:
            raise ManutencaoValidationError(
                "Periodicidade invalida. Use formatos como '30 DIAS', '6 MESES' ou '500 HORAS'."
            )

    def _validar_conclusao_ordem_servico(self, ordem: OrdemServicoReadSchema) -> None:
        if ordem.status == STATUS_CONCLUIDA:
            raise ManutencaoConflictError("Ordem de servico ja esta concluida.")
        if ordem.status != STATUS_EM_EXECUCAO:
            raise ManutencaoConflictError(
                "Ordem de servico so pode ser concluida apos iniciar a execucao."
            )
        if not ordem.descricao or not ordem.descricao.strip():
            raise ManutencaoValidationError(
                "Ordem de servico exige descricao da execucao antes da conclusao."
            )

        manutencao = self._obter_manutencao(ordem.id_manutencao)
        if manutencao.status in FINAL_MANUTENCAO_STATUSES:
            raise ManutencaoConflictError(
                "Manutencao vinculada esta encerrada."
            )

    def calcular_proxima_execucao_plano(
        self,
        periodicidade: str,
        dt_base: date | None = None,
    ) -> date | None:
        """Calcula a proxima execucao por data a partir da periodicidade do plano."""
        dt_base = dt_base or date.today()
        parsed = self._parse_periodicidade(periodicidade)
        if parsed is None:
            return None

        unidade, quantidade = parsed
        if unidade in {"DIA", "DIAS"}:
            return dt_base + timedelta(days=quantidade)
        if unidade in {"MES", "MESES"}:
            return dt_base + timedelta(days=quantidade * 30)
        return None

    def _recalcular_ciclo_preventivo(
        self,
        plano: PlanoManutencaoReadSchema | None,
        preventiva: ManutencaoPreventivaReadSchema | None,
        dt_base: date,
    ) -> tuple[date | None, float | None]:
        """Recalcula proxima execucao e hodometro com base na periodicidade do plano."""
        if plano is None or not plano.periodicidade:
            return None, None

        proxima_execucao = self.calcular_proxima_execucao_plano(
            plano.periodicidade,
            dt_base,
        )
        proxima_hodometro = None
        parsed = self._parse_periodicidade(plano.periodicidade)
        if parsed is None:
            return proxima_execucao, None

        unidade, quantidade = parsed
        if unidade in {"HORA", "HORAS"} and preventiva is not None:
            if preventiva.hodometro_execucao is not None:
                proxima_hodometro = preventiva.hodometro_execucao + quantidade

        return proxima_execucao, proxima_hodometro

    @staticmethod
    def _parse_periodicidade(periodicidade: str) -> tuple[str, int] | None:
        match = re.search(
            r"(\d+)\s*(DIAS|DIA|MESES|MES|HORAS|HORA)",
            periodicidade.upper(),
        )
        if match is None:
            return None
        return match.group(2), int(match.group(1))

    @staticmethod
    def _montar_observacao_historico(
        manutencao: ManutencaoReadSchema,
        *,
        dt_fim: date,
        custo: float | None,
        corretiva: ManutencaoCorretivaReadSchema | None = None,
        preventiva: ManutencaoPreventivaReadSchema | None = None,
        proxima_execucao: date | None = None,
        proxima_hodometro: float | None = None,
    ) -> str:
        linhas = [
            f"Manutencao {manutencao.id_manutencao} concluida.",
            f"Tipo: {manutencao.tipo or 'NAO INFORMADO'}.",
            f"Maquina: {manutencao.id_maquina}.",
            f"Periodo: {manutencao.dt_inicio or '-'} ate {dt_fim}.",
        ]

        if custo is not None:
            linhas.append(f"Custo registrado: R$ {custo:.2f}.")

        if corretiva is not None:
            linhas.append(f"Defeito: {corretiva.defeito_relatado or '-'}")
            if corretiva.causa_raiz:
                linhas.append(f"Causa raiz: {corretiva.causa_raiz}")
            if corretiva.solucao_aplicada:
                linhas.append(f"Solucao: {corretiva.solucao_aplicada}")

        if preventiva is not None:
            linhas.append(f"Plano: {preventiva.id_plano}.")
            if preventiva.hodometro_execucao is not None:
                linhas.append(
                    f"Hodometro execucao: {preventiva.hodometro_execucao:.2f}."
                )
            if proxima_execucao is not None:
                linhas.append(f"Proxima execucao: {proxima_execucao}.")
            if proxima_hodometro is not None:
                linhas.append(f"Proximo hodometro: {proxima_hodometro:.2f}.")

        return "\n".join(linhas)
