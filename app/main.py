"""Entrypoint da camada de aplicacao (API HTTP)."""

from __future__ import annotations

from fastapi import FastAPI

from app.comercial.controller import router as comercial_router
from app.compras.controller import router as purchases_router
from app.core.database import check_connection
from app.estoque.controller import router as estoque_router
from app.identity.controller import router as identity_router
from app.identity.controller import users_router
from app.inteligencia.controller import router as inteligencia_router
from app.manutencao.controller import router as manutencao_router
from app.producao.controller import router as producao_router

app = FastAPI(title="Agro Tech API")
app.include_router(identity_router)
app.include_router(users_router)
app.include_router(manutencao_router)
app.include_router(producao_router)
app.include_router(purchases_router)
app.include_router(estoque_router)
app.include_router(inteligencia_router)
app.include_router(comercial_router)


@app.get("/health")
def health() -> dict:
    ok, message = check_connection()
    return {"status": "ok" if ok else "error", "message": message}
