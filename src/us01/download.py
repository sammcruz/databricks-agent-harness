"""Download the zip to local disk with retry, hash and zip checks (criteria 2 and 7).

Nothing is left behind on failure: the partial file is removed before the error goes up.
"""

import hashlib
import http.client
import socket
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from src.us01.erros import ErroUS01

BLOCO = 8 << 20
TENTATIVAS_PADRAO = 5  # O9
ESPERA_INICIAL_S = 10.0  # O9: doubles after each attempt
TEMPO_LIMITE_S = 60.0  # O9: no retry on timeout


@dataclass(frozen=True)
class Baixado:
    caminho: Path
    sha256: str
    tamanho: int


def _repetivel(codigo: int) -> bool:
    return codigo == 429 or 500 <= codigo <= 599


def baixar(
    endereco: str,
    pasta,
    dormir=time.sleep,
    espera_inicial: float = ESPERA_INICIAL_S,
    tentativas: int = TENTATIVAS_PADRAO,
    tempo_limite: float = TEMPO_LIMITE_S,
    nome: str = None,
) -> Baixado:
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    nome = nome or Path(urlparse(endereco).path).name or "arquivo.zip"
    destino = pasta / nome
    parcial = pasta / (nome + ".parcial")
    espera = espera_inicial
    try:
        for tentativa in range(1, tentativas + 1):
            try:
                sha, tamanho = _transferir(endereco, parcial, tempo_limite)
                break
            except urllib.error.HTTPError as erro:
                if _repetivel(erro.code) and tentativa < tentativas:
                    dormir(espera)
                    espera *= 2
                    continue
                raise ErroUS01(
                    "E_HTTP",
                    "download",
                    f"o servidor respondeu HTTP {erro.code} em {tentativa} tentativa(s)",
                ) from None
        _validar_zip(parcial)
        parcial.replace(destino)
        return Baixado(caminho=destino, sha256=sha, tamanho=tamanho)
    except BaseException:
        parcial.unlink(missing_ok=True)
        raise


def _transferir(endereco: str, parcial: Path, tempo_limite: float):
    requisicao = urllib.request.Request(endereco, headers={"User-Agent": "us01-bronze"})
    try:
        with urllib.request.urlopen(requisicao, timeout=tempo_limite) as resposta:
            declarado = resposta.headers.get("Content-Length")
            sha = hashlib.sha256()
            tamanho = 0
            with open(parcial, "wb") as saida:
                while True:
                    bloco = resposta.read(BLOCO)
                    if not bloco:
                        break
                    saida.write(bloco)
                    sha.update(bloco)
                    tamanho += len(bloco)
    except urllib.error.HTTPError:
        raise
    except (TimeoutError, socket.timeout):
        raise ErroUS01(
            "E_TIMEOUT", "download", f"tempo esgotado após {tempo_limite:g} s"
        ) from None
    except urllib.error.URLError as erro:
        if isinstance(erro.reason, (TimeoutError, socket.timeout)):
            raise ErroUS01(
                "E_TIMEOUT", "download", f"tempo esgotado após {tempo_limite:g} s"
            ) from None
        raise ErroUS01(
            "E_HTTP", "download", "não foi possível conectar ao endereço do arquivo"
        ) from None
    except http.client.IncompleteRead:
        raise ErroUS01(
            "E_ZIP_TRUNCADO", "download", "a conexão terminou antes do fim do arquivo"
        ) from None
    if declarado is not None and int(declarado) != tamanho:
        raise ErroUS01(
            "E_ZIP_TRUNCADO",
            "download",
            f"recebidos {tamanho} bytes de {declarado} anunciados",
        )
    return sha.hexdigest(), tamanho


def _validar_zip(parcial: Path) -> None:
    if parcial.stat().st_size == 0:
        raise ErroUS01("E_ARQUIVO_VAZIO", "download", "o arquivo recebido tem zero bytes")
    try:
        with zipfile.ZipFile(parcial) as arquivo:
            if arquivo.testzip() is not None:
                raise ErroUS01("E_ZIP_INVALIDO", "download", "o zip tem entrada corrompida")
    except zipfile.BadZipFile:
        raise ErroUS01(
            "E_ZIP_INVALIDO", "download", "o arquivo recebido não é um zip válido"
        ) from None
