#!/usr/bin/env python3
"""Read-only check of the tools the labs need. Installs nothing and prints no credentials.

Works with old Python 3 versions on purpose: it runs before the setup is done.
Exit code 1 means something is missing or too old.
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# (label, command, minimum version or None)
TOOLS = [
    ("git", ["git", "--version"], None),
    ("Databricks CLI", ["databricks", "-v"], (1, 0, 0)),
    ("GitHub CLI", ["gh", "--version"], None),
    ("uv", ["uv", "--version"], None),
    ("Spec Kit", ["specify", "version"], None),
]

# `uv tool install` puts these in ~/.local/bin, which is often not on PATH yet.
LOCAL_BIN_TOOLS = {"specify"}


def parse_version(text):
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text)
    return tuple(int(part) for part in match.groups()) if match else None


def find_local_bin(name):
    """Path of `name` in ~/.local/bin, or None. Does not change PATH."""
    names = [name + ".exe", name] if os.name == "nt" else [name]
    for file_name in names:
        candidate = Path.home() / ".local" / "bin" / file_name
        if candidate.is_file() and os.access(str(candidate), os.X_OK):
            return str(candidate)
    return None


def find_tool(name):
    path = shutil.which(name)
    if path or name not in LOCAL_BIN_TOOLS:
        return path
    return find_local_bin(name)


def check(command, minimum):
    path = find_tool(command[0])
    if not path:
        return "missing", ""
    try:
        done = subprocess.run(
            [path] + command[1:],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "error", ""
    if done.returncode != 0:
        return "error", ""
    version = parse_version(done.stdout)
    shown = ".".join(str(n) for n in version) if version else "?"
    if minimum and (version is None or version < minimum):
        return "too old", shown
    return "ok", shown


def uv_has_python():
    """True if uv can find a Python 3.11 or newer."""
    uv = shutil.which("uv")
    if not uv:
        return False
    try:
        done = subprocess.run(
            [uv, "python", "find", ">=3.11"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return done.returncode == 0


def main():
    results = [(label,) + check(command, minimum) for label, command, minimum in TOOLS]
    python_ok = sys.version_info >= (3, 11) or uv_has_python()
    results.append(("Python 3.11+", "ok" if python_ok else "missing", ""))
    for label, status, version in results:
        print("{:<16} {:<8} {}".format(label, status, version))
    problems = [label for label, status, _ in results if status != "ok"]
    if problems:
        print("\nNeeds attention: " + ", ".join(problems))
        print("Follow skills/core/environment-setup/SKILL.md")
        return 1
    print("\nAll tools found. Logins are not checked here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
