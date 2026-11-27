"""Staging: the splitter's contracts as NDJSON, one contract per line, in batches (criterion 3).

Every value is already text or null (see stream.py), so Spark can read the lines with an
all-string schema and keep the source spelling of each number.
"""

import json
from pathlib import Path

LOTE = 10_000  # contracts per staging file


def _gravar(pasta: Path, numero: int, lote: list) -> None:
    caminho = pasta / f"part-{numero:05d}.ndjson"
    with open(caminho, "w", encoding="utf-8") as arquivo:
        for contrato in lote:
            arquivo.write(json.dumps(contrato, ensure_ascii=False) + "\n")


def escrever_ndjson(contratos, pasta, tamanho_lote: int = LOTE):
    """Write the contracts; return (total rows, set of field names, repeated idcontrato count).

    Every row is kept, repeated keys included (O12); repeats are only counted.
    """
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    total = 0
    repetidos = 0
    chaves: set = set()
    vistos: set = set()
    lote: list = []
    numero = 0
    for contrato in contratos:
        total += 1
        chaves.update(contrato.keys())
        chave = contrato.get("idcontrato")
        if chave in vistos:
            repetidos += 1
        else:
            vistos.add(chave)
        lote.append(contrato)
        if len(lote) >= tamanho_lote:
            _gravar(pasta, numero, lote)
            numero += 1
            lote = []
    if lote:
        _gravar(pasta, numero, lote)
    return total, chaves, repetidos
