"""Recebe requisicoes da interface para o dominio manutencao."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import TypeVar

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.manutencao.repository import MaquinaFilters, OrdemServicoFilters
from app.manutencao.schemas.maquina import (
    MaquinaCreateSchema,
    MaquinaReadSchema,
    MaquinaUpdateSchema,
)
from app.manutencao.schemas.manutencao import ManutencaoCreateSchema, ManutencaoReadSchema
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
from app.manutencao.service import (
    ManutencaoConflictError,
    ManutencaoError,
    ManutencaoNotFoundError,
    ManutencaoService,
    ManutencaoValidationError,
)

T = TypeVar("T")


class MaquinaCreateRequest(MaquinaCreateSchema):
    id_fazenda: int


class ManutencaoPreventivaCreateRequest(ManutencaoCreateSchema):
    id_plano: int
    hodometro_execucao: float | None = Field(default=None, ge=0)
    proxima_hodometro: float | None = Field(default=None, ge=0)


class ManutencaoCorretivaCreateRequest(ManutencaoCreateSchema):
    defeito_relatado: str = Field(min_length=1)
    causa_raiz: str | None = None
    solucao_aplicada: str | None = None


class ConcluirManutencaoRequest(BaseModel):
    custo: float = Field(gt=0)
    dt_fim: date | None = None
    proxima_execucao: date | None = None


class ManutencaoPreventivaResponse(BaseModel):
    manutencao: ManutencaoReadSchema
    preventiva: ManutencaoPreventivaReadSchema


class ManutencaoCorretivaResponse(BaseModel):
    manutencao: ManutencaoReadSchema
    corretiva: ManutencaoCorretivaReadSchema


class MessageResponse(BaseModel):
    message: str


class ManutencaoController:
    """Adaptador entre interface HTTP (FastAPI) e service."""

    def __init__(self, service: ManutencaoService | None = None) -> None:
        self.service = service or ManutencaoService()
        self.router = APIRouter(prefix="/manutencao", tags=["manutencao"])
        self._register_routes()

    def _register_routes(self) -> None:
        self.router.post(
            "/tipos-maquina",
            response_model=TipoMaquinaReadSchema,
            name="create_tipo_maquina",
        )(self.create_tipo_maquina)
        self.router.get(
            "/tipos-maquina",
            response_model=list[TipoMaquinaReadSchema],
            name="list_tipos_maquina",
        )(self.list_tipos_maquina)
        self.router.get(
            "/tipos-maquina/{id_tipo_maquina}",
            response_model=TipoMaquinaReadSchema,
            name="get_tipo_maquina",
        )(self.get_tipo_maquina)
        self.router.put(
            "/tipos-maquina/{id_tipo_maquina}",
            response_model=TipoMaquinaReadSchema,
            name="update_tipo_maquina",
        )(self.update_tipo_maquina)
        self.router.delete(
            "/tipos-maquina/{id_tipo_maquina}",
            response_model=MessageResponse,
            name="delete_tipo_maquina",
        )(self.delete_tipo_maquina)

        self.router.post(
            "/maquinas",
            response_model=MaquinaReadSchema,
            name="create_maquina",
        )(self.create_maquina)
        self.router.get(
            "/maquinas",
            response_model=list[MaquinaReadSchema],
            name="list_maquinas",
        )(self.list_maquinas)
        self.router.get(
            "/maquinas/{id_maquina}",
            response_model=MaquinaReadSchema,
            name="get_maquina",
        )(self.get_maquina)
        self.router.put(
            "/maquinas/{id_maquina}",
            response_model=MaquinaReadSchema,
            name="update_maquina",
        )(self.update_maquina)
        self.router.delete(
            "/maquinas/{id_maquina}",
            response_model=MessageResponse,
            name="delete_maquina",
        )(self.delete_maquina)

        self.router.post(
            "/planos-manutencao",
            response_model=PlanoManutencaoDetalheSchema,
            name="create_plano_manutencao",
        )(self.create_plano_manutencao)
        self.router.get(
            "/planos-manutencao",
            response_model=list[PlanoManutencaoDetalheSchema],
            name="list_planos_manutencao",
        )(self.list_planos_manutencao)
        self.router.get(
            "/planos-manutencao/{id_plano}",
            response_model=PlanoManutencaoReadSchema,
            name="get_plano_manutencao",
        )(self.get_plano_manutencao)
        self.router.put(
            "/planos-manutencao/{id_plano}",
            response_model=PlanoManutencaoDetalheSchema,
            name="update_plano_manutencao",
        )(self.update_plano_manutencao)
        self.router.delete(
            "/planos-manutencao/{id_plano}",
            response_model=MessageResponse,
            name="delete_plano_manutencao",
        )(self.delete_plano_manutencao)

        self.router.post(
            "/ordens-servico",
            response_model=OrdemServicoReadSchema,
            name="create_ordem_servico",
        )(self.create_ordem_servico)
        self.router.get(
            "/ordens-servico",
            response_model=list[OrdemServicoDetalheSchema],
            name="list_ordens_servico",
        )(self.list_ordens_servico)
        self.router.get(
            "/ordens-servico/{id_ordem_servico}",
            response_model=OrdemServicoReadSchema,
            name="get_ordem_servico",
        )(self.get_ordem_servico)
        self.router.put(
            "/ordens-servico/{id_ordem_servico}",
            response_model=OrdemServicoReadSchema,
            name="update_ordem_servico",
        )(self.update_ordem_servico)
        self.router.post(
            "/ordens-servico/{id_ordem_servico}/concluir",
            response_model=OrdemServicoReadSchema,
            name="concluir_ordem_servico",
        )(self.concluir_ordem_servico)
        self.router.delete(
            "/ordens-servico/{id_ordem_servico}",
            response_model=MessageResponse,
            name="delete_ordem_servico",
        )(self.delete_ordem_servico)

        self.router.post(
            "/manutencoes/preventiva",
            response_model=ManutencaoPreventivaResponse,
            name="criar_manutencao_preventiva",
        )(self.criar_manutencao_preventiva)
        self.router.get(
            "/manutencoes/preventiva",
            response_model=list[ManutencaoPreventivaDetalheSchema],
            name="list_manutencoes_preventivas",
        )(self.list_manutencoes_preventivas)
        self.router.post(
            "/manutencoes/corretiva",
            response_model=ManutencaoCorretivaResponse,
            name="criar_manutencao_corretiva",
        )(self.criar_manutencao_corretiva)
        self.router.get(
            "/manutencoes/corretiva",
            response_model=list[ManutencaoCorretivaDetalheSchema],
            name="list_manutencoes_corretivas",
        )(self.list_manutencoes_corretivas)
        self.router.get(
            "/manutencoes/{id_manutencao}",
            response_model=ManutencaoReadSchema,
            name="get_manutencao",
        )(self.get_manutencao)
        self.router.post(
            "/manutencoes/{id_manutencao}/iniciar",
            response_model=ManutencaoReadSchema,
            name="iniciar_manutencao",
        )(self.iniciar_manutencao)
        self.router.post(
            "/manutencoes/{id_manutencao}/concluir",
            response_model=ManutencaoReadSchema,
            name="concluir_manutencao",
        )(self.concluir_manutencao)
        self.router.post(
            "/manutencoes/{id_manutencao}/cancelar",
            response_model=ManutencaoReadSchema,
            name="cancelar_manutencao",
        )(self.cancelar_manutencao)
        self.router.patch(
            "/manutencoes/{id_manutencao}/corretiva",
            response_model=ManutencaoCorretivaReadSchema,
            name="atualizar_manutencao_corretiva",
        )(self.atualizar_manutencao_corretiva)
        self.router.patch(
            "/manutencoes/{id_manutencao}/preventiva",
            response_model=ManutencaoPreventivaReadSchema,
            name="atualizar_manutencao_preventiva",
        )(self.atualizar_manutencao_preventiva)

    @staticmethod
    def _handle_errors(action: Callable[[], T]) -> T:
        try:
            return action()
        except ManutencaoNotFoundError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
        except ManutencaoValidationError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
        except ManutencaoConflictError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        except ManutencaoError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    def create_tipo_maquina(
        self,
        payload: TipoMaquinaCreateSchema,
    ) -> TipoMaquinaReadSchema:
        return self._handle_errors(lambda: self.service.create_tipo_maquina(payload))

    def list_tipos_maquina(self) -> list[TipoMaquinaReadSchema]:
        return self._handle_errors(lambda: self.service.list_tipos_maquina())

    def get_tipo_maquina(self, id_tipo_maquina: int) -> TipoMaquinaReadSchema:
        return self._handle_errors(
            lambda: self.service.get_tipo_maquina(id_tipo_maquina)
        )

    def update_tipo_maquina(
        self,
        id_tipo_maquina: int,
        payload: TipoMaquinaUpdateSchema,
    ) -> TipoMaquinaReadSchema:
        return self._handle_errors(
            lambda: self.service.update_tipo_maquina(id_tipo_maquina, payload)
        )

    def delete_tipo_maquina(self, id_tipo_maquina: int) -> MessageResponse:
        deleted = self._handle_errors(
            lambda: self.service.delete_tipo_maquina(id_tipo_maquina)
        )
        if not deleted:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Nao foi possivel excluir o tipo de maquina.",
            )
        return MessageResponse(message="Tipo de maquina excluido.")

    def create_maquina(self, payload: MaquinaCreateRequest) -> MaquinaReadSchema:
        return self._handle_errors(
            lambda: self.service.create_maquina(
                MaquinaCreateSchema.model_validate(payload.model_dump()),
                id_fazenda=payload.id_fazenda,
            )
        )

    def list_maquinas(
        self,
        id_tipo_maquina: int | None = Query(default=None),
        id_fazenda: int | None = Query(default=None),
        status: str | None = Query(default=None),
        nome: str | None = Query(default=None),
    ) -> list[MaquinaReadSchema]:
        filters = MaquinaFilters(
            id_tipo_maquina=id_tipo_maquina,
            id_fazenda=id_fazenda,
            status=status,
            nome=nome,
        )
        return self._handle_errors(lambda: self.service.list_maquinas(filters))

    def get_maquina(self, id_maquina: int) -> MaquinaReadSchema:
        return self._handle_errors(lambda: self.service.get_maquina(id_maquina))

    def update_maquina(
        self,
        id_maquina: int,
        payload: MaquinaUpdateSchema,
    ) -> MaquinaReadSchema:
        return self._handle_errors(
            lambda: self.service.update_maquina(id_maquina, payload)
        )

    def delete_maquina(self, id_maquina: int) -> MessageResponse:
        deleted = self._handle_errors(lambda: self.service.delete_maquina(id_maquina))
        if not deleted:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Nao foi possivel excluir a maquina.",
            )
        return MessageResponse(message="Maquina excluida.")

    def create_plano_manutencao(
        self,
        payload: PlanoManutencaoCreateSchema,
    ) -> PlanoManutencaoDetalheSchema:
        return self._handle_errors(lambda: self.service.create_plano(payload))

    def list_planos_manutencao(
        self,
        id_maquina: int | None = Query(default=None),
    ) -> list[PlanoManutencaoDetalheSchema]:
        return self._handle_errors(
            lambda: self.service.list_planos(id_maquina=id_maquina)
        )

    def get_plano_manutencao(self, id_plano: int) -> PlanoManutencaoReadSchema:
        return self._handle_errors(lambda: self.service.get_plano(id_plano))

    def update_plano_manutencao(
        self,
        id_plano: int,
        payload: PlanoManutencaoUpdateSchema,
    ) -> PlanoManutencaoDetalheSchema:
        return self._handle_errors(
            lambda: self.service.update_plano(id_plano, payload)
        )

    def delete_plano_manutencao(self, id_plano: int) -> MessageResponse:
        deleted = self._handle_errors(lambda: self.service.delete_plano(id_plano))
        if not deleted:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Nao foi possivel excluir o plano de manutencao.",
            )
        return MessageResponse(message="Plano de manutencao excluido.")

    def create_ordem_servico(
        self,
        payload: OrdemServicoCreateSchema,
    ) -> OrdemServicoReadSchema:
        return self._handle_errors(lambda: self.service.create_ordem_servico(payload))

    def list_ordens_servico(
        self,
        id_manutencao: int | None = Query(default=None),
        id_maquina: int | None = Query(default=None),
        status: str | None = Query(default=None),
    ) -> list[OrdemServicoDetalheSchema]:
        filters = OrdemServicoFilters(
            id_manutencao=id_manutencao,
            id_maquina=id_maquina,
            status=status,
        )
        return self._handle_errors(lambda: self.service.list_ordens_servico(filters))

    def get_ordem_servico(self, id_ordem_servico: int) -> OrdemServicoReadSchema:
        return self._handle_errors(
            lambda: self.service.get_ordem_servico(id_ordem_servico)
        )

    def update_ordem_servico(
        self,
        id_ordem_servico: int,
        payload: OrdemServicoUpdateSchema,
    ) -> OrdemServicoReadSchema:
        return self._handle_errors(
            lambda: self.service.update_ordem_servico(id_ordem_servico, payload)
        )

    def concluir_ordem_servico(self, id_ordem_servico: int) -> OrdemServicoReadSchema:
        return self._handle_errors(
            lambda: self.service.concluir_ordem_servico(id_ordem_servico)
        )

    def delete_ordem_servico(self, id_ordem_servico: int) -> MessageResponse:
        deleted = self._handle_errors(
            lambda: self.service.delete_ordem_servico(id_ordem_servico)
        )
        if not deleted:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Nao foi possivel excluir a ordem de servico.",
            )
        return MessageResponse(message="Ordem de servico excluida.")

    def criar_manutencao_preventiva(
        self,
        payload: ManutencaoPreventivaCreateRequest,
    ) -> ManutencaoPreventivaResponse:
        def _create() -> ManutencaoPreventivaResponse:
            data = payload.model_dump()
            id_plano = data.pop("id_plano")
            hodometro_execucao = data.pop("hodometro_execucao")
            proxima_hodometro = data.pop("proxima_hodometro")
            result = self.service.criar_manutencao_preventiva(
                ManutencaoCreateSchema.model_validate(data),
                id_plano=id_plano,
                hodometro_execucao=hodometro_execucao,
                proxima_hodometro=proxima_hodometro,
            )
            return ManutencaoPreventivaResponse(
                manutencao=result.manutencao,
                preventiva=result.preventiva,
            )

        return self._handle_errors(_create)

    def criar_manutencao_corretiva(
        self,
        payload: ManutencaoCorretivaCreateRequest,
    ) -> ManutencaoCorretivaResponse:
        def _create() -> ManutencaoCorretivaResponse:
            data = payload.model_dump()
            defeito_relatado = data.pop("defeito_relatado")
            causa_raiz = data.pop("causa_raiz")
            solucao_aplicada = data.pop("solucao_aplicada")
            result = self.service.criar_manutencao_corretiva(
                ManutencaoCreateSchema.model_validate(data),
                defeito_relatado=defeito_relatado,
                causa_raiz=causa_raiz,
                solucao_aplicada=solucao_aplicada,
            )
            return ManutencaoCorretivaResponse(
                manutencao=result.manutencao,
                corretiva=result.corretiva,
            )

        return self._handle_errors(_create)

    def list_manutencoes_preventivas(
        self,
        id_maquina: int | None = Query(default=None),
        id_plano: int | None = Query(default=None),
        status: str | None = Query(default=None),
    ) -> list[ManutencaoPreventivaDetalheSchema]:
        return self._handle_errors(
            lambda: self.service.list_manutencoes_preventivas(
                id_maquina=id_maquina,
                id_plano=id_plano,
                status=status,
            )
        )

    def list_manutencoes_corretivas(
        self,
        id_maquina: int | None = Query(default=None),
        status: str | None = Query(default=None),
    ) -> list[ManutencaoCorretivaDetalheSchema]:
        return self._handle_errors(
            lambda: self.service.list_manutencoes_corretivas(
                id_maquina=id_maquina,
                status=status,
            )
        )

    def get_manutencao(self, id_manutencao: int) -> ManutencaoReadSchema:
        return self._handle_errors(
            lambda: self.service.get_manutencao(id_manutencao)
        )

    def iniciar_manutencao(self, id_manutencao: int) -> ManutencaoReadSchema:
        return self._handle_errors(
            lambda: self.service.iniciar_manutencao(id_manutencao)
        )

    def concluir_manutencao(
        self,
        id_manutencao: int,
        payload: ConcluirManutencaoRequest,
    ) -> ManutencaoReadSchema:
        return self._handle_errors(
            lambda: self.service.concluir_manutencao(
                id_manutencao,
                custo=payload.custo,
                dt_fim=payload.dt_fim,
                proxima_execucao=payload.proxima_execucao,
            )
        )

    def cancelar_manutencao(self, id_manutencao: int) -> ManutencaoReadSchema:
        return self._handle_errors(
            lambda: self.service.cancelar_manutencao(id_manutencao)
        )

    def atualizar_manutencao_corretiva(
        self,
        id_manutencao: int,
        payload: ManutencaoCorretivaUpdateSchema,
    ) -> ManutencaoCorretivaReadSchema:
        return self._handle_errors(
            lambda: self.service.atualizar_manutencao_corretiva(id_manutencao, payload)
        )

    def atualizar_manutencao_preventiva(
        self,
        id_manutencao: int,
        payload: ManutencaoPreventivaUpdateSchema,
    ) -> ManutencaoPreventivaReadSchema:
        return self._handle_errors(
            lambda: self.service.atualizar_manutencao_preventiva(id_manutencao, payload)
        )


manutencao_controller = ManutencaoController()
router = manutencao_controller.router
