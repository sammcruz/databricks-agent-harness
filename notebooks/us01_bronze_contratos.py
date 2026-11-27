# Databricks notebook source
# US01: load one year of public contracts (IMPIC / Portal BASE) into bronze.
# Thin wiring only: the logic lives in src/us01/. Dev target, serverless.

# COMMAND ----------

import json
import sys
from pathlib import Path

# The bundle syncs the repo; this notebook sits in <repo>/notebooks/,
# so the repo root is two levels up.
_nb = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
sys.path.insert(0, "/Workspace" + str(Path(_nb).parent.parent))

from src.us01.bronze import gravar_ano  # noqa: E402
from src.us01.catalogo import ano_mais_recente, buscar_dataset  # noqa: E402
from src.us01.pipeline import carregar_ano  # noqa: E402

# COMMAND ----------

# Source address (fixed by the story: the IMPIC dataset on dados.gov.pt).
API_BASE = "https://dados.gov.pt/api/1/datasets"

dbutils.widgets.text("ano", "")
dbutils.widgets.text("catalogo", "workspace")
dbutils.widgets.text("schema", "samantha_contratos_pt")
dbutils.widgets.text("volume", "contratos_raw")
dbutils.widgets.text("tabela", "bronze_contratos")
dbutils.widgets.text("dataset_id", "66d72d488ca4b7cb2de28712")

catalogo = dbutils.widgets.get("catalogo")
schema = dbutils.widgets.get("schema")
volume = dbutils.widgets.get("volume")
tabela = f"{catalogo}.{schema}.{dbutils.widgets.get('tabela')}"
dataset_id = dbutils.widgets.get("dataset_id")

# Idempotent: Free Edition dev objects, created on the first run.
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalogo}.{schema}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalogo}.{schema}.{volume}")

# COMMAND ----------

payload = buscar_dataset(API_BASE, dataset_id)
ano_texto = dbutils.widgets.get("ano").strip()
ano = int(ano_texto) if ano_texto else ano_mais_recente(payload)
print(f"ano escolhido: {ano}")

# COMMAND ----------

pasta_download = Path("/tmp/us01_download")
pasta_download.mkdir(parents=True, exist_ok=True)


def gravar_bronze(pasta_staging, colunas, metadados):
    return gravar_ano(spark, pasta_staging, colunas, metadados, tabela, ano)


resumo = carregar_ano(
    ano,
    api_base=API_BASE,
    dataset_id=dataset_id,
    raiz_volume=f"/Volumes/{catalogo}/{schema}/{volume}",
    pasta_download=pasta_download,
    gravar_bronze=gravar_bronze,
)

# Only step names and counts in the output: no row content.
saida = {
    "ano": resumo.ano,
    "linhas": resumo.linhas,
    "repetidos": resumo.repetidos,
    "sha256": resumo.sha256,
    "bytes_arquivo": resumo.bytes_arquivo,
    "data_publicacao": resumo.data_publicacao,
    "duracao_s": round(resumo.duracao_s, 1),
    "volume_arquivo": str(resumo.volume_arquivo),
    "tabela": tabela,
}
print(json.dumps(saida, ensure_ascii=False))
dbutils.notebook.exit(json.dumps(saida, ensure_ascii=False))
