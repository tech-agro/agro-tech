"""HTTP client for the estoque Streamlit UI → FastAPI."""

from __future__ import annotations

from datetime import datetime

import requests

from app.estoque.schemas.certificacao_lote import (
    CertificacaoLoteCreateSchema,
    CertificacaoLoteReadSchema,
    CertificacaoLoteUpdateSchema,
)
from app.estoque.schemas.entrada_colheita_estoque import (
    EntradaColheitaCreateSchema,
    EntradaColheitaReadSchema,
)
from app.estoque.schemas.estoque import EstoqueCreateSchema, EstoqueReadSchema
from app.estoque.schemas.local_armazenamento import (
    LocalArmazenamentoCreateSchema,
    LocalArmazenamentoReadSchema,
    LocalArmazenamentoUpdateSchema,
    OcupacaoLocalSchema,
)
from app.estoque.schemas.lookups import (
    CertificacaoOptionSchema,
    ColheitaOptionSchema,
    EstoqueOptionSchema,
    ItemPedidoOptionSchema,
    LocalArmazenamentoOptionSchema,
    LoteOptionSchema,
    ProdutoOptionSchema,
)
from app.estoque.schemas.lote import (
    LocalizacaoLoteSchema,
    LoteCreateSchema,
    LoteReadSchema,
    LoteUpdateSchema,
)
from app.estoque.schemas.movimentacao_estoque import MovimentacaoEstoqueReadSchema
from app.estoque.schemas.recebimento_compra import (
    RecebimentoCompraCreateSchema,
    RecebimentoCompraReadSchema,
)
from app.estoque.schemas.saldo_estoque import SaldoEstoqueReadSchema
from app.core.config import settings


