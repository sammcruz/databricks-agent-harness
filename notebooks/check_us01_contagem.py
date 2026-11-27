# Databricks notebook source
# US01 check: independent count of contracts in the stored zip (ijson, not the loader's splitter)
# versus the bronze rows of the same year. Read-only. Dev target.

# COMMAND ----------

import json
import sys
from pathlib import Path

_nb = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
sys.path.insert(0, "/Workspace" + str(Path(_nb).parent.parent))

from src.us01.contagem import contar_independente  # noqa: E402

# COMMAND ----------

dbutils.widgets.text("ano", "")
dbutils.widgets.text("catalogo", "workspace")
dbutils.widgets.text("schema", "samantha_contratos_pt")
dbutils.widgets.text("volume", "contratos_raw")
dbutils.widgets.text("tabela", "bronze_contratos")

catalogo = dbutils.widgets.get("catalogo")
schema = dbutils.widgets.get("schema")
volume = dbutils.widgets.get("volume")
tabela = f"{catalogo}.{schema}.{dbutils.widgets.get('tabela')}"
ano_texto = dbutils.widgets.get("ano").strip()
raiz_contratos = Path(f"/Volumes/{catalogo}/{schema}/{volume}/contratos")
# Empty year: check the latest year folder stored in the Volume.
ano = int(ano_texto) if ano_texto else max(int(p.name) for p in raiz_contratos.iterdir() if p.is_dir())

# COMMAND ----------

# Latest stored publication for the year (file names start with the publication date).
pasta = raiz_contratos / str(ano)
arquivos = sorted(pasta.glob(f"*_contratos{ano}.zip"))
if not arquivos:
    raise RuntimeError(f"E_SEM_ARQUIVO_VOLUME: nenhum zip guardado para {ano}")
zip_guardado = arquivos[-1]

independente = contar_independente(zip_guardado)

# COMMAND ----------

linhas_bronze = spark.sql(
    f"SELECT COUNT(*) AS n, COUNT(DISTINCT idcontrato) AS distintos FROM {tabela} WHERE _source_year = '{ano}'"
).first()
nulos_meta = spark.sql(
    f"""
    SELECT SUM(CASE WHEN _source_url IS NULL THEN 1 ELSE 0 END) AS url,
           SUM(CASE WHEN _source_modified IS NULL THEN 1 ELSE 0 END) AS modificado,
           SUM(CASE WHEN _ingested_at IS NULL THEN 1 ELSE 0 END) AS ingerido,
           SUM(CASE WHEN _file_sha256 IS NULL THEN 1 ELSE 0 END) AS sha,
           SUM(CASE WHEN _source_year IS NULL THEN 1 ELSE 0 END) AS ano
    FROM {tabela} WHERE _source_year = '{ano}'
    """
).first()

resultado = {
    "ano": ano,
    "arquivo": zip_guardado.name,
    "contagem_independente": independente,
    "linhas_bronze": linhas_bronze["n"],
    "idcontrato_distintos": linhas_bronze["distintos"],
    "confere": independente == linhas_bronze["n"],
    "nulos_metadados": nulos_meta.asDict(),
}
print(json.dumps(resultado, ensure_ascii=False))
if not resultado["confere"]:
    raise RuntimeError(f"E_CONTAGEM: independente={independente} bronze={linhas_bronze['n']}")
dbutils.notebook.exit(json.dumps(resultado, ensure_ascii=False))
