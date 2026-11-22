import jwt

from app.config import JWT_ALGORITMO, JWT_EMISSOR, JWT_SEGREDO


def test_senha_errada_recebe_401(cliente, contas):
    r = cliente.post("/auth/login", json={"email": "ana@x.com", "senha": "errada"})
    assert r.status_code == 401


def test_muitas_tentativas_bloqueiam_o_login(cliente, contas):
    codigos = [cliente.post("/auth/login", json={"email": "ana@x.com", "senha": "errada"}).status_code
               for _ in range(10)]
    assert 429 in codigos


def test_token_traz_id_e_perfil_para_os_outros_servicos(contas):
    """Contrato entre serviços: Inventário e Chamados dependem destes campos."""
    dados = jwt.decode(contas["carla"]["token"], JWT_SEGREDO, algorithms=[JWT_ALGORITMO], issuer=JWT_EMISSOR)
    assert dados["sub"] == str(contas["carla"]["id"])
    assert dados["perfil"] == "tecnico"


def test_sem_token_recebe_401(cliente, contas):
    assert cliente.get("/usuarios").status_code == 401
    assert cliente.get("/auth/eu").status_code == 401
    assert cliente.get(f"/usuarios/{contas['ana']['id']}").status_code == 401


def test_so_admin_cria_usuario(cliente, contas):
    novo = {"nome": "Novo", "email": "novo@x.com", "perfil": "solicitante", "senha": "Senha123"}
    assert cliente.post("/usuarios", json=novo, headers=contas["ana"]["headers"]).status_code == 403
    assert cliente.post("/usuarios", json=novo, headers=contas["carla"]["headers"]).status_code == 403
    assert cliente.post("/usuarios", json=novo, headers=contas["admin"]["headers"]).status_code == 201


def test_listagem_nao_expoe_email(cliente, contas):
    lista = cliente.get("/usuarios", headers=contas["ana"]["headers"]).json()
    assert lista and all("email" not in u for u in lista)


def test_consulta_de_tecnico_usada_pelo_servico_de_chamados(cliente, contas):
    r = cliente.get(f"/usuarios/{contas['carla']['id']}", headers=contas["ana"]["headers"])
    assert r.status_code == 200 and r.json()["perfil"] == "tecnico"