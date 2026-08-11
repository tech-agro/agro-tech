from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from app.comercial.enum import StatusCliente, UnitSymbol
from app.core.enum import StatusCertificacao
from app.comercial.models import (
    CategoriaProdutoModel,
    CentroCustoOption,
    CertificacaoFazendaModel,
    CertificacaoModel,
    ClienteModel,
    ClienteOption,
    CotacaoGraoModel,
    GraoModel,
    InsumoModel,
    ItemVendaEntrada,
    ProdutoComercialModel,
    ProdutoModel,
    ProdutoOption,
    UnidadeMedidaModel,
    VendaComItens,
    VendaModel,
)
from app.comercial.repository import ComercialRepository
from app.core.database import pg_connector
from app.estoque.enum import StatusLote
from app.integrations.brasilapi import BrasilApiCnpjClient
from app.integrations.exceptions import (
    IntegrationHttpError,
    IntegrationNotFoundError,
    IntegrationValidationError,
)
from app.integrations.schemas import CompanyData

if TYPE_CHECKING:
    from app.estoque.service import EstoqueService
    from app.financeiro.service import FinanceiroService
    from app.logistica.service import LogisticsService

logger = logging.getLogger(__name__)


class ComercialService:
    """Camada de orquestracao das regras de negocio."""

    def __init__(
        self,
        repository: ComercialRepository | None = None,
        inventory_service: "EstoqueService | None" = None,
        financeiro_service: "FinanceiroService | None" = None,
        logistica_service: "LogisticsService | None" = None,
        brasilapi_client: BrasilApiCnpjClient | None = None,
    ) -> None:
        self.repository = repository or ComercialRepository(pg_connector, logger)
        self._inventory_service = inventory_service
        self._financeiro_service = financeiro_service
        self._logistica_service = logistica_service
        self._brasilapi_client = brasilapi_client

    def _brasilapi(self) -> BrasilApiCnpjClient:
        if self._brasilapi_client is None:
            self._brasilapi_client = BrasilApiCnpjClient()
        return self._brasilapi_client

    def _inventory(self) -> "EstoqueService":
        if self._inventory_service is None:
            from app.estoque.service import EstoqueService

            self._inventory_service = EstoqueService()
        return self._inventory_service

    def _financeiro(self) -> "FinanceiroService":
        if self._financeiro_service is None:
            from app.financeiro.service import FinanceiroService

            self._financeiro_service = FinanceiroService()
        return self._financeiro_service

    def _logistica(self) -> "LogisticsService":
        if self._logistica_service is None:
            from app.logistica.service import LogisticsService

            self._logistica_service = LogisticsService()
        return self._logistica_service

    # ------------------------------------------------------------------
    # CategoriaProduto
    # ------------------------------------------------------------------
    def create_categoria_produto(self, nome: str) -> CategoriaProdutoModel | None:
        return self.repository.create_categoria_produto(nome)

    def get_categoria_produto_by_id(self, id_categoria: int) -> CategoriaProdutoModel | None:
        return self.repository.get_categoria_produto_by_id(id_categoria)

    def list_categorias_produto(self, filters: dict | None = None) -> list[CategoriaProdutoModel]:
        return self.repository.list_categorias_produto(filters)

    def update_categoria_produto(self, id_categoria: int, nome: str | None = None) -> bool:
        return self.repository.update_categoria_produto(id_categoria, nome)

    def delete_categoria_produto(self, id_categoria: int) -> bool:
        return self.repository.delete_categoria_produto(id_categoria)

    # ------------------------------------------------------------------
    # UnidadeMedida
    # ------------------------------------------------------------------
    def create_unidade_medida(self, sigla: UnitSymbol, descricao: str) -> UnidadeMedidaModel | None:
        return self.repository.create_unidade_medida(sigla, descricao)

    def get_unidade_medida_by_id(self, id_unidade: int) -> UnidadeMedidaModel | None:
        return self.repository.get_unidade_medida_by_id(id_unidade)

    def list_unidades_medida(self, filters: dict | None = None) -> list[UnidadeMedidaModel]:
        return self.repository.list_unidades_medida(filters)

    def update_unidade_medida(self, id_unidade: int, descricao: str | None = None) -> bool:
        return self.repository.update_unidade_medida(id_unidade, descricao)

    def delete_unidade_medida(self, id_unidade: int) -> bool:
        return self.repository.delete_unidade_medida(id_unidade)

    # ------------------------------------------------------------------
    # Produto
    # ------------------------------------------------------------------
    def create_produto(
        self,
        id_categoria: int,
        id_unidade: int,
        nome: str,
        tipo: str | None = None,
        preco: Decimal | None = None,
    ) -> ProdutoModel | None:
        if self.repository.get_categoria_produto_by_id(id_categoria) is None:
            raise ValueError("Categoria de produto nao encontrada.")
        if self.repository.get_unidade_medida_by_id(id_unidade) is None:
            raise ValueError("Unidade de medida nao encontrada.")
        if preco is not None and preco < 0:
            raise ValueError("O preco do produto nao pode ser negativo.")
        return self.repository.create_produto(id_categoria, id_unidade, nome, tipo, preco)

    def get_produto_by_id(self, id_produto: int) -> ProdutoModel | None:
        return self.repository.get_produto_by_id(id_produto)

    def list_produtos(self, filters: dict | None = None) -> list[ProdutoModel]:
        return self.repository.list_produtos(filters)

    def update_produto(
        self, id_produto: int, nome: str | None = None, tipo: str | None = None, preco: Decimal | None = None
    ) -> bool:
        if preco is not None and preco < 0:
            raise ValueError("O preco do produto nao pode ser negativo.")
        return self.repository.update_produto(id_produto, nome, tipo, preco)

    def delete_produto(self, id_produto: int) -> bool:
        return self.repository.delete_produto(id_produto)

    # ------------------------------------------------------------------
    # ProdutoComercial / Grao / Insumo (detalhe 1:1 de Produto)
    # ------------------------------------------------------------------
    def upsert_produto_comercial(
        self,
        id_produto: int,
        codigo_comercial: str | None = None,
        marca: str | None = None,
        descricao_comercial: str | None = None,
    ) -> ProdutoComercialModel | None:
        if self.repository.get_produto_by_id(id_produto) is None:
            raise ValueError("Produto nao encontrado.")
        return self.repository.upsert_produto_comercial(id_produto, codigo_comercial, marca, descricao_comercial)

    def get_produto_comercial_by_produto(self, id_produto: int) -> ProdutoComercialModel | None:
        return self.repository.get_produto_comercial_by_produto(id_produto)

    def delete_produto_comercial(self, id_produto: int) -> bool:
        return self.repository.delete_produto_comercial(id_produto)

    def upsert_grao(
        self,
        id_produto: int,
        umidade_maxima: Decimal | None = None,
        impureza_maxima: Decimal | None = None,
        classificacao_tipo: str | None = None,
    ) -> GraoModel | None:
        if self.repository.get_produto_by_id(id_produto) is None:
            raise ValueError("Produto nao encontrado.")
        return self.repository.upsert_grao(id_produto, umidade_maxima, impureza_maxima, classificacao_tipo)

    def get_grao_by_produto(self, id_produto: int) -> GraoModel | None:
        return self.repository.get_grao_by_produto(id_produto)

    def delete_grao(self, id_produto: int) -> bool:
        return self.repository.delete_grao(id_produto)

    def create_cotacao_grao(self, id_produto: int, data_cotacao: date, preco: Decimal) -> CotacaoGraoModel | None:
        if self.repository.get_produto_by_id(id_produto) is None:
            raise ValueError("Produto nao encontrado.")
        if preco < 0:
            raise ValueError("O preco da cotacao nao pode ser negativo.")
        return self.repository.create_cotacao_grao(id_produto, data_cotacao, preco)

    def list_cotacoes_grao(self, filters: dict | None = None) -> list[CotacaoGraoModel]:
        return self.repository.list_cotacoes_grao(filters)

    def delete_cotacao_grao(self, id_cotacao: int) -> bool:
        return self.repository.delete_cotacao_grao(id_cotacao)

    def upsert_insumo(
        self,
        id_produto: int,
        classe_agronomica: str | None = None,
        principio_ativo: str | None = None,
        periodo_carencia_dias: int | None = None,
        registro_mapa: str | None = None,
    ) -> InsumoModel | None:
        if self.repository.get_produto_by_id(id_produto) is None:
            raise ValueError("Produto nao encontrado.")
        return self.repository.upsert_insumo(
            id_produto, classe_agronomica, principio_ativo, periodo_carencia_dias, registro_mapa
        )

    def get_insumo_by_produto(self, id_produto: int) -> InsumoModel | None:
        return self.repository.get_insumo_by_produto(id_produto)

    def delete_insumo(self, id_produto: int) -> bool:
        return self.repository.delete_insumo(id_produto)

    # ------------------------------------------------------------------
    # Certificacao / CertificacaoFazenda
    # ------------------------------------------------------------------
    def create_certificacao(
        self, nome: str, orgao_emissor: str | None = None, tipo: str | None = None
    ) -> CertificacaoModel | None:
        return self.repository.create_certificacao(nome, orgao_emissor, tipo)

    def get_certificacao_by_id(self, id_certificacao: int) -> CertificacaoModel | None:
        return self.repository.get_certificacao_by_id(id_certificacao)

    def list_certificacoes(self, filters: dict | None = None) -> list[CertificacaoModel]:
        return self.repository.list_certificacoes(filters)

    def update_certificacao(
        self, id_certificacao: int, nome: str | None = None, orgao_emissor: str | None = None, tipo: str | None = None
    ) -> bool:
        return self.repository.update_certificacao(id_certificacao, nome, orgao_emissor, tipo)

    def delete_certificacao(self, id_certificacao: int) -> bool:
        return self.repository.delete_certificacao(id_certificacao)

    def create_certificacao_fazenda(
        self,
        id_certificacao: int,
        id_fazenda: int,
        status: StatusCertificacao,
        dt_emissao: date | None = None,
        dt_validade: date | None = None,
        numero_certificado: str | None = None,
    ) -> CertificacaoFazendaModel | None:
        if self.repository.get_certificacao_by_id(id_certificacao) is None:
            raise ValueError("Certificacao nao encontrada.")
        if dt_emissao is not None and dt_validade is not None and dt_validade < dt_emissao:
            raise ValueError("A data de validade nao pode ser anterior a data de emissao.")
        return self.repository.create_certificacao_fazenda(
            id_certificacao, id_fazenda, status, dt_emissao, dt_validade, numero_certificado
        )

    def get_certificacao_fazenda_by_id(self, id_cert_fazenda: int) -> CertificacaoFazendaModel | None:
        return self.repository.get_certificacao_fazenda_by_id(id_cert_fazenda)

    def list_certificacoes_fazenda(self, filters: dict | None = None) -> list[CertificacaoFazendaModel]:
        return self.repository.list_certificacoes_fazenda(filters)

    def update_status_certificacao_fazenda(self, id_cert_fazenda: int, status: StatusCertificacao) -> bool:
        atual = self.repository.get_certificacao_fazenda_by_id(id_cert_fazenda)
        if atual is None:
            return False
        return self.repository.update_status_certificacao_fazenda(id_cert_fazenda, status)

    def delete_certificacao_fazenda(self, id_cert_fazenda: int) -> bool:
        return self.repository.delete_certificacao_fazenda(id_cert_fazenda)

    # ------------------------------------------------------------------
    # Cliente
    # ------------------------------------------------------------------
    def create_cliente(
        self, nome: str, documento: str, status: StatusCliente = StatusCliente.ATIVO
    ) -> ClienteModel | None:
        return self.repository.create_cliente(nome, documento, status)

    def get_cliente_by_id(self, id_cliente: int) -> ClienteModel | None:
        return self.repository.get_cliente_by_id(id_cliente)

    def list_clientes(self) -> list[ClienteModel]:
        return self.repository.list_clientes()

    def update_status_cliente(self, id_cliente: int, status: StatusCliente) -> bool:
        if self.repository.get_cliente_by_id(id_cliente) is None:
            return False
        return self.repository.update_status_cliente(id_cliente, status)

    def delete_cliente(self, id_cliente: int) -> bool:
        return self.repository.delete_cliente(id_cliente)

    def lookup_empresa_por_cnpj(self, cnpj: str) -> CompanyData:
        """Busca dados de empresa no BrasilAPI para autocompletar cadastro de cliente."""
        try:
            return self._brasilapi().fetch(cnpj)
        except IntegrationNotFoundError as exc:
            raise ValueError(str(exc.message)) from exc
        except IntegrationValidationError as exc:
            raise ValueError(str(exc.message)) from exc
        except IntegrationHttpError as exc:
            raise ValueError(
                "Nao foi possivel consultar o CNPJ na BrasilAPI. Tente novamente."
            ) from exc

    # ------------------------------------------------------------------
    # Venda — fluxo central do modulo
    # ------------------------------------------------------------------
    def registrar_venda(
        self,
        id_cliente: int,
        id_centro_custo: int,
        itens: list[ItemVendaEntrada],
        data_venda: date | None = None,
    ) -> VendaComItens | None:
        """Registra uma venda: valida cliente, lotes e saldo, grava a venda e os
        itens, da baixa real no Estoque e aciona os indicadores/integracoes de
        Financeiro, Logistica e Inteligencia (placeholders ate esses modulos
        existirem)."""
        cliente = self.repository.get_cliente_by_id(id_cliente)
        if cliente is None:
            raise ValueError("Cliente nao encontrado.")
        if cliente.status != StatusCliente.ATIVO:
            raise ValueError("Cliente nao esta ativo para realizar vendas.")

        if not itens:
            raise ValueError("A venda precisa ter ao menos um item.")

        for item in itens:
            if item.quantidade <= 0:
                raise ValueError("A quantidade do item deve ser maior que zero.")
            if item.valor_unitario < 0:
                raise ValueError("O valor unitario do item nao pode ser negativo.")

            # Regra: produto sem rastreabilidade (sem lote) nao pode ser faturado.
            if item.id_lote is None:
                raise ValueError(
                    f"Produto {item.id_produto} sem rastreabilidade (lote) nao pode ser faturado."
                )

            lote = self.repository.get_lote_info(item.id_lote)
            if lote is None:
                raise ValueError(f"Lote {item.id_lote} nao encontrado.")
            if lote.id_produto != item.id_produto:
                raise ValueError(f"O lote {item.id_lote} nao pertence ao produto informado.")
            # Regra: somente lotes liberados podem ser vendidos.
            if lote.status != StatusLote.LIBERADO:
                raise ValueError(f"Lote {lote.codigo_lote} nao esta liberado para venda.")

            # Regra: saldo disponivel no estoque informado.
            saldo = self._inventory().get_saldo(item.id_estoque, item.id_produto)
            if saldo is None or saldo.quantidade_atual < item.quantidade:
                raise ValueError(
                    f"Saldo insuficiente para o produto {item.id_produto} no estoque {item.id_estoque}."
                )

        valor_total = sum((item.quantidade * item.valor_unitario for item in itens), Decimal("0"))

        # Venda + baixa de estoque numa unica transacao: se qualquer etapa
        # falhar, tudo e revertido — nunca fica venda confirmada sem estoque
        # debitado. O Financeiro roda apos o commit (sessao propria + FK).
        with pg_connector.pool.begin() as conn:
            resultado = self.repository.create_venda_com_itens(
                id_cliente=id_cliente,
                id_centro_custo=id_centro_custo,
                valor_total=valor_total,
                data_venda=data_venda,
                itens=[
                    {
                        "id_produto": item.id_produto,
                        "id_lote": item.id_lote,
                        "quantidade": item.quantidade,
                        "valor_unitario": item.valor_unitario,
                    }
                    for item in itens
                ],
                conn=conn,
            )
            if resultado is None:
                raise ValueError("Nao foi possivel registrar a venda.")

            venda, itens_criados = resultado

            # Baixa real no Estoque (unico modulo dependente ja implementado).
            for item_criado, item_entrada in zip(itens_criados, itens):
                self._inventory().registrar_saida_venda(
                    id_estoque=item_entrada.id_estoque,
                    id_produto=item_criado.id_produto,
                    id_item_venda=item_criado.id_item_venda,
                    quantidade=item_criado.quantidade,
                    id_lote=item_criado.id_lote,
                    conn=conn,
                )

        # Financeiro e Logistica rodam apos o commit da venda: os hooks usam
        # sessao propria e precisam da venda ja persistida (FK).
        self._financeiro().receber_venda_confirmada(
            venda.id_venda,
            Decimal(str(venda.valor_total)),
            venda.data_venda,
        )

        # Logistica: ainda placeholder documentado (sem veiculo/rota definidos
        # no momento da venda) — roda so depois da venda confirmada de verdade,
        # como efeito posterior/eventual, nao como parte da transacao acima.
        self._logistica().receber_venda_confirmada(venda.id_venda)

        # Inteligencia (app/inteligencia) ja foi implementada de verdade, mas
        # como um modulo generico de indicadores (indicador/medicao_indicador),
        # sem hook especifico para venda: medicao_indicador nao tem FK para
        # venda, so para indicador+safra, e uma venda pode nao ter uma safra
        # unica e inequivoca (itens de lotes/safras diferentes). Nao ha,
        # portanto, um jeito nao-ambiguo de derivar essa atualizacao aqui.

        return VendaComItens(**venda.model_dump(), itens=itens_criados)

    def get_venda_by_id(self, id_venda: int) -> VendaComItens | None:
        venda = self.repository.get_venda_by_id(id_venda)
        if venda is None:
            return None
        itens = self.repository.list_itens_por_venda(id_venda)
        return VendaComItens(**venda.model_dump(), itens=itens)

    def list_vendas(self, filters: dict | None = None) -> list[VendaModel]:
        return self.repository.list_vendas(filters)

    # ------------------------------------------------------------------
    # Lookups (para preencher comboboxes/selects no frontend)
    # ------------------------------------------------------------------
    def list_produto_options(self) -> list[ProdutoOption]:
        return self.repository.list_produto_options()

    def list_cliente_options(self) -> list[ClienteOption]:
        return self.repository.list_cliente_options()

    def list_centro_custo_options(self) -> list[CentroCustoOption]:
        return self.repository.list_centro_custo_options()

    def create_centro_custo(self, nome: str) -> CentroCustoOption | None:
        return self.repository.create_centro_custo(nome)

    def delete_centro_custo(self, id_centro_custo: int) -> bool:
        return self.repository.delete_centro_custo(id_centro_custo)

    def list_lote_options(self):
        return self.repository.list_lote_options()
