import requests

from app.core.config import settings

BASE_URL = f"{settings.api_base_url}/producao"


def _levantar_erro_amigavel(resposta: requests.Response) -> None:
    if resposta.ok:
        return
    try:
        detalhe = resposta.json().get("detail", resposta.text)
    except ValueError:
        detalhe = resposta.text
    raise RuntimeError(detalhe)


def listar(caminho: str, params: dict | None = None) -> list[dict]:
    resposta = requests.get(f"{BASE_URL}{caminho}", params=params, timeout=10)
    resposta.raise_for_status()
    return resposta.json()


def obter(caminho: str) -> dict | None:
    resposta = requests.get(f"{BASE_URL}{caminho}", timeout=10)
    if resposta.status_code == 404:
        return None
    resposta.raise_for_status()
    return resposta.json()


def criar(caminho: str, payload: dict) -> dict:
    resposta = requests.post(f"{BASE_URL}{caminho}", json=payload, timeout=10)
    _levantar_erro_amigavel(resposta)
    return resposta.json()


def acionar(caminho: str, payload: dict | None = None) -> dict:
    """POST para uma operacao nomeada (ex: /plantios/{id}/iniciar), sem semantica de criacao de recurso."""
    resposta = requests.post(f"{BASE_URL}{caminho}", json=payload, timeout=10)
    _levantar_erro_amigavel(resposta)
    return resposta.json()


def upsert(caminho: str, payload: dict) -> dict:
    resposta = requests.put(f"{BASE_URL}{caminho}", json=payload, timeout=10)
    _levantar_erro_amigavel(resposta)
    return resposta.json()


def atualizar(caminho: str, params: dict | None = None) -> dict:
    resposta = requests.patch(f"{BASE_URL}{caminho}", params=params, timeout=10)
    _levantar_erro_amigavel(resposta)
    return resposta.json()


def remover(caminho: str) -> dict:
    resposta = requests.delete(f"{BASE_URL}{caminho}", timeout=10)
    _levantar_erro_amigavel(resposta)
    return resposta.json()
