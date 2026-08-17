"""Recebe requisicoes da interface para o dominio inteligencia."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.inteligencia.errors import (
    InteligenciaConflictError,
    InteligenciaError,
    InteligenciaNotFoundError,
    InteligenciaValidationError,
)
from app.inteligencia.repository import IndicadorFilters, MedicaoIndicadorFilters
from app.inteligencia.schemas import (
    ClimaSyncRequestSchema,
    ClimaSyncResponseSchema,
    CotacaoSyncRequestSchema,
    CotacaoSyncResponseSchema,
    CustoFitossanidadeTalhaoSchema,
    IndicadorAgregacaoSchema,
    IndicadorCreateSchema,
    IndicadorReadSchema,
    IndicadorUpdateSchema,
    MedicaoIndicadorCreateSchema,
    MedicaoIndicadorReadSchema,
    MedicaoIndicadorUpdateSchema,
    OcorrenciaFitossanidadeSchema,
    ProdutividadeTalhaoSchema,
)
from app.inteligencia.service import InteligenciaService
from app.integrations.exceptions import IntegrationError
from app.integrations.schemas import MarketPriceData, WeatherData


class InteligenciaController:
    """Adaptador entre interface HTTP (FastAPI) e service."""

    def __init__(self, service: InteligenciaService | None = None) -> None:
        self.service = service or InteligenciaService()
        self.router = APIRouter(prefix="/inteligencia", tags=["inteligencia"])
        self._register_routes()

    @staticmethod
    def _map_error(exc: InteligenciaError) -> HTTPException:
        if isinstance(exc, InteligenciaNotFoundError):
            return HTTPException(status.HTTP_404_NOT_FOUND, exc.message)
        if isinstance(exc, InteligenciaConflictError):
            return HTTPException(status.HTTP_409_CONFLICT, exc.message)
        if isinstance(exc, InteligenciaValidationError):
            return HTTPException(status.HTTP_400_BAD_REQUEST, exc.message)
        return HTTPException(status.HTTP_400_BAD_REQUEST, exc.message)

    def _register_routes(self) -> None:
        self.router.post("/indicadores", response_model=IndicadorReadSchema)(
            self.create_indicador
        )
        self.router.get("/indicadores", response_model=list[IndicadorReadSchema])(
            self.list_indicadores
        )
        self.router.get(
            "/indicadores/{id_indicador}",
            response_model=IndicadorReadSchema,
        )(self.get_indicador)
        self.router.patch(
            "/indicadores/{id_indicador}",
            response_model=IndicadorReadSchema,
        )(self.update_indicador)
        self.router.delete(
            "/indicadores/{id_indicador}",
            status_code=status.HTTP_204_NO_CONTENT,
        )(self.delete_indicador)
        self.router.get(
            "/indicadores/{id_indicador}/agregacao",
            response_model=IndicadorAgregacaoSchema,
        )(self.agregar_medicoes)
        self.router.post(
            "/indicadores/clima/sync",
            response_model=ClimaSyncResponseSchema,
        )(self.sync_clima)
        self.router.get(
            "/indicadores/clima/atual",
            response_model=WeatherData,
        )(self.clima_atual)
        self.router.get(
            "/indicadores/cotacao/atual",
            response_model=list[MarketPriceData],
        )(self.cotacao_atual)
        self.router.post(
            "/indicadores/cotacao/sync",
            response_model=CotacaoSyncResponseSchema,
        )(self.sync_cotacao)

        self.router.get(
            "/produtividade",
            response_model=list[ProdutividadeTalhaoSchema],
        )(self.listar_produtividade)
        self.router.get(
            "/fitossanidade/custos",
            response_model=list[CustoFitossanidadeTalhaoSchema],
        )(self.listar_custos_fitossanidade)
        self.router.get(
            "/fitossanidade/ocorrencias",
            response_model=list[OcorrenciaFitossanidadeSchema],
        )(self.listar_ocorrencias_fitossanidade)

        self.router.post("/medicoes", response_model=MedicaoIndicadorReadSchema)(
            self.create_medicao
        )
        self.router.get("/medicoes", response_model=list[MedicaoIndicadorReadSchema])(
            self.list_medicoes
        )
        self.router.get(
            "/medicoes/{id_medicao}",
            response_model=MedicaoIndicadorReadSchema,
        )(self.get_medicao)
        self.router.patch(
            "/medicoes/{id_medicao}",
            response_model=MedicaoIndicadorReadSchema,
        )(self.update_medicao)
        self.router.delete(
            "/medicoes/{id_medicao}",
            status_code=status.HTTP_204_NO_CONTENT,
        )(self.delete_medicao)

    def create_indicador(self, payload: IndicadorCreateSchema) -> IndicadorReadSchema:
        try:
            return self.service.criar_indicador(payload)
        except InteligenciaError as exc:
            raise self._map_error(exc) from exc

    def list_indicadores(
        self,
        nome: str | None = Query(default=None),
        unidade: str | None = Query(default=None),
    ) -> list[IndicadorReadSchema]:
        filters = IndicadorFilters(nome=nome, unidade=unidade)
        return self.service.listar_indicadores(filters)

    def get_indicador(self, id_indicador: int) -> IndicadorReadSchema:
        try:
            return self.service.obter_indicador(id_indicador)
        except InteligenciaError as exc:
            raise self._map_error(exc) from exc

    def update_indicador(
        self,
        id_indicador: int,
        payload: IndicadorUpdateSchema,
    ) -> IndicadorReadSchema:
        try:
            return self.service.atualizar_indicador(id_indicador, payload)
        except InteligenciaError as exc:
            raise self._map_error(exc) from exc

    def delete_indicador(self, id_indicador: int) -> None:
        try:
            self.service.excluir_indicador(id_indicador)
        except InteligenciaError as exc:
            raise self._map_error(exc) from exc

    def agregar_medicoes(
        self,
        id_indicador: int,
        id_safra: int | None = Query(default=None),
        data_inicio: date | None = Query(default=None),
        data_fim: date | None = Query(default=None),
    ) -> IndicadorAgregacaoSchema:
        try:
            return self.service.agregar_medicoes(
                id_indicador,
                id_safra=id_safra,
                data_inicio=data_inicio,
                data_fim=data_fim,
            )
        except InteligenciaError as exc:
            raise self._map_error(exc) from exc

    def clima_atual(self, latitude: float, longitude: float) -> WeatherData:
        try:
            return self.service.consultar_clima_atual(latitude=latitude, longitude=longitude)
        except IntegrationError as exc:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, exc.message) from exc

    def sync_clima(self, payload: ClimaSyncRequestSchema) -> ClimaSyncResponseSchema:
        try:
            ids_medicao = self.service.register_weather_measurement(
                latitude=payload.latitude,
                longitude=payload.longitude,
                id_safra=payload.id_safra,
                data_referencia=payload.data_referencia,
            )
        except IntegrationError as exc:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, exc.message) from exc
        return ClimaSyncResponseSchema(ids_medicao=ids_medicao)

    def cotacao_atual(self, uf: str | None = Query(default=None)) -> list[MarketPriceData]:
        try:
            return self.service.consultar_cotacao_atual(uf=uf)
        except IntegrationError as exc:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, exc.message) from exc

    def sync_cotacao(self, payload: CotacaoSyncRequestSchema) -> CotacaoSyncResponseSchema:
        try:
            ids_medicao = self.service.register_market_price_measurement(
                uf=payload.uf,
                id_safra=payload.id_safra,
                data_referencia=payload.data_referencia,
            )
        except IntegrationError as exc:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, exc.message) from exc
        return CotacaoSyncResponseSchema(ids_medicao=ids_medicao)

    def create_medicao(
        self,
        payload: MedicaoIndicadorCreateSchema,
    ) -> MedicaoIndicadorReadSchema:
        try:
            return self.service.registrar_medicao(payload)
        except InteligenciaError as exc:
            raise self._map_error(exc) from exc

    def list_medicoes(
        self,
        id_indicador: int | None = Query(default=None),
        id_safra: int | None = Query(default=None),
        data_inicio: date | None = Query(default=None),
        data_fim: date | None = Query(default=None),
    ) -> list[MedicaoIndicadorReadSchema]:
        try:
            filters = MedicaoIndicadorFilters(
                id_indicador=id_indicador,
                id_safra=id_safra,
                data_inicio=data_inicio,
                data_fim=data_fim,
            )
            return self.service.listar_medicoes(filters)
        except InteligenciaError as exc:
            raise self._map_error(exc) from exc

    def get_medicao(self, id_medicao: int) -> MedicaoIndicadorReadSchema:
        try:
            return self.service.obter_medicao(id_medicao)
        except InteligenciaError as exc:
            raise self._map_error(exc) from exc

    def update_medicao(
        self,
        id_medicao: int,
        payload: MedicaoIndicadorUpdateSchema,
    ) -> MedicaoIndicadorReadSchema:
        try:
            return self.service.atualizar_medicao(id_medicao, payload)
        except InteligenciaError as exc:
            raise self._map_error(exc) from exc

    def delete_medicao(self, id_medicao: int) -> None:
        try:
            self.service.excluir_medicao(id_medicao)
        except InteligenciaError as exc:
            raise self._map_error(exc) from exc

    def listar_produtividade(
        self,
        id_safra: int | None = Query(default=None),
        id_talhao: int | None = Query(default=None),
    ) -> list[ProdutividadeTalhaoSchema]:
        try:
            return self.service.listar_produtividade(id_safra=id_safra, id_talhao=id_talhao)
        except InteligenciaError as exc:
            raise self._map_error(exc) from exc

    def listar_custos_fitossanidade(
        self,
        id_safra: int | None = Query(default=None),
        id_talhao: int | None = Query(default=None),
    ) -> list[CustoFitossanidadeTalhaoSchema]:
        try:
            return self.service.listar_custos_fitossanidade(
                id_safra=id_safra, id_talhao=id_talhao
            )
        except InteligenciaError as exc:
            raise self._map_error(exc) from exc

    def listar_ocorrencias_fitossanidade(
        self,
        id_safra: int | None = Query(default=None),
        id_talhao: int | None = Query(default=None),
    ) -> list[OcorrenciaFitossanidadeSchema]:
        try:
            return self.service.listar_ocorrencias_fitossanidade(
                id_safra=id_safra, id_talhao=id_talhao
            )
        except InteligenciaError as exc:
            raise self._map_error(exc) from exc


inteligencia_controller = InteligenciaController()
router = inteligencia_controller.router
