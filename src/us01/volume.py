"""Store the validated zip in the Volume unchanged, under its publication date (criteria 1 and 3).

Layout: contratos/<ANO>/<AAAA-MM-DD>_contratos<ANO>.zip. Earlier publications stay in place.
The copy is re-read and its SHA-256 must match the download before it gets its final name.
"""

import hashlib
import shutil
from pathlib import Path

from src.us01.erros import ErroUS01


def caminho_arquivo(ano: int, data_publicacao: str) -> Path:
    return Path("contratos") / str(ano) / f"{data_publicacao}_contratos{ano}.zip"


def _sha256_do_arquivo(caminho: Path) -> str:
    sha = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(8 << 20), b""):
            sha.update(bloco)
    return sha.hexdigest()


def guardar(origem: Path, sha256_esperado: str, raiz: Path, ano: int, data_publicacao: str) -> Path:
    destino = Path(raiz) / caminho_arquivo(ano, data_publicacao)
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_name(destino.name + ".parcial")
    try:
        shutil.copyfile(origem, parcial)
        if _sha256_do_arquivo(parcial) != sha256_esperado:
            raise ErroUS01(
                "E_HASH_DIVERGE",
                "volume",
                "a cópia no volume não tem o mesmo SHA-256 do download",
            )
        parcial.replace(destino)
    except BaseException:
        parcial.unlink(missing_ok=True)
        raise
    return destino
