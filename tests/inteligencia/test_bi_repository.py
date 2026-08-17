"""Testes de integracao dos repositorios de BI (produtividade e fitossanidade)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.inteligencia.repository import FitossanidadeBiRepository, ProdutividadeRepository

pytestmark = pytest.mark.integration


class TestProdutividadeRepository:
    def test_listar_calcula_realizado_e_variacao(
        self,
        produtividade_repository: ProdutividadeRepository,
        cenario_bi: dict,
    ) -> None:
        itens = {
            i.id_talhao: i
            for i in produtividade_repository.listar(id_safra=cenario_bi["id_safra"])
        }

        talhao_a = itens[cenario_bi["id_talhao_a"]]
        assert talhao_a.area_hectares == Decimal("10.00")
        assert talhao_a.meta_produtividade == Decimal("100.00")
        assert talhao_a.quantidade_colhida_total == Decimal("1000.00")
        assert talhao_a.produtividade_realizada == Decimal("100.00")
        assert talhao_a.variacao_percentual == Decimal("0.00")
        assert talhao_a.cultura_nome == cenario_bi["cultura_nome"]
        assert talhao_a.safra_ano == cenario_bi["safra_ano"]

        talhao_b = itens[cenario_bi["id_talhao_b"]]
        assert talhao_b.area_hectares == Decimal("20.00")
        assert talhao_b.meta_produtividade == Decimal("200.00")
        assert talhao_b.quantidade_colhida_total == Decimal("3000.00")
        assert talhao_b.produtividade_realizada == Decimal("150.00")
        assert talhao_b.variacao_percentual == Decimal("-25.00")

    def test_listar_filtra_por_talhao(
        self,
        produtividade_repository: ProdutividadeRepository,
        cenario_bi: dict,
    ) -> None:
        itens = produtividade_repository.listar(id_talhao=cenario_bi["id_talhao_a"])

        assert len(itens) == 1
        assert itens[0].id_talhao == cenario_bi["id_talhao_a"]

    def test_listar_sem_colheita_nao_calcula_realizado(
        self,
        produtividade_repository: ProdutividadeRepository,
        cenario_bi: dict,
        db_engine,
    ) -> None:
        from sqlalchemy import text

        with db_engine.begin() as conn:
            conn.execute(text("DELETE FROM colheita"))

        itens = {
            i.id_talhao: i
            for i in produtividade_repository.listar(id_safra=cenario_bi["id_safra"])
        }

        assert itens[cenario_bi["id_talhao_a"]].quantidade_colhida_total is None
        assert itens[cenario_bi["id_talhao_a"]].produtividade_realizada is None
        assert itens[cenario_bi["id_talhao_a"]].variacao_percentual is None


class TestFitossanidadeBiRepository:
    def test_custos_por_talhao(
        self,
        fitossanidade_bi_repository: FitossanidadeBiRepository,
        cenario_bi: dict,
    ) -> None:
        itens = {
            i.id_talhao: i
            for i in fitossanidade_bi_repository.custos_por_talhao(
                id_safra=cenario_bi["id_safra"]
            )
        }

        talhao_a = itens[cenario_bi["id_talhao_a"]]
        assert talhao_a.total_aplicacoes == 1
        assert talhao_a.custo_total == Decimal("500.00")

        talhao_b = itens[cenario_bi["id_talhao_b"]]
        assert talhao_b.total_aplicacoes == 0
        assert talhao_b.custo_total == Decimal("0")

    def test_custos_filtra_por_talhao(
        self,
        fitossanidade_bi_repository: FitossanidadeBiRepository,
        cenario_bi: dict,
    ) -> None:
        itens = fitossanidade_bi_repository.custos_por_talhao(
            id_talhao=cenario_bi["id_talhao_b"]
        )

        assert len(itens) == 1
        assert itens[0].id_talhao == cenario_bi["id_talhao_b"]
        assert itens[0].custo_total == Decimal("0")

    def test_ocorrencias_por_severidade(
        self,
        fitossanidade_bi_repository: FitossanidadeBiRepository,
        cenario_bi: dict,
    ) -> None:
        itens = fitossanidade_bi_repository.ocorrencias_por_severidade(
            id_safra=cenario_bi["id_safra"]
        )

        assert len(itens) == 1
        ocorrencia = itens[0]
        assert ocorrencia.id_talhao == cenario_bi["id_talhao_a"]
        assert ocorrencia.nivel_severidade == "Alto"
        assert ocorrencia.total_ocorrencias == 1

    def test_ocorrencias_talhao_sem_registro_fica_vazio(
        self,
        fitossanidade_bi_repository: FitossanidadeBiRepository,
        cenario_bi: dict,
    ) -> None:
        itens = fitossanidade_bi_repository.ocorrencias_por_severidade(
            id_talhao=cenario_bi["id_talhao_b"]
        )

        assert itens == []
