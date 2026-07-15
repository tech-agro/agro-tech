"""Entrypoint da camada de aplicacao."""

from app.core.database import check_connection

def startup() -> dict:
    ok, message = check_connection()
    return {"status": "ok" if ok else "error", "message": message}
