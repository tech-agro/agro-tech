"""Select helpers for Manutencao dialogs and screens."""

from __future__ import annotations

import streamlit as st

from components.manutencao.constants import STATUS_MANUTENCAO_LABELS, status_label


def rotulo_fazenda(fazenda: dict) -> str:
    localizacao = fazenda.get("localizacao")
    if localizacao:
        return f"{fazenda['nome']} — {localizacao}"
    return fazenda["nome"]


def select_fazenda(
    label: str,
    fazendas: list[dict],
    *,
    key: str,
    permitir_todos: bool = False,
) -> int | None:
    if not fazendas and not permitir_todos:
        st.caption("Cadastre uma fazenda em Producao antes de continuar.")
        return None

    opcoes: list[str] = []
    mapa: dict[str, int] = {}
    if permitir_todos:
        opcoes.append("Todos")
    for fazenda in fazendas:
        rotulo = rotulo_fazenda(fazenda)
        opcoes.append(rotulo)
        mapa[rotulo] = fazenda["id_fazenda"]

    escolha = st.selectbox(label, opcoes, key=key)
    if escolha == "Todos":
        return None
    return mapa.get(escolha)


def select_tipo_maquina(
    label: str,
    tipos: list[dict],
    *,
    key: str,
    permitir_todos: bool = False,
    id_atual: int | None = None,
) -> int | None:
    if not tipos and not permitir_todos:
        st.caption("Cadastre um tipo de maquina antes de continuar.")
        return None

    opcoes: list[str] = []
    mapa: dict[str, int] = {}
    if permitir_todos:
        opcoes.append("Todos")
    for tipo in tipos:
        rotulo = tipo["descricao"]
        opcoes.append(rotulo)
        mapa[rotulo] = tipo["id_tipo_maquina"]

    index = 0
    if id_atual is not None:
        for indice, rotulo in enumerate(opcoes):
            if mapa.get(rotulo) == id_atual:
                index = indice
                break

    escolha = st.selectbox(label, opcoes, index=index, key=key)
    if escolha == "Todos":
        return None
    return mapa.get(escolha)


def select_maquina(
    label: str,
    maquinas: list[dict],
    *,
    key: str,
    permitir_todos: bool = False,
    id_atual: int | None = None,
) -> int | None:
    if not maquinas and not permitir_todos:
        st.caption("Cadastre uma maquina antes de continuar.")
        return None

    opcoes: list[str] = []
    mapa: dict[str, int] = {}
    if permitir_todos:
        opcoes.append("Todos")
    for maquina in maquinas:
        rotulo = f"#{maquina['id_maquina']} - {maquina['nome']}"
        opcoes.append(rotulo)
        mapa[rotulo] = maquina["id_maquina"]

    index = 0
    if id_atual is not None:
        for indice, rotulo in enumerate(opcoes):
            if mapa.get(rotulo) == id_atual:
                index = indice
                break

    escolha = st.selectbox(label, opcoes, index=index, key=key)
    if escolha == "Todos":
        return None
    return mapa.get(escolha)


def rotulo_plano(plano: dict) -> str:
    nome = plano.get("nome_maquina") or "maquina"
    periodicidade = plano.get("periodicidade") or "—"
    proxima = plano.get("proxima_execucao") or "—"
    return f"#{plano['id_plano']} - {nome} ({periodicidade}) prox: {proxima}"


def select_plano(
    label: str,
    planos: list[dict],
    *,
    key: str,
    permitir_todos: bool = False,
    id_maquina: int | None = None,
) -> dict | None:
    itens = planos
    if id_maquina is not None:
        itens = [plano for plano in planos if plano["id_maquina"] == id_maquina]

    if not itens and not permitir_todos:
        st.caption("Cadastre um plano de manutencao antes de continuar.")
        return None

    opcoes: list[str] = []
    mapa: dict[str, dict] = {}
    if permitir_todos:
        opcoes.append("Todos")
    for plano in itens:
        rotulo = rotulo_plano(plano)
        opcoes.append(rotulo)
        mapa[rotulo] = plano

    escolha = st.selectbox(label, opcoes, key=key)
    if escolha == "Todos":
        return None
    return mapa.get(escolha)


def rotulo_manutencao(item: dict) -> str:
    manutencao = item["manutencao"]
    nome = item.get("nome_maquina") or "maquina"
    defeito = item["corretiva"].get("defeito_relatado") or "sem defeito"
    data = manutencao.get("dt_inicio") or "—"
    status = status_label(manutencao.get("status"), STATUS_MANUTENCAO_LABELS)
    return (
        f"#{manutencao['id_manutencao']} - {nome} "
        f"({status}) - {defeito} [{data}]"
    )


def select_manutencao_corretiva(
    label: str,
    manutencoes: list[dict],
    *,
    key: str,
    permitir_todos: bool = False,
    apenas_abertas: bool = False,
) -> int | None:
    itens = manutencoes
    if apenas_abertas:
        itens = [
            item
            for item in manutencoes
            if item["manutencao"]["status"] in {"ABERTA", "EM_EXECUCAO"}
        ]

    if not itens and not permitir_todos:
        st.caption("Registre uma manutencao corretiva aberta antes de continuar.")
        return None

    opcoes: list[str] = []
    mapa: dict[str, int] = {}
    if permitir_todos:
        opcoes.append("Todos")
    for item in itens:
        rotulo = rotulo_manutencao(item)
        opcoes.append(rotulo)
        mapa[rotulo] = item["manutencao"]["id_manutencao"]

    escolha = st.selectbox(label, opcoes, key=key)
    if escolha == "Todos":
        return None
    return mapa.get(escolha)
