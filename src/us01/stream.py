"""Stream the single-line JSON array and yield one contract at a time (criteria 3, 9, 10).

Hand-written splitter (O6). Only braces and strings are tokenised, with bounded buffers.
Values are kept as text: numbers keep their literal spelling (O5), booleans become
"true"/"false", null stays null, nested objects and arrays are stored as JSON text.
"""

import json
import re

from src.us01.erros import ErroUS01

BLOCO = 1 << 20
TOKEN = re.compile(rb'"(?:[^"\\]|\\.)*"|"|[{}]', re.S)


class _Numero(str):
    """A number exactly as written in the source."""


def _constante(nome):
    raise ValueError(nome)


def _json_invalido():
    return ErroUS01(
        "E_JSON_INVALIDO",
        "leitura do JSON",
        "um contrato do arquivo não é JSON válido; o conteúdo não é mostrado",
    )


def _aninhado(valor) -> str:
    if valor is None:
        return "null"
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if isinstance(valor, _Numero):
        return str(valor)
    if isinstance(valor, str):
        return json.dumps(valor, ensure_ascii=False)
    if isinstance(valor, list):
        return "[" + ",".join(_aninhado(v) for v in valor) + "]"
    return (
        "{"
        + ",".join(json.dumps(k, ensure_ascii=False) + ":" + _aninhado(v) for k, v in valor.items())
        + "}"
    )


def _campo(valor):
    if valor is None:
        return None
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if isinstance(valor, _Numero):
        return str(valor)
    if isinstance(valor, str):
        return valor
    return _aninhado(valor)


def _converter(objeto: bytes) -> dict:
    try:
        bruto = json.loads(
            objeto.decode("utf-8"),
            parse_float=_Numero,
            parse_int=_Numero,
            parse_constant=_constante,
        )
    except (ValueError, UnicodeDecodeError):
        raise _json_invalido() from None
    if not isinstance(bruto, dict):
        raise _json_invalido()
    return {chave: _campo(valor) for chave, valor in bruto.items()}


def contratos_do_fluxo(fluxo, tamanho_bloco: int = BLOCO):
    """Yield one dict per contract from a binary stream holding a JSON array of objects."""
    buf = b""
    cursor = 0
    profundidade = 0
    inicio = None
    while True:
        bloco = fluxo.read(tamanho_bloco)
        fim = not bloco
        if bloco:
            buf = buf + bloco
        parada = len(buf)
        for casamento in TOKEN.finditer(buf, cursor):
            token = casamento.group()
            if token[:1] == b'"':
                if token == b'"':  # lone quote: the string is not closed yet
                    if fim:
                        raise _json_invalido()
                    parada = casamento.start()  # wait for more bytes
                    break
                continue  # a complete string: its braces are text, not structure
            if token == b"{":
                if profundidade == 0:
                    inicio = casamento.start()
                profundidade += 1
            else:
                profundidade -= 1
                if profundidade < 0:
                    raise _json_invalido()
                if profundidade == 0:
                    yield _converter(buf[inicio : casamento.end()])
                    inicio = None
        if fim:
            if profundidade != 0:
                raise _json_invalido()
            return
        corte = inicio if inicio is not None else parada
        buf = buf[corte:]
        cursor = parada - corte
        inicio = 0 if inicio is not None else None
