"""US01: the stored file is the downloaded file, byte for byte, under a dated name."""

import hashlib
import re

import pytest

from src.us01.erros import ErroUS01
from src.us01.volume import caminho_arquivo, guardar
from tests.us01_fixtures import contrato_texto, json_da_fonte, zip_com_json

ZIP = zip_com_json(json_da_fonte([contrato_texto("1"), contrato_texto("2")]))


def _baixado(tmp_path):
    origem = tmp_path / "download" / "contratos2026.zip"
    origem.parent.mkdir()
    origem.write_bytes(ZIP)
    return origem, hashlib.sha256(ZIP).hexdigest()


def test_arquivo_guardado_igual_ao_baixado(tmp_path):
    origem, sha = _baixado(tmp_path)
    volume = tmp_path / "volume"
    destino = guardar(origem, sha, volume, ano=2026, data_publicacao="2026-11-22")
    assert destino.read_bytes() == ZIP
    assert hashlib.sha256(destino.read_bytes()).hexdigest() == sha


def test_nome_tem_a_data_de_publicacao(tmp_path):
    origem, sha = _baixado(tmp_path)
    destino = guardar(origem, sha, tmp_path / "volume", ano=2026, data_publicacao="2026-11-22")
    assert destino.name == "2026-11-22_contratos2026.zip"
    assert destino.parent.name == "2026"
    assert destino.parent.parent.name == "contratos"


def test_publicacao_nova_nao_apaga_a_anterior(tmp_path):
    origem, sha = _baixado(tmp_path)
    volume = tmp_path / "volume"
    guardar(origem, sha, volume, ano=2026, data_publicacao="2026-11-01")
    guardar(origem, sha, volume, ano=2026, data_publicacao="2026-11-22")
    nomes = sorted(p.name for p in (volume / "contratos" / "2026").iterdir())
    assert nomes == ["2026-11-01_contratos2026.zip", "2026-11-22_contratos2026.zip"]


def test_copia_com_hash_diferente_falha_e_nao_fica_arquivo(tmp_path, monkeypatch):
    origem, sha = _baixado(tmp_path)
    volume = tmp_path / "volume"
    monkeypatch.setattr("src.us01.volume._sha256_do_arquivo", lambda caminho: "0" * 64)
    with pytest.raises(ErroUS01) as info:
        guardar(origem, sha, volume, ano=2026, data_publicacao="2026-11-22")
    assert info.value.codigo == "E_HASH_DIVERGE"
    assert not any((volume / "contratos" / "2026").glob("*.zip"))


def test_caminho_segue_o_layout_combinado():
    assert re.fullmatch(
        r"contratos/2026/2026-11-22_contratos2026\.zip",
        str(caminho_arquivo(2026, "2026-11-22").as_posix()),
    )
