"""Count the contracts in the stored zip with a reader other than the loader (criterion 9).

Uses ijson, which is separate from the loader's splitter (stream.py). Only the count leaves
this module: no row content.
"""

import zipfile


def _membro_json(z: zipfile.ZipFile) -> str:
    nomes = [n for n in z.namelist() if n.lower().endswith(".json")]
    if not nomes:
        raise ValueError("o zip não tem arquivo .json")
    return nomes[0]


def contar_independente(caminho_zip) -> int:
    import ijson  # a separate reader on purpose: it is not stream.py

    with zipfile.ZipFile(caminho_zip) as z, z.open(_membro_json(z)) as arquivo:
        return sum(1 for _ in ijson.items(arquivo, "item"))
