"""Entrypoint da camada de aplicacao (API HTTP)."""

from __future__ import annotations

from fastapi import FastAPI

from app.core.database import check_connection
from app.identity.controller import router as identity_router
from app.identity.controller import users_router

app = FastAPI(title="Agro Tech API")
app.include_router(identity_router)
app.include_router(users_router)


@app.get("/health")
def health() -> dict:
    ok, message = check_connection()
    return {"status": "ok" if ok else "error", "message": message}
