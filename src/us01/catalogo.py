"""Resolve the file address from the catalogue API at load time (criteria 1 and 8).

No host or catalogue path is written here: the API base comes from configuration.
"""

import json
import re
import urllib.request
from dataclasses import dataclass
from typing import Optional

from src.us01.erros import ErroUS01

PADRAO_ZIP = re.compile(r"^contratos(\d{4})\.zip$")
TIMEOUT_S = 60.0


@dataclass(frozen=True)
class Recurso:
    titulo: str
    endereco: str  # used for download (O1: the resource API address when present)
    endereco_direto: Optional[str]
    ultima_modificacao: Optional[str]
    tamanho: Optional[int]


def resolver_recurso(payload: dict, ano) -> Recurso:
    if ano is None:
        raise ErroUS01("E_ANO_AUSENTE", "catálogo", "o ano não foi informado")
    titulo_esperado = f"contratos{ano}.zip"
    for recurso in payload.get("resources", []):
        if recurso.get("title") != titulo_esperado:
            continue
        endereco = recurso.get("latest") or recurso.get("url")
        if not endereco:
            raise ErroUS01(
                "E_SEM_ARQUIVO",
                "catálogo",
                f"o recurso {titulo_esperado} existe, mas não tem endereço para download",
            )
        return Recurso(
            titulo=titulo_esperado,
            endereco=endereco,
            endereco_direto=recurso.get("url"),
            ultima_modificacao=recurso.get("last_modified"),
            tamanho=recurso.get("filesize"),
        )
    raise ErroUS01(
        "E_ANO_AUSENTE",
        "catálogo",
        f"o catálogo não tem arquivo para o ano {ano} ({titulo_esperado})",
    )


def ano_mais_recente(payload: dict) -> int:
    anos = []
    for recurso in payload.get("resources", []):
        casamento = PADRAO_ZIP.match(recurso.get("title") or "")
        if casamento:
            anos.append(int(casamento.group(1)))
    if not anos:
        raise ErroUS01("E_ANO_AUSENTE", "catálogo", "nenhum arquivo contratosAAAA.zip no catálogo")
    return max(anos)


def buscar_dataset(api_base: str, dataset_id: str) -> dict:
    url = f"{api_base.rstrip('/')}/{dataset_id}/"
    requisicao = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(requisicao, timeout=TIMEOUT_S) as resposta:
            return json.loads(resposta.read().decode("utf-8"))
    except Exception as erro:  # noqa: BLE001 - re-raised as a step error
        raise ErroUS01(
            "E_HTTP", "catálogo", f"não foi possível ler o dataset ({type(erro).__name__})"
        ) from None
