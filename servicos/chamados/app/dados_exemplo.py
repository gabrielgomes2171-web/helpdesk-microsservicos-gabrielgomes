"""Chamados de exemplo (só para aula). Use DADOS_EXEMPLO=0 em produção.

Gravados direto no banco, sem chamar os outros serviços (na inicialização
eles podem ainda não estar no ar). Os ids abaixo precisam bater com os
dados de exemplo dos serviços de Usuários e Inventário.
"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.chamados import repositorio
from app.chamados.modelos import Chamado
from app.chamados.servico import calcular_prazo
from app.notificacoes import servico as notificacoes

ANA, BRUNO, CARLA = 2, 3, 4          # ids no serviço de Usuários
PC, IMPRESSORA = 1, 2                # ids no serviço de Inventário


def carregar(db: Session) -> None:
    if db.scalar(select(Chamado).limit(1)):
        return
    agora = datetime.now()

    def novo(titulo, descricao, prioridade, solicitante_id, ativo_id=None):
        chamado = repositorio.salvar(db, Chamado(
            titulo=titulo, descricao=descricao, prioridade=prioridade, ativo_id=ativo_id,
            solicitante_id=solicitante_id, status="aberto", criado_em=agora,
            prazo_sla=calcular_prazo(prioridade, agora),
        ))
        notificacoes.notificar(db, "ChamadoAberto", solicitante_id, f"Seu chamado #{chamado.id} foi aberto.")
        return chamado

    c1 = novo("Computador não liga", "Apertei o botão e nada acontece.", "alta", ANA, PC)
    novo("Impressora atolando papel", "Atola a cada 3 folhas.", "media", BRUNO, IMPRESSORA)
    novo("Acesso ao sistema de RH", "Preciso de acesso para a nova estagiária.", "baixa", BRUNO)

    c1.tecnico_id, c1.status = CARLA, "em_atendimento"
    repositorio.salvar(db, c1)
    notificacoes.notificar(db, "ChamadoAtribuido", CARLA, f"O chamado #{c1.id} foi atribuído a você.")