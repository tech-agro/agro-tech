"""Shared constants for Manutencao UI."""

STATUS_MAQUINA = ["DISPONIVEL", "EM_USO", "EM_MANUTENCAO", "INATIVA"]
STATUS_ORDEM = ["ABERTA", "EM_EXECUCAO", "CONCLUIDA", "CANCELADA"]
STATUS_MANUTENCAO = ["ABERTA", "EM_EXECUCAO", "CONCLUIDA", "CANCELADA"]

STATUS_MAQUINA_LABELS = {
    "DISPONIVEL": "Disponivel",
    "EM_USO": "Em uso",
    "EM_MANUTENCAO": "Em manutencao",
    "INATIVA": "Inativa",
}

STATUS_ORDEM_LABELS = {
    "ABERTA": "Aberta",
    "EM_EXECUCAO": "Em execucao",
    "CONCLUIDA": "Concluida",
    "CANCELADA": "Cancelada",
}

STATUS_MANUTENCAO_LABELS = {
    "ABERTA": "Aberta",
    "EM_EXECUCAO": "Em execucao",
    "CONCLUIDA": "Concluida",
    "CANCELADA": "Cancelada",
}

PERIODICIDADE_OPCOES = [
    "30 DIAS",
    "60 DIAS",
    "90 DIAS",
    "180 DIAS",
    "6 MESES",
    "12 MESES",
    "500 HORAS",
    "1000 HORAS",
]


def plano_usa_hodometro(plano: dict) -> bool:
    return "HORA" in (plano.get("periodicidade") or "").upper()


def status_label(status: str | None, labels: dict[str, str]) -> str:
    if not status:
        return "—"
    return labels.get(status, status)


def status_options(values: list[str], labels: dict[str, str]) -> list[str]:
    return [labels.get(value, value) for value in values]


def status_from_label(
    label: str,
    values: list[str],
    labels: dict[str, str],
) -> str:
    for value in values:
        if labels.get(value, value) == label:
            return value
    return label