_API_DETAIL_TO_PT: tuple[tuple[str, str], ...] = (
    ("já está em uso", "Este código de lote já está em uso."),
    ("Saldo insuficiente", "Saldo insuficiente para registrar a saída."),
    ("Quantidade recebida excede", "A quantidade recebida excede o que foi pedido."),
    ("Nenhuma compra registrada", "Nenhuma compra registrada para este pedido ainda."),
    ("possui movimentações", "Não é possível excluir: há movimentações vinculadas."),
    ("possui certificações", "Não é possível excluir: há certificações vinculadas."),
    ("possui saldo", "Não é possível excluir: há saldo vinculado a este estoque."),
    ("possui estoques", "Não é possível excluir: há estoques vinculados a este local."),
    ("Lote não encontrado", "Lote não encontrado."),
    ("Local não encontrado", "Local não encontrado."),
    ("Estoque não encontrado", "Estoque não encontrado."),
    ("Certificação não encontrada", "Certificação não encontrada."),
    ("Saldo não encontrado", "Saldo não encontrado."),
    ("Item de pedido não encontrado", "Item de pedido não encontrado."),
    ("foreign key", "Não foi possível concluir: há registros vinculados."),
    ("não encontrado", "Registro não encontrado."),
    ("já existe", "Já existe um registro com esses dados."),
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
        return "Não foi possível concluir a operação. Verifique os dados informados."
    if status_code == 422:
        return "Dados inválidos. Revise o formulário."
    return "Falha na comunicação com a API."


class EstoqueApiError(Exception):
    """Gerada quando a API de estoque retorna uma resposta de erro."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        self.user_message = _to_user_message(message, status_code)
        super().__init__(message)


class EstoqueClient:
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
        raise EstoqueApiError(detail, status_code=response.status_code)

    # --- Lookups ---

    def list_produto_options(self) -> list[ProdutoOptionSchema]:
        response = requests.get(self._url("/estoque/lookups/produtos"), timeout=self.timeout)
        self._raise_for_api(response)
        return [ProdutoOptionSchema.model_validate(item) for item in response.json()]

    def list_colheita_options(self) -> list[ColheitaOptionSchema]:
        response = requests.get(self._url("/estoque/lookups/colheitas"), timeout=self.timeout)
        self._raise_for_api(response)
        return [ColheitaOptionSchema.model_validate(item) for item in response.json()]

    def list_local_options(self) -> list[LocalArmazenamentoOptionSchema]:
        response = requests.get(self._url("/estoque/lookups/locais"), timeout=self.timeout)
        self._raise_for_api(response)
        return [LocalArmazenamentoOptionSchema.model_validate(item) for item in response.json()]

    def list_estoque_options(self) -> list[EstoqueOptionSchema]:
        response = requests.get(self._url("/estoque/lookups/estoques"), timeout=self.timeout)
        self._raise_for_api(response)
        return [EstoqueOptionSchema.model_validate(item) for item in response.json()]

    def list_lote_options(self) -> list[LoteOptionSchema]:
        response = requests.get(self._url("/estoque/lookups/lotes"), timeout=self.timeout)
        self._raise_for_api(response)
        return [LoteOptionSchema.model_validate(item) for item in response.json()]

    def list_certificacao_options(self) -> list[CertificacaoOptionSchema]:
        response = requests.get(
            self._url("/estoque/lookups/certificacoes"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [CertificacaoOptionSchema.model_validate(item) for item in response.json()]

    def list_item_pedido_options(self) -> list[ItemPedidoOptionSchema]:
        response = requests.get(
            self._url("/estoque/lookups/itens-pedido"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [ItemPedidoOptionSchema.model_validate(item) for item in response.json()]

    # --- Lotes ---

    def list_lotes(self, limit: int = 50, offset: int = 0) -> list[LoteReadSchema]:
        response = requests.get(
            self._url("/estoque/lotes"),
            params={"limit": limit, "offset": offset},
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [LoteReadSchema.model_validate(item) for item in response.json()]

    def list_lotes_vencidos(self) -> list[LoteReadSchema]:
        response = requests.get(self._url("/estoque/lotes/vencidos"), timeout=self.timeout)
        self._raise_for_api(response)
        return [LoteReadSchema.model_validate(item) for item in response.json()]

    def list_lotes_proximos_vencimento(self, dias: int = 30) -> list[LoteReadSchema]:
        response = requests.get(
            self._url("/estoque/lotes/proximos-vencimento"),
            params={"dias": dias},
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [LoteReadSchema.model_validate(item) for item in response.json()]

    def list_localizacao_lotes(self) -> list[LocalizacaoLoteSchema]:
        response = requests.get(self._url("/estoque/lotes/localizacao"), timeout=self.timeout)
        self._raise_for_api(response)
        return [LocalizacaoLoteSchema.model_validate(item) for item in response.json()]

    def get_lote_by_codigo(self, codigo: str) -> LoteReadSchema:
        response = requests.get(
            self._url(f"/estoque/lotes/codigo/{codigo}"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return LoteReadSchema.model_validate(response.json())

    def get_lote(self, id_lote: int) -> LoteReadSchema:
        response = requests.get(self._url(f"/estoque/lotes/{id_lote}"), timeout=self.timeout)
        self._raise_for_api(response)
        return LoteReadSchema.model_validate(response.json())

    def update_lote(self, id_lote: int, payload: LoteUpdateSchema) -> LoteReadSchema:
        response = requests.patch(
            self._url(f"/estoque/lotes/{id_lote}"),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return LoteReadSchema.model_validate(response.json())

    def delete_lote(self, id_lote: int) -> None:
        response = requests.delete(self._url(f"/estoque/lotes/{id_lote}"), timeout=self.timeout)
        self._raise_for_api(response)

    # --- Locais de armazenamento ---

    def list_locais(self) -> list[LocalArmazenamentoReadSchema]:
        response = requests.get(self._url("/estoque/locais"), timeout=self.timeout)
        self._raise_for_api(response)
        return [LocalArmazenamentoReadSchema.model_validate(item) for item in response.json()]

    def list_ocupacao_locais(self) -> list[OcupacaoLocalSchema]:
        response = requests.get(self._url("/estoque/locais/ocupacao"), timeout=self.timeout)
        self._raise_for_api(response)
        return [OcupacaoLocalSchema.model_validate(item) for item in response.json()]

    def get_local(self, id_local: int) -> LocalArmazenamentoReadSchema:
        response = requests.get(self._url(f"/estoque/locais/{id_local}"), timeout=self.timeout)
        self._raise_for_api(response)
        return LocalArmazenamentoReadSchema.model_validate(response.json())

    def create_local(
        self, payload: LocalArmazenamentoCreateSchema
    ) -> LocalArmazenamentoReadSchema:
        response = requests.post(
            self._url("/estoque/locais"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return LocalArmazenamentoReadSchema.model_validate(response.json())

    def update_local(
        self, id_local: int, payload: LocalArmazenamentoUpdateSchema
    ) -> LocalArmazenamentoReadSchema:
        response = requests.patch(
            self._url(f"/estoque/locais/{id_local}"),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return LocalArmazenamentoReadSchema.model_validate(response.json())

    def delete_local(self, id_local: int) -> None:
        response = requests.delete(self._url(f"/estoque/locais/{id_local}"), timeout=self.timeout)
        self._raise_for_api(response)

    # --- Estoques ---

    def list_estoques(self) -> list[EstoqueReadSchema]:
        response = requests.get(self._url("/estoque/estoques"), timeout=self.timeout)
        self._raise_for_api(response)
        return [EstoqueReadSchema.model_validate(item) for item in response.json()]

    def list_estoques_by_local(self, id_local: int) -> list[EstoqueReadSchema]:
        response = requests.get(
            self._url(f"/estoque/estoques/local/{id_local}"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [EstoqueReadSchema.model_validate(item) for item in response.json()]

    def get_estoque(self, id_estoque: int) -> EstoqueReadSchema:
        response = requests.get(
            self._url(f"/estoque/estoques/{id_estoque}"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return EstoqueReadSchema.model_validate(response.json())

    def create_estoque(self, payload: EstoqueCreateSchema) -> EstoqueReadSchema:
        response = requests.post(
            self._url("/estoque/estoques"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return EstoqueReadSchema.model_validate(response.json())

    def delete_estoque(self, id_estoque: int) -> None:
        response = requests.delete(
            self._url(f"/estoque/estoques/{id_estoque}"), timeout=self.timeout
        )
        self._raise_for_api(response)

    # --- Certificações de lote ---

    def list_certificacoes(
        self, limit: int = 50, offset: int = 0
    ) -> list[CertificacaoLoteReadSchema]:
        response = requests.get(
            self._url("/estoque/certificacoes"),
            params={"limit": limit, "offset": offset},
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [CertificacaoLoteReadSchema.model_validate(item) for item in response.json()]

    def list_certificacoes_by_lote(self, id_lote: int) -> list[CertificacaoLoteReadSchema]:
        response = requests.get(
            self._url(f"/estoque/certificacoes/lote/{id_lote}"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [CertificacaoLoteReadSchema.model_validate(item) for item in response.json()]

    def get_certificacao(self, id_certificacao_lote: int) -> CertificacaoLoteReadSchema:
        response = requests.get(
            self._url(f"/estoque/certificacoes/{id_certificacao_lote}"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return CertificacaoLoteReadSchema.model_validate(response.json())

    def create_certificacao(
        self, payload: CertificacaoLoteCreateSchema
    ) -> CertificacaoLoteReadSchema:
        response = requests.post(
            self._url("/estoque/certificacoes"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return CertificacaoLoteReadSchema.model_validate(response.json())

    def update_certificacao(
        self, id_certificacao_lote: int, payload: CertificacaoLoteUpdateSchema
    ) -> CertificacaoLoteReadSchema:
        response = requests.patch(
            self._url(f"/estoque/certificacoes/{id_certificacao_lote}"),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return CertificacaoLoteReadSchema.model_validate(response.json())

    def delete_certificacao(self, id_certificacao_lote: int) -> None:
        response = requests.delete(
            self._url(f"/estoque/certificacoes/{id_certificacao_lote}"), timeout=self.timeout
        )
        self._raise_for_api(response)

    # --- Saldo ---

    def get_saldo(self, id_estoque: int, id_produto: int) -> SaldoEstoqueReadSchema:
        response = requests.get(
            self._url(f"/estoque/saldo/{id_estoque}/{id_produto}"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return SaldoEstoqueReadSchema.model_validate(response.json())

    def list_saldo_by_estoque(self, id_estoque: int) -> list[SaldoEstoqueReadSchema]:
        response = requests.get(
            self._url(f"/estoque/saldo/estoque/{id_estoque}"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [SaldoEstoqueReadSchema.model_validate(item) for item in response.json()]

    def list_saldo_by_produto(self, id_produto: int) -> list[SaldoEstoqueReadSchema]:
        response = requests.get(
            self._url(f"/estoque/saldo/produto/{id_produto}"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [SaldoEstoqueReadSchema.model_validate(item) for item in response.json()]

    # --- Movimentações ---

    def list_movimentacoes_by_estoque(
        self, id_estoque: int, limit: int = 50, offset: int = 0
    ) -> list[MovimentacaoEstoqueReadSchema]:
        response = requests.get(
            self._url(f"/estoque/movimentacoes/estoque/{id_estoque}"),
            params={"limit": limit, "offset": offset},
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [MovimentacaoEstoqueReadSchema.model_validate(item) for item in response.json()]

    def list_movimentacoes_by_lote(
        self, id_lote: int, limit: int = 50, offset: int = 0
    ) -> list[MovimentacaoEstoqueReadSchema]:
        response = requests.get(
            self._url(f"/estoque/movimentacoes/lote/{id_lote}"),
            params={"limit": limit, "offset": offset},
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [MovimentacaoEstoqueReadSchema.model_validate(item) for item in response.json()]

    def list_movimentacoes_by_periodo(
        self,
        id_estoque: int,
        data_inicio: datetime,
        data_fim: datetime,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MovimentacaoEstoqueReadSchema]:
        response = requests.get(
            self._url(f"/estoque/movimentacoes/estoque/{id_estoque}/periodo"),
            params={
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat(),
                "limit": limit,
                "offset": offset,
            },
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [MovimentacaoEstoqueReadSchema.model_validate(item) for item in response.json()]

    # --- Recebimento de compra ---

    def registrar_recebimento(
        self, payload: RecebimentoCompraCreateSchema
    ) -> RecebimentoCompraReadSchema:
        response = requests.post(
            self._url("/estoque/recebimentos"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return RecebimentoCompraReadSchema.model_validate(response.json())

    def list_recebimentos_by_item(
        self, id_item_pedido: int
    ) -> list[RecebimentoCompraReadSchema]:
        response = requests.get(
            self._url(f"/estoque/recebimentos/item/{id_item_pedido}"), timeout=self.timeout
        )
        self._raise_for_api(response)
        return [RecebimentoCompraReadSchema.model_validate(item) for item in response.json()]

    def list_recebimentos_by_estoque(
        self, id_estoque: int, limit: int = 50, offset: int = 0
    ) -> list[RecebimentoCompraReadSchema]:
        response = requests.get(
            self._url(f"/estoque/recebimentos/estoque/{id_estoque}"),
            params={"limit": limit, "offset": offset},
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [RecebimentoCompraReadSchema.model_validate(item) for item in response.json()]

    # --- Entrada por colheita ---

    def registrar_entrada_colheita(
        self, payload: EntradaColheitaCreateSchema
    ) -> EntradaColheitaReadSchema:
        response = requests.post(
            self._url("/estoque/entradas-colheita"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return EntradaColheitaReadSchema.model_validate(response.json())