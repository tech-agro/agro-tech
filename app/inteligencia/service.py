"""Regras de negocio do dominio inteligencia."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import text

from app.core.database import get_session
from app.inteligencia.errors import (
    InteligenciaConflictError,
    InteligenciaNotFoundError,
    InteligenciaValidationError,
)
from app.integrations.agrodoc import AgroDocClient
from app.integrations.open_meteo import OpenMeteoClient
from app.integrations.schemas import MarketPriceData, WeatherData
from app.inteligencia.repository import (
    IndicadorFilters,
    IndicadorRepository,
    MedicaoIndicadorFilters,
    MedicaoIndicadorRepository,
)
from app.inteligencia.schemas import (
    IndicadorAgregacaoSchema,
    IndicadorCreateSchema,
    IndicadorReadSchema,
    IndicadorUpdateSchema,
    MedicaoIndicadorCreateSchema,
    MedicaoIndicadorReadSchema,
    MedicaoIndicadorUpdateSchema,
)


class InteligenciaService:
    """Orquestra indicadores, medicoes e agregacoes basicas."""

    def __init__(
        self,
        indicador_repo: IndicadorRepository | None = None,
        medicao_repo: MedicaoIndicadorRepository | None = None,
    ) -> None:
        self.indicador_repo = indicador_repo or IndicadorRepository()
        self.medicao_repo = medicao_repo or MedicaoIndicadorRepository()

    # --- Indicadores ---

    def criar_indicador(self, payload: IndicadorCreateSchema) -> IndicadorReadSchema:
        nome = payload.nome.strip()
        if self.indicador_repo.get_by_nome(nome) is not None:
            raise InteligenciaConflictError(f"Indicador '{nome}' ja cadastrado.")
        return self.indicador_repo.create_indicador(
            payload.model_copy(update={"nome": nome})
        )

    def obter_indicador(self, id_indicador: int) -> IndicadorReadSchema:
        indicador = self.indicador_repo.get_indicador(id_indicador)
        if indicador is None:
            raise InteligenciaNotFoundError(f"Indicador {id_indicador} nao encontrado.")
        return indicador

    def listar_indicadores(
        self,
        filters: IndicadorFilters | None = None,
    ) -> list[IndicadorReadSchema]:
        return self.indicador_repo.list_indicadores(filters)

    def atualizar_indicador(
        self,
        id_indicador: int,
        payload: IndicadorUpdateSchema,
    ) -> IndicadorReadSchema:
        if not self.indicador_repo.exists(id_indicador):
            raise InteligenciaNotFoundError(f"Indicador {id_indicador} nao encontrado.")

        dados = payload.model_dump(exclude_unset=True)
        if "nome" in dados and dados["nome"] is not None:
            nome = dados["nome"].strip()
            existente = self.indicador_repo.get_by_nome(nome)
            if existente is not None and existente.id_indicador != id_indicador:
                raise InteligenciaConflictError(f"Indicador '{nome}' ja cadastrado.")
            payload = payload.model_copy(update={"nome": nome})

        indicador = self.indicador_repo.update_indicador(id_indicador, payload)
        if indicador is None:
            raise InteligenciaNotFoundError(f"Indicador {id_indicador} nao encontrado.")
        return indicador

    def excluir_indicador(self, id_indicador: int) -> None:
        if not self.indicador_repo.exists(id_indicador):
            raise InteligenciaNotFoundError(f"Indicador {id_indicador} nao encontrado.")
        if self.indicador_repo.count_medicoes(id_indicador) > 0:
            raise InteligenciaConflictError(
                "Indicador possui medicoes registradas e nao pode ser excluido."
            )
        if not self.indicador_repo.delete_indicador(id_indicador):
            raise InteligenciaNotFoundError(f"Indicador {id_indicador} nao encontrado.")

    # --- Medicoes ---

    def registrar_medicao(
        self,
        payload: MedicaoIndicadorCreateSchema,
    ) -> MedicaoIndicadorReadSchema:
        self._validar_medicao(
            id_indicador=payload.id_indicador,
            id_safra=payload.id_safra,
            valor=payload.valor,
            data_referencia=payload.data_referencia,
        )
        data_referencia = payload.data_referencia or date.today()
        if self.medicao_repo.exists_medicao_duplicada(
            id_indicador=payload.id_indicador,
            id_safra=payload.id_safra,
            data_referencia=data_referencia,
        ):
            raise InteligenciaConflictError(
                "Ja existe medicao para este indicador, safra e data de referencia."
            )
        return self.medicao_repo.create_medicao(
            payload.model_copy(update={"data_referencia": data_referencia})
        )

    def obter_medicao(self, id_medicao: int) -> MedicaoIndicadorReadSchema:
        medicao = self.medicao_repo.get_medicao(id_medicao)
        if medicao is None:
            raise InteligenciaNotFoundError(f"Medicao {id_medicao} nao encontrada.")
        return medicao

    def listar_medicoes(
        self,
        filters: MedicaoIndicadorFilters | None = None,
    ) -> list[MedicaoIndicadorReadSchema]:
        if filters is not None:
            self._validar_periodo(filters.data_inicio, filters.data_fim)
        return self.medicao_repo.list_medicoes(filters)

    def atualizar_medicao(
        self,
        id_medicao: int,
        payload: MedicaoIndicadorUpdateSchema,
    ) -> MedicaoIndicadorReadSchema:
        atual = self.medicao_repo.get_medicao(id_medicao)
        if atual is None:
            raise InteligenciaNotFoundError(f"Medicao {id_medicao} nao encontrada.")

        id_indicador = (
            payload.id_indicador
            if payload.id_indicador is not None
            else atual.id_indicador
        )
        id_safra = payload.id_safra if payload.id_safra is not None else atual.id_safra
        dados = payload.model_dump(exclude_unset=True)
        valor = dados.get("valor", atual.valor)
        data_referencia = (
            payload.data_referencia
            if payload.data_referencia is not None
            else atual.data_referencia
        )

        self._validar_medicao(
            id_indicador=id_indicador,
            id_safra=id_safra,
            valor=valor,
            data_referencia=data_referencia,
        )

        if data_referencia is not None and self.medicao_repo.exists_medicao_duplicada(
            id_indicador=id_indicador,
            id_safra=id_safra,
            data_referencia=data_referencia,
            exclude_id=id_medicao,
        ):
            raise InteligenciaConflictError(
                "Ja existe medicao para este indicador, safra e data de referencia."
            )

        medicao = self.medicao_repo.update_medicao(id_medicao, payload)
        if medicao is None:
            raise InteligenciaNotFoundError(f"Medicao {id_medicao} nao encontrada.")
        return medicao

    def excluir_medicao(self, id_medicao: int) -> None:
        if not self.medicao_repo.delete_medicao(id_medicao):
            raise InteligenciaNotFoundError(f"Medicao {id_medicao} nao encontrada.")

    # --- Agregacao ---

    def agregar_medicoes(
        self,
        id_indicador: int,
        *,
        id_safra: int | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
    ) -> IndicadorAgregacaoSchema:
        if not self.indicador_repo.exists(id_indicador):
            raise InteligenciaNotFoundError(f"Indicador {id_indicador} nao encontrado.")
        if id_safra is not None and not self.medicao_repo.exists_safra(id_safra):
            raise InteligenciaNotFoundError(f"Safra {id_safra} nao encontrada.")
        self._validar_periodo(data_inicio, data_fim)
        return self.medicao_repo.agregar_medicoes(
            id_indicador=id_indicador,
            id_safra=id_safra,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

    def _validar_medicao(
        self,
        *,
        id_indicador: int,
        id_safra: int,
        valor: object,
        data_referencia: date | None,
    ) -> None:
        if not self.indicador_repo.exists(id_indicador):
            raise InteligenciaNotFoundError(f"Indicador {id_indicador} nao encontrado.")
        if not self.medicao_repo.exists_safra(id_safra):
            raise InteligenciaNotFoundError(f"Safra {id_safra} nao encontrada.")
        if valor is None:
            raise InteligenciaValidationError("Informe o valor da medicao.")
        if data_referencia is not None and data_referencia > date.today():
            raise InteligenciaValidationError(
                "Data de referencia nao pode ser futura."
            )

    @staticmethod
    def _validar_periodo(data_inicio: date | None, data_fim: date | None) -> None:
        if (
            data_inicio is not None
            and data_fim is not None
            and data_fim < data_inicio
        ):
            raise InteligenciaValidationError(
                "data_fim deve ser maior ou igual a data_inicio."
            )

    def register_logistics_kpi(
        self,
        *,
        indicador_nome: str,
        valor: Decimal | float | int = 1,
        data_referencia: date | None = None,
        unidade: str | None = None,
    ) -> int | None:
        """Called by Logistics to record operational performance metrics."""
        with get_session() as session:
            row = session.execute(
                text("SELECT id_indicador FROM indicador WHERE nome = :nome LIMIT 1"),
                {"nome": indicador_nome},
            ).first()
            if row is None:
                row = session.execute(
                    text(
                        """
                        INSERT INTO indicador (nome, unidade)
                        VALUES (:nome, :unidade)
                        RETURNING id_indicador
                        """
                    ),
                    {"nome": indicador_nome, "unidade": unidade},
                ).first()
            id_indicador = int(row[0])
            med = session.execute(
                text(
                    """
                    INSERT INTO medicao_indicador (id_indicador, id_safra, valor, data_referencia)
                    VALUES (:id_indicador, NULL, :valor, :data_referencia)
                    RETURNING id_medicao
                    """
                ),
                {
                    "id_indicador": id_indicador,
                    "valor": Decimal(str(valor)),
                    "data_referencia": data_referencia or date.today(),
                },
            ).first()
            return int(med[0]) if med is not None else None

    def consultar_clima_atual(
        self,
        *,
        latitude: float,
        longitude: float,
        client: OpenMeteoClient | None = None,
    ) -> WeatherData:
        """Leitura ao vivo do clima (sem persistir), para widgets de dashboard."""
        return (client or OpenMeteoClient()).fetch(latitude, longitude)

    def register_weather_measurement(
        self,
        *,
        latitude: float,
        longitude: float,
        id_safra: int | None = None,
        data_referencia: date | None = None,
        client: OpenMeteoClient | None = None,
    ) -> list[int]:
        """Called by Producao/Fitossanidade to record weather indicators (Open-Meteo)."""
        weather = (client or OpenMeteoClient()).fetch(latitude, longitude)
        referencia = data_referencia or date.today()
        metrics = (
            ("Temperatura", weather.temperature_c, "C"),
            ("Umidade relativa", weather.humidity_pct, "%"),
            ("Precipitacao", weather.precipitation_mm, "mm"),
        )

        ids_medicao: list[int] = []
        with get_session() as session:
            for nome, valor, unidade in metrics:
                if valor is None:
                    continue
                row = session.execute(
                    text("SELECT id_indicador FROM indicador WHERE nome = :nome LIMIT 1"),
                    {"nome": nome},
                ).first()
                if row is None:
                    row = session.execute(
                        text(
                            """
                            INSERT INTO indicador (nome, unidade)
                            VALUES (:nome, :unidade)
                            RETURNING id_indicador
                            """
                        ),
                        {"nome": nome, "unidade": unidade},
                    ).first()
                id_indicador = int(row[0])
                med = session.execute(
                    text(
                        """
                        INSERT INTO medicao_indicador (id_indicador, id_safra, valor, data_referencia)
                        VALUES (:id_indicador, :id_safra, :valor, :data_referencia)
                        RETURNING id_medicao
                        """
                    ),
                    {
                        "id_indicador": id_indicador,
                        "id_safra": id_safra,
                        "valor": Decimal(str(valor)),
                        "data_referencia": referencia,
                    },
                ).first()
                if med is not None:
                    ids_medicao.append(int(med[0]))
        return ids_medicao

    def consultar_cotacao_atual(
        self,
        *,
        uf: str | None = None,
        client: AgroDocClient | None = None,
    ) -> list[MarketPriceData]:
        """Leitura ao vivo da cotacao (sem persistir), para widgets de dashboard."""
        return (client or AgroDocClient()).fetch(uf=uf)

    def register_market_price_measurement(
        self,
        *,
        uf: str | None = None,
        id_safra: int | None = None,
        data_referencia: date | None = None,
        client: AgroDocClient | None = None,
    ) -> list[int]:
        """Called by Comercial to record CEPEA market price indicators (AgroDoc)."""
        quotes = (client or AgroDocClient()).fetch(uf=uf)
        referencia = data_referencia or date.today()

        ids_medicao: list[int] = []
        with get_session() as session:
            for quote in quotes:
                row = session.execute(
                    text("SELECT id_indicador FROM indicador WHERE nome = :nome LIMIT 1"),
                    {"nome": quote.product},
                ).first()
                if row is None:
                    row = session.execute(
                        text(
                            """
                            INSERT INTO indicador (nome, unidade)
                            VALUES (:nome, :unidade)
                            RETURNING id_indicador
                            """
                        ),
                        {"nome": quote.product, "unidade": quote.unit},
                    ).first()
                id_indicador = int(row[0])
                med = session.execute(
                    text(
                        """
                        INSERT INTO medicao_indicador (id_indicador, id_safra, valor, data_referencia)
                        VALUES (:id_indicador, :id_safra, :valor, :data_referencia)
                        RETURNING id_medicao
                        """
                    ),
                    {
                        "id_indicador": id_indicador,
                        "id_safra": id_safra,
                        "valor": Decimal(str(quote.price)),
                        "data_referencia": referencia,
                    },
                ).first()
                if med is not None:
                    ids_medicao.append(int(med[0]))
        return ids_medicao

