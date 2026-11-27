"""Helpers for the US01 tests: a local HTTP server and generated zips. No network access."""

import http.server
import io
import json
import threading
import time
import zipfile

# Resposta(caminho, numero_da_chamada) -> (status, cabecalhos, corpo, pausa_em_segundos)
Resposta = tuple


class Servidor:
    """Serve respostas fixas ou geradas por uma função, em 127.0.0.1 e porta livre."""

    def __init__(self, resposta):
        self._resposta = resposta
        self.chamadas = 0
        self._lock = threading.Lock()
        servidor = self

        class Manipulador(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.0"

            def do_GET(self):
                self._responder()

            def do_HEAD(self):
                self._responder()

            def _responder(self):
                with servidor._lock:
                    servidor.chamadas += 1
                    numero = servidor.chamadas
                status, cabecalhos, corpo, pausa = servidor._resposta(self.path, numero)
                if pausa:
                    time.sleep(pausa)
                self.send_response(status)
                cabecalhos = dict(cabecalhos)
                if "Content-Length" not in cabecalhos:
                    cabecalhos["Content-Length"] = str(len(corpo))
                for nome, valor in cabecalhos.items():
                    self.send_header(nome, valor)
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(corpo)

            def log_message(self, *args):
                return

        self._http = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Manipulador)
        self._http.daemon_threads = True
        self.base = f"http://127.0.0.1:{self._http.server_address[1]}"
        self._thread = threading.Thread(target=self._http.serve_forever, daemon=True)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *args):
        self._http.shutdown()
        self._http.server_close()


def resposta_fixa(corpo: bytes, status: int = 200, cabecalhos=None, pausa: float = 0):
    """Uma resposta igual para todas as chamadas."""
    return lambda caminho, n: (status, cabecalhos or {}, corpo, pausa)


def contrato_texto(idcontrato: str, extra: str = "") -> str:
    """Um contrato como texto JSON, com números escritos exatamente como na fonte."""
    campos = f'"idcontrato":"{idcontrato}"'
    if extra:
        campos += "," + extra
    return "{" + campos + "}"


def json_da_fonte(objetos: list) -> bytes:
    """O JSON da fonte: um array em uma única linha, sem quebra de linha."""
    return ("[" + ",".join(objetos) + "]").encode("utf-8")


def zip_com_json(json_bytes: bytes, nome: str = "Contratos2026.json") -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as arquivo:
        arquivo.writestr(nome, json_bytes)
    return buffer.getvalue()


def payload_do_catalogo(base: str, anos, titulo_extra=None) -> dict:
    """Um payload parecido com o da API do catálogo (dados.gov.pt), só com os campos usados."""
    recursos = []
    for ano in anos:
        recursos.append(
            {
                "id": f"id-{ano}",
                "title": f"contratos{ano}.zip",
                "latest": f"{base}/api/1/datasets/r/id-{ano}",
                "url": f"{base}/s/resources/contratos/{ano}/contratos{ano}.zip",
                "last_modified": f"{ano}-11-22T10:06:20.880000+00:00",
                "filesize": 1234,
                "format": "zip",
            }
        )
    for titulo in titulo_extra or []:
        recursos.append({"id": titulo, "title": titulo, "latest": None, "url": None})
    return {"id": "66d72d488ca4b7cb2de28712", "resources": recursos}


def json_do_payload(payload: dict) -> bytes:
    return json.dumps(payload).encode("utf-8")
