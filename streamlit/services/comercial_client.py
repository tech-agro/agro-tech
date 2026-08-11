"""HTTP client for the comercial Streamlit UI → FastAPI."""

from __future__ import annotations

import requests

from app.comercial.models import (
    CategoriaProdutoModel,
    CentroCustoOption,
    CertificacaoModel,
    ClienteModel,
    ClienteOption,
    LoteOption,
    NovaCategoriaProduto,
    NovaCertificacao,
    NovaUnidadeMedida,
    NovaVenda,
    NovoCentroCusto,
    NovoCliente,
    NovoProduto,
    ProdutoModel,
    ProdutoOption,
    UnidadeMedidaModel,
    VendaComItens,
    VendaModel,
)
from app.integrations.schemas import CompanyData
from app.comercial.enum import StatusCliente
from app.core.config import settings


_API_DETAIL_TO_PT: tuple[tuple[str, str], ...] = (
    ("nao esta ativo", "O cliente selecionado não está ativo."),
    ("nao esta liberado para venda", "Um dos lotes selecionados não está liberado para venda."),
    ("sem rastreabilidade", "Um dos itens não tem lote informado (rastreabilidade obrigatória para faturar)."),
    ("Saldo insuficiente", "Saldo insuficiente no estoque informado."),
    ("Cliente nao encontrado", "Cliente não encontrado."),
    ("Produto nao encontrado", "Produto não encontrado."),
    ("Categoria de produto nao encontrada", "Categoria de produto não encontrada."),
    ("Unidade de medida nao encontrada", "Unidade de medida não encontrada."),
    ("Lote", "Lote inválido para esta venda."),
    ("foreign key", "Não foi possível concluir: há registros vinculados."),
    ("nao encontrad", "Registro não encontrado."),
    ("ja esta em uso", "Já existe um registro com esses dados."),
    ("unique constraint", "Já existe um registro com esses dados."),
)


def _to_user_message(detail: str, status_code: int | None) -> str:
    lowered = detail.lower()
    for needle, portuguese in _API_DETAIL_TO_PT:
        if needle.lower() in lowered:
            return portuguese
    if status_code == 404:
        return "Registro não encontrado."
    if status_code == 400:
        return detail or "Não foi possível concluir a operação. Verifique os dados informados."
    if status_code == 422:
        return "Dados inválidos. Revise o formulário."
    return "Falha na comunicação com a API."


