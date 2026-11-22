"""Validação dos tokens JWT.

Este serviço só CONFERE tokens. Quem cria os tokens é o serviço de Usuários,
no login. Os dois usam o mesmo JWT_SEGREDO (vindo do .env).
"""
from dataclasses import dataclass

import jwt

from app.config import JWT_ALGORITMO, JWT_EMISSOR, JWT_SEGREDO


class TokenInvalido(Exception):
    pass


@dataclass(frozen=True)
class UsuarioDoToken:
    """Quem está chamando, segundo o token (sem consultar banco)."""
    id: int
    perfil: str


def ler(token: str) -> UsuarioDoToken:
    """Confere assinatura, validade e emissor; devolve id e perfil."""
    try:
        dados = jwt.decode(
            token, JWT_SEGREDO, algorithms=[JWT_ALGORITMO], issuer=JWT_EMISSOR,
            options={"require": ["exp", "iat", "sub", "iss", "perfil"]},
        )
        return UsuarioDoToken(id=int(dados["sub"]), perfil=str(dados["perfil"]))
    except (jwt.PyJWTError, ValueError, KeyError) as erro:
        raise TokenInvalido() from erro