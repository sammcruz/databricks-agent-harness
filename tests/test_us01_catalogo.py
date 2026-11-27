"""US01: the file address comes from the catalog API at load time (criteria 1 and 8)."""

import json
from pathlib import Path

import pytest

from src.us01.catalogo import ano_mais_recente, resolver_recurso
from src.us01.erros import ErroUS01
from tests.us01_fixtures import Servidor, payload_do_catalogo, resposta_fixa

RAIZ = Path(__file__).resolve().parents[1]


def test_endereco_vem_da_api_do_catalogo():
    payload = payload_do_catalogo("http://catalogo.exemplo", [2025, 2026])
    recurso = resolver_recurso(payload, 2026)
    assert recurso.endereco == "http://catalogo.exemplo/api/1/datasets/r/id-2026"
    assert recurso.endereco_direto == "http://catalogo.exemplo/s/resources/contratos/2026/contratos2026.zip"
    assert recurso.ultima_modificacao == "2026-11-22T10:06:20.880000+00:00"
    assert recurso.titulo == "contratos2026.zip"


def test_endereco_muda_com_o_payload_sem_mudar_o_codigo():
    payload = payload_do_catalogo("http://outro-host.exemplo", [2026])
    assert resolver_recurso(payload, 2026).endereco.startswith("http://outro-host.exemplo/")


def test_nenhum_endereco_fixo_no_codigo():
    """No host or catalogue path is written in src/us01 (the address comes from the API)."""
    proibidos = ("dados.gov.pt", "http://", "https://", "/api/1/datasets")
    for arquivo in (RAIZ / "src" / "us01").rglob("*.py"):
        texto = arquivo.read_text(encoding="utf-8")
        for trecho in proibidos:
            assert trecho not in texto, f"{arquivo.name} contains {trecho!r}"


def test_ano_sem_arquivo_no_catalogo_falha_com_mensagem_clara():
    payload = payload_do_catalogo("http://catalogo.exemplo", [2025, 2026])
    with pytest.raises(ErroUS01) as info:
        resolver_recurso(payload, 2019)
    assert info.value.codigo == "E_ANO_AUSENTE"
    assert "2019" in str(info.value)
    assert "Causa" in str(info.value)


def test_ano_ausente_como_parametro_falha():
    payload = payload_do_catalogo("http://catalogo.exemplo", [2026])
    with pytest.raises(ErroUS01) as info:
        resolver_recurso(payload, None)
    assert info.value.codigo == "E_ANO_AUSENTE"


def test_recurso_sem_endereco_falha_com_sem_arquivo():
    payload = payload_do_catalogo("http://catalogo.exemplo", [], titulo_extra=["contratos2026.zip"])
    with pytest.raises(ErroUS01) as info:
        resolver_recurso(payload, 2026)
    assert info.value.codigo == "E_SEM_ARQUIVO"


def test_ano_padrao_de_dev_e_o_maior_ano_do_catalogo():
    payload = payload_do_catalogo("http://catalogo.exemplo", [2012, 2026, 2025])
    assert ano_mais_recente(payload) == 2026


def test_xlsx_nao_conta_como_arquivo_do_ano():
    payload = {
        "resources": [
            {"title": "contratos2027.xlsx", "latest": "http://x", "url": "http://x"},
            {"title": "contratos2026.zip", "latest": "http://y", "url": "http://y"},
        ]
    }
    assert ano_mais_recente(payload) == 2026


def test_busca_do_dataset_usa_a_api_configurada():
    from src.us01.catalogo import buscar_dataset

    payload = payload_do_catalogo("http://catalogo.exemplo", [2026])
    corpo = json.dumps(payload).encode("utf-8")
    with Servidor(resposta_fixa(corpo, cabecalhos={"Content-Type": "application/json"})) as s:
        lido = buscar_dataset(f"{s.base}/api/1/datasets", "66d72d488ca4b7cb2de28712")
    assert lido["resources"][0]["title"] == "contratos2026.zip"