class ComercialApiError(Exception):
    """Gerada quando a API comercial retorna uma resposta de erro."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        self.user_message = _to_user_message(message, status_code)
        super().__init__(message)


class ComercialClient:
    def __init__(self, base_url: str | None = None, timeout: float = 15) -> None:
        self.base_url = (base_url or settings.api_base_url).rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _raise_for_api(self, response: requests.Response) -> None:
        if response.ok:
            return
        detail: str
        try:
            payload = response.json()
            detail = str(payload.get("detail", response.text))
        except Exception:
            detail = response.text or response.reason
        raise ComercialApiError(detail, status_code=response.status_code)

    # --- Lookups ---

    def list_produto_options(self) -> list[ProdutoOption]:
        response = requests.get(self._url("/comercial/lookups/produtos"), timeout=self.timeout)
        self._raise_for_api(response)
        return [ProdutoOption.model_validate(item) for item in response.json()]

    def list_cliente_options(self) -> list[ClienteOption]:
        response = requests.get(self._url("/comercial/lookups/clientes"), timeout=self.timeout)
        self._raise_for_api(response)
        return [ClienteOption.model_validate(item) for item in response.json()]

    def list_centro_custo_options(self) -> list[CentroCustoOption]:
        response = requests.get(self._url("/comercial/lookups/centros-custo"), timeout=self.timeout)
        self._raise_for_api(response)
        return [CentroCustoOption.model_validate(item) for item in response.json()]

    def create_centro_custo(self, payload: NovoCentroCusto) -> CentroCustoOption:
        response = requests.post(
            self._url("/comercial/centros-custo"), json=payload.model_dump(mode="json"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return CentroCustoOption.model_validate(response.json())

    def delete_centro_custo(self, id_centro_custo: int) -> None:
        response = requests.delete(
            self._url(f"/comercial/centros-custo/{id_centro_custo}"), timeout=self.timeout
        )
        self._raise_for_api(response)

    def list_lote_options(self) -> list[LoteOption]:
        response = requests.get(self._url("/comercial/lookups/lotes"), timeout=self.timeout)
        self._raise_for_api(response)
        return [LoteOption.model_validate(item) for item in response.json()]

    # --- CategoriaProduto ---

    def list_categorias_produto(self) -> list[CategoriaProdutoModel]:
        response = requests.get(self._url("/comercial/categorias-produto"), timeout=self.timeout)
        self._raise_for_api(response)
        return [CategoriaProdutoModel.model_validate(item) for item in response.json()]

    def create_categoria_produto(self, payload: NovaCategoriaProduto) -> CategoriaProdutoModel:
        response = requests.post(
            self._url("/comercial/categorias-produto"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return CategoriaProdutoModel.model_validate(response.json())

    def delete_categoria_produto(self, id_categoria: int) -> None:
        response = requests.delete(
            self._url(f"/comercial/categorias-produto/{id_categoria}"), timeout=self.timeout
        )
        self._raise_for_api(response)

    # --- UnidadeMedida ---

    def list_unidades_medida(self) -> list[UnidadeMedidaModel]:
        response = requests.get(self._url("/comercial/unidades-medida"), timeout=self.timeout)
        self._raise_for_api(response)
        return [UnidadeMedidaModel.model_validate(item) for item in response.json()]

    def create_unidade_medida(self, payload: NovaUnidadeMedida) -> UnidadeMedidaModel:
        response = requests.post(
            self._url("/comercial/unidades-medida"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return UnidadeMedidaModel.model_validate(response.json())

    def delete_unidade_medida(self, id_unidade: int) -> None:
        response = requests.delete(self._url(f"/comercial/unidades-medida/{id_unidade}"), timeout=self.timeout)
        self._raise_for_api(response)

    # --- Produto ---

    def list_produtos(self) -> list[ProdutoModel]:
        response = requests.get(self._url("/comercial/produtos"), timeout=self.timeout)
        self._raise_for_api(response)
        return [ProdutoModel.model_validate(item) for item in response.json()]

    def get_produto(self, id_produto: int) -> ProdutoModel:
        response = requests.get(self._url(f"/comercial/produtos/{id_produto}"), timeout=self.timeout)
        self._raise_for_api(response)
        return ProdutoModel.model_validate(response.json())

    def create_produto(self, payload: NovoProduto) -> ProdutoModel:
        response = requests.post(
            self._url("/comercial/produtos"), json=payload.model_dump(mode="json"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return ProdutoModel.model_validate(response.json())

    def delete_produto(self, id_produto: int) -> None:
        response = requests.delete(self._url(f"/comercial/produtos/{id_produto}"), timeout=self.timeout)
        self._raise_for_api(response)

    # --- Certificacao ---

    def list_certificacoes(self) -> list[CertificacaoModel]:
        response = requests.get(self._url("/comercial/certificacoes"), timeout=self.timeout)
        self._raise_for_api(response)
        return [CertificacaoModel.model_validate(item) for item in response.json()]

    def create_certificacao(self, payload: NovaCertificacao) -> CertificacaoModel:
        response = requests.post(
            self._url("/comercial/certificacoes"), json=payload.model_dump(mode="json"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return CertificacaoModel.model_validate(response.json())

    def delete_certificacao(self, id_certificacao: int) -> None:
        response = requests.delete(self._url(f"/comercial/certificacoes/{id_certificacao}"), timeout=self.timeout)
        self._raise_for_api(response)

    # --- Cliente ---

    def list_clientes(self) -> list[ClienteModel]:
        response = requests.get(self._url("/comercial/clientes"), timeout=self.timeout)
        self._raise_for_api(response)
        return [ClienteModel.model_validate(item) for item in response.json()]

    def create_cliente(self, payload: NovoCliente) -> ClienteModel:
        response = requests.post(
            self._url("/comercial/clientes"), json=payload.model_dump(mode="json"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return ClienteModel.model_validate(response.json())

    def update_status_cliente(self, id_cliente: int, status_cliente: StatusCliente) -> ClienteModel:
        response = requests.post(
            self._url(f"/comercial/clientes/{id_cliente}/status"),
            params={"status_cliente": status_cliente.value},
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return ClienteModel.model_validate(response.json())

    def delete_cliente(self, id_cliente: int) -> None:
        response = requests.delete(self._url(f"/comercial/clientes/{id_cliente}"), timeout=self.timeout)
        self._raise_for_api(response)

    def lookup_empresa_por_cnpj(self, cnpj: str) -> CompanyData:
        response = requests.get(self._url(f"/comercial/cnpj/{cnpj}"), timeout=self.timeout)
        self._raise_for_api(response)
        return CompanyData.model_validate(response.json())

    # --- Venda ---

    def list_vendas(self) -> list[VendaModel]:
        response = requests.get(self._url("/comercial/vendas"), timeout=self.timeout)
        self._raise_for_api(response)
        return [VendaModel.model_validate(item) for item in response.json()]

    def get_venda(self, id_venda: int) -> VendaComItens:
        response = requests.get(self._url(f"/comercial/vendas/{id_venda}"), timeout=self.timeout)
        self._raise_for_api(response)
        return VendaComItens.model_validate(response.json())

    def registrar_venda(self, payload: NovaVenda) -> VendaComItens:
        response = requests.post(
            self._url("/comercial/vendas"), json=payload.model_dump(mode="json"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return VendaComItens.model_validate(response.json())
