"""Bronze write (Spark): all source fields as text, metadata columns, one year replaced per run.

Criterion 5 and 6: Delta replaceWhere on _source_year, so a reload of the same year replaces
the year in one write (O2, O7).
"""

from pyspark.sql import functions as F
from pyspark.sql.types import StringType, StructField, StructType

COLUNAS_METADADOS = [
    "_source_url",
    "_source_modified",
    "_ingested_at",
    "_file_sha256",
    "_source_year",
]


def esquema_texto(colunas):
    """An all-string schema for the source fields (no type inference)."""
    return StructType([StructField(nome, StringType(), True) for nome in colunas])


def adicionar_metadados(df, metadados: dict):
    for nome in COLUNAS_METADADOS:
        df = df.withColumn(nome, F.lit(str(metadados[nome])))
    return df


def gravar_ano(spark, pasta, colunas, metadados: dict, tabela: str, ano) -> int:
    """Replace the rows of one year in the bronze table; return the rows read from staging."""
    df = spark.read.schema(esquema_texto(colunas)).option("mode", "FAILFAST").json(str(pasta))
    df = adicionar_metadados(df, metadados)
    linhas = df.count()
    if spark.catalog.tableExists(tabela):
        (
            df.write.format("delta")
            .mode("overwrite")
            .option("replaceWhere", f"_source_year = '{ano}'")
            .saveAsTable(tabela)
        )
    else:
        (
            df.write.format("delta")
            .mode("overwrite")
            .partitionBy("_source_year")
            .saveAsTable(tabela)
        )
    return linhas
