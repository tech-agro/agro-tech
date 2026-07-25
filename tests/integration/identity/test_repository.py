"""Testes de integracao do IdentityRepository."""

from sqlalchemy import text

from app.identity.models import Pessoa


def test_create_person_persists_pessoa_and_email(identity_repository, sample_person_data):
    pessoa = identity_repository.create_person(**sample_person_data)

    assert pessoa is not None
    assert pessoa.nome == sample_person_data["nome"]
    assert pessoa.documento == sample_person_data["documento"]

    found = identity_repository.get_person_by_email(sample_person_data["email"])
    assert found == pessoa


def test_create_user_assigns_default_profile(identity_repository, sample_person_data):
    pessoa = identity_repository.create_person(**sample_person_data)
    usuario = identity_repository.create_user(pessoa)

    assert usuario is not None
    assert usuario.id_pessoa == pessoa.id_pessoa
    assert usuario.ativo is True
    assert usuario.perfis == ["usuario"]

    by_id = identity_repository.get_user_by_id(usuario.id_usuario)
    by_person = identity_repository.get_user_by_person_id(pessoa.id_pessoa)

    assert by_id == usuario
    assert by_person == usuario


def test_create_user_with_admin_profile(identity_repository, sample_person_data):
    pessoa = identity_repository.create_person(**sample_person_data)

    usuario = identity_repository.create_user(pessoa, perfil_padrao="admin")

    assert usuario is not None
    assert usuario.perfis == ["admin"]
    assert identity_repository.user_has_profile(usuario.id_usuario, "admin")


def test_provision_user_for_person_creates_user_and_external_identity(
    identity_repository, sample_person_data
):
    pessoa = identity_repository.create_person(**sample_person_data)
    google_sub = "google-sub-123"
    google_email = sample_person_data["email"]

    usuario = identity_repository.provision_user_for_person(
        pessoa, "google", google_sub, google_email
    )

    assert usuario is not None
    assert usuario.perfis == ["usuario"]

    found = identity_repository.get_user_by_external_id("google", google_sub)
    assert found is not None
    assert found.id_usuario == usuario.id_usuario


def test_link_external_identity(identity_repository, sample_person_data):
    pessoa = identity_repository.create_person(**sample_person_data)
    usuario = identity_repository.create_user(pessoa)

    linked = identity_repository.link_external_identity(
        usuario.id_usuario, "google", "google-sub-456", sample_person_data["email"]
    )

    assert linked is True
    found = identity_repository.get_user_by_external_id("google", "google-sub-456")
    assert found is not None
    assert found.id_usuario == usuario.id_usuario


def test_update_person_add_email_and_phone(identity_repository, sample_person_data, unique_suffix):
    pessoa = identity_repository.create_person(**sample_person_data)

    assert identity_repository.update_person(pessoa.id_pessoa, nome="Nome Atualizado") is True

    extra_email = f"extra-{unique_suffix}@example.com"
    phone = "11999990000"

    assert identity_repository.add_email(pessoa.id_pessoa, extra_email) is True
    assert identity_repository.add_phone(pessoa.id_pessoa, phone) is True

    updated = identity_repository.get_person_by_email(extra_email)
    assert updated is not None
    assert updated.id_pessoa == pessoa.id_pessoa


def test_assign_and_revoke_profile(identity_repository, sample_person_data):
    pessoa = identity_repository.create_person(**sample_person_data)
    usuario = identity_repository.create_user(pessoa)

    assert identity_repository.assign_profile(usuario.id_usuario, "admin") is True
    assert identity_repository.user_has_profile(usuario.id_usuario, "admin") is True

    refreshed = identity_repository.get_user_by_id(usuario.id_usuario)
    assert refreshed is not None
    assert "admin" in refreshed.perfis

    assert identity_repository.revoke_profile(usuario.id_usuario, "admin") is True
    assert identity_repository.user_has_profile(usuario.id_usuario, "admin") is False


def test_deactivate_and_reactivate_user(identity_repository, sample_person_data):
    pessoa = identity_repository.create_person(**sample_person_data)
    usuario = identity_repository.create_user(pessoa)

    assert identity_repository.deactivate_user(usuario.id_usuario) is True

    deactivated = identity_repository.get_user_by_id(usuario.id_usuario)
    assert deactivated is not None
    assert deactivated.ativo is False

    assert identity_repository.reactivate_user(usuario.id_usuario) is True

    reactivated = identity_repository.get_user_by_id(usuario.id_usuario)
    assert reactivated is not None
    assert reactivated.ativo is True


def test_has_permission(identity_repository, sample_person_data, pg_connector):
    pessoa = identity_repository.create_person(**sample_person_data)
    usuario = identity_repository.create_user(pessoa, perfil_padrao="admin")
    permission = f"perm-{sample_person_data['documento']}"

    with pg_connector.pool.begin() as conn:
        conn.execute(
            text("INSERT INTO permissao (descricao) VALUES (:descricao) ON CONFLICT DO NOTHING"),
            {"descricao": permission},
        )
        conn.execute(
            text(
                """
                INSERT INTO perfil_permissao (id_perfil, id_permissao)
                SELECT pa.id_perfil, pm.id_permissao
                FROM perfil_acesso pa, permissao pm
                WHERE pa.nome = 'admin' AND pm.descricao = :descricao
                ON CONFLICT DO NOTHING
                """
            ),
            {"descricao": permission},
        )

    assert identity_repository.has_permission(usuario.id_usuario, permission) is True
    assert identity_repository.has_permission(usuario.id_usuario, "permissao-inexistente") is False
