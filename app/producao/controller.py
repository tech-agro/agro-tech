"""Recebe requisicoes HTTP (FastAPI) e as encaminha para o service do dominio producao."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status

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
    NovaAdubacao,
    NovaAnaliseSolo,
    NovaAtividadeAgricola,
    NovaCondicaoClimatica,
    NovaCultura,
    NovaFazenda,
    NovaIrrigacao,
    NovaOperacaoAgricola,
    NovaOrdemProducao,
    NovaPulverizacao,
    NovaSafra,
    NovoMonitoramentoSafra,
    NovoParametroMonitoramento,
    NovoPlanejamentoSafra,
    NovoPlantio,
    NovoSolo,
    NovoTalhao,
    OperacaoAgricolaModel,
    OrdemProducaoModel,
    ParametroMonitoramentoModel,
    PlanejamentoSafraModel,
    PlantioModel,
    PulverizacaoModel,
    RegistroColheitaPlantio,
    SafraModel,
    SoloModel,
    TalhaoModel,
)
from app.producao.service import ProducaoService


class ProducaoController:
    """Adaptador entre a interface HTTP (FastAPI) e o service."""

    def __init__(self, service: ProducaoService | None = None) -> None:
        self.service = service or ProducaoService()
        self.router = APIRouter(prefix="/producao", tags=["producao"])
        self._register_routes()

    @staticmethod
    def _executar(fn, *args, **kwargs):
        """Traduz regra de negocio violada (ValueError) em 400."""
        try:
            return fn(*args, **kwargs)
        except ValueError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    @staticmethod
    def _filtros(**kwargs) -> dict:
        return {chave: valor for chave, valor in kwargs.items() if valor is not None}

    def _register_routes(self) -> None:
        # --- Fazenda ---
        self.router.get("/fazendas", response_model=list[FazendaModel])(self.list_fazendas)
        self.router.post("/fazendas", response_model=FazendaModel)(self.create_fazenda)
        self.router.get("/fazendas/{id_fazenda}", response_model=FazendaModel)(self.get_fazenda)
        self.router.patch("/fazendas/{id_fazenda}", response_model=FazendaModel)(self.update_fazenda)
        self.router.delete("/fazendas/{id_fazenda}")(self.delete_fazenda)

        # --- Talhao ---
        self.router.get("/talhoes", response_model=list[TalhaoModel])(self.list_talhoes)
        self.router.post("/talhoes", response_model=TalhaoModel)(self.create_talhao)
        self.router.get("/talhoes/{id_talhao}", response_model=TalhaoModel)(self.get_talhao)
        self.router.patch("/talhoes/{id_talhao}", response_model=TalhaoModel)(self.update_talhao)
        self.router.delete("/talhoes/{id_talhao}")(self.delete_talhao)

        # --- Solo ---
        self.router.get("/solos", response_model=list[SoloModel])(self.list_solos)
        self.router.post("/solos", response_model=SoloModel)(self.create_solo)
        self.router.get("/talhoes/{id_talhao}/solo", response_model=SoloModel)(self.get_solo_by_talhao)
        self.router.patch("/solos/{id_solo}")(self.update_solo)
        self.router.delete("/solos/{id_solo}")(self.delete_solo)

        # --- CondicaoClimatica ---
        self.router.get("/condicoes-climaticas", response_model=list[CondicaoClimaticaModel])(
            self.list_condicoes_climaticas
        )
        self.router.post("/condicoes-climaticas", response_model=CondicaoClimaticaModel)(
            self.create_condicao_climatica
        )
        self.router.get("/condicoes-climaticas/{id_condicao}", response_model=CondicaoClimaticaModel)(
            self.get_condicao_climatica
        )
        self.router.delete("/condicoes-climaticas/{id_condicao}")(self.delete_condicao_climatica)

        # --- Cultura ---
        self.router.get("/culturas", response_model=list[CulturaModel])(self.list_culturas)
        self.router.post("/culturas", response_model=CulturaModel)(self.create_cultura)
        self.router.get("/culturas/{id_cultura}", response_model=CulturaModel)(self.get_cultura)
        self.router.patch("/culturas/{id_cultura}", response_model=CulturaModel)(self.update_cultura)
        self.router.delete("/culturas/{id_cultura}")(self.delete_cultura)

        # --- Safra ---
        self.router.get("/safras", response_model=list[SafraModel])(self.list_safras)
        self.router.post("/safras", response_model=SafraModel)(self.create_safra)
        self.router.get("/safras/{id_safra}", response_model=SafraModel)(self.get_safra)
        self.router.patch("/safras/{id_safra}", response_model=SafraModel)(self.update_safra)
        self.router.post("/safras/{id_safra}/iniciar", response_model=SafraModel)(self.iniciar_safra)
        self.router.post("/safras/{id_safra}/finalizar", response_model=SafraModel)(self.finalizar_safra)
        self.router.post("/safras/{id_safra}/cancelar", response_model=SafraModel)(self.cancelar_safra)
        self.router.delete("/safras/{id_safra}")(self.delete_safra)

        # --- PlanejamentoSafra ---
        self.router.get("/planejamentos-safra", response_model=list[PlanejamentoSafraModel])(
            self.list_planejamentos_safra
        )
        self.router.post("/planejamentos-safra", response_model=PlanejamentoSafraModel)(
            self.create_planejamento_safra
        )
        self.router.get("/planejamentos-safra/{id_planejamento}", response_model=PlanejamentoSafraModel)(
            self.get_planejamento_safra
        )
        self.router.patch("/planejamentos-safra/{id_planejamento}", response_model=PlanejamentoSafraModel)(
            self.update_planejamento_safra
        )
        self.router.post(
            "/planejamentos-safra/{id_planejamento}/aprovar", response_model=PlanejamentoSafraModel
        )(self.aprovar_planejamento_safra)
        self.router.post(
            "/planejamentos-safra/{id_planejamento}/iniciar-execucao", response_model=PlanejamentoSafraModel
        )(self.iniciar_execucao_planejamento_safra)
        self.router.post(
            "/planejamentos-safra/{id_planejamento}/concluir", response_model=PlanejamentoSafraModel
        )(self.concluir_planejamento_safra)
        self.router.post(
            "/planejamentos-safra/{id_planejamento}/cancelar", response_model=PlanejamentoSafraModel
        )(self.cancelar_planejamento_safra)
        self.router.delete("/planejamentos-safra/{id_planejamento}")(self.delete_planejamento_safra)

        # --- AnaliseSolo ---
        self.router.get("/analises-solo", response_model=list[AnaliseSoloModel])(self.list_analises_solo)
        self.router.post("/analises-solo", response_model=AnaliseSoloModel)(self.create_analise_solo)
        self.router.get("/analises-solo/{id_analise}", response_model=AnaliseSoloModel)(self.get_analise_solo)
        self.router.delete("/analises-solo/{id_analise}")(self.delete_analise_solo)

        # --- MonitoramentoSafra ---
        self.router.get("/monitoramentos-safra", response_model=list[MonitoramentoSafraModel])(
            self.list_monitoramentos_safra
        )
        self.router.post("/monitoramentos-safra", response_model=MonitoramentoSafraModel)(
            self.create_monitoramento_safra
        )
        self.router.get("/monitoramentos-safra/{id_monitoramento}", response_model=MonitoramentoSafraModel)(
            self.get_monitoramento_safra
        )
        self.router.delete("/monitoramentos-safra/{id_monitoramento}")(self.delete_monitoramento_safra)

        # --- ParametroMonitoramento (aninhado em MonitoramentoSafra) ---
        self.router.get(
            "/monitoramentos-safra/{id_monitoramento}/parametros",
            response_model=list[ParametroMonitoramentoModel],
        )(self.list_parametros_monitoramento)
        self.router.post(
            "/monitoramentos-safra/{id_monitoramento}/parametros", response_model=ParametroMonitoramentoModel
        )(self.create_parametro_monitoramento)
        self.router.delete("/parametros-monitoramento/{id_parametro}")(self.delete_parametro_monitoramento)

        # --- OrdemProducao ---
        self.router.get("/ordens-producao", response_model=list[OrdemProducaoModel])(self.list_ordens_producao)
        self.router.post("/ordens-producao", response_model=OrdemProducaoModel)(self.create_ordem_producao)
        self.router.get("/ordens-producao/{id_ordem}", response_model=OrdemProducaoModel)(self.get_ordem_producao)
        self.router.post("/ordens-producao/{id_ordem}/iniciar", response_model=OrdemProducaoModel)(
            self.iniciar_ordem_producao
        )
        self.router.post("/ordens-producao/{id_ordem}/concluir", response_model=OrdemProducaoModel)(
            self.concluir_ordem_producao
        )
        self.router.post("/ordens-producao/{id_ordem}/cancelar", response_model=OrdemProducaoModel)(
            self.cancelar_ordem_producao
        )
        self.router.delete("/ordens-producao/{id_ordem}")(self.delete_ordem_producao)

        # --- Plantio ---
        self.router.get("/plantios", response_model=list[PlantioModel])(self.list_plantios)
        self.router.post("/plantios", response_model=PlantioModel)(self.create_plantio)
        self.router.get("/plantios/{id_plantio}", response_model=PlantioModel)(self.get_plantio)
        self.router.post("/plantios/{id_plantio}/iniciar", response_model=PlantioModel)(self.iniciar_plantio)
        self.router.post("/plantios/{id_plantio}/cancelar", response_model=PlantioModel)(self.cancelar_plantio)
        self.router.post("/plantios/{id_plantio}/colher", response_model=ColheitaModel)(self.colher_plantio)
        self.router.delete("/plantios/{id_plantio}")(self.delete_plantio)

        # --- OperacaoAgricola ---
        self.router.get("/operacoes-agricolas", response_model=list[OperacaoAgricolaModel])(
            self.list_operacoes_agricolas
        )
        self.router.post("/operacoes-agricolas", response_model=OperacaoAgricolaModel)(
            self.create_operacao_agricola
        )
        self.router.get("/operacoes-agricolas/{id_operacao}", response_model=OperacaoAgricolaModel)(
            self.get_operacao_agricola
        )
        self.router.post("/operacoes-agricolas/{id_operacao}/iniciar", response_model=OperacaoAgricolaModel)(
            self.iniciar_operacao_agricola
        )
        self.router.post("/operacoes-agricolas/{id_operacao}/concluir", response_model=OperacaoAgricolaModel)(
            self.concluir_operacao_agricola
        )
        self.router.post("/operacoes-agricolas/{id_operacao}/cancelar", response_model=OperacaoAgricolaModel)(
            self.cancelar_operacao_agricola
        )
        self.router.delete("/operacoes-agricolas/{id_operacao}")(self.delete_operacao_agricola)

        # --- AtividadeAgricola ---
        self.router.get("/atividades-agricolas", response_model=list[AtividadeAgricolaModel])(
            self.list_atividades_agricolas
        )
        self.router.post("/atividades-agricolas", response_model=AtividadeAgricolaModel)(
            self.create_atividade_agricola
        )
        self.router.get("/atividades-agricolas/{id_atividade}", response_model=AtividadeAgricolaModel)(
            self.get_atividade_agricola
        )
        self.router.post(
            "/atividades-agricolas/{id_atividade}/iniciar", response_model=AtividadeAgricolaModel
        )(self.iniciar_atividade_agricola)
        self.router.post(
            "/atividades-agricolas/{id_atividade}/concluir", response_model=AtividadeAgricolaModel
        )(self.concluir_atividade_agricola)
        self.router.post(
            "/atividades-agricolas/{id_atividade}/cancelar", response_model=AtividadeAgricolaModel
        )(self.cancelar_atividade_agricola)
        self.router.delete("/atividades-agricolas/{id_atividade}")(self.delete_atividade_agricola)

        # --- FuncionarioAtividade (tabela associativa) ---
        self.router.post("/atividades-agricolas/{id_atividade}/funcionarios/{id_funcionario}")(
            self.link_funcionario_atividade
        )
        self.router.delete("/atividades-agricolas/{id_atividade}/funcionarios/{id_funcionario}")(
            self.unlink_funcionario_atividade
        )
        self.router.get(
            "/atividades-agricolas/{id_atividade}/funcionarios",
            response_model=list[FuncionarioAtividadeModel],
        )(self.list_funcionarios_por_atividade)
        self.router.get(
            "/funcionarios/{id_funcionario}/atividades", response_model=list[FuncionarioAtividadeModel]
        )(self.list_atividades_por_funcionario)

        # --- Adubacao / Irrigacao / Pulverizacao (detalhe 1:1 de AtividadeAgricola) ---
        self.router.put("/atividades-agricolas/{id_atividade}/adubacao", response_model=AdubacaoModel)(
            self.upsert_adubacao
        )
        self.router.get("/atividades-agricolas/{id_atividade}/adubacao", response_model=AdubacaoModel)(
            self.get_adubacao
        )
        self.router.delete("/atividades-agricolas/{id_atividade}/adubacao")(self.delete_adubacao)

        self.router.put("/atividades-agricolas/{id_atividade}/irrigacao", response_model=IrrigacaoModel)(
            self.upsert_irrigacao
        )
        self.router.get("/atividades-agricolas/{id_atividade}/irrigacao", response_model=IrrigacaoModel)(
            self.get_irrigacao
        )
        self.router.delete("/atividades-agricolas/{id_atividade}/irrigacao")(self.delete_irrigacao)

        self.router.put(
            "/atividades-agricolas/{id_atividade}/pulverizacao", response_model=PulverizacaoModel
        )(self.upsert_pulverizacao)
        self.router.get(
            "/atividades-agricolas/{id_atividade}/pulverizacao", response_model=PulverizacaoModel
        )(self.get_pulverizacao)
        self.router.delete("/atividades-agricolas/{id_atividade}/pulverizacao")(self.delete_pulverizacao)

        # --- Colheita ---
        # Nao ha POST /colheitas generico: a colheita nasce da operacao
        # POST /plantios/{id_plantio}/colher, que ja fecha o plantio junto.
        self.router.get("/colheitas", response_model=list[ColheitaModel])(self.list_colheitas)
        self.router.get("/colheitas/{id_colheita}", response_model=ColheitaModel)(self.get_colheita)
        self.router.post("/colheitas/{id_colheita}/iniciar", response_model=ColheitaModel)(self.iniciar_colheita)
        self.router.post("/colheitas/{id_colheita}/concluir", response_model=ColheitaModel)(self.concluir_colheita)
        self.router.post("/colheitas/{id_colheita}/cancelar", response_model=ColheitaModel)(self.cancelar_colheita)
        self.router.delete("/colheitas/{id_colheita}")(self.delete_colheita)

    # ------------------------------------------------------------------
    # Fazenda
    # ------------------------------------------------------------------
    def create_fazenda(self, dados: NovaFazenda) -> FazendaModel:
        fazenda = self._executar(self.service.create_fazenda, dados.nome, dados.localizacao)
        if fazenda is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel criar a fazenda.")
        return fazenda

    def get_fazenda(self, id_fazenda: int) -> FazendaModel:
        fazenda = self.service.get_fazenda_by_id(id_fazenda)
        if fazenda is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Fazenda nao encontrada.")
        return fazenda

    def list_fazendas(self) -> list[FazendaModel]:
        return self.service.list_fazendas()

    def update_fazenda(self, id_fazenda: int, nome: str | None = None, localizacao: str | None = None) -> FazendaModel:
        if not self.service.update_fazenda(id_fazenda, nome, localizacao):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Fazenda nao encontrada.")
        return self.service.get_fazenda_by_id(id_fazenda)

    def delete_fazenda(self, id_fazenda: int) -> dict:
        if not self.service.delete_fazenda(id_fazenda):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Fazenda nao encontrada.")
        return {"message": "Fazenda removida."}

    # ------------------------------------------------------------------
    # Talhao
    # ------------------------------------------------------------------
    def create_talhao(self, dados: NovoTalhao) -> TalhaoModel:
        talhao = self._executar(
            self.service.create_talhao, dados.id_fazenda, dados.id_safra, dados.nome, dados.area_hectares
        )
        if talhao is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel criar o talhao.")
        return talhao

    def get_talhao(self, id_talhao: int) -> TalhaoModel:
        talhao = self.service.get_talhao_by_id(id_talhao)
        if talhao is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Talhao nao encontrado.")
        return talhao

    def list_talhoes(self, id_fazenda: int | None = None, id_safra: int | None = None) -> list[TalhaoModel]:
        return self.service.list_talhoes(self._filtros(id_fazenda=id_fazenda, id_safra=id_safra))

    def update_talhao(self, id_talhao: int, nome: str | None = None, area_hectares: Decimal | None = None) -> TalhaoModel:
        if not self._executar(self.service.update_talhao, id_talhao, nome, area_hectares):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Talhao nao encontrado.")
        return self.service.get_talhao_by_id(id_talhao)

    def delete_talhao(self, id_talhao: int) -> dict:
        if not self.service.delete_talhao(id_talhao):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Talhao nao encontrado.")
        return {"message": "Talhao removido."}

    # ------------------------------------------------------------------
    # Solo (1:1 com Talhao)
    # ------------------------------------------------------------------
    def create_solo(self, dados: NovoSolo) -> SoloModel:
        solo = self._executar(
            self.service.create_solo, dados.id_talhao, dados.tipo_solo, dados.textura, dados.profundidade_cm
        )
        if solo is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel criar o solo.")
        return solo

    def get_solo_by_talhao(self, id_talhao: int) -> SoloModel:
        solo = self.service.get_solo_by_talhao(id_talhao)
        if solo is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Solo nao encontrado.")
        return solo

    def list_solos(self, id_talhao: int | None = None) -> list[SoloModel]:
        return self.service.list_solos(self._filtros(id_talhao=id_talhao))

    def update_solo(
        self, id_solo: int, tipo_solo: str | None = None, textura: str | None = None, profundidade_cm: Decimal | None = None
    ) -> dict:
        # Repository nao expoe get-by-id proprio para Solo (so get_solo_by_talhao), entao
        # nao ha como reconsultar e devolver a entidade atualizada aqui.
        if not self.service.update_solo(id_solo, tipo_solo, textura, profundidade_cm):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Solo nao encontrado.")
        return {"message": "Solo atualizado."}

    def delete_solo(self, id_solo: int) -> dict:
        if not self.service.delete_solo(id_solo):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Solo nao encontrado.")
        return {"message": "Solo removido."}

    # ------------------------------------------------------------------
    # CondicaoClimatica
    # ------------------------------------------------------------------
    def create_condicao_climatica(self, dados: NovaCondicaoClimatica) -> CondicaoClimaticaModel:
        condicao = self._executar(
            self.service.create_condicao_climatica,
            dados.id_talhao,
            dados.dt_registro,
            dados.temperatura_min,
            dados.temperatura_max,
            dados.umidade_relativa,
            dados.precipitacao_mm,
            dados.velocidade_vento,
            dados.direcao_vento,
            dados.radiacao_solar,
        )
        if condicao is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel registrar a condicao climatica.")
        return condicao

    def get_condicao_climatica(self, id_condicao: int) -> CondicaoClimaticaModel:
        condicao = self.service.get_condicao_climatica_by_id(id_condicao)
        if condicao is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Condicao climatica nao encontrada.")
        return condicao

    def list_condicoes_climaticas(self, id_talhao: int | None = None) -> list[CondicaoClimaticaModel]:
        return self.service.list_condicoes_climaticas(self._filtros(id_talhao=id_talhao))

    def delete_condicao_climatica(self, id_condicao: int) -> dict:
        if not self.service.delete_condicao_climatica(id_condicao):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Condicao climatica nao encontrada.")
        return {"message": "Condicao climatica removida."}

    # ------------------------------------------------------------------
    # Cultura
    # ------------------------------------------------------------------
    def create_cultura(self, dados: NovaCultura) -> CulturaModel:
        cultura = self._executar(
            self.service.create_cultura,
            dados.nome,
            dados.nome_cientifico,
            dados.variedade,
            dados.ciclo_dias,
            dados.tipo_cultura,
        )
        if cultura is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel criar a cultura.")
        return cultura

    def get_cultura(self, id_cultura: int) -> CulturaModel:
        cultura = self.service.get_cultura_by_id(id_cultura)
        if cultura is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Cultura nao encontrada.")
        return cultura

    def list_culturas(self, nome: str | None = None, tipo_cultura: str | None = None) -> list[CulturaModel]:
        return self.service.list_culturas(self._filtros(nome=nome, tipo_cultura=tipo_cultura))

    def update_cultura(
        self,
        id_cultura: int,
        nome: str | None = None,
        nome_cientifico: str | None = None,
        variedade: str | None = None,
        ciclo_dias: int | None = None,
        tipo_cultura: str | None = None,
    ) -> CulturaModel:
        if not self.service.update_cultura(id_cultura, nome, nome_cientifico, variedade, ciclo_dias, tipo_cultura):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Cultura nao encontrada.")
        return self.service.get_cultura_by_id(id_cultura)

    def delete_cultura(self, id_cultura: int) -> dict:
        if not self.service.delete_cultura(id_cultura):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Cultura nao encontrada.")
        return {"message": "Cultura removida."}

    # ------------------------------------------------------------------
    # Safra
    # ------------------------------------------------------------------
    def create_safra(self, dados: NovaSafra) -> SafraModel:
        safra = self._executar(
            self.service.create_safra, dados.nome, dados.ano, dados.status, dados.dt_inicio, dados.dt_fim
        )
        if safra is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel criar a safra.")
        return safra

    def get_safra(self, id_safra: int) -> SafraModel:
        safra = self.service.get_safra_by_id(id_safra)
        if safra is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Safra nao encontrada.")
        return safra

    def list_safras(self, ano: int | None = None, status_safra: StatusSafra | None = None) -> list[SafraModel]:
        return self.service.list_safras(self._filtros(ano=ano, status=status_safra))

    def update_safra(
        self,
        id_safra: int,
        nome: str | None = None,
        ano: int | None = None,
        dt_inicio: date | None = None,
        dt_fim: date | None = None,
    ) -> SafraModel:
        if not self._executar(self.service.update_safra, id_safra, nome, ano, dt_inicio, dt_fim):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Safra nao encontrada.")
        return self.service.get_safra_by_id(id_safra)

    def iniciar_safra(self, id_safra: int) -> SafraModel:
        if not self._executar(self.service.iniciar_safra, id_safra):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Safra nao encontrada.")
        return self.service.get_safra_by_id(id_safra)

    def finalizar_safra(self, id_safra: int) -> SafraModel:
        if not self._executar(self.service.finalizar_safra, id_safra):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Safra nao encontrada.")
        return self.service.get_safra_by_id(id_safra)

    def cancelar_safra(self, id_safra: int) -> SafraModel:
        if not self._executar(self.service.cancelar_safra, id_safra):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Safra nao encontrada.")
        return self.service.get_safra_by_id(id_safra)

    def delete_safra(self, id_safra: int) -> dict:
        if not self.service.delete_safra(id_safra):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Safra nao encontrada.")
        return {"message": "Safra removida."}

    # ------------------------------------------------------------------
    # PlanejamentoSafra
    # ------------------------------------------------------------------
    def create_planejamento_safra(self, dados: NovoPlanejamentoSafra) -> PlanejamentoSafraModel:
        planejamento = self._executar(
            self.service.create_planejamento_safra,
            dados.id_safra,
            dados.id_talhao,
            dados.id_cultura,
            dados.status,
            dados.meta_produtividade,
            dados.area_planejada,
            dados.dt_plantio_previsto,
            dados.dt_colheita_previsto,
        )
        if planejamento is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel criar o planejamento de safra.")
        return planejamento

    def get_planejamento_safra(self, id_planejamento: int) -> PlanejamentoSafraModel:
        planejamento = self.service.get_planejamento_safra_by_id(id_planejamento)
        if planejamento is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Planejamento de safra nao encontrado.")
        return planejamento

    def list_planejamentos_safra(
        self,
        id_safra: int | None = None,
        id_talhao: int | None = None,
        id_cultura: int | None = None,
        status_planejamento: StatusPlanejamentoSafra | None = None,
    ) -> list[PlanejamentoSafraModel]:
        return self.service.list_planejamentos_safra(
            self._filtros(id_safra=id_safra, id_talhao=id_talhao, id_cultura=id_cultura, status=status_planejamento)
        )

    def update_planejamento_safra(
        self,
        id_planejamento: int,
        meta_produtividade: Decimal | None = None,
        area_planejada: Decimal | None = None,
        dt_plantio_previsto: date | None = None,
        dt_colheita_previsto: date | None = None,
    ) -> PlanejamentoSafraModel:
        atualizado = self._executar(
            self.service.update_planejamento_safra,
            id_planejamento,
            meta_produtividade,
            area_planejada,
            dt_plantio_previsto,
            dt_colheita_previsto,
        )
        if not atualizado:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Planejamento de safra nao encontrado.")
        return self.service.get_planejamento_safra_by_id(id_planejamento)

    def aprovar_planejamento_safra(self, id_planejamento: int) -> PlanejamentoSafraModel:
        if not self._executar(self.service.aprovar_planejamento_safra, id_planejamento):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Planejamento de safra nao encontrado.")
        return self.service.get_planejamento_safra_by_id(id_planejamento)

    def iniciar_execucao_planejamento_safra(self, id_planejamento: int) -> PlanejamentoSafraModel:
        if not self._executar(self.service.iniciar_execucao_planejamento_safra, id_planejamento):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Planejamento de safra nao encontrado.")
        return self.service.get_planejamento_safra_by_id(id_planejamento)

    def concluir_planejamento_safra(self, id_planejamento: int) -> PlanejamentoSafraModel:
        if not self._executar(self.service.concluir_planejamento_safra, id_planejamento):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Planejamento de safra nao encontrado.")
        return self.service.get_planejamento_safra_by_id(id_planejamento)

    def cancelar_planejamento_safra(self, id_planejamento: int) -> PlanejamentoSafraModel:
        if not self._executar(self.service.cancelar_planejamento_safra, id_planejamento):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Planejamento de safra nao encontrado.")
        return self.service.get_planejamento_safra_by_id(id_planejamento)

    def delete_planejamento_safra(self, id_planejamento: int) -> dict:
        if not self.service.delete_planejamento_safra(id_planejamento):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Planejamento de safra nao encontrado.")
        return {"message": "Planejamento de safra removido."}

    # ------------------------------------------------------------------
    # AnaliseSolo
    # ------------------------------------------------------------------
    def create_analise_solo(self, dados: NovaAnaliseSolo) -> AnaliseSoloModel:
        analise = self._executar(
            self.service.create_analise_solo,
            dados.id_solo,
            dados.id_safra,
            dados.id_funcionario,
            dados.dt_coleta,
            dados.dt_resultado,
            dados.ph,
            dados.materia_organica,
            dados.fosforo,
            dados.potassio,
            dados.calcio,
            dados.magnesio,
            dados.saturacao_bases,
            dados.observacao,
        )
        if analise is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel registrar a analise de solo.")
        return analise

    def get_analise_solo(self, id_analise: int) -> AnaliseSoloModel:
        analise = self.service.get_analise_solo_by_id(id_analise)
        if analise is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Analise de solo nao encontrada.")
        return analise

    def list_analises_solo(
        self, id_solo: int | None = None, id_safra: int | None = None, id_funcionario: int | None = None
    ) -> list[AnaliseSoloModel]:
        return self.service.list_analises_solo(
            self._filtros(id_solo=id_solo, id_safra=id_safra, id_funcionario=id_funcionario)
        )

    def delete_analise_solo(self, id_analise: int) -> dict:
        if not self.service.delete_analise_solo(id_analise):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Analise de solo nao encontrada.")
        return {"message": "Analise de solo removida."}

    # ------------------------------------------------------------------
    # MonitoramentoSafra
    # ------------------------------------------------------------------
    def create_monitoramento_safra(self, dados: NovoMonitoramentoSafra) -> MonitoramentoSafraModel:
        monitoramento = self._executar(
            self.service.create_monitoramento_safra,
            dados.id_safra,
            dados.id_talhao,
            dados.id_funcionario,
            dados.dt_monitoramento,
            dados.estagio_fenologico,
            dados.observacao,
        )
        if monitoramento is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel registrar o monitoramento de safra.")
        return monitoramento

    def get_monitoramento_safra(self, id_monitoramento: int) -> MonitoramentoSafraModel:
        monitoramento = self.service.get_monitoramento_safra_by_id(id_monitoramento)
        if monitoramento is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Monitoramento de safra nao encontrado.")
        return monitoramento

    def list_monitoramentos_safra(
        self, id_safra: int | None = None, id_talhao: int | None = None, id_funcionario: int | None = None
    ) -> list[MonitoramentoSafraModel]:
        return self.service.list_monitoramentos_safra(
            self._filtros(id_safra=id_safra, id_talhao=id_talhao, id_funcionario=id_funcionario)
        )

    def delete_monitoramento_safra(self, id_monitoramento: int) -> dict:
        if not self.service.delete_monitoramento_safra(id_monitoramento):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Monitoramento de safra nao encontrado.")
        return {"message": "Monitoramento de safra removido."}

    # ------------------------------------------------------------------
    # ParametroMonitoramento (aninhado em MonitoramentoSafra)
    # ------------------------------------------------------------------
    def create_parametro_monitoramento(
        self, id_monitoramento: int, dados: NovoParametroMonitoramento
    ) -> ParametroMonitoramentoModel:
        parametro = self._executar(
            self.service.create_parametro_monitoramento,
            id_monitoramento,
            dados.nome_parametro,
            dados.valor,
            dados.unidade,
        )
        if parametro is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel registrar o parametro.")
        return parametro

    def list_parametros_monitoramento(self, id_monitoramento: int) -> list[ParametroMonitoramentoModel]:
        return self.service.list_parametros_por_monitoramento(id_monitoramento)

    def delete_parametro_monitoramento(self, id_parametro: int) -> dict:
        if not self.service.delete_parametro_monitoramento(id_parametro):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Parametro de monitoramento nao encontrado.")
        return {"message": "Parametro de monitoramento removido."}

    # ------------------------------------------------------------------
    # OrdemProducao
    # ------------------------------------------------------------------
    def create_ordem_producao(self, dados: NovaOrdemProducao) -> OrdemProducaoModel:
        ordem = self._executar(
            self.service.create_ordem_producao, dados.id_safra, dados.status, dados.data_abertura
        )
        if ordem is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel criar a ordem de producao.")
        return ordem

    def get_ordem_producao(self, id_ordem: int) -> OrdemProducaoModel:
        ordem = self.service.get_ordem_producao_by_id(id_ordem)
        if ordem is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Ordem de producao nao encontrada.")
        return ordem

    def list_ordens_producao(
        self, id_safra: int | None = None, status_ordem: StatusOrdemProducao | None = None
    ) -> list[OrdemProducaoModel]:
        return self.service.list_ordens_producao(self._filtros(id_safra=id_safra, status=status_ordem))

    def iniciar_ordem_producao(self, id_ordem: int) -> OrdemProducaoModel:
        if not self._executar(self.service.iniciar_ordem_producao, id_ordem):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Ordem de producao nao encontrada.")
        return self.service.get_ordem_producao_by_id(id_ordem)

    def concluir_ordem_producao(self, id_ordem: int) -> OrdemProducaoModel:
        if not self._executar(self.service.concluir_ordem_producao, id_ordem):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Ordem de producao nao encontrada.")
        return self.service.get_ordem_producao_by_id(id_ordem)

    def cancelar_ordem_producao(self, id_ordem: int) -> OrdemProducaoModel:
        if not self._executar(self.service.cancelar_ordem_producao, id_ordem):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Ordem de producao nao encontrada.")
        return self.service.get_ordem_producao_by_id(id_ordem)

    def delete_ordem_producao(self, id_ordem: int) -> dict:
        if not self.service.delete_ordem_producao(id_ordem):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Ordem de producao nao encontrada.")
        return {"message": "Ordem de producao removida."}

    # ------------------------------------------------------------------
    # Plantio
    # ------------------------------------------------------------------
    def create_plantio(self, dados: NovoPlantio) -> PlantioModel:
        plantio = self._executar(
            self.service.create_plantio,
            dados.id_ordem,
            dados.id_talhao,
            dados.id_produto,
            dados.id_cultura,
            dados.id_planejamento,
            dados.status,
            dados.dt_plantio,
        )
        if plantio is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel criar o plantio.")
        return plantio

    def get_plantio(self, id_plantio: int) -> PlantioModel:
        plantio = self.service.get_plantio_by_id(id_plantio)
        if plantio is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Plantio nao encontrado.")
        return plantio

    def list_plantios(
        self,
        id_ordem: int | None = None,
        id_talhao: int | None = None,
        id_cultura: int | None = None,
        id_planejamento: int | None = None,
        status_plantio: StatusPlantio | None = None,
    ) -> list[PlantioModel]:
        return self.service.list_plantios(
            self._filtros(
                id_ordem=id_ordem,
                id_talhao=id_talhao,
                id_cultura=id_cultura,
                id_planejamento=id_planejamento,
                status=status_plantio,
            )
        )

    def iniciar_plantio(self, id_plantio: int) -> PlantioModel:
        if not self._executar(self.service.iniciar_plantio, id_plantio):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Plantio nao encontrado.")
        return self.service.get_plantio_by_id(id_plantio)

    def cancelar_plantio(self, id_plantio: int) -> PlantioModel:
        if not self._executar(self.service.cancelar_plantio, id_plantio):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Plantio nao encontrado.")
        return self.service.get_plantio_by_id(id_plantio)

    def colher_plantio(self, id_plantio: int, dados: RegistroColheitaPlantio) -> ColheitaModel:
        colheita = self._executar(
            self.service.colher_plantio, id_plantio, dados.quantidade_colhida, dados.dt_inicio, dados.dt_fim
        )
        if colheita is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel registrar a colheita.")
        return colheita

    def delete_plantio(self, id_plantio: int) -> dict:
        if not self.service.delete_plantio(id_plantio):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Plantio nao encontrado.")
        return {"message": "Plantio removido."}

    # ------------------------------------------------------------------
    # OperacaoAgricola
    # ------------------------------------------------------------------
    def create_operacao_agricola(self, dados: NovaOperacaoAgricola) -> OperacaoAgricolaModel:
        operacao = self._executar(
            self.service.create_operacao_agricola,
            dados.id_plantio,
            dados.id_funcionario,
            dados.status,
            dados.tipo_operacao,
            dados.descricao,
            dados.dt_inicio,
            dados.dt_fim,
        )
        if operacao is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel criar a operacao agricola.")
        return operacao

    def get_operacao_agricola(self, id_operacao: int) -> OperacaoAgricolaModel:
        operacao = self.service.get_operacao_agricola_by_id(id_operacao)
        if operacao is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Operacao agricola nao encontrada.")
        return operacao

    def list_operacoes_agricolas(
        self,
        id_plantio: int | None = None,
        id_funcionario: int | None = None,
        status_operacao: StatusOperacaoAgricola | None = None,
    ) -> list[OperacaoAgricolaModel]:
        return self.service.list_operacoes_agricolas(
            self._filtros(id_plantio=id_plantio, id_funcionario=id_funcionario, status=status_operacao)
        )

    def iniciar_operacao_agricola(self, id_operacao: int) -> OperacaoAgricolaModel:
        if not self._executar(self.service.iniciar_operacao_agricola, id_operacao):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Operacao agricola nao encontrada.")
        return self.service.get_operacao_agricola_by_id(id_operacao)

    def concluir_operacao_agricola(self, id_operacao: int) -> OperacaoAgricolaModel:
        if not self._executar(self.service.concluir_operacao_agricola, id_operacao):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Operacao agricola nao encontrada.")
        return self.service.get_operacao_agricola_by_id(id_operacao)

    def cancelar_operacao_agricola(self, id_operacao: int) -> OperacaoAgricolaModel:
        if not self._executar(self.service.cancelar_operacao_agricola, id_operacao):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Operacao agricola nao encontrada.")
        return self.service.get_operacao_agricola_by_id(id_operacao)

    def delete_operacao_agricola(self, id_operacao: int) -> dict:
        if not self.service.delete_operacao_agricola(id_operacao):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Operacao agricola nao encontrada.")
        return {"message": "Operacao agricola removida."}

    # ------------------------------------------------------------------
    # AtividadeAgricola
    # ------------------------------------------------------------------
    def create_atividade_agricola(self, dados: NovaAtividadeAgricola) -> AtividadeAgricolaModel:
        atividade = self._executar(
            self.service.create_atividade_agricola,
            dados.id_operacao,
            dados.status,
            dados.descricao,
            dados.dt_inicio,
            dados.dt_fim,
        )
        if atividade is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel criar a atividade agricola.")
        return atividade

    def get_atividade_agricola(self, id_atividade: int) -> AtividadeAgricolaModel:
        atividade = self.service.get_atividade_agricola_by_id(id_atividade)
        if atividade is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Atividade agricola nao encontrada.")
        return atividade

    def list_atividades_agricolas(
        self, id_operacao: int | None = None, status_atividade: StatusAtividadeAgricola | None = None
    ) -> list[AtividadeAgricolaModel]:
        return self.service.list_atividades_agricolas(
            self._filtros(id_operacao=id_operacao, status=status_atividade)
        )

    def iniciar_atividade_agricola(self, id_atividade: int) -> AtividadeAgricolaModel:
        if not self._executar(self.service.iniciar_atividade_agricola, id_atividade):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Atividade agricola nao encontrada.")
        return self.service.get_atividade_agricola_by_id(id_atividade)

    def concluir_atividade_agricola(self, id_atividade: int) -> AtividadeAgricolaModel:
        if not self._executar(self.service.concluir_atividade_agricola, id_atividade):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Atividade agricola nao encontrada.")
        return self.service.get_atividade_agricola_by_id(id_atividade)

    def cancelar_atividade_agricola(self, id_atividade: int) -> AtividadeAgricolaModel:
        if not self._executar(self.service.cancelar_atividade_agricola, id_atividade):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Atividade agricola nao encontrada.")
        return self.service.get_atividade_agricola_by_id(id_atividade)

    def delete_atividade_agricola(self, id_atividade: int) -> dict:
        if not self.service.delete_atividade_agricola(id_atividade):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Atividade agricola nao encontrada.")
        return {"message": "Atividade agricola removida."}

    # ------------------------------------------------------------------
    # FuncionarioAtividade (tabela associativa, PK composta)
    # ------------------------------------------------------------------
    def link_funcionario_atividade(self, id_atividade: int, id_funcionario: int) -> dict:
        if not self._executar(self.service.link_funcionario_atividade, id_funcionario, id_atividade):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel vincular o funcionario a atividade.")
        return {"message": "Funcionario vinculado a atividade."}

    def unlink_funcionario_atividade(self, id_atividade: int, id_funcionario: int) -> dict:
        if not self.service.unlink_funcionario_atividade(id_funcionario, id_atividade):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel desvincular o funcionario da atividade.")
        return {"message": "Funcionario desvinculado da atividade."}

    def list_funcionarios_por_atividade(self, id_atividade: int) -> list[FuncionarioAtividadeModel]:
        return self.service.list_funcionarios_por_atividade(id_atividade)

    def list_atividades_por_funcionario(self, id_funcionario: int) -> list[FuncionarioAtividadeModel]:
        return self.service.list_atividades_por_funcionario(id_funcionario)

    # ------------------------------------------------------------------
    # Adubacao (detalhe 1:1 de AtividadeAgricola, PK = FK)
    # ------------------------------------------------------------------
    def upsert_adubacao(self, id_atividade: int, dados: NovaAdubacao) -> AdubacaoModel:
        adubacao = self._executar(
            self.service.upsert_adubacao,
            id_atividade,
            dados.id_insumo,
            dados.tipo_adubacao,
            dados.dose_hectare,
            dados.metodo_aplicacao,
        )
        if adubacao is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel registrar a adubacao.")
        return adubacao

    def get_adubacao(self, id_atividade: int) -> AdubacaoModel:
        adubacao = self.service.get_adubacao_by_atividade(id_atividade)
        if adubacao is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Adubacao nao encontrada.")
        return adubacao

    def delete_adubacao(self, id_atividade: int) -> dict:
        if not self.service.delete_adubacao(id_atividade):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Adubacao nao encontrada.")
        return {"message": "Adubacao removida."}

    # ------------------------------------------------------------------
    # Irrigacao (detalhe 1:1 de AtividadeAgricola, PK = FK)
    # ------------------------------------------------------------------
    def upsert_irrigacao(self, id_atividade: int, dados: NovaIrrigacao) -> IrrigacaoModel:
        irrigacao = self._executar(
            self.service.upsert_irrigacao,
            id_atividade,
            dados.lamina_agua,
            dados.metodo_irrigacao,
            dados.duracao_horas,
        )
        if irrigacao is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel registrar a irrigacao.")
        return irrigacao

    def get_irrigacao(self, id_atividade: int) -> IrrigacaoModel:
        irrigacao = self.service.get_irrigacao_by_atividade(id_atividade)
        if irrigacao is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Irrigacao nao encontrada.")
        return irrigacao

    def delete_irrigacao(self, id_atividade: int) -> dict:
        if not self.service.delete_irrigacao(id_atividade):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Irrigacao nao encontrada.")
        return {"message": "Irrigacao removida."}

    # ------------------------------------------------------------------
    # Pulverizacao (detalhe 1:1 de AtividadeAgricola, PK = FK)
    # ------------------------------------------------------------------
    def upsert_pulverizacao(self, id_atividade: int, dados: NovaPulverizacao) -> PulverizacaoModel:
        pulverizacao = self._executar(
            self.service.upsert_pulverizacao, id_atividade, dados.id_insumo, dados.volume_calda, dados.vazao
        )
        if pulverizacao is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel registrar a pulverizacao.")
        return pulverizacao

    def get_pulverizacao(self, id_atividade: int) -> PulverizacaoModel:
        pulverizacao = self.service.get_pulverizacao_by_atividade(id_atividade)
        if pulverizacao is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Pulverizacao nao encontrada.")
        return pulverizacao

    def delete_pulverizacao(self, id_atividade: int) -> dict:
        if not self.service.delete_pulverizacao(id_atividade):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Pulverizacao nao encontrada.")
        return {"message": "Pulverizacao removida."}

    # ------------------------------------------------------------------
    # Colheita
    # ------------------------------------------------------------------
    def get_colheita(self, id_colheita: int) -> ColheitaModel:
        colheita = self.service.get_colheita_by_id(id_colheita)
        if colheita is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Colheita nao encontrada.")
        return colheita

    def list_colheitas(
        self, id_plantio: int | None = None, status_colheita: StatusColheita | None = None
    ) -> list[ColheitaModel]:
        return self.service.list_colheitas(self._filtros(id_plantio=id_plantio, status=status_colheita))

    def iniciar_colheita(self, id_colheita: int) -> ColheitaModel:
        if not self._executar(self.service.iniciar_colheita, id_colheita):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Colheita nao encontrada.")
        return self.service.get_colheita_by_id(id_colheita)

    def concluir_colheita(self, id_colheita: int) -> ColheitaModel:
        if not self._executar(self.service.concluir_colheita, id_colheita):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Colheita nao encontrada.")
        return self.service.get_colheita_by_id(id_colheita)

    def cancelar_colheita(self, id_colheita: int) -> ColheitaModel:
        if not self._executar(self.service.cancelar_colheita, id_colheita):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Colheita nao encontrada.")
        return self.service.get_colheita_by_id(id_colheita)

    def delete_colheita(self, id_colheita: int) -> dict:
        if not self.service.delete_colheita(id_colheita):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Colheita nao encontrada.")
        return {"message": "Colheita removida."}


producao_controller = ProducaoController()
router = producao_controller.router
