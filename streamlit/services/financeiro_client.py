"""HTTP client for the financeiro Streamlit UI → FastAPI."""

from __future__ import annotations

from datetime import date

import requests

from app.core.config import settings
from app.financeiro.lookups import (
    CompraOptionSchema,
    ContaPagarOptionSchema,
    ContaReceberOptionSchema,
    DespesaLogisticaOptionSchema,
    FormaPagamentoOptionSchema,
    ManutencaoOptionSchema,
    VendaOptionSchema,
)
from app.financeiro.schemas import (
    ConfiguracaoFinanceiraReadSchema,
    ConfiguracaoFinanceiraUpdateSchema,
    ContaPagarCreateSchema,
    ContaPagarReadSchema,
    ContaPagarUpdateSchema,
    ContaReceberCreateSchema,
    ContaReceberReadSchema,
    ContaReceberUpdateSchema,
    FluxoCaixaReadSchema,
    PagamentoCreateSchema,
    PagamentoReadSchema,
    PagamentoUpdateSchema,
    RecebimentoCreateSchema,
    RecebimentoReadSchema,
    RecebimentoUpdateSchema,
)

_API_DETAIL_TO_PT: tuple[tuple[str, str], ...] = (
    ("Conta a pagar", "Conta a pagar não encontrada."),
    ("Conta a receber", "Conta a receber não encontrada."),
    ("Pagamento", "Pagamento não encontrado."),
    ("Recebimento", "Recebimento não encontrado."),
    ("Configuração financeira", "Configuração financeira não encontrada."),
    ("Saldo insuficiente", "Saldo insuficiente para concluir a operação."),
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


class FinanceiroApiError(Exception):
    """Gerada quando a API de financeiro retorna uma resposta de erro."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        self.user_message = _to_user_message(message, status_code)
        super().__init__(message)


class FinanceiroClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 15,
    ) -> None:
        self.base_url = (base_url or settings.api_base_url).rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _raise_for_api(self, response: requests.Response) -> None:
        if response.ok:
            return

        try:
            payload = response.json()
            detail = str(payload.get("detail", response.text))
        except Exception:
            detail = response.text or response.reason

        raise FinanceiroApiError(detail, status_code=response.status_code)

    # ============================================================
    # LOOKUPS
    # ============================================================

    def list_compra_options(self) -> list[CompraOptionSchema]:
        response = requests.get(
            self._url("/financeiro/lookups/compras"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [CompraOptionSchema.model_validate(item) for item in response.json()]

    def list_manutencao_options(self) -> list[ManutencaoOptionSchema]:
        response = requests.get(
            self._url("/financeiro/lookups/manutencoes"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [ManutencaoOptionSchema.model_validate(item) for item in response.json()]

    def list_despesa_logistica_options(self) -> list[DespesaLogisticaOptionSchema]:
        response = requests.get(
            self._url("/financeiro/lookups/despesas-logisticas"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [
            DespesaLogisticaOptionSchema.model_validate(item)
            for item in response.json()
        ]

    def list_venda_options(self) -> list[VendaOptionSchema]:
        response = requests.get(
            self._url("/financeiro/lookups/vendas"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [VendaOptionSchema.model_validate(item) for item in response.json()]

    def list_conta_pagar_options(self) -> list[ContaPagarOptionSchema]:
        response = requests.get(
            self._url("/financeiro/lookups/contas-pagar"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [
            ContaPagarOptionSchema.model_validate(item)
            for item in response.json()
        ]

    def list_conta_receber_options(self) -> list[ContaReceberOptionSchema]:
        response = requests.get(
            self._url("/financeiro/lookups/contas-receber"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [
            ContaReceberOptionSchema.model_validate(item)
            for item in response.json()
        ]

    def list_forma_pagamento_options(self) -> list[FormaPagamentoOptionSchema]:
        response = requests.get(
            self._url("/financeiro/lookups/formas-pagamento"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [
            FormaPagamentoOptionSchema.model_validate(item)
            for item in response.json()
        ]

    # ============================================================
    # CONTAS A PAGAR
    # ============================================================

    def create_conta_pagar(
        self,
        payload: ContaPagarCreateSchema,
    ) -> ContaPagarReadSchema:
        response = requests.post(
            self._url("/financeiro/contas-pagar"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return ContaPagarReadSchema.model_validate(response.json())

    def list_contas_pagar(
        self,
        status: str | None = None,
        vencendo_em: int | None = None,
        vencidas: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ContaPagarReadSchema]:
        params = {
            "vencendo_em": vencendo_em,
            "vencidas": vencidas,
            "limit": limit,
            "offset": offset,
        }

        if status is not None:
            params["status"] = status

        response = requests.get(
            self._url("/financeiro/contas-pagar"),
            params=params,
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [ContaPagarReadSchema.model_validate(item) for item in response.json()]

    def get_conta_pagar(self, id_conta_pagar: int) -> ContaPagarReadSchema:
        response = requests.get(
            self._url(f"/financeiro/contas-pagar/{id_conta_pagar}"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return ContaPagarReadSchema.model_validate(response.json())

    def update_conta_pagar(
        self,
        id_conta_pagar: int,
        payload: ContaPagarUpdateSchema,
    ) -> ContaPagarReadSchema:
        response = requests.patch(
            self._url(f"/financeiro/contas-pagar/{id_conta_pagar}"),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return ContaPagarReadSchema.model_validate(response.json())

    def delete_conta_pagar(self, id_conta_pagar: int) -> None:
        response = requests.delete(
            self._url(f"/financeiro/contas-pagar/{id_conta_pagar}"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)

    # ============================================================
    # PAGAMENTOS
    # ============================================================

    def create_pagamento(
        self,
        payload: PagamentoCreateSchema,
    ) -> PagamentoReadSchema:
        response = requests.post(
            self._url("/financeiro/pagamentos"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return PagamentoReadSchema.model_validate(response.json())

    def list_pagamentos(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PagamentoReadSchema]:
        response = requests.get(
            self._url("/financeiro/pagamentos"),
            params={
                "limit": limit,
                "offset": offset,
            },
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [PagamentoReadSchema.model_validate(item) for item in response.json()]

    def list_pagamentos_por_conta(
        self,
        id_conta_pagar: int,
    ) -> list[PagamentoReadSchema]:
        response = requests.get(
            self._url(f"/financeiro/contas-pagar/{id_conta_pagar}/pagamentos"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [PagamentoReadSchema.model_validate(item) for item in response.json()]

    def get_pagamento(self, id_pagamento: int) -> PagamentoReadSchema:
        response = requests.get(
            self._url(f"/financeiro/pagamentos/{id_pagamento}"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return PagamentoReadSchema.model_validate(response.json())

    def update_pagamento(
        self,
        id_pagamento: int,
        payload: PagamentoUpdateSchema,
    ) -> PagamentoReadSchema:
        response = requests.patch(
            self._url(f"/financeiro/pagamentos/{id_pagamento}"),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return PagamentoReadSchema.model_validate(response.json())

    def delete_pagamento(self, id_pagamento: int) -> None:
        response = requests.delete(
            self._url(f"/financeiro/pagamentos/{id_pagamento}"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)


    # ============================================================
    # CONTAS A RECEBER
    # ============================================================

    def create_conta_receber(
        self,
        payload: ContaReceberCreateSchema,
    ) -> ContaReceberReadSchema:
        response = requests.post(
            self._url("/financeiro/contas-receber"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return ContaReceberReadSchema.model_validate(response.json())

    def list_contas_receber(
        self,
        status: str | None = None,
        vencendo_em: int | None = None,
        vencidas: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ContaReceberReadSchema]:
        params = {
            "vencendo_em": vencendo_em,
            "vencidas": vencidas,
            "limit": limit,
            "offset": offset,
        }

        if status is not None:
            params["status"] = status

        response = requests.get(
            self._url("/financeiro/contas-receber"),
            params=params,
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [ContaReceberReadSchema.model_validate(item) for item in response.json()]

    def get_conta_receber(self, id_conta_receber: int) -> ContaReceberReadSchema:
        response = requests.get(
            self._url(f"/financeiro/contas-receber/{id_conta_receber}"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return ContaReceberReadSchema.model_validate(response.json())

    def update_conta_receber(
        self,
        id_conta_receber: int,
        payload: ContaReceberUpdateSchema,
    ) -> ContaReceberReadSchema:
        response = requests.patch(
            self._url(f"/financeiro/contas-receber/{id_conta_receber}"),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return ContaReceberReadSchema.model_validate(response.json())

    def delete_conta_receber(self, id_conta_receber: int) -> None:
        response = requests.delete(
            self._url(f"/financeiro/contas-receber/{id_conta_receber}"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)

    # ============================================================
    # RECEBIMENTOS
    # ============================================================

    def create_recebimento(
        self,
        payload: RecebimentoCreateSchema,
    ) -> RecebimentoReadSchema:
        response = requests.post(
            self._url("/financeiro/recebimentos"),
            json=payload.model_dump(mode="json"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return RecebimentoReadSchema.model_validate(response.json())

    def list_recebimentos(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RecebimentoReadSchema]:
        response = requests.get(
            self._url("/financeiro/recebimentos"),
            params={
                "limit": limit,
                "offset": offset,
            },
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [RecebimentoReadSchema.model_validate(item) for item in response.json()]

    def list_recebimentos_por_conta(
        self,
        id_conta_receber: int,
    ) -> list[RecebimentoReadSchema]:
        response = requests.get(
            self._url(f"/financeiro/contas-receber/{id_conta_receber}/recebimentos"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [RecebimentoReadSchema.model_validate(item) for item in response.json()]

    def get_recebimento(self, id_recebimento: int) -> RecebimentoReadSchema:
        response = requests.get(
            self._url(f"/financeiro/recebimentos/{id_recebimento}"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return RecebimentoReadSchema.model_validate(response.json())

    def update_recebimento(
        self,
        id_recebimento: int,
        payload: RecebimentoUpdateSchema,
    ) -> RecebimentoReadSchema:
        response = requests.patch(
            self._url(f"/financeiro/recebimentos/{id_recebimento}"),
            json=payload.model_dump(mode="json", exclude_unset=True),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return RecebimentoReadSchema.model_validate(response.json())

    def delete_recebimento(self, id_recebimento: int) -> None:
        response = requests.delete(
            self._url(f"/financeiro/recebimentos/{id_recebimento}"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)


    # ============================================================
    # FLUXO DE CAIXA
    # ============================================================

    def list_fluxo_por_periodo(
        self,
        data_inicio: date,
        data_fim: date,
        tipo: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[FluxoCaixaReadSchema]:
        params = {
            "data_inicio": data_inicio.isoformat(),
            "data_fim": data_fim.isoformat(),
            "limit": limit,
            "offset": offset,
        }

        if tipo is not None:
            params["tipo"] = tipo

        response = requests.get(
            self._url("/financeiro/fluxo-caixa"),
            params=params,
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [FluxoCaixaReadSchema.model_validate(item) for item in response.json()]

    def resumo_fluxo_por_periodo(
        self,
        data_inicio: date,
        data_fim: date,
    ) -> dict[str, str]:
        response = requests.get(
            self._url("/financeiro/fluxo-caixa/resumo"),
            params={
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat(),
            },
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return response.json()

    def list_fluxo_por_conta_pagar(
        self,
        id_conta_pagar: int,
    ) -> list[FluxoCaixaReadSchema]:
        response = requests.get(
            self._url(f"/financeiro/contas-pagar/{id_conta_pagar}/fluxo-caixa"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [FluxoCaixaReadSchema.model_validate(item) for item in response.json()]

    def list_fluxo_por_conta_receber(
        self,
        id_conta_receber: int,
    ) -> list[FluxoCaixaReadSchema]:
        response = requests.get(
            self._url(f"/financeiro/contas-receber/{id_conta_receber}/fluxo-caixa"),
            timeout=self.timeout,
        )
        self._raise_for_api(response)
        return [FluxoCaixaReadSchema.model_validate(item) for item in response.json()]