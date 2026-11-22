from conftest import token_de

TECNICA = token_de(4, "tecnico")
SOLICITANTE = token_de(2, "solicitante")
ATIVO = {"patrimonio": "PAT-1", "tipo": "computador", "descricao": "Desktop", "setor": "TI"}


def test_saude_e_publica(cliente):
    assert cliente.get("/saude").status_code == 200


def test_sem_token_recebe_401(cliente):
    assert cliente.get("/ativos").status_code == 401
    assert cliente.get("/ativos/1").status_code == 401
    assert cliente.post("/ativos", json=ATIVO).status_code == 401


def test_token_com_segredo_errado_recebe_401(cliente):
    falso = token_de(4, "tecnico", segredo="outro-segredo-qualquer-com-mais-de-32-caracteres")
    assert cliente.get("/ativos", headers=falso).status_code == 401


def test_token_expirado_recebe_401(cliente):
    assert cliente.get("/ativos", headers=token_de(4, "tecnico", minutos=-5)).status_code == 401


def test_token_sem_perfil_recebe_401(cliente):
    assert cliente.get("/ativos", headers=token_de(4, perfil=None)).status_code == 401


def test_solicitante_nao_cadastra_equipamento(cliente):
    assert cliente.post("/ativos", json=ATIVO, headers=SOLICITANTE).status_code == 403


def test_tecnico_cadastra_e_todos_consultam(cliente):
    criado = cliente.post("/ativos", json=ATIVO, headers=TECNICA)
    assert criado.status_code == 201
    assert cliente.get(f"/ativos/{criado.json()['id']}", headers=SOLICITANTE).status_code == 200


def test_cabecalhos_de_seguranca(cliente):
    r = cliente.get("/saude")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"