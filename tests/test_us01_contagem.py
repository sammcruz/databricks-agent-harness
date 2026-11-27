"""US01: the independent count (ijson) agrees with the splitter on a generated zip (criterion 9)."""

import zipfile

import pytest

from src.us01.contagem import contar_independente
from src.us01.stream import contratos_do_fluxo
from tests.us01_fixtures import contrato_texto, json_da_fonte, zip_com_json

pytest.importorskip("ijson", reason="ijson indisponível no Mac (PyPI 503); roda no dev")


def _zip_em_disco(tmp_path, objetos):
    caminho = tmp_path / "contratos2026.zip"
    caminho.write_bytes(zip_com_json(json_da_fonte(objetos)))
    return caminho


def test_contagem_igual_ao_divisor_do_load(tmp_path):
    objetos = [contrato_texto(str(i), f'"valor":{i}.50') for i in range(1000)]
    caminho = _zip_em_disco(tmp_path, objetos)
    with zipfile.ZipFile(caminho) as z, z.open(z.namelist()[0]) as f:
        pelo_divisor = sum(1 for _ in contratos_do_fluxo(f, tamanho_bloco=4096))
    assert contar_independente(caminho) == 1000 == pelo_divisor


def test_contagem_de_zip_vazio_e_zero(tmp_path):
    caminho = _zip_em_disco(tmp_path, [])
    assert contar_independente(caminho) == 0


def test_contagem_nao_usa_o_divisor_do_load():
    import src.us01.contagem as contagem

    codigo = open(contagem.__file__, encoding="utf-8").read()
    assert "contratos_do_fluxo" not in codigo
    assert "import ijson" in codigo
