import os

# Configuração de teste ANTES de importar o app (o config.py exige JWT_SEGREDO)
os.environ["JWT_SEGREDO"] = "segredo-so-para-testes-com-mais-de-32-caracteres"
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["DADOS_EXEMPLO"] = "0"

from datetime import datetime, timedelta, timezone  # noqa: E402

import jwt  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.config import JWT_ALGORITMO, JWT_EMISSOR, JWT_SEGREDO  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


def token_de(usuario_id: int, perfil: str, segredo: str = JWT_SEGREDO, minutos: int = 60, **extra) -> dict:
    """Fabrica um token como o serviço de Usuários faria no login."""
    agora = datetime.now(timezone.utc)
    dados = {"sub": str(usuario_id), "perfil": perfil, "iat": agora,
             "exp": agora + timedelta(minutes=minutos), "iss": JWT_EMISSOR, **extra}
    dados = {k: v for k, v in dados.items() if v is not None}
    return {"Authorization": f"Bearer {jwt.encode(dados, segredo, algorithm=JWT_ALGORITMO)}"}


@pytest.fixture
def cliente():
    """Banco novo, em memória, para cada teste."""
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