"""US01: the staging file holds one contract per line, every value as text (criterion 3)."""

import json

from src.us01.staging import escrever_ndjson


def _linhas(pasta):
    arquivos = sorted(pasta.glob("*.ndjson"))
    linhas = []
    for arquivo in arquivos:
        linhas += arquivo.read_text(encoding="utf-8").splitlines()
    return linhas


def test_uma_linha_por_contrato(tmp_path):
    contratos = [{"idcontrato": str(i), "objeto": f"obj {i}"} for i in range(3)]
    total, chaves, repetidos = escrever_ndjson(iter(contratos), tmp_path, tamanho_lote=10)
    linhas = _linhas(tmp_path)
    assert total == 3
    assert len(linhas) == 3
    assert [json.loads(linha)["idcontrato"] for linha in linhas] == ["0", "1", "2"]
    assert chaves == {"idcontrato", "objeto"}
    assert repetidos == 0


def test_valores_ficam_como_texto_e_nulo_continua_nulo(tmp_path):
    contrato = {"idcontrato": "1", "valor": "9000.00", "notas": None, "vazio": ""}
    escrever_ndjson(iter([contrato]), tmp_path, tamanho_lote=10)
    lido = json.loads(_linhas(tmp_path)[0])
    assert lido == {"idcontrato": "1", "valor": "9000.00", "notas": None, "vazio": ""}
    assert isinstance(lido["valor"], str)


def test_lotes_de_tamanho_fixo(tmp_path):
    contratos = [{"idcontrato": str(i)} for i in range(5)]
    escrever_ndjson(iter(contratos), tmp_path, tamanho_lote=2)
    assert len(list(tmp_path.glob("*.ndjson"))) == 3
    assert len(_linhas(tmp_path)) == 5


def test_idcontrato_repetido_e_contado_e_mantido(tmp_path):
    contratos = [{"idcontrato": "1"}, {"idcontrato": "2"}, {"idcontrato": "1"}]
    total, _, repetidos = escrever_ndjson(iter(contratos), tmp_path, tamanho_lote=10)
    assert total == 3  # every row is kept (O12)
    assert repetidos == 1
