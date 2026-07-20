from datetime import datetime
from pydantic import BaseModel

class Pessoa(BaseModel):
    id_pessoa: int
    nome: str
    documento: str

class Usuario(BaseModel):
    id_usuario: int
    id_pessoa: int
    nome: str
    ativo: bool
    perfis: list[str] = []

    def has_profile(self, nome_perfil: str) -> bool:
        return nome_perfil in self.perfis

class IdentidadeExterna(BaseModel):
    id_identidade_externa: int
    id_usuario: int
    provedor: str
    provedor_user_id: str
    email_provedor: str
    criado_em: datetime

class LoginResult(BaseModel):
    usuario: Usuario
    novo_vinculo: bool

class NovoUsuario(BaseModel):
    nome: str
    documento: str
    email: str
    perfil: str = "usuario"
