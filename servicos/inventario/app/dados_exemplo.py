"""Equipamentos de exemplo (só para aula). Use DADOS_EXEMPLO=0 em produção.

Atenção: a ordem importa. Os chamados de exemplo (no serviço de Chamados)
apontam para ativo_id=1 (PAT-0001) e ativo_id=2 (PAT-0002).
"""
from sqlalchemy.orm import Session

from app.inventario import servico as inventario
from app.inventario.esquemas import AtivoCriar

ATIVOS = [
    dict(patrimonio="PAT-0001", tipo="computador", descricao="Desktop Dell OptiPlex", setor="Financeiro"),
    dict(patrimonio="PAT-0002", tipo="impressora", descricao="Impressora HP LaserJet", setor="RH"),
    dict(patrimonio="PAT-0003", tipo="notebook", descricao="Notebook Lenovo ThinkPad", setor="TI"),
]


def carregar(db: Session) -> None:
    if inventario.listar(db):
        return
    for ativo in ATIVOS:
        inventario.criar(db, AtivoCriar(**ativo))