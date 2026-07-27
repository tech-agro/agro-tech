"""Funções auxiliares para exibição de rótulos no módulo comercial."""

from __future__ import annotations

from app.comercial.enum import StatusCliente
from app.comercial.models import CentroCustoOption, ClienteOption, LoteOption, ProdutoOption
from app.core.enum import StatusCertificacao
from app.estoque.enum import StatusLote

STATUS_CLIENTE_LABELS: dict[StatusCliente, str] = {
    StatusCliente.ATIVO: "Ativo",
    StatusCliente.INATIVO: "Inativo",
    StatusCliente.BLOQUEADO: "Bloqueado",
}

STATUS_LOTE_LABELS: dict[StatusLote, str] = {
    StatusLote.EM_ANALISE: "Em análise",
    StatusLote.LIBERADO: "Liberado",
    StatusLote.BLOQUEADO: "Bloqueado",
}

STATUS_CERTIFICACAO_LABELS: dict[StatusCertificacao, str] = {
    StatusCertificacao.VIGENTE: "Vigente",
    StatusCertificacao.VENCIDA: "Vencida",
    StatusCertificacao.SUSPENSA: "Suspensa",
    StatusCertificacao.CANCELADA: "Cancelada",
}


def produto_label(option: ProdutoOption) -> str:
    return f"{option.nome} (#{option.id_produto})"


def cliente_label(option: ClienteOption) -> str:
    return f"{option.nome} (#{option.id_cliente})"


def centro_custo_label(option: CentroCustoOption) -> str:
    return f"{option.nome} (#{option.id_centro_custo})"


def lote_label(option: LoteOption) -> str:
    status = STATUS_LOTE_LABELS.get(option.status, option.status.value)
    base = f"{option.codigo_lote} — {option.produto_nome}" if option.produto_nome else option.codigo_lote
    return f"{base} [{status}]"
