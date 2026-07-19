from datetime import datetime, timezone
from sqlalchemy import text

from app.identity.models import Pessoa, Usuario

class IdentityRepository:
    def __init__(self, pg_connector, logger):
        self.pg_connector = pg_connector
        self.logger = logger

    def get_user_by_external_id(self, provider: str, provider_user_id: str) -> Usuario | None:
        sql = text(
            """
            select u.id_usuario, u.id_pessoa, u.ativo, p.nome
            from usuario u
            join pessoa p on p.id_pessoa = u.id_pessoa
            join identidade_externa ie on ie.id_usuario = u.id_usuario
            where ie.provedor = :provider and ie.provedor_user_id = :provider_user_id
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                var_dict = {"provider": provider, "provider_user_id": provider_user_id}
                result = conn.execute(sql, var_dict).fetchone()
                if result is None:
                    return None
                return Usuario(
                    id_usuario=result.id_usuario,
                    id_pessoa=result.id_pessoa,
                    nome=result.nome,
                    ativo=result.ativo,
                    perfis=self.list_user_profiles(conn, result.id_usuario),
                )
        except Exception as e:
            self.logger.error(f"Error fetching user by external ID: {e}")
            return None

    def get_person_by_email(self, email: str) -> Pessoa | None:
        sql = text(
            """
            select p.id_pessoa, p.nome, p.documento
            from pessoa p
            join email e on e.id_pessoa = p.id_pessoa
            where e.email = :email
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                result = conn.execute(sql, {"email": email}).fetchone()
                if result is None:
                    return None
                return Pessoa(
                    id_pessoa=result.id_pessoa,
                    nome=result.nome,
                    documento=result.documento,
                )
        except Exception as e:
            self.logger.error(f"Error fetching person by email: {e}")
            return None

    def get_user_by_person_id(self, id_pessoa: int) -> Usuario | None:
        sql = text(
            """
            select u.id_usuario, u.id_pessoa, u.ativo, p.nome
            from usuario u
            join pessoa p on p.id_pessoa = u.id_pessoa
            where u.id_pessoa = :id_pessoa
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                result = conn.execute(sql, {"id_pessoa": id_pessoa}).fetchone()
                if result is None:
                    return None
                return Usuario(
                    id_usuario=result.id_usuario,
                    id_pessoa=result.id_pessoa,
                    nome=result.nome,
                    ativo=result.ativo,
                    perfis=self.list_user_profiles(conn, result.id_usuario),
                )
        except Exception as e:
            self.logger.error(f"Error fetching user by person id: {e}")
            return None

    def link_external_identity(
        self, id_usuario: int, provider: str, provider_user_id: str, provider_email: str
    ) -> bool:
        try:
            with self.pg_connector.pool.begin() as conn:
                self._insert_external_identity(conn, id_usuario, provider, provider_user_id, provider_email)
            return True
        except Exception as e:
            self.logger.error(f"Error linking external identity: {e}")
            return False

    def provision_user_for_person(
        self,
        pessoa: Pessoa,
        provider: str,
        provider_user_id: str,
        provider_email: str,
        default_profile: str = "usuario",
    ) -> Usuario | None:
        try:
            with self.pg_connector.pool.begin() as conn:
                id_usuario = self._insert_usuario(conn, pessoa.id_pessoa, default_profile)
                self._insert_external_identity(conn, id_usuario, provider, provider_user_id, provider_email)
                return Usuario(
                    id_usuario=id_usuario,
                    id_pessoa=pessoa.id_pessoa,
                    nome=pessoa.nome,
                    ativo=True,
                    perfis=self.list_user_profiles(conn, id_usuario),
                )
        except Exception as e:
            self.logger.error(f"Error provisioning user for person: {e}")
            return None

    def create_person(self, nome: str, documento: str, email: str) -> Pessoa | None:
        """Cria a pessoa e ja registra o e-mail (necessario pro login via Google casar depois)."""
        try:
            with self.pg_connector.pool.begin() as conn:
                id_pessoa = conn.execute(
                    text("insert into pessoa (nome, documento) values (:nome, :documento) returning id_pessoa"),
                    {"nome": nome, "documento": documento},
                ).scalar_one()
                conn.execute(
                    text("insert into email (id_pessoa, email) values (:id_pessoa, :email)"),
                    {"id_pessoa": id_pessoa, "email": email},
                )
                return Pessoa(id_pessoa=id_pessoa, nome=nome, documento=documento)
        except Exception as e:
            self.logger.error(f"Error creating person: {e}")
            return None

    def create_user(self, pessoa: Pessoa, perfil_padrao: str = "usuario") -> Usuario | None:
        try:
            with self.pg_connector.pool.begin() as conn:
                id_usuario = self._insert_usuario(conn, pessoa.id_pessoa, perfil_padrao)
                return Usuario(
                    id_usuario=id_usuario,
                    id_pessoa=pessoa.id_pessoa,
                    nome=pessoa.nome,
                    ativo=True,
                    perfis=self.list_user_profiles(conn, id_usuario),
                )
        except Exception as e:
            self.logger.error(f"Error creating user: {e}")
            return None

    def get_user_by_id(self, id_usuario: int) -> Usuario | None:
        sql = text(
            """
            select u.id_usuario, u.id_pessoa, u.ativo, p.nome
            from usuario u
            join pessoa p on p.id_pessoa = u.id_pessoa
            where u.id_usuario = :id_usuario
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                result = conn.execute(sql, {"id_usuario": id_usuario}).fetchone()
                if result is None:
                    return None
                return Usuario(
                    id_usuario=result.id_usuario,
                    id_pessoa=result.id_pessoa,
                    nome=result.nome,
                    ativo=result.ativo,
                    perfis=self.list_user_profiles(conn, result.id_usuario),
                )
        except Exception as e:
            self.logger.error(f"Error fetching user by id: {e}")
            return None

    def list_user_profiles(self, conn, id_usuario: int) -> list[str]:
        sql = text(
            """
            select pa.nome
            from perfil_acesso pa
            join usuario_perfil up on up.id_perfil = pa.id_perfil
            where up.id_usuario = :id_usuario
            """
        )
        return [row.nome for row in conn.execute(sql, {"id_usuario": id_usuario})]

    def assign_profile(self, id_usuario: int, nome_perfil: str) -> bool:
        sql = text(
            """
            insert into usuario_perfil (id_usuario, id_perfil)
            select :id_usuario, id_perfil from perfil_acesso where nome = :nome_perfil
            on conflict do nothing
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                conn.execute(sql, {"id_usuario": id_usuario, "nome_perfil": nome_perfil})
            return True
        except Exception as e:
            self.logger.error(f"Error assigning profile: {e}")
            return False

    def revoke_profile(self, id_usuario: int, nome_perfil: str) -> bool:
        sql = text(
            """
            delete from usuario_perfil
            where id_usuario = :id_usuario
            and id_perfil = (select id_perfil from perfil_acesso where nome = :nome_perfil)
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                conn.execute(sql, {"id_usuario": id_usuario, "nome_perfil": nome_perfil})
            return True
        except Exception as e:
            self.logger.error(f"Error revoking profile: {e}")
            return False

    def deactivate_user(self, id_usuario: int) -> bool:
        try:
            with self.pg_connector.pool.begin() as conn:
                conn.execute(
                    text("update usuario set ativo = false where id_usuario = :id_usuario"),
                    {"id_usuario": id_usuario},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error deactivating user: {e}")
            return False

    def reactivate_user(self, id_usuario: int) -> bool:
        try:
            with self.pg_connector.pool.begin() as conn:
                conn.execute(
                    text("update usuario set ativo = true where id_usuario = :id_usuario"),
                    {"id_usuario": id_usuario},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error reactivating user: {e}")
            return False

    def update_person(self, id_pessoa: int, nome: str | None = None, documento: str | None = None) -> bool:
        sql = text(
            """
            update pessoa
            set nome = coalesce(:nome, nome),
                documento = coalesce(:documento, documento)
            where id_pessoa = :id_pessoa
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                conn.execute(sql, {"nome": nome, "documento": documento, "id_pessoa": id_pessoa})
            return True
        except Exception as e:
            self.logger.error(f"Error updating person: {e}")
            return False

    def add_email(self, id_pessoa: int, email: str) -> bool:
        try:
            with self.pg_connector.pool.begin() as conn:
                conn.execute(
                    text("insert into email (id_pessoa, email) values (:id_pessoa, :email)"),
                    {"id_pessoa": id_pessoa, "email": email},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error adding email: {e}")
            return False

    def add_phone(self, id_pessoa: int, telefone: str) -> bool:
        try:
            with self.pg_connector.pool.begin() as conn:
                conn.execute(
                    text("insert into telefone (id_pessoa, telefone) values (:id_pessoa, :telefone)"),
                    {"id_pessoa": id_pessoa, "telefone": telefone},
                )
            return True
        except Exception as e:
            self.logger.error(f"Error adding phone: {e}")
            return False

    def has_permission(self, id_usuario: int, descricao_permissao: str) -> bool:
        sql = text(
            """
            select 1
            from perfil_permissao pp
            join permissao pm on pm.id_permissao = pp.id_permissao
            join usuario_perfil up on up.id_perfil = pp.id_perfil
            where up.id_usuario = :id_usuario and pm.descricao = :descricao_permissao
            limit 1
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                var_dict = {"id_usuario": id_usuario, "descricao_permissao": descricao_permissao}
                return conn.execute(sql, var_dict).first() is not None
        except Exception as e:
            self.logger.error(f"Error checking permission: {e}")
            return False

    def user_has_profile(self, id_usuario: int, nome_perfil: str) -> bool:
        sql = text(
            """
            select 1
            from usuario_perfil up
            join perfil_acesso pa on pa.id_perfil = up.id_perfil
            where up.id_usuario = :id_usuario and pa.nome = :nome_perfil
            limit 1
            """
        )
        try:
            with self.pg_connector.pool.begin() as conn:
                var_dict = {"id_usuario": id_usuario, "nome_perfil": nome_perfil}
                return conn.execute(sql, var_dict).first() is not None
        except Exception as e:
            self.logger.error(f"Error checking user profile: {e}")
            return False

    def _insert_usuario(self, conn, id_pessoa: int, perfil_padrao: str) -> int:
        id_usuario = conn.execute(
            text("insert into usuario (id_pessoa, ativo) values (:id_pessoa, true) returning id_usuario"),
            {"id_pessoa": id_pessoa},
        ).scalar_one()
        conn.execute(
            text(
                """
                insert into usuario_perfil (id_usuario, id_perfil)
                select :id_usuario, id_perfil from perfil_acesso where nome = :perfil_padrao
                """
            ),
            {"id_usuario": id_usuario, "perfil_padrao": perfil_padrao},
        )
        return id_usuario

    def _insert_external_identity(
        self, conn, id_usuario: int, provider: str, provider_user_id: str, provider_email: str
    ) -> None:
        conn.execute(
            text(
                """
                insert into identidade_externa
                    (id_usuario, provedor, provedor_user_id, email_provedor, criado_em)
                values
                    (:id_usuario, :provider, :provider_user_id, :provider_email, :criado_em)
                """
            ),
            {
                "id_usuario": id_usuario,
                "provider": provider,
                "provider_user_id": provider_user_id,
                "provider_email": provider_email,
                "criado_em": datetime.now(timezone.utc),
            },
        )
