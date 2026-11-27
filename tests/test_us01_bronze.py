"""US01: the bronze table (Spark): all text, metadata non-null, one year replaced per run.

These need a local Java runtime. Without one they are skipped; the dev load checks them
on Databricks serverless (see the story's dev acceptance).
"""

import shutil
import subprocess

import pytest

from src.us01.bronze import COLUNAS_METADADOS, esquema_texto

java = pytest.mark.skipif(shutil.which("java") is None, reason="sem Java local (rodar no dev)")


def _tem_jdk() -> bool:
    # macOS tem um stub /usr/bin/java sem JDK; só conta se `java -version` funcionar
    if shutil.which("java") is None:
        return False
    return subprocess.run(["java", "-version"], capture_output=True).returncode == 0


@pytest.fixture
def spark():
    if not _tem_jdk():
        pytest.skip("sem JDK local (rodar no dev)")
    from pyspark.sql import SparkSession

    sessao = SparkSession.builder.master("local[1]").appName("us01-tests").getOrCreate()
    yield sessao


def test_esquema_e_todo_texto():
    esquema = esquema_texto(["idcontrato", "valor"])
    assert [campo.dataType.typeName() for campo in esquema.fields] == ["string", "string"]


def test_colunas_de_metadados_definidas():
    assert COLUNAS_METADADOS == [
        "_source_url",
        "_source_modified",
        "_ingested_at",
        "_file_sha256",
        "_source_year",
    ]


@java
def test_metadados_presentes_e_nao_nulos(spark, tmp_path):
    from src.us01.bronze import gravar_ano

    pasta = tmp_path / "staging"
    pasta.mkdir()
    (pasta / "part-00000.ndjson").write_text('{"idcontrato":"1","valor":"9000.00"}\n')
    metadados = {c: "x" for c in COLUNAS_METADADOS}
    tabela = "tmp_us01_bronze_meta"
    gravar_ano(spark, pasta, ["idcontrato", "valor"], metadados, tabela, ano=2026)
    df = spark.table(tabela)
    for coluna in COLUNAS_METADADOS:
        assert df.filter(df[coluna].isNull()).count() == 0
    spark.sql(f"DROP TABLE IF EXISTS {tabela}")


@java
def test_duas_cargas_do_mesmo_ano_nao_duplicam(spark, tmp_path):
    from src.us01.bronze import gravar_ano

    pasta = tmp_path / "staging"
    pasta.mkdir()
    (pasta / "part-00000.ndjson").write_text('{"idcontrato":"1"}\n{"idcontrato":"2"}\n')
    metadados = {c: "x" for c in COLUNAS_METADADOS}
    tabela = "tmp_us01_bronze_idem"
    gravar_ano(spark, pasta, ["idcontrato"], metadados, tabela, ano=2026)
    gravar_ano(spark, pasta, ["idcontrato"], metadados, tabela, ano=2026)
    assert spark.table(tabela).count() == 2
    spark.sql(f"DROP TABLE IF EXISTS {tabela}")
