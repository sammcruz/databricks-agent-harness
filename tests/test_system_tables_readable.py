import re

import pytest

import scripts.system_tables_readable as sut
from scripts.dbquery import check_read_only
from scripts.system_tables_readable import (
    DOCUMENTED_TABLES,
    QueryError,
    build_statements,
    build_table_statement,
    build_visible_tables_statement,
    check_table,
    main,
    merge_tables,
    parse_visible_tables,
    render_markdown,
    result_rows,
    short_error,
)

CHECKED = "2026-11-27"
COUNT_ONLY = re.compile(r"^SELECT COUNT\(\*\) FROM system\.[a-z_]+\.[a-z_]+$")


def fake_runner(answers):
    """Return a run_query(sql) that answers from a dict {sql: payload or QueryError}."""

    def run(sql):
        answer = answers[sql]
        if isinstance(answer, Exception):
            raise answer
        return answer

    return run


def test_success_row_is_rendered_with_count_and_date():
    check = check_table(
        "billing", "usage", "documented", CHECKED,
        fake_runner({"SELECT COUNT(*) FROM system.billing.usage": [{"count(1)": 42}]}),
    )  # fmt: skip
    text = render_markdown([check], CHECKED, "unverified")
    assert check.ok and check.counts == {"rows": 42}
    assert "| billing | usage | documented | 2026-11-27 | success | 42 |  |" in text


def test_error_row_is_rendered_with_short_message():
    error = QueryError("PERMISSION_DENIED: no SELECT on system.access.table_lineage\nDetails...")
    check = check_table(
        "access", "table_lineage", "documented", CHECKED,
        fake_runner({"SELECT COUNT(*) FROM system.access.table_lineage": error}),
    )  # fmt: skip
    text = render_markdown([check], CHECKED, "unverified")
    assert not check.ok
    expected = (
        "| access | table_lineage | documented | 2026-11-27 | error | — | "
        "PERMISSION_DENIED: no SELECT on system.access.table_lineage |"
    )
    assert expected in text
    assert "Details" not in text


def test_pipe_and_newline_in_error_do_not_break_the_table():
    check = check_table(
        "x", "y", "visible", CHECKED,
        fake_runner({"SELECT COUNT(*) FROM system.x.y": QueryError("bad | value")}),
    )  # fmt: skip
    text = render_markdown([check], CHECKED, "unverified")
    assert "bad \\| value" in text


def test_audit_is_counts_only_total_and_last_7_days():
    sql = build_table_statement("access", "audit")
    assert "COUNT_IF" in sql and "INTERVAL 7 DAYS" in sql
    check = check_table(
        "access", "audit", "documented", CHECKED,
        fake_runner({sql: [{"total": 100, "last_7_days": 7, "user_email": "a@b.c"}]}),
    )  # fmt: skip
    assert check.counts == {"total": 100, "last_7_days": 7}
    text = render_markdown([check], CHECKED, "unverified")
    assert "total 100; last 7 days 7" in text
    assert "a@b.c" not in text


def test_no_data_row_is_written_to_the_file(tmp_path, monkeypatch):
    secret = "customer-secret-value-123"
    visible = [{"table_schema": "billing", "table_name": "usage"}]

    def fake_run(sql, profile="free"):
        if sql.startswith("SELECT table_schema"):
            return visible
        return [{"count(1)": 5, "payload": secret}]

    monkeypatch.setattr(sut, "run_databricks", fake_run)
    out = tmp_path / "report.md"
    assert main(["--output", str(out), "--status", "verified"]) == 0
    text = out.read_text(encoding="utf-8")
    assert secret not in text
    assert "[verified]" in text and "Last checked: " in text


def test_one_statement_per_table_and_no_union():
    tables = merge_tables(DOCUMENTED_TABLES, {("billing", "usage"), ("custom", "t")})
    statements = build_statements(tables)
    assert len(statements) == len(tables)
    for schema, table, sql in statements:
        assert "UNION" not in sql.upper()
        assert sql.count(";") == 0
        if (schema, table) != ("access", "audit"):
            assert COUNT_ONLY.match(sql), sql
            assert sql == "SELECT COUNT(*) FROM system.{}.{}".format(schema, table)


def test_visible_statement_passes_the_read_only_guard():
    assert check_read_only(build_visible_tables_statement()) is None


def test_merge_combines_sources_without_duplicates():
    documented = [("billing", "usage"), ("access", "audit")]
    merged = merge_tables(documented, {("billing", "usage"), ("lakebase", "x")})
    assert merged == [
        ("access", "audit", "documented"),
        ("billing", "usage", "documented+visible"),
        ("lakebase", "x", "visible"),
    ]


def test_visible_tables_parse_and_skip_odd_names():
    rows = [
        {"table_schema": "billing", "table_name": "usage"},
        {"table_schema": "bad schema", "table_name": "x"},
    ]
    assert parse_visible_tables(rows) == {("billing", "usage")}


def test_unsafe_identifier_is_refused():
    with pytest.raises(ValueError):
        build_table_statement("billing", "usage; DROP TABLE x")


def test_error_message_hides_urls_and_is_short():
    message = short_error("failed at https://host.example.com/x\nsecond line " + "a" * 500)
    assert "host.example" not in message
    assert message.startswith("failed at <url>")
    assert len(message) <= sut.MAX_ERROR_CHARS


def test_result_rows_accepts_columns_and_rows_form():
    payload = {"columns": [{"name": "n"}], "rows": [[3]]}
    assert result_rows(payload) == [{"n": 3}]


def test_result_rows_raises_on_statement_error():
    with pytest.raises(QueryError):
        result_rows([{"sql": "x", "rows": [], "error": "no table"}])


def test_empty_result_is_an_error_row():
    sql = "SELECT COUNT(*) FROM system.billing.usage"
    check = check_table("billing", "usage", "documented", CHECKED, fake_runner({sql: []}))
    assert not check.ok and check.error == "no rows returned"


def test_run_databricks_refuses_a_write_without_calling_cli(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("the CLI must not be called")

    monkeypatch.setattr("scripts.system_tables_readable.subprocess.run", fail)
    with pytest.raises(QueryError):
        sut.run_databricks("DELETE FROM system.billing.usage")


def test_show_statements_does_not_connect(monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise AssertionError("no connection when showing statements")

    monkeypatch.setattr(sut, "run_databricks", fail)
    assert main(["--show-statements"]) == 0
    out = capsys.readouterr().out
    assert "SELECT COUNT(*) FROM system.billing.usage;" in out


def test_rejects_unknown_status():
    with pytest.raises(ValueError):
        render_markdown([], CHECKED, "maybe")
