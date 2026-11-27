#!/usr/bin/env python3
"""Read-only check of the GitHub and Databricks logins and of the repo default.

Runs four checks and prints one line per check. It never prints the output of
gh or databricks, and never prints a token or account data. A secret-scan hit
is reported only as file and line number.
Exit code 0 means every check passed; 1 means at least one failed.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_REPO = "sammcruz/databricks-agent-harness"
REQUIRED_GH_SCOPE = "project"
# Same pattern as the secret scan in the issue; keep the two in sync.
TOKEN_PATTERN = r"gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}|dapi[a-f0-9]{32}"


class Result:
    def __init__(self, label, ok, reason):
        self.label = label
        self.ok = ok
        self.reason = reason


def run(command, discard=False):
    """Run a command without a shell. Returns (returncode, stdout), or (None, "") if it could not run.

    With discard=True the output goes to DEVNULL and is never read.
    """
    kwargs = {
        "cwd": str(REPO_ROOT),
        "timeout": 60,
        "universal_newlines": True,
        "encoding": "utf-8",
        "errors": "replace",
    }
    if discard:
        kwargs["stdin"] = subprocess.DEVNULL
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
    else:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.STDOUT
    try:
        done = subprocess.run(command, **kwargs)
    except (OSError, subprocess.TimeoutExpired):
        return None, ""
    return done.returncode, done.stdout or ""


def active_token_scopes(text):
    """Scopes of the active gh account, or None if the active account cannot be determined.

    `gh auth status` prints one block per account, each starting with a "Logged in to" line.
    Only the block marked "Active account: true" counts; scopes on other accounts are ignored.
    """
    blocks = []
    for line in text.splitlines():
        if "Logged in to" in line:
            blocks.append({"active": None, "scopes": set()})
        elif blocks and "Active account:" in line:
            blocks[-1]["active"] = line.partition(":")[2].strip().lower() == "true"
        elif blocks and "Token scopes" in line:
            blocks[-1]["scopes"] = set(re.findall(r"[A-Za-z0-9_:.-]+", line.partition(":")[2]))
    active = [block for block in blocks if block["active"] is True]
    if len(active) != 1:
        return None
    return active[0]["scopes"]


def has_scope(text, scope):
    """True if the active gh account's token lists the scope. Other accounts are ignored."""
    scopes = active_token_scopes(text)
    return scopes is not None and scope in scopes


def check_gh_login():
    code, out = run(["gh", "auth", "status"])
    if code is None:
        return Result("GitHub CLI login", False, "gh not found or did not run")
    if code != 0:
        return Result("GitHub CLI login", False, "gh is not logged in")
    if active_token_scopes(out) is None:
        return Result("GitHub CLI login", False, "could not tell the active gh account")
    if not has_scope(out, REQUIRED_GH_SCOPE):
        return Result("GitHub CLI login", False, "active account's token has no 'project' scope")
    return Result("GitHub CLI login", True, "logged in with 'project' scope")


def check_databricks_login():
    # Output is discarded on purpose: it can contain account data.
    code, _ = run(["databricks", "current-user", "me", "--profile", "free"], discard=True)
    if code is None:
        return Result("Databricks login", False, "databricks not found or did not run")
    if code != 0:
        return Result("Databricks login", False, "profile 'free' check failed")
    return Result("Databricks login", True, "profile 'free' works")


def check_default_repo():
    code, out = run(["gh", "repo", "set-default", "--view"])
    if code is None:
        return Result("GitHub default repo", False, "gh not found or did not run")
    if code != 0:
        return Result("GitHub default repo", False, "no default repo set")
    if out.strip() != EXPECTED_REPO:
        return Result("GitHub default repo", False, "default repo is not " + EXPECTED_REPO)
    return Result("GitHub default repo", True, EXPECTED_REPO)


def check_no_token_strings():
    # git grep exits 1 when nothing matches, 0 when something matches.
    code, out = run(["git", "grep", "-nE", TOKEN_PATTERN])
    if code is None or code > 1:
        return Result("No tokens in repo", False, "git grep failed")
    if code == 1:
        return Result("No tokens in repo", True, "no token-like strings in tracked files")
    # Print only file and line number; the matched text is never shown.
    lines = out.splitlines()
    location = "unknown location"
    match = re.match(r"^(.+?):(\d+):", lines[0]) if lines else None
    if match:
        location = match.group(1) + ":" + match.group(2)
    return Result(
        "No tokens in repo",
        False,
        "{} token-like match(es), first at {}".format(len(lines), location),
    )


def main():
    results = [
        check_gh_login(),
        check_databricks_login(),
        check_default_repo(),
        check_no_token_strings(),
    ]
    for result in results:
        status = "ok" if result.ok else "fail"
        print("{:<22} {:<5} {}".format(result.label, status, result.reason))
    if all(result.ok for result in results):
        print("\nAll GitHub and Databricks checks passed.")
        return 0
    print("\nSome checks failed. Fix the lines marked fail, then run this again.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
