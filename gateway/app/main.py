"""API Gateway: ponto único de entrada do HelpDesk (porta 8000).

- Entrega a tela (index.html, app.js, estilo.css).
- Repassa cada rota da API para o serviço certo, pela rede interna do Docker.
- Os serviços não ficam expostos para fora: só o gateway publica porta.
"""
import os
from pathlib import Path

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.seguranca_http import CabecalhosDeSeguranca

USUARIOS = os.getenv("USUARIOS_URL", "http://usuarios:8000")
INVENTARIO = os.getenv("INVENTARIO_URL", "http://inventario:8000")
CHAMADOS = os.getenv("CHAMADOS_URL", "http://chamados:8000")

# Primeiro pedaço da rota → serviço responsável
ROTAS = {
    "auth": USUARIOS,
    "usuarios": USUARIOS,
    "ativos": INVENTARIO,
    "chamados": CHAMADOS,
    "notificacoes": CHAMADOS,
}
SERVICOS = {"usuarios": USUARIOS, "inventario": INVENTARIO, "chamados": CHAMADOS}

# Só estes cabeçalhos passam (evita repassar lixo ou cabeçalhos internos)
CABECALHOS_IDA = {"authorization", "content-type", "accept"}
CABECALHOS_VOLTA = {"content-type", "www-authenticate", "cache-control", "retry-after"}
METODOS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
WEB = Path(__file__).parent / "web"

app = FastAPI(title="HelpDesk TI - Gateway", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(CabecalhosDeSeguranca)
cliente = httpx.AsyncClient(timeout=httpx.Timeout(10.0))


async def repassar(request: Request) -> Response:
    prefixo = request.url.path.strip("/").split("/")[0]
    destino = ROTAS[prefixo] + request.url.path
    if request.url.query:
        destino += "?" + request.url.query
    cabecalhos = {k: v for k, v in request.headers.items() if k.lower() in CABECALHOS_IDA}
    try:
        resposta = await cliente.request(request.method, destino, headers=cabecalhos, content=await request.body())
    except httpx.RequestError:
        return JSONResponse(status_code=503, content={"detail": f"Serviço de '{prefixo}' indisponível no momento."})
    volta = {k: v for k, v in resposta.headers.items() if k.lower() in CABECALHOS_VOLTA}
    return Response(content=resposta.content, status_code=resposta.status_code, headers=volta)


for prefixo in ROTAS:
    app.add_api_route(f"/{prefixo}", repassar, methods=METODOS, include_in_schema=False)
    app.add_api_route(f"/{prefixo}/{{resto:path}}", repassar, methods=METODOS, include_in_schema=False)


@app.get("/saude")
async def saude():
    """Bônus: mostra quais serviços estão no ar."""
    estado = {}
    for nome, url in SERVICOS.items():
        try:
            r = await cliente.get(f"{url}/saude", timeout=2.0)
            estado[nome] = "ok" if r.status_code == 200 else f"erro {r.status_code}"
        except httpx.RequestError:
            estado[nome] = "fora do ar"
    return {"gateway": "ok", "servicos": estado}


# Por último: a tela. "/" entrega o index.html; /app.js e /estilo.css também saem daqui.
app.mount("/", StaticFiles(directory=WEB, html=True), name="web")