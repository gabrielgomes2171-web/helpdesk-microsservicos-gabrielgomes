import os

os.environ["JWT_SEGREDO"] = "segredo-so-para-testes-com-mais-de-32-caracteres"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["DADOS_EXEMPLO"] = "0"

from datetime import datetime, timedelta, timezone  # noqa: E402

import httpx  # noqa: E402
import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import clientes  # noqa: E402
from app.config import JWT_ALGORITMO, JWT_EMISSOR, JWT_SEGREDO  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

ANA, BIA, CARLA = 2, 3, 4


def token_de(usuario_id: int, perfil: str, segredo: str = JWT_SEGREDO) -> dict:
    agora = datetime.now(timezone.utc)
    dados = {"sub": str(usuario_id), "perfil": perfil, "iat": agora,
             "exp": agora + timedelta(minutes=60), "iss": JWT_EMISSOR}
    return {"Authorization": f"Bearer {jwt.encode(dados, segredo, algorithm=JWT_ALGORITMO)}"}


class RedeFalsa:
    """Simula os serviços de Usuários e Inventário (e a queda deles)."""

    def __init__(self):
        self.fora_do_ar: set[str] = set()
        self.chamadas: list[tuple[str, dict]] = []

    def get(self, url, headers=None, timeout=None):
        self.chamadas.append((url, headers or {}))
        for servico in self.fora_do_ar:
            if servico in url:
                raise httpx.ConnectError(f"{servico} fora do ar")
        respostas = {
            "/ativos/1": {"id": 1, "patrimonio": "PAT-1", "tipo": "computador", "descricao": "PC", "setor": "TI"},
            f"/usuarios/{CARLA}": {"id": CARLA, "nome": "Carla", "perfil": "tecnico"},
            f"/usuarios/{ANA}": {"id": ANA, "nome": "Ana", "perfil": "solicitante"},
        }
        for fim, corpo in respostas.items():
            if url.endswith(fim):
                return httpx.Response(200, json=corpo)
        return httpx.Response(404, json={"detail": "não encontrado"})


@pytest.fixture
def rede(monkeypatch):
    falsa = RedeFalsa()
    monkeypatch.setattr(clientes.httpx, "get", falsa.get)
    return falsa


@pytest.fixture
def cliente(rede):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def db_de_teste():
        db = Sessao()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = db_de_teste
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()