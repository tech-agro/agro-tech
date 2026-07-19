import logging

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import settings
from app.core.database import pg_connector
from app.core.errors import InactiveUserError, LoginNotAuthorizedError
from app.identity.models import LoginResult, Usuario
from app.identity.repository import IdentityRepository

PROVEDOR_GOOGLE = "google"

logger = logging.getLogger(__name__)


class IdentityService:

    def __init__(self, repository: IdentityRepository | None = None) -> None:
        self.repository = repository or IdentityRepository(pg_connector, logger)

    def login_com_google(self, id_token_jwt: str) -> LoginResult:
        """Valida o id_token do Google e resolve (ou vincula) o usuario correspondente."""
        claims = google_id_token.verify_oauth2_token(
            id_token_jwt, google_requests.Request(), audience=settings.google_client_id
        )
        sub = claims["sub"]
        email = claims["email"]

        usuario = self.repository.get_user_by_external_id(PROVEDOR_GOOGLE, sub)
        novo_vinculo = usuario is None

        if usuario is None:
            pessoa = self.repository.get_person_by_email(email)
            if pessoa is None:
                raise LoginNotAuthorizedError(
                    "No registration found for this e-mail. Contact the administrator."
                )
            usuario = self.repository.get_user_by_person_id(pessoa.id_pessoa)
            if usuario is not None:
                self.repository.link_external_identity(usuario.id_usuario, PROVEDOR_GOOGLE, sub, email)
            else:
                usuario = self.repository.provision_user_for_person(pessoa, PROVEDOR_GOOGLE, sub, email)

        if usuario is None:
            raise LoginNotAuthorizedError("Could not provision access. Please try again.")
        if not usuario.ativo:
            raise InactiveUserError("This user is deactivated.")

        return LoginResult(usuario=usuario, novo_vinculo=novo_vinculo)

    def has_permission(self, id_usuario: int, descricao_permissao: str) -> bool:
        return self.repository.has_permission(id_usuario, descricao_permissao)

    def is_admin(self, id_usuario: int) -> bool:
        return self.repository.user_has_profile(id_usuario, "admin")

    def create_user(self, nome: str, documento: str, email: str, perfil: str = "usuario") -> Usuario | None:
        pessoa = self.repository.create_person(nome, documento, email)
        if pessoa is None:
            return None
        return self.repository.create_user(pessoa, perfil)

    def get_user(self, id_usuario: int) -> Usuario | None:
        return self.repository.get_user_by_id(id_usuario)

    def remove_user(self, id_usuario: int) -> bool:
        return self.repository.deactivate_user(id_usuario)
