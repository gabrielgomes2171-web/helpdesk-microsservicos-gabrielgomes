"""Chamadas HTTP para os outros serviços.

No monólito eram chamadas de função (inventario.obter, usuarios.obter_tecnico).
Agora passam pela rede, então podem demorar ou falhar. Por isso:
- toda chamada tem tempo limite (timeout);
- qualquer falha de rede vira ServicoIndisponivel, que responde 503;
- o token do usuário é repassado no cabeçalho Authorization.
"""
import os

import httpx

from app.erros import NaoEncontrado, RegraDeNegocio

USUARIOS_URL = os.getenv("USUARIOS_URL", "http://usuarios:8000")
INVENTARIO_URL = os.getenv("INVENTARIO_URL", "http://inventario:8000")
TIMEOUT = httpx.Timeout(float(os.getenv("TIMEOUT_SEGUNDOS", "3")))


class ServicoIndisponivel(Exception):
    pass


def _get(url: str, token: str, servico: str) -> dict | None:
    """Faz o GET. Devolve o JSON, None se 404, ou lança ServicoIndisponivel."""
    try:
        resposta = httpx.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT)
    except httpx.RequestError as erro:  # timeout, conexão recusada, serviço fora do ar...
        raise ServicoIndisponivel(
            f"O serviço de {servico} está indisponível. Tente novamente em instantes."
        ) from erro
    if resposta.status_code == 404:
        return None
    if resposta.status_code != 200:
        raise ServicoIndisponivel(f"O serviço de {servico} respondeu com erro ({resposta.status_code}).")
    return resposta.json()


def obter_ativo(ativo_id: int, token: str) -> dict:
    ativo = _get(f"{INVENTARIO_URL}/ativos/{ativo_id}", token, "Inventário")
    if ativo is None:
        raise NaoEncontrado(f"Ativo {ativo_id} não encontrado.")
    return ativo


def obter_tecnico(usuario_id: int, token: str) -> dict:
    usuario = _get(f"{USUARIOS_URL}/usuarios/{usuario_id}", token, "Usuários")
    if usuario is None:
        raise NaoEncontrado(f"Usuário {usuario_id} não encontrado.")
    if usuario.get("perfil") != "tecnico":
        raise RegraDeNegocio(f"Usuário {usuario_id} não é técnico.")
    return usuario