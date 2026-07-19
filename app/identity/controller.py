from datetime import datetime, timedelta, timezone
from urllib.parse import quote, urlencode

import jwt
import requests
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.core.errors import InactiveUserError, LoginNotAuthorizedError
from app.core.security import generate_oauth_state
from app.identity.models import NovoUsuario, Usuario
from app.identity.service import IdentityService

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
JWT_ALGORITHM = "HS256"
STATE_TTL_SECONDS = 300

bearer_scheme = HTTPBearer(auto_error=False)


class IdentityController:
    """Adapter between the HTTP interface (FastAPI) and the identity service."""

    def __init__(self, service: IdentityService | None = None) -> None:
        self.service = service or IdentityService()
        self.router = APIRouter(prefix="/auth", tags=["auth"])
        self.users_router = APIRouter(prefix="/users", tags=["users"])
        self._register_routes()

    def _register_routes(self) -> None:
        self.router.get("/login", name="login")(self.login)
        self.router.get("/callback", name="oauth_callback")(self.callback)
        self.router.get("/me", name="get_current_user", response_model=Usuario)(self.me)
        self.router.post("/logout", name="logout")(self.logout)
        self.router.get("/permissions/{descricao_permissao}", name="check_permission")(self.check_permission)
        self.router.get("/is-admin", name="is_admin")(self.is_admin)

        self.users_router.post("", name="create_user", response_model=Usuario)(self.create_user)
        self.users_router.get("/{id_usuario}", name="get_user", response_model=Usuario)(self.get_user)
        self.users_router.delete("/{id_usuario}", name="remove_user")(self.remove_user)

    def _authenticate(self, credentials: HTTPAuthorizationCredentials | None) -> Usuario:
        if credentials is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing authentication token.")
        try:
            payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=[JWT_ALGORITHM])
        except jwt.PyJWTError as exc:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token.") from exc
        return Usuario(
            id_usuario=payload["id_usuario"],
            id_pessoa=payload["id_pessoa"],
            nome=payload["nome"],
            ativo=payload["ativo"],
            perfis=payload["perfis"],
        )

    def _authenticate_admin(self, credentials: HTTPAuthorizationCredentials | None) -> Usuario:
        usuario = self._authenticate(credentials)
        if not self.service.is_admin(usuario.id_usuario):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin profile required.")
        return usuario

    def _issue_state(self) -> str:
        """Signed, self-expiring OAuth state: no server-side storage needed,
        so it works the same with 1 or N API workers."""
        payload = {
            "nonce": generate_oauth_state(),
            "exp": datetime.now(timezone.utc) + timedelta(seconds=STATE_TTL_SECONDS),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)

    def _is_valid_state(self, state: str) -> bool:
        try:
            jwt.decode(state, settings.jwt_secret_key, algorithms=[JWT_ALGORITHM])
            return True
        except jwt.PyJWTError:
            return False

    def _issue_jwt(self, usuario: Usuario) -> str:
        payload = {
            **usuario.model_dump(),
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=JWT_ALGORITHM)

    def _redirect_with_error(self, message: str) -> RedirectResponse:
        return RedirectResponse(f"{settings.frontend_url}/?login_error={quote(message)}")

    def login(self) -> dict:
        """Returns the Google authorization URL for the client to redirect the user to."""
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": self._issue_state(),
            "prompt": "select_account",
        }
        return {"authorization_url": f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}"}

    def callback(self, code: str, state: str) -> RedirectResponse:
        """Receives Google's redirect, exchanges the code for tokens, and issues the app's own JWT.

        On any failure, redirects back to the frontend with `login_error` in the query string
        instead of returning a raw HTTP error: the browser never gets stuck on an API page.
        """
        if not self._is_valid_state(state):
            return self._redirect_with_error("Invalid or expired OAuth state.")

        token_response = requests.post(
            GOOGLE_TOKEN_ENDPOINT,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        if not token_response.ok:
            return self._redirect_with_error("Could not validate the login with Google.")
        id_token_jwt = token_response.json()["id_token"]

        try:
            resultado = self.service.login_com_google(id_token_jwt)
        except (LoginNotAuthorizedError, InactiveUserError) as exc:
            return self._redirect_with_error(str(exc))

        app_token = self._issue_jwt(resultado.usuario)
        return RedirectResponse(f"{settings.frontend_url}/?token={app_token}")

    def me(self, credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> Usuario:
        return self._authenticate(credentials)

    def logout(self, credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> dict:
        """Stateless: the client is the one who discards the token. Endpoint exists for API symmetry."""
        self._authenticate(credentials)
        return {"message": "Logged out."}

    def check_permission(
        self, descricao_permissao: str, credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)
    ) -> dict:
        usuario = self._authenticate(credentials)
        return {"has_permission": self.service.has_permission(usuario.id_usuario, descricao_permissao)}

    def is_admin(self, credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> dict:
        usuario = self._authenticate(credentials)
        return {"is_admin": self.service.is_admin(usuario.id_usuario)}

    def create_user(
        self, dados: NovoUsuario, credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)
    ) -> Usuario:
        self._authenticate_admin(credentials)
        usuario = self.service.create_user(dados.nome, dados.documento, dados.email, dados.perfil)
        if usuario is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Could not create the user (document or e-mail already registered?)."
            )
        return usuario

    def get_user(
        self, id_usuario: int, credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)
    ) -> Usuario:
        self._authenticate_admin(credentials)
        usuario = self.service.get_user(id_usuario)
        if usuario is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
        return usuario

    def remove_user(
        self, id_usuario: int, credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)
    ) -> dict:
        self._authenticate_admin(credentials)
        if not self.service.remove_user(id_usuario):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not remove the user.")
        return {"message": "User deactivated."}


identity_controller = IdentityController()
router = identity_controller.router
users_router = identity_controller.users_router
