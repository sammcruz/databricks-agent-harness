#!/usr/bin/env python3
"""List the Databricks `system` tables that `SELECT COUNT(*)` can read, and write a Markdown report.

Read-only. The tables come from two sources: the tables visible in `system.information_schema`
and the fixed list of tables documented by Databricks. Each table gets one statement,
`SELECT COUNT(*) FROM system.<schema>.<table>`. The only exception is `system.access.audit`,
which gets counts only (total and last 7 days). No data rows are ever written to the report.

Pure functions build the statements and render the report. `run_databricks` is the only function
that calls the Databricks CLI, through `scripts/dbquery.py`.

Usage (from the repository root):
  python -m scripts.system_tables_readable --show-statements
  python -m scripts.system_tables_readable --profile free --status verified
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from scripts.dbquery import build_command, check_read_only

DEFAULT_OUTPUT = Path("docs/knowledge/learnings/system-tables-readable.md")
AUDIT = ("access", "audit")
IDENTIFIER = re.compile(r"^[a-z_][a-z0-9_]*$")
MAX_ERROR_CHARS = 200

# Fixed list from the Databricks documentation ("System tables reference", updated 2026-11-25).
# `system.lakebase.*` is a wildcard in the docs, so it is not listed here. Visible tables cover it.
DOCUMENTED_TABLES = (
    ("alert", "alerts"),
    ("alert", "alert_evaluation_history"),
    ("access", "audit"),
    ("billing", "usage"),
    ("billing", "list_prices"),
    ("access", "clean_room_events"),
    ("compute", "clusters"),
    ("access", "column_lineage"),
    ("data_classification", "results"),
    ("data_quality_monitoring", "table_results"),
    ("tags", "governed_tags"),
    ("access", "assistant_events"),
    ("ai_gateway", "usage"),
    ("ai_gateway", "external_model_spend"),
    ("sharing", "materialization_history"),
    ("compute", "instance_events"),
    ("compute", "instance_pools"),
    ("lakeflow", "job_run_timeline"),
    ("lakeflow", "job_task_run_timeline"),
    ("lakeflow", "job_tasks"),
    ("lakeflow", "jobs"),
    ("marketplace", "listing_funnel_events"),
    ("marketplace", "listing_access_events"),
    ("mlflow", "experiments_latest"),
    ("mlflow", "runs_latest"),
    ("mlflow", "run_metrics_history"),
    ("serving", "served_entities"),
    ("serving", "endpoint_usage"),
    ("access", "inbound_network"),
    ("access", "outbound_network"),
    ("compute", "node_timeline"),
    ("compute", "node_types"),
    ("lakeflow_pipeline_events_preview", "pipeline_events"),
    ("lakeflow", "pipeline_update_timeline"),
    ("lakeflow", "pipelines"),
    ("storage", "auto_upgrade_operations_history"),
    ("storage", "predictive_optimization_operations_history"),
    ("storage", "table_metrics_history"),
    ("query", "history"),
    ("replication", "states"),
    ("compute", "warehouse_events"),
    ("compute", "warehouses"),
    ("access", "table_lineage"),
    ("access", "workspaces_latest"),
    ("lakeflow", "zerobus_stream"),
    ("lakeflow", "zerobus_ingest"),
)


@dataclass(frozen=True)
class TableCheck:
    """The result of one table check. `counts` holds only numbers, never data rows."""

    schema: str
    table: str
    source: str
    checked_on: str
    ok: bool
    counts: dict | None = None
    error: str | None = None


class QueryError(Exception):
    """A statement failed. The message is already short and safe to write to the report."""


def _check_identifier(name):
    if not IDENTIFIER.match(name):
        raise ValueError("unsafe identifier: {!r}".format(name))
    return name


def build_visible_tables_statement():
    """One statement that lists the visible tables of the `system` catalog."""
    return (
        "SELECT table_schema, table_name FROM system.information_schema.tables "
        "WHERE table_catalog = 'system' AND table_schema <> 'information_schema' "
        "ORDER BY table_schema, table_name"
    )


def parse_visible_tables(rows):
    """Turn rows of (table_schema, table_name) into a set of (schema, table) pairs."""
    visible = set()
    for row in rows:
        schema = str(row["table_schema"]).strip()
        table = str(row["table_name"]).strip()
        if IDENTIFIER.match(schema) and IDENTIFIER.match(table):
            visible.add((schema, table))
    return visible


def merge_tables(documented, visible):
    """Combine both lists into sorted (schema, table, source) rows without duplicates.

    `source` is "documented", "visible" or "documented+visible".
    """
    documented = set(documented)
    everything = documented | set(visible)
    merged = []
    for schema, table in sorted(everything):
        if (schema, table) in documented and (schema, table) in visible:
            source = "documented+visible"
        elif (schema, table) in documented:
            source = "documented"
        else:
            source = "visible"
        merged.append((schema, table, source))
    return merged


def build_table_statement(schema, table):
    """The statement for one table. `system.access.audit` gets counts only: total and last 7 days."""
    _check_identifier(schema)
    _check_identifier(table)
    if (schema, table) == AUDIT:
        return (
            "SELECT COUNT(*) AS total, "
            "COUNT_IF(event_time >= current_timestamp() - INTERVAL 7 DAYS) AS last_7_days "
            "FROM system.access.audit"
        )
    return "SELECT COUNT(*) FROM system.{}.{}".format(schema, table)


def build_statements(tables):
    """One (schema, table, sql) per table. Never a UNION ALL across tables."""
    return [(schema, table, build_table_statement(schema, table)) for schema, table, _ in tables]


def short_error(message):
    """Keep the first line, hide URLs and cap the length, so the report stays short and safe."""
    lines = [line.strip() for line in str(message).splitlines() if line.strip()]
    first = lines[0] if lines else "unknown error"
    first = re.sub(r"https?://\S+", "<url>", first)
    if len(first) > MAX_ERROR_CHARS:
        first = first[: MAX_ERROR_CHARS - 3] + "..."
    return first


def result_rows(payload):
    """All result rows as dicts, from the CLI JSON output. Raise QueryError on a statement error.

    Accepts a list of row objects, a `{columns, rows}` object, or the multi-query form
    `[{sql, columns, rows, error}]`. Lists of row objects are read as they are.
    """
    if isinstance(payload, dict) and "rows" in payload:
        payload = [payload]
    if isinstance(payload, list) and payload and isinstance(payload[0], dict) and "rows" in payload[0]:
        item = payload[0]
        if item.get("error"):
            raise QueryError(short_error(item["error"]))
        columns = [c["name"] if isinstance(c, dict) else c for c in item.get("columns") or []]
        return [r if isinstance(r, dict) else dict(zip(columns, r)) for r in item.get("rows") or []]
    if isinstance(payload, list):
        return payload
    raise QueryError("unexpected output shape")


def check_table(schema, table, source, checked_on, run_query):
    """Run the statement for one table and return a TableCheck. `run_query(sql)` returns the payload."""
    sql = build_table_statement(schema, table)
    try:
        rows = result_rows(run_query(sql))
        if not rows:
            raise QueryError("no rows returned")
        row = rows[0]
        if (schema, table) == AUDIT:
            counts = {"total": int(row["total"]), "last_7_days": int(row["last_7_days"])}
        else:
            counts = {"rows": int(next(iter(row.values())))}
    except (QueryError, KeyError, TypeError, ValueError) as error:
        return TableCheck(schema, table, source, checked_on, ok=False, error=short_error(error))
    return TableCheck(schema, table, source, checked_on, ok=True, counts=counts)


def _cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ")


def _rows_text(check):
    if not check.ok:
        return "—"
    if "total" in check.counts:
        return "total {}; last 7 days {}".format(check.counts["total"], check.counts["last_7_days"])
    return str(check.counts["rows"])


def render_markdown(checks, checked_on, status, note=""):
    """Render the report. It holds only table names, dates, results and counts."""
    if status not in ("verified", "unverified"):
        raise ValueError("status must be verified or unverified")
    ok_count = sum(1 for c in checks if c.ok)
    lines = [
        "# System tables readable with COUNT(*)",
        "",
        "Status: [{}]".format(status),
        "Last checked: {}".format(checked_on),
        "",
        "Read-only check. One statement per table: `SELECT COUNT(*) FROM system.<schema>.<table>`.",
        "`system.access.audit` gets counts only (total and last 7 days). No data rows are written here.",
        "The list joins the tables visible in `system.information_schema` with the fixed list from the",
        "Databricks documentation (source column). The documented `system.lakebase.*` wildcard is not listed.",
        "",
        "Summary: {} tables checked, {} readable, {} with error.".format(
            len(checks), ok_count, len(checks) - ok_count
        ),
    ]
    if note:
        lines += ["", "Note: " + _cell(note)]
    lines += [
        "",
        "| Schema | Table | Source | Checked on | Result | Rows | Error |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for c in checks:
        result = "success" if c.ok else "error"
        lines.append(
            "| {} | {} | {} | {} | {} | {} | {} |".format(
                _cell(c.schema),
                _cell(c.table),
                _cell(c.source),
                _cell(c.checked_on),
                result,
                _cell(_rows_text(c)),
                _cell(c.error or ""),
            )
        )
    return "\n".join(lines) + "\n"


def run_databricks(sql, profile="free"):
    """The only Databricks call. Refuses anything that is not a read. Returns the parsed JSON."""
    reason = check_read_only(sql)
    if reason:
        raise QueryError("refused: " + reason)
    try:
        completed = subprocess.run(
            build_command(sql, profile, "json"), capture_output=True, text=True
        )
    except FileNotFoundError:
        raise QueryError("Databricks CLI not found") from None
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "statement failed").strip()
        raise QueryError(short_error(message))
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        raise QueryError("output is not JSON") from None


def main(argv=None):
    parser = argparse.ArgumentParser(description="List readable system tables (read-only).")
    parser.add_argument("--profile", default="free", help="Databricks CLI profile")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Markdown file to write")
    parser.add_argument("--status", choices=["verified", "unverified"], default="unverified")
    parser.add_argument(
        "--show-statements", action="store_true", help="print the documented statements and stop"
    )
    args = parser.parse_args(argv)

    today = date.today().isoformat()
    if args.show_statements:
        for _, _, sql in build_statements(merge_tables(DOCUMENTED_TABLES, ())):
            print(sql + ";")
        return 0

    note = ""
    try:
        visible = parse_visible_tables(result_rows(run_databricks(build_visible_tables_statement(), args.profile)))
    except QueryError as error:
        visible = set()
        note = "Visible tables could not be listed ({}). Only the documented list was checked.".format(error)

    tables = merge_tables(DOCUMENTED_TABLES, visible)
    checks = []
    for schema, table, source in tables:
        checks.append(
            check_table(schema, table, source, today, lambda sql: run_databricks(sql, args.profile))
        )
        print("{}.{}: {}".format(schema, table, "ok" if checks[-1].ok else "error"))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(checks, today, args.status, note), encoding="utf-8")
    print("Wrote {} ({} tables)".format(args.output, len(checks)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
