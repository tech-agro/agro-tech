"""Recebe requisicoes da interface para o dominio financeiro."""

from __future__ import annotations

from app.financeiro.service import FinanceiroService


class FinanceiroController:
    """Adaptador entre interface e service.

    Sem router HTTP por enquanto: nenhuma rota chama este modulo hoje, ele so e
    usado internamente pelo hook `receber_venda_confirmada` (chamado direto por
    ComercialService.registrar_venda).
    """

    def __init__(self, service: FinanceiroService | None = None) -> None:
        self.service = service or FinanceiroService()
