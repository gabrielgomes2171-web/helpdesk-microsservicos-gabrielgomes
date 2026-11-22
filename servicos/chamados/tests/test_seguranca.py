from conftest import ANA, BIA, CARLA, token_de

H_ANA, H_BIA, H_CARLA = token_de(ANA, "solicitante"), token_de(BIA, "solicitante"), token_de(CARLA, "tecnico")


def abrir(cliente, headers, **extra):
    corpo = {"titulo": "Sem internet", "descricao": "Cabo ok, mas não navega", "prioridade": "alta", **extra}
    return cliente.post("/chamados", json=corpo, headers=headers)


def test_sem_token_recebe_401(cliente):
    for rota in ("/chamados", "/chamados/painel", "/notificacoes"):
        assert cliente.get(rota).status_code == 401


def test_token_com_segredo_errado_recebe_401(cliente):
    falso = token_de(CARLA, "tecnico", segredo="outro-segredo-qualquer-com-mais-de-32-caracteres")
    assert cliente.get("/chamados", headers=falso).status_code == 401


def test_solicitante_so_ve_os_proprios_chamados(cliente):
    id_ana = abrir(cliente, H_ANA).json()["id"]
    abrir(cliente, H_BIA)
    assert cliente.get(f"/chamados/{id_ana}", headers=H_BIA).status_code == 404  # não revela que existe
    assert all(c["solicitante_id"] == BIA for c in cliente.get("/chamados", headers=H_BIA).json())
    assert len(cliente.get("/chamados", headers=H_CARLA).json()) == 2            # equipe vê todos


def test_solicitante_nao_atribui(cliente):
    id_ = abrir(cliente, H_ANA).json()["id"]
    r = cliente.patch(f"/chamados/{id_}/atribuir", json={"tecnico_id": CARLA}, headers=H_ANA)
    assert r.status_code == 403


def test_token_do_usuario_e_repassado_ao_inventario(cliente, rede):
    assert abrir(cliente, H_ANA, ativo_id=1).status_code == 201
    url, cabecalhos = rede.chamadas[-1]
    assert url.endswith("/ativos/1")
    assert cabecalhos["Authorization"] == H_ANA["Authorization"]


def test_equipamento_inexistente_recebe_404(cliente):
    assert abrir(cliente, H_ANA, ativo_id=999).status_code == 404


def test_atribuir_a_quem_nao_e_tecnico_recebe_422(cliente):
    id_ = abrir(cliente, H_ANA).json()["id"]
    r = cliente.patch(f"/chamados/{id_}/atribuir", json={"tecnico_id": ANA}, headers=H_CARLA)
    assert r.status_code == 422


def test_inventario_fora_do_ar_responde_503_e_lista_continua(cliente, rede):
    rede.fora_do_ar.add("inventario")
    r = abrir(cliente, H_ANA, ativo_id=1)
    assert r.status_code == 503
    assert "Inventário" in r.json()["detail"]
    assert cliente.get("/chamados", headers=H_ANA).status_code == 200           # não travou o resto
    assert abrir(cliente, H_ANA).status_code == 201                              # sem equipamento funciona


def test_usuarios_fora_do_ar_responde_503_ao_atribuir(cliente, rede):
    id_ = abrir(cliente, H_ANA).json()["id"]
    rede.fora_do_ar.add("usuarios")
    r = cliente.patch(f"/chamados/{id_}/atribuir", json={"tecnico_id": CARLA}, headers=H_CARLA)
    assert r.status_code == 503


def test_fluxo_completo_com_sla_e_transicoes(cliente):
    id_ = abrir(cliente, H_ANA).json()["id"]
    assert cliente.patch(f"/chamados/{id_}/atribuir", json={"tecnico_id": CARLA}, headers=H_CARLA).json()["status"] == "em_atendimento"
    assert cliente.patch(f"/chamados/{id_}/status", json={"status": "fechado"}, headers=H_CARLA).status_code == 422  # pulo proibido
    assert cliente.patch(f"/chamados/{id_}/status", json={"status": "resolvido"}, headers=H_CARLA).status_code == 200
    assert cliente.patch(f"/chamados/{id_}/status", json={"status": "fechado"}, headers=H_ANA).status_code == 200    # solicitante confirma