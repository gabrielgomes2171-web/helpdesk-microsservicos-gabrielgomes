"""Usuários de exemplo (só para aula). Use DADOS_EXEMPLO=0 em produção.

A ORDEM IMPORTA: os ids gerados (admin=1, ana=2, bruno=3, carla=4, diego=5)
são usados pelos chamados de exemplo no serviço de Chamados.
"""
import os

from sqlalchemy.orm import Session

from app.usuarios import servico as usuarios
from app.usuarios.esquemas import UsuarioCriar

SENHA = os.getenv("SENHA_EXEMPLO", "Helpdesk2026")

USUARIOS = [
    ("Admin TI", "admin@empresa.com", "admin"),
    ("Ana Souza", "ana@empresa.com", "solicitante"),
    ("Bruno Lima", "bruno@empresa.com", "solicitante"),
    ("Carla Dias", "carla@empresa.com", "tecnico"),
    ("Diego Rocha", "diego@empresa.com", "tecnico"),
]


def carregar(db: Session) -> None:
    if usuarios.listar(db):
        return
    for nome, email, perfil in USUARIOS:
        usuarios.criar(db, UsuarioCriar(nome=nome, email=email, perfil=perfil, senha=SENHA))