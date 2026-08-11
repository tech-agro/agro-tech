"""Recebe requisicoes HTTP (FastAPI) e as encaminha para o service do dominio comercial."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status

from app.comercial.enum import StatusCliente
from app.core.enum import StatusCertificacao
from app.estoque.errors import EstoqueError
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
    LoteOption,
    NovaCategoriaProduto,
    NovaCertificacao,
    NovaCertificacaoFazenda,
    NovaCotacaoGrao,
    NovaUnidadeMedida,
    NovaVenda,
    NovoCentroCusto,
    NovoCliente,
    NovoGrao,
    NovoInsumo,
    NovoProduto,
    NovoProdutoComercial,
    ProdutoComercialModel,
    ProdutoModel,
    ProdutoOption,
    UnidadeMedidaModel,
    VendaComItens,
    VendaModel,
)
from app.integrations.schemas import CompanyData
from app.comercial.service import ComercialService


class ComercialController:
    """Adaptador entre a interface HTTP (FastAPI) e o service."""

    def __init__(self, service: ComercialService | None = None) -> None:
        self.service = service or ComercialService()
        self.router = APIRouter(prefix="/comercial", tags=["comercial"])
        self._register_routes()

    @staticmethod
    def _executar(fn, *args, **kwargs):
        """Traduz regra de negocio violada (ValueError) ou erro de dominio de
        outro modulo (EstoqueError) em 400."""
        try:
            return fn(*args, **kwargs)
        except (ValueError, EstoqueError) as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    @staticmethod
    def _filtros(**kwargs) -> dict:
        return {chave: valor for chave, valor in kwargs.items() if valor is not None}

    def _register_routes(self) -> None:
        # --- CategoriaProduto ---
        self.router.get("/categorias-produto", response_model=list[CategoriaProdutoModel])(
            self.list_categorias_produto
        )
        self.router.post("/categorias-produto", response_model=CategoriaProdutoModel)(
            self.create_categoria_produto
        )
        self.router.get("/categorias-produto/{id_categoria}", response_model=CategoriaProdutoModel)(
            self.get_categoria_produto
        )
        self.router.patch("/categorias-produto/{id_categoria}", response_model=CategoriaProdutoModel)(
            self.update_categoria_produto
        )
        self.router.delete("/categorias-produto/{id_categoria}")(self.delete_categoria_produto)

        # --- CentroCusto ---
        self.router.post("/centros-custo", response_model=CentroCustoOption)(self.create_centro_custo)
        self.router.delete("/centros-custo/{id_centro_custo}")(self.delete_centro_custo)

        # --- UnidadeMedida ---
        self.router.get("/unidades-medida", response_model=list[UnidadeMedidaModel])(self.list_unidades_medida)
        self.router.post("/unidades-medida", response_model=UnidadeMedidaModel)(self.create_unidade_medida)
        self.router.get("/unidades-medida/{id_unidade}", response_model=UnidadeMedidaModel)(
            self.get_unidade_medida
        )
        self.router.patch("/unidades-medida/{id_unidade}", response_model=UnidadeMedidaModel)(
            self.update_unidade_medida
        )
        self.router.delete("/unidades-medida/{id_unidade}")(self.delete_unidade_medida)

        # --- Produto ---
        self.router.get("/produtos", response_model=list[ProdutoModel])(self.list_produtos)
        self.router.post("/produtos", response_model=ProdutoModel)(self.create_produto)
        self.router.get("/produtos/{id_produto}", response_model=ProdutoModel)(self.get_produto)
        self.router.patch("/produtos/{id_produto}", response_model=ProdutoModel)(self.update_produto)
        self.router.delete("/produtos/{id_produto}")(self.delete_produto)

        # --- ProdutoComercial / Grao / Insumo (detalhe 1:1 de Produto) ---
        self.router.put("/produtos/{id_produto}/comercial", response_model=ProdutoComercialModel)(
            self.upsert_produto_comercial
        )
        self.router.get("/produtos/{id_produto}/comercial", response_model=ProdutoComercialModel)(
            self.get_produto_comercial
        )
        self.router.delete("/produtos/{id_produto}/comercial")(self.delete_produto_comercial)

        self.router.put("/produtos/{id_produto}/grao", response_model=GraoModel)(self.upsert_grao)
        self.router.get("/produtos/{id_produto}/grao", response_model=GraoModel)(self.get_grao)
        self.router.delete("/produtos/{id_produto}/grao")(self.delete_grao)

        self.router.put("/produtos/{id_produto}/insumo", response_model=InsumoModel)(self.upsert_insumo)
        self.router.get("/produtos/{id_produto}/insumo", response_model=InsumoModel)(self.get_insumo)
        self.router.delete("/produtos/{id_produto}/insumo")(self.delete_insumo)

        # --- CotacaoGrao ---
        self.router.get("/cotacoes-grao", response_model=list[CotacaoGraoModel])(self.list_cotacoes_grao)
        self.router.post("/cotacoes-grao", response_model=CotacaoGraoModel)(self.create_cotacao_grao)
        self.router.delete("/cotacoes-grao/{id_cotacao}")(self.delete_cotacao_grao)

        # --- Certificacao ---
        self.router.get("/certificacoes", response_model=list[CertificacaoModel])(self.list_certificacoes)
        self.router.post("/certificacoes", response_model=CertificacaoModel)(self.create_certificacao)
        self.router.get("/certificacoes/{id_certificacao}", response_model=CertificacaoModel)(
            self.get_certificacao
        )
        self.router.patch("/certificacoes/{id_certificacao}", response_model=CertificacaoModel)(
            self.update_certificacao
        )
        self.router.delete("/certificacoes/{id_certificacao}")(self.delete_certificacao)

        # --- CertificacaoFazenda ---
        self.router.get("/certificacoes-fazenda", response_model=list[CertificacaoFazendaModel])(
            self.list_certificacoes_fazenda
        )
        self.router.post("/certificacoes-fazenda", response_model=CertificacaoFazendaModel)(
            self.create_certificacao_fazenda
        )
        self.router.get(
            "/certificacoes-fazenda/{id_cert_fazenda}", response_model=CertificacaoFazendaModel
        )(self.get_certificacao_fazenda)
        self.router.post(
            "/certificacoes-fazenda/{id_cert_fazenda}/status", response_model=CertificacaoFazendaModel
        )(self.update_status_certificacao_fazenda)
        self.router.delete("/certificacoes-fazenda/{id_cert_fazenda}")(self.delete_certificacao_fazenda)

        # --- Cliente ---
        self.router.get("/clientes", response_model=list[ClienteModel])(self.list_clientes)
        self.router.post("/clientes", response_model=ClienteModel)(self.create_cliente)
        self.router.get("/clientes/{id_cliente}", response_model=ClienteModel)(self.get_cliente)
        self.router.post("/clientes/{id_cliente}/status", response_model=ClienteModel)(
            self.update_status_cliente
        )
        self.router.delete("/clientes/{id_cliente}")(self.delete_cliente)
        self.router.get("/cnpj/{cnpj}", response_model=CompanyData)(self.lookup_empresa_por_cnpj)

        # --- Venda ---
        self.router.get("/vendas", response_model=list[VendaModel])(self.list_vendas)
        self.router.post("/vendas", response_model=VendaComItens)(self.registrar_venda)
        self.router.get("/vendas/{id_venda}", response_model=VendaComItens)(self.get_venda)

        # --- Lookups (para preencher comboboxes/selects no frontend) ---
        self.router.get("/lookups/produtos", response_model=list[ProdutoOption])(self.list_produto_options)
        self.router.get("/lookups/clientes", response_model=list[ClienteOption])(self.list_cliente_options)
        self.router.get("/lookups/centros-custo", response_model=list[CentroCustoOption])(
            self.list_centro_custo_options
        )
        self.router.get("/lookups/lotes", response_model=list[LoteOption])(self.list_lote_options)

    # ------------------------------------------------------------------
    # CategoriaProduto
    # ------------------------------------------------------------------
    def create_categoria_produto(self, dados: NovaCategoriaProduto) -> CategoriaProdutoModel:
        categoria = self._executar(self.service.create_categoria_produto, dados.nome)
        if categoria is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel criar a categoria de produto.")
        return categoria

    def get_categoria_produto(self, id_categoria: int) -> CategoriaProdutoModel:
        categoria = self.service.get_categoria_produto_by_id(id_categoria)
        if categoria is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria de produto nao encontrada.")
        return categoria

    def list_categorias_produto(self) -> list[CategoriaProdutoModel]:
        return self.service.list_categorias_produto()

    def update_categoria_produto(self, id_categoria: int, nome: str | None = None) -> CategoriaProdutoModel:
        if not self.service.update_categoria_produto(id_categoria, nome):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria de produto nao encontrada.")
        return self.service.get_categoria_produto_by_id(id_categoria)

    def delete_categoria_produto(self, id_categoria: int) -> dict:
        if not self.service.delete_categoria_produto(id_categoria):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria de produto nao encontrada.")
        return {"message": "Categoria de produto removida."}

    # ------------------------------------------------------------------
    # UnidadeMedida
    # ------------------------------------------------------------------
    def create_unidade_medida(self, dados: NovaUnidadeMedida) -> UnidadeMedidaModel:
        unidade = self._executar(self.service.create_unidade_medida, dados.sigla, dados.descricao)
        if unidade is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel criar a unidade de medida.")
        return unidade

    def get_unidade_medida(self, id_unidade: int) -> UnidadeMedidaModel:
        unidade = self.service.get_unidade_medida_by_id(id_unidade)
        if unidade is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Unidade de medida nao encontrada.")
        return unidade

    def list_unidades_medida(self) -> list[UnidadeMedidaModel]:
        return self.service.list_unidades_medida()

    def update_unidade_medida(self, id_unidade: int, descricao: str | None = None) -> UnidadeMedidaModel:
        if not self.service.update_unidade_medida(id_unidade, descricao):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Unidade de medida nao encontrada.")
        return self.service.get_unidade_medida_by_id(id_unidade)

    def delete_unidade_medida(self, id_unidade: int) -> dict:
        if not self.service.delete_unidade_medida(id_unidade):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Unidade de medida nao encontrada.")
        return {"message": "Unidade de medida removida."}

    # ------------------------------------------------------------------
    # Produto
    # ------------------------------------------------------------------
    def create_produto(self, dados: NovoProduto) -> ProdutoModel:
        produto = self._executar(
            self.service.create_produto, dados.id_categoria, dados.id_unidade, dados.nome, dados.tipo, dados.preco
        )
        if produto is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel criar o produto.")
        return produto

    def get_produto(self, id_produto: int) -> ProdutoModel:
        produto = self.service.get_produto_by_id(id_produto)
        if produto is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Produto nao encontrado.")
        return produto

    def list_produtos(self, id_categoria: int | None = None) -> list[ProdutoModel]:
        return self.service.list_produtos(self._filtros(id_categoria=id_categoria))

    def update_produto(
        self, id_produto: int, nome: str | None = None, tipo: str | None = None, preco: Decimal | None = None
    ) -> ProdutoModel:
        if not self._executar(self.service.update_produto, id_produto, nome, tipo, preco):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Produto nao encontrado.")
        return self.service.get_produto_by_id(id_produto)

    def delete_produto(self, id_produto: int) -> dict:
        if not self.service.delete_produto(id_produto):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Produto nao encontrado.")
        return {"message": "Produto removido."}

    # ------------------------------------------------------------------
    # ProdutoComercial / Grao / Insumo
    # ------------------------------------------------------------------
    def upsert_produto_comercial(self, id_produto: int, dados: NovoProdutoComercial) -> ProdutoComercialModel:
        produto_comercial = self._executar(
            self.service.upsert_produto_comercial,
            id_produto,
            dados.codigo_comercial,
            dados.marca,
            dados.descricao_comercial,
        )
        if produto_comercial is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel registrar os dados comerciais.")
        return produto_comercial

    def get_produto_comercial(self, id_produto: int) -> ProdutoComercialModel:
        dados = self.service.get_produto_comercial_by_produto(id_produto)
        if dados is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Dados comerciais nao encontrados.")
        return dados

    def delete_produto_comercial(self, id_produto: int) -> dict:
        if not self.service.delete_produto_comercial(id_produto):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Dados comerciais nao encontrados.")
        return {"message": "Dados comerciais removidos."}

    def upsert_grao(self, id_produto: int, dados: NovoGrao) -> GraoModel:
        grao = self._executar(
            self.service.upsert_grao,
            id_produto,
            dados.umidade_maxima,
            dados.impureza_maxima,
            dados.classificacao_tipo,
        )
        if grao is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel registrar os dados de grao.")
        return grao

    def get_grao(self, id_produto: int) -> GraoModel:
        grao = self.service.get_grao_by_produto(id_produto)
        if grao is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Dados de grao nao encontrados.")
        return grao

    def delete_grao(self, id_produto: int) -> dict:
        if not self.service.delete_grao(id_produto):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Dados de grao nao encontrados.")
        return {"message": "Dados de grao removidos."}

    def upsert_insumo(self, id_produto: int, dados: NovoInsumo) -> InsumoModel:
        insumo = self._executar(
            self.service.upsert_insumo,
            id_produto,
            dados.classe_agronomica,
            dados.principio_ativo,
            dados.periodo_carencia_dias,
            dados.registro_mapa,
        )
        if insumo is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel registrar os dados de insumo.")
        return insumo

    def get_insumo(self, id_produto: int) -> InsumoModel:
        insumo = self.service.get_insumo_by_produto(id_produto)
        if insumo is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Dados de insumo nao encontrados.")
        return insumo

    def delete_insumo(self, id_produto: int) -> dict:
        if not self.service.delete_insumo(id_produto):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Dados de insumo nao encontrados.")
        return {"message": "Dados de insumo removidos."}

    # ------------------------------------------------------------------
    # CotacaoGrao
    # ------------------------------------------------------------------
    def create_cotacao_grao(self, dados: NovaCotacaoGrao) -> CotacaoGraoModel:
        cotacao = self._executar(
            self.service.create_cotacao_grao, dados.id_produto, dados.data_cotacao, dados.preco
        )
        if cotacao is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel registrar a cotacao.")
        return cotacao

    def list_cotacoes_grao(self, id_produto: int | None = None) -> list[CotacaoGraoModel]:
        return self.service.list_cotacoes_grao(self._filtros(id_produto=id_produto))

    def delete_cotacao_grao(self, id_cotacao: int) -> dict:
        if not self.service.delete_cotacao_grao(id_cotacao):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Cotacao nao encontrada.")
        return {"message": "Cotacao removida."}

    # ------------------------------------------------------------------
    # Certificacao
    # ------------------------------------------------------------------
    def create_certificacao(self, dados: NovaCertificacao) -> CertificacaoModel:
        certificacao = self._executar(
            self.service.create_certificacao, dados.nome, dados.orgao_emissor, dados.tipo
        )
        if certificacao is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel criar a certificacao.")
        return certificacao

    def get_certificacao(self, id_certificacao: int) -> CertificacaoModel:
        certificacao = self.service.get_certificacao_by_id(id_certificacao)
        if certificacao is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificacao nao encontrada.")
        return certificacao

    def list_certificacoes(self) -> list[CertificacaoModel]:
        return self.service.list_certificacoes()

    def update_certificacao(
        self, id_certificacao: int, nome: str | None = None, orgao_emissor: str | None = None, tipo: str | None = None
    ) -> CertificacaoModel:
        if not self.service.update_certificacao(id_certificacao, nome, orgao_emissor, tipo):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificacao nao encontrada.")
        return self.service.get_certificacao_by_id(id_certificacao)

    def delete_certificacao(self, id_certificacao: int) -> dict:
        if not self.service.delete_certificacao(id_certificacao):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificacao nao encontrada.")
        return {"message": "Certificacao removida."}

    # ------------------------------------------------------------------
    # CertificacaoFazenda
    # ------------------------------------------------------------------
    def create_certificacao_fazenda(self, dados: NovaCertificacaoFazenda) -> CertificacaoFazendaModel:
        cert = self._executar(
            self.service.create_certificacao_fazenda,
            dados.id_certificacao,
            dados.id_fazenda,
            dados.status,
            dados.dt_emissao,
            dados.dt_validade,
            dados.numero_certificado,
        )
        if cert is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel vincular a certificacao a fazenda.")
        return cert

    def get_certificacao_fazenda(self, id_cert_fazenda: int) -> CertificacaoFazendaModel:
        cert = self.service.get_certificacao_fazenda_by_id(id_cert_fazenda)
        if cert is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificacao de fazenda nao encontrada.")
        return cert

    def list_certificacoes_fazenda(self, id_fazenda: int | None = None) -> list[CertificacaoFazendaModel]:
        return self.service.list_certificacoes_fazenda(self._filtros(id_fazenda=id_fazenda))

    def update_status_certificacao_fazenda(
        self, id_cert_fazenda: int, status_certificacao: StatusCertificacao
    ) -> CertificacaoFazendaModel:
        if not self.service.update_status_certificacao_fazenda(id_cert_fazenda, status_certificacao):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificacao de fazenda nao encontrada.")
        return self.service.get_certificacao_fazenda_by_id(id_cert_fazenda)

    def delete_certificacao_fazenda(self, id_cert_fazenda: int) -> dict:
        if not self.service.delete_certificacao_fazenda(id_cert_fazenda):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificacao de fazenda nao encontrada.")
        return {"message": "Certificacao de fazenda removida."}

    # ------------------------------------------------------------------
    # Cliente
    # ------------------------------------------------------------------
    def create_cliente(self, dados: NovoCliente) -> ClienteModel:
        cliente = self._executar(self.service.create_cliente, dados.nome, dados.documento, dados.status)
        if cliente is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel criar o cliente.")
        return cliente

    def get_cliente(self, id_cliente: int) -> ClienteModel:
        cliente = self.service.get_cliente_by_id(id_cliente)
        if cliente is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente nao encontrado.")
        return cliente

    def list_clientes(self) -> list[ClienteModel]:
        return self.service.list_clientes()

    def update_status_cliente(self, id_cliente: int, status_cliente: StatusCliente) -> ClienteModel:
        if not self.service.update_status_cliente(id_cliente, status_cliente):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente nao encontrado.")
        return self.service.get_cliente_by_id(id_cliente)

    def delete_cliente(self, id_cliente: int) -> dict:
        if not self.service.delete_cliente(id_cliente):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente nao encontrado.")
        return {"message": "Cliente removido."}

    def lookup_empresa_por_cnpj(self, cnpj: str) -> CompanyData:
        return self._executar(self.service.lookup_empresa_por_cnpj, cnpj)

    # ------------------------------------------------------------------
    # Venda
    # ------------------------------------------------------------------
    def registrar_venda(self, dados: NovaVenda) -> VendaComItens:
        venda = self._executar(
            self.service.registrar_venda, dados.id_cliente, dados.id_centro_custo, dados.itens, dados.data_venda
        )
        if venda is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel registrar a venda.")
        return venda

    def get_venda(self, id_venda: int) -> VendaComItens:
        venda = self.service.get_venda_by_id(id_venda)
        if venda is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Venda nao encontrada.")
        return venda

    def list_vendas(self, id_cliente: int | None = None) -> list[VendaModel]:
        return self.service.list_vendas(self._filtros(id_cliente=id_cliente))

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------
    def list_produto_options(self) -> list[ProdutoOption]:
        return self.service.list_produto_options()

    def list_cliente_options(self) -> list[ClienteOption]:
        return self.service.list_cliente_options()

    def list_centro_custo_options(self) -> list[CentroCustoOption]:
        return self.service.list_centro_custo_options()

    def create_centro_custo(self, dados: NovoCentroCusto) -> CentroCustoOption:
        centro_custo = self._executar(self.service.create_centro_custo, dados.nome)
        if centro_custo is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nao foi possivel criar o centro de custo.")
        return centro_custo

    def delete_centro_custo(self, id_centro_custo: int) -> dict:
        if not self.service.delete_centro_custo(id_centro_custo):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Centro de custo nao encontrado.")
        return {"message": "Centro de custo removido."}

    def list_lote_options(self) -> list[LoteOption]:
        return self.service.list_lote_options()


comercial_controller = ComercialController()
router = comercial_controller.router
