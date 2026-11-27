"""US01: download with retry, hash and zip checks; failures leave no partial file (criteria 7)."""

import hashlib

import pytest

from src.us01.download import baixar
from src.us01.erros import ErroUS01
from tests.us01_fixtures import Servidor, json_da_fonte, resposta_fixa, zip_com_json

ZIP_VALIDO = zip_com_json(json_da_fonte(['{"idcontrato":"1"}', '{"idcontrato":"2"}']))


def sem_espera(segundos):
    """Replaces time.sleep so retries do not take minutes in the test."""
    return None


def test_baixa_o_zip_e_calcula_o_sha256(tmp_path):
    with Servidor(resposta_fixa(ZIP_VALIDO)) as s:
        resultado = baixar(f"{s.base}/contratos2026.zip", tmp_path, dormir=sem_espera)
    assert resultado.caminho.read_bytes() == ZIP_VALIDO
    assert resultado.sha256 == hashlib.sha256(ZIP_VALIDO).hexdigest()
    assert resultado.tamanho == len(ZIP_VALIDO)


def test_http_429_e_repetido_com_espera_crescente_e_termina_em_200(tmp_path):
    def resposta(caminho, n):
        if n < 3:
            return (429, {}, b"muitas requisicoes", 0)
        return (200, {}, ZIP_VALIDO, 0)

    espera = []
    with Servidor(resposta) as s:
        resultado = baixar(
            f"{s.base}/z.zip", tmp_path, dormir=espera.append, espera_inicial=10.0
        )
    assert resultado.tamanho == len(ZIP_VALIDO)
    assert espera == [10.0, 20.0]


def test_http_429_sempre_falha_depois_do_limite_de_tentativas(tmp_path):
    espera = []
    with Servidor(resposta_fixa(b"muitas", status=429)) as s:
        with pytest.raises(ErroUS01) as info:
            baixar(f"{s.base}/z.zip", tmp_path, dormir=espera.append, tentativas=5)
    assert info.value.codigo == "E_HTTP"
    assert info.value.passo == "download"
    assert "429" in info.value.causa
    assert len(espera) == 4  # 5 attempts, 4 waits
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("status", [404, 500])
def test_http_erro_falha_com_mensagem_em_portugues(tmp_path, status):
    with Servidor(resposta_fixa(b"erro", status=status)) as s:
        with pytest.raises(ErroUS01) as info:
            baixar(f"{s.base}/z.zip", tmp_path, dormir=sem_espera, tentativas=2)
    mensagem = str(info.value)
    assert "download" in mensagem
    assert str(status) in mensagem
    assert mensagem.startswith("Falha")
    assert list(tmp_path.iterdir()) == []


def test_tempo_esgotado_falha_sem_arquivo_parcial(tmp_path):
    with Servidor(resposta_fixa(ZIP_VALIDO, pausa=3)) as s:
        with pytest.raises(ErroUS01) as info:
            baixar(f"{s.base}/z.zip", tmp_path, dormir=sem_espera, tempo_limite=0.5)
    assert info.value.codigo == "E_TIMEOUT"
    assert "tempo esgotado" in info.value.causa
    assert list(tmp_path.iterdir()) == []


def test_zip_truncado_falha_sem_arquivo_parcial(tmp_path):
    cabecalhos = {"Content-Length": str(len(ZIP_VALIDO) + 1000)}
    with Servidor(resposta_fixa(ZIP_VALIDO, cabecalhos=cabecalhos)) as s:
        with pytest.raises(ErroUS01) as info:
            baixar(f"{s.base}/z.zip", tmp_path, dormir=sem_espera)
    assert info.value.codigo == "E_ZIP_TRUNCADO"
    assert list(tmp_path.iterdir()) == []


def test_zip_invalido_falha_sem_arquivo_parcial(tmp_path):
    with Servidor(resposta_fixa(b"isto nao e um zip" * 100)) as s:
        with pytest.raises(ErroUS01) as info:
            baixar(f"{s.base}/z.zip", tmp_path, dormir=sem_espera)
    assert info.value.codigo == "E_ZIP_INVALIDO"
    assert list(tmp_path.iterdir()) == []


def test_arquivo_vazio_falha_com_mensagem_clara(tmp_path):
    with Servidor(resposta_fixa(b"")) as s:
        with pytest.raises(ErroUS01) as info:
            baixar(f"{s.base}/z.zip", tmp_path, dormir=sem_espera)
    assert info.value.codigo == "E_ARQUIVO_VAZIO"
    assert list(tmp_path.iterdir()) == []
