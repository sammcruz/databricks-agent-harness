"""US01 load pipeline: catalogue, download, Volume, stream to staging, bronze write.

The bronze writer is injected (Spark in the job notebook; a fake in the local tests), so this
module imports no Spark. Logs name the steps and counts only, never row content.
"""

import logging
import shutil
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.us01.catalogo import buscar_dataset, resolver_recurso
from src.us01.download import baixar
from src.us01.erros import ErroUS01
from src.us01.staging import LOTE, escrever_ndjson
from src.us01.stream import contratos_do_fluxo
from src.us01.volume import guardar

log = logging.getLogger("us01")


@dataclass
class Resumo:
    ano: int
    linhas: int
    repetidos: int
    sha256: str
    bytes_arquivo: int
    data_publicacao: str
    endereco: str
    duracao_s: float
    volume_arquivo: Optional[Path] = None


def _membro_json(z: zipfile.ZipFile) -> str:
    nomes = [n for n in z.namelist() if n.lower().endswith(".json")]
    if not nomes:
        raise ErroUS01("E_ZIP_INVALIDO", "leitura do zip", "o zip não tem arquivo .json")
    return nomes[0]


def carregar_ano(
    ano,
    *,
    api_base: str,
    dataset_id: str,
    raiz_volume,
    pasta_download,
    gravar_bronze,
    agora: Optional[datetime] = None,
    tamanho_lote: int = LOTE,
) -> Resumo:
    """Load one year. `gravar_bronze(pasta_staging, colunas, metadados) -> linhas` writes bronze."""
    inicio = time.monotonic()
    agora = agora or datetime.now(timezone.utc)
    raiz_volume = Path(raiz_volume)

    log.info("passo catalogo ano=%s", ano)
    recurso = resolver_recurso(buscar_dataset(api_base, dataset_id), ano)
    data_publicacao = (recurso.ultima_modificacao or agora.isoformat())[:10]

    log.info("passo download ano=%s", ano)
    baixado = baixar(recurso.endereco, pasta_download, nome=f"contratos{ano}.zip")
    if baixado.tamanho == 0:
        raise ErroUS01("E_ARQUIVO_VAZIO", "download", "o arquivo baixado tem zero bytes")
    log.info("passo download ok bytes=%s sha256=%s", baixado.tamanho, baixado.sha256)

    log.info("passo volume ano=%s", ano)
    destino = guardar(baixado.caminho, baixado.sha256, raiz_volume, int(ano), data_publicacao)

    pasta_staging = raiz_volume / "staging" / str(ano)
    shutil.rmtree(pasta_staging, ignore_errors=True)
    try:
        log.info("passo staging ano=%s", ano)
        with zipfile.ZipFile(destino) as z, z.open(_membro_json(z)) as fluxo:
            total, chaves, repetidos = escrever_ndjson(
                contratos_do_fluxo(fluxo), pasta_staging, tamanho_lote
            )
        log.info("passo staging ok contratos=%s repetidos=%s", total, repetidos)
        if total == 0:
            raise ErroUS01(
                "E_ARQUIVO_VAZIO",
                "leitura do JSON",
                "o arquivo não tem nenhum contrato",
            )

        metadados = {
            "_source_url": recurso.endereco,
            "_source_modified": recurso.ultima_modificacao or "",
            "_ingested_at": agora.isoformat(),
            "_file_sha256": baixado.sha256,
            "_source_year": str(ano),
        }
        log.info("passo bronze ano=%s", ano)
        try:
            linhas = gravar_bronze(pasta_staging, sorted(chaves), metadados)
        except ErroUS01:
            raise
        except Exception as erro:  # noqa: BLE001 - the step name is what the user needs
            raise ErroUS01(
                "E_BRONZE",
                "gravação da bronze",
                f"a gravação falhou ({type(erro).__name__}); a bronze mantém a versão anterior",
            ) from None
        if linhas != total:
            raise ErroUS01(
                "E_CONTAGEM",
                "gravação da bronze",
                f"a bronze recebeu {linhas} linhas e o staging tem {total}",
            )
    finally:
        shutil.rmtree(pasta_staging, ignore_errors=True)

    duracao = round(time.monotonic() - inicio, 1)
    log.info("passo fim ano=%s linhas=%s duracao_s=%s", ano, total, duracao)
    return Resumo(
        ano=int(ano),
        linhas=total,
        repetidos=repetidos,
        sha256=baixado.sha256,
        bytes_arquivo=baixado.tamanho,
        data_publicacao=data_publicacao,
        endereco=recurso.endereco,
        duracao_s=duracao,
        volume_arquivo=destino,
    )
