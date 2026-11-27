"""US01: the load pipeline, end to end with a local server and an injected bronze writer.

No Spark here: the bronze writer is a fake that records what it receives.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone

import pytest

from src.us01.erros import ErroUS01
from src.us01.pipeline import carregar_ano
from tests.us01_fixtures import (
    Servidor,
    contrato_texto,
    json_da_fonte,
    json_do_payload,
    payload_do_catalogo,
    zip_com_json,
)

DATASET = "66d72d488ca4b7cb2de28712"
AGORA = datetime(2026, 11, 27, 12, 0, tzinfo=timezone.utc)


def _servidor(zip_bytes: bytes):
    def resposta(caminho, n):
        base = servidor.base
        if caminho == f"/api/1/datasets/{DATASET}/":
            corpo = json_do_payload(payload_do_catalogo(base, [2025, 2026]))
            return 200, {"Content-Type": "application/json"}, corpo, 0
        if caminho == "/api/1/datasets/r/id-2026":
            return 200, {"Content-Type": "application/zip"}, zip_bytes, 0
        return 404, {}, b"", 0

    servidor = Servidor(resposta)
    return servidor


class Gravador:
    def __init__(self):
        self.chamadas = []

    def __call__(self, pasta_staging, colunas, metadados):
        linhas = []
        for arquivo in sorted(pasta_staging.glob("*.ndjson")):
            linhas += arquivo.read_text(encoding="utf-8").splitlines()
        self.chamadas.append({"colunas": colunas, "metadados": metadados, "linhas": linhas})
        return len(linhas)


def _carregar(servidor, tmp_path, gravador, ano=2026):
    return carregar_ano(
        ano,
        api_base=servidor.base + "/api/1/datasets",
        dataset_id=DATASET,
        raiz_volume=tmp_path / "volume",
        pasta_download=tmp_path / "download",
        gravar_bronze=gravador,
        agora=AGORA,
        tamanho_lote=2,
    )


def test_carrega_o_ano_e_entrega_metadados_e_linhas(tmp_path):
    zip_bytes = zip_com_json(json_da_fonte([contrato_texto("1"), contrato_texto("2")]))
    gravador = Gravador()
    with _servidor(zip_bytes) as servidor:
        resumo = _carregar(servidor, tmp_path, gravador)
    assert resumo.linhas == 2
    assert len(gravador.chamadas) == 1
    chamada = gravador.chamadas[0]
    metadados = chamada["metadados"]
    assert metadados["_source_year"] == "2026"
    assert metadados["_source_modified"] == "2026-11-22T10:06:20.880000+00:00"
    assert metadados["_source_url"].endswith("/api/1/datasets/r/id-2026")
    assert metadados["_file_sha256"] == hashlib.sha256(zip_bytes).hexdigest()
    assert metadados["_ingested_at"] == "2026-11-27T12:00:00+00:00"
    assert "idcontrato" in chamada["colunas"]
    assert [json.loads(linha)["idcontrato"] for linha in chamada["linhas"]] == ["1", "2"]


def test_arquivo_guardado_no_volume_com_data_da_publicacao(tmp_path):
    zip_bytes = zip_com_json(json_da_fonte([contrato_texto("1")]))
    with _servidor(zip_bytes) as servidor:
        _carregar(servidor, tmp_path, Gravador())
    guardado = tmp_path / "volume" / "contratos" / "2026" / "2026-11-22_contratos2026.zip"
    assert guardado.read_bytes() == zip_bytes


def test_zero_contratos_falha_e_nao_chama_a_bronze(tmp_path):
    zip_bytes = zip_com_json(json_da_fonte([]))
    gravador = Gravador()
    with _servidor(zip_bytes) as servidor, pytest.raises(ErroUS01) as erro:
        _carregar(servidor, tmp_path, gravador)
    assert erro.value.codigo == "E_ARQUIVO_VAZIO"
    assert gravador.chamadas == []


def test_ano_ausente_falha_antes_de_baixar(tmp_path):
    zip_bytes = zip_com_json(json_da_fonte([contrato_texto("1")]))
    gravador = Gravador()
    with _servidor(zip_bytes) as servidor, pytest.raises(ErroUS01) as erro:
        _carregar(servidor, tmp_path, gravador, ano=1999)
    assert erro.value.codigo == "E_ANO_AUSENTE"  # year not in the catalogue (spec: missing year)
    assert gravador.chamadas == []


def test_repetidos_sao_contados_e_mantidos(tmp_path):
    zip_bytes = zip_com_json(json_da_fonte([contrato_texto("1"), contrato_texto("1")]))
    gravador = Gravador()
    with _servidor(zip_bytes) as servidor:
        resumo = _carregar(servidor, tmp_path, gravador)
    assert resumo.linhas == 2
    assert resumo.repetidos == 1


def test_logs_sem_conteudo_de_linha(tmp_path, caplog):
    sentinela = "SENTINELA-NAO-PODE-APARECER-42"
    zip_bytes = zip_com_json(json_da_fonte([contrato_texto("1", f'"objeto":"{sentinela}"')]))
    caplog.set_level(logging.DEBUG)
    with _servidor(zip_bytes) as servidor:
        _carregar(servidor, tmp_path, Gravador())
    assert sentinela not in caplog.text
    assert "2026" in caplog.text  # the step log does name the year
