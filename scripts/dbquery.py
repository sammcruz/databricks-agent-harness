#!/usr/bin/env python3
"""Run one read-only SQL statement on a Databricks SQL warehouse.

Wraps `databricks experimental aitools tools query` and refuses anything that is not a single
read statement. This is a guardrail against mistakes, not a security boundary: the real
boundary is what your Databricks user is allowed to do.

Usage:
  python scripts/dbquery.py "SELECT current_date()"
  python scripts/dbquery.py --file query.sql --profile free
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

ALLOWED_FIRST_WORDS = {"select", "with", "show", "describe", "desc", "explain"}
FORBIDDEN_WORDS = {
    "insert", "update", "delete", "merge", "drop", "alter", "truncate", "create", "grant",
    "revoke", "vacuum", "optimize",
}  # fmt: skip
# Functions that reach outside the warehouse, run arbitrary code or bill separately.
FORBIDDEN_FUNCTIONS = {"http_request", "remote_query", "ai_query", "reflect", "java_method"}

# String literals, quoted identifiers and comments, matched left to right.
IGNORED = re.compile(
    r"'(?:\\.|''|[^'\\])*'"
    r'|"(?:\\.|""|[^"\\])*"'
    r"|`(?:``|[^`])*`"
    r"|--[^\n]*"
    r"|/\*.*?\*/",
    re.DOTALL,
)


def check_read_only(sql):
    """Return None if the statement looks read-only, otherwise the reason to refuse it."""
    # A backticked name can still call a function, so keep those names visible.
    unquoted = re.sub(r"`(\w+)`(?=\s*\()", r"\1", sql)
    code = IGNORED.sub(" ", unquoted).lower().strip().rstrip(";").strip()
    if not code:
        return "empty statement"
    if any(mark in code for mark in ("'", '"', "`", "/*")):
        return "unterminated string, identifier or comment"
    if ";" in code:
        return "only one statement is allowed"
    words = re.findall(r"[a-z_]\w*", code)
    if not words or words[0] not in ALLOWED_FIRST_WORDS:
        return "statement must start with " + ", ".join(sorted(ALLOWED_FIRST_WORDS))
    # SHOW CREATE TABLE only reads the definition.
    checked = re.sub(r"^show\s+create\s+table\b", "show table", code)
    found = FORBIDDEN_WORDS.intersection(re.findall(r"[a-z_]\w*", checked))
    if found:
        return "write keyword found: " + ", ".join(sorted(found))
    for name in sorted(FORBIDDEN_FUNCTIONS):
        if re.search(r"\b" + name + r"\s*\(", code):
            return "function not allowed: " + name
    return None


def build_command(sql, profile="free", output="json"):
    """Return the Databricks CLI command that runs one statement. The SQL goes after `--`."""
    return [
        "databricks", "experimental", "aitools", "tools", "query",
        "--profile", profile, "--output", output,
        "--", sql.strip(),
    ]  # fmt: skip


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run one read-only SQL statement.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("sql", nargs="?", help="the statement")
    source.add_argument("--file", help="file with the statement")
    parser.add_argument("--profile", default="free", help="Databricks CLI profile")
    parser.add_argument("--output", choices=["json", "csv"], default="json")
    args = parser.parse_args(argv)

    sql = Path(args.file).read_text(encoding="utf-8") if args.file else args.sql
    reason = check_read_only(sql)
    if reason:
        print("Refused: {}.".format(reason), file=sys.stderr)
        return 2

    command = build_command(sql, args.profile, args.output)
    try:
        return subprocess.run(command).returncode
    except FileNotFoundError:
        print("Databricks CLI not found. See skill environment-setup.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
