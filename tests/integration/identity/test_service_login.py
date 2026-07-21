"""Testes de integracao do fluxo de login (IdentityService.login_com_google)."""

from unittest.mock import patch

import pytest

from app.core.errors import InactiveUserError, LoginNotAuthorizedError
from app.identity.service import PROVEDOR_GOOGLE


def _google_claims(sub: str, email: str) -> dict[str, str]:
    return {"sub": sub, "email": email}


@patch("app.identity.service.google_id_token.verify_oauth2_token")
def test_login_returns_existing_user_by_external_id(
    mock_verify, identity_service, identity_repository, sample_person_data
):
    pessoa = identity_repository.create_person(**sample_person_data)
    google_sub = "google-existing-sub"
    usuario = identity_repository.provision_user_for_person(
        pessoa, PROVEDOR_GOOGLE, google_sub, sample_person_data["email"]
    )
    mock_verify.return_value = _google_claims(google_sub, sample_person_data["email"])

    result = identity_service.login_com_google("fake-token")

    assert result.novo_vinculo is False
    assert result.usuario.id_usuario == usuario.id_usuario
    assert result.usuario.ativo is True


@patch("app.identity.service.google_id_token.verify_oauth2_token")
def test_login_provisions_user_when_person_exists_without_user(
    mock_verify, identity_service, identity_repository, sample_person_data
):
    pessoa = identity_repository.create_person(**sample_person_data)
    google_sub = "google-new-user-sub"
    mock_verify.return_value = _google_claims(google_sub, sample_person_data["email"])

    result = identity_service.login_com_google("fake-token")

    assert result.novo_vinculo is True
    assert result.usuario.id_pessoa == pessoa.id_pessoa
    assert result.usuario.perfis == ["usuario"]

    found = identity_repository.get_user_by_external_id(PROVEDOR_GOOGLE, google_sub)
    assert found is not None
    assert found.id_usuario == result.usuario.id_usuario


@patch("app.identity.service.google_id_token.verify_oauth2_token")
def test_login_links_external_identity_for_existing_user_without_link(
    mock_verify, identity_service, identity_repository, sample_person_data
):
    pessoa = identity_repository.create_person(**sample_person_data)
    usuario = identity_repository.create_user(pessoa)
    google_sub = "google-link-sub"
    mock_verify.return_value = _google_claims(google_sub, sample_person_data["email"])

    result = identity_service.login_com_google("fake-token")

    assert result.novo_vinculo is True
    assert result.usuario.id_usuario == usuario.id_usuario

    found = identity_repository.get_user_by_external_id(PROVEDOR_GOOGLE, google_sub)
    assert found is not None
    assert found.id_usuario == usuario.id_usuario


@patch("app.identity.service.google_id_token.verify_oauth2_token")
def test_login_rejects_unknown_email(mock_verify, identity_service):
    mock_verify.return_value = _google_claims("google-unknown-sub", "unknown@example.com")

    with pytest.raises(LoginNotAuthorizedError, match="No registration found"):
        identity_service.login_com_google("fake-token")


@patch("app.identity.service.google_id_token.verify_oauth2_token")
def test_login_rejects_inactive_user(
    mock_verify, identity_service, identity_repository, sample_person_data
):
    pessoa = identity_repository.create_person(**sample_person_data)
    google_sub = "google-inactive-sub"
    usuario = identity_repository.provision_user_for_person(
        pessoa, PROVEDOR_GOOGLE, google_sub, sample_person_data["email"]
    )
    identity_repository.deactivate_user(usuario.id_usuario)
    mock_verify.return_value = _google_claims(google_sub, sample_person_data["email"])

    with pytest.raises(InactiveUserError, match="deactivated"):
        identity_service.login_com_google("fake-token")


def test_create_user_registers_person_and_user(identity_service, identity_repository, sample_person_data):
    usuario = identity_service.create_user(**sample_person_data)

    assert usuario is not None
    assert usuario.nome == sample_person_data["nome"]
    assert usuario.perfis == ["usuario"]

    pessoa = identity_repository.get_person_by_email(sample_person_data["email"])
    assert pessoa is not None
    assert pessoa.documento == sample_person_data["documento"]
