"""US01: the JSON is read as a stream, source fields stay text (criteria 3, 9, 10)."""

import io
import tracemalloc
import zipfile

import pytest

from src.us01.erros import ErroUS01
from src.us01.stream import contratos_do_fluxo
from tests.us01_fixtures import contrato_texto, json_da_fonte

CONTRATO_COMPLETO = contrato_texto(
    "1001",
    '"preco":9000.00,"valor":1e5,"ativo":true,"suspenso":false,"vazio":null,'
    '"nome":"","obs":"chave } e { no texto \\" aspas",'
    '"adjudicante":{"nif":"123","valor":2.50,"lista":[1.0,"a",null]}',
)


def test_campos_da_fonte_ficam_como_texto():
    fluxo = io.BytesIO(json_da_fonte([CONTRATO_COMPLETO]))
    (contrato,) = list(contratos_do_fluxo(fluxo))
    assert contrato["idcontrato"] == "1001"
    assert contrato["preco"] == "9000.00"  # not 9000.0
    assert contrato["valor"] == "1e5"  # not 100000.0
    assert contrato["ativo"] == "true"
    assert contrato["suspenso"] == "false"
    assert contrato["vazio"] is None
    assert contrato["nome"] == ""
    assert contrato["obs"] == 'chave } e { no texto " aspas'
    assert contrato["adjudicante"] == '{"nif":"123","valor":2.50,"lista":[1.0,"a",null]}'


def test_todos_os_valores_sao_texto_ou_nulo():
    fluxo = io.BytesIO(json_da_fonte([CONTRATO_COMPLETO]))
    (contrato,) = list(contratos_do_fluxo(fluxo))
    assert all(v is None or isinstance(v, str) for v in contrato.values())


@pytest.mark.parametrize("tamanho_bloco", [1, 2, 7, 64, 1 << 20])
def test_pedacos_de_qualquer_tamanho_dao_o_mesmo_resultado(tamanho_bloco):
    objetos = [contrato_texto(str(i), '"obs":"} { \\\\ \\" ]"') for i in range(20)]
    fluxo = io.BytesIO(json_da_fonte(objetos))
    lidos = list(contratos_do_fluxo(fluxo, tamanho_bloco=tamanho_bloco))
    assert [c["idcontrato"] for c in lidos] == [str(i) for i in range(20)]
    assert all(c["obs"] == '} { \\ " ]' for c in lidos)


def test_array_vazio_nao_produz_contratos():
    assert list(contratos_do_fluxo(io.BytesIO(b"[]"))) == []


def test_json_invalido_falha_sem_mostrar_o_conteudo():
    fluxo = io.BytesIO(b'[{"idcontrato":"SENTINELA_99"')
    with pytest.raises(ErroUS01) as info:
        list(contratos_do_fluxo(fluxo))
    assert info.value.codigo == "E_JSON_INVALIDO"
    assert "SENTINELA_99" not in str(info.value)


def test_objeto_invalido_falha_sem_mostrar_o_conteudo():
    fluxo = io.BytesIO(b'[{"idcontrato":SENTINELA_98}]')
    with pytest.raises(ErroUS01) as info:
        list(contratos_do_fluxo(fluxo))
    assert info.value.codigo == "E_JSON_INVALIDO"
    assert "SENTINELA_98" not in str(info.value)


def test_leitura_em_streaming_com_memoria_limitada(tmp_path):
    """A ~50 MB single-line JSON must not be held in memory at once."""
    objetos = [
        contrato_texto(str(i), '"preco":1234.50,"descricao":"' + "x" * 200 + '"')
        for i in range(190_000)
    ]
    dados = json_da_fonte(objetos)
    assert len(dados) > 40_000_000
    arquivo = tmp_path / "grande.zip"
    with zipfile.ZipFile(arquivo, "w", zipfile.ZIP_DEFLATED) as zipado:
        zipado.writestr("Contratos2026.json", dados)
    del dados, objetos

    tracemalloc.start()
    total = 0
    try:
        with zipfile.ZipFile(arquivo) as zipado:
            with zipado.open("Contratos2026.json") as fluxo:
                for _ in contratos_do_fluxo(fluxo):
                    total += 1
        _, pico = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert total == 190_000
    assert pico < 20 * 1024 * 1024, f"peak {pico / 1e6:.1f} MB"
