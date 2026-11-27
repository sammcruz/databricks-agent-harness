import runpy
import subprocess
from pathlib import Path

import pytest

import scripts.check_github_login as check_github_login

SCRIPT = Path(check_github_login.__file__)

# Built at runtime so this file holds no token-shaped literal.
FAKE_TOKEN = "gh" + "p_" + "Z" * 36
SENTINEL_DATABRICKS_OUTPUT = "sentinel-databricks-output-0001"

GH_AUTH_OK = (
    "github.com\n"
    "  ✓ Logged in to github.com account sentinel-account (keyring)\n"
    "  - Active account: true\n"
    "  - Token scopes: 'gist', 'project', 'read:org', 'repo'\n"
)

GH_AUTH_PROJECT_ONLY_ON_INACTIVE = (
    "github.com\n"
    "  ✓ Logged in to github.com account sentinel-active (keyring)\n"
    "  - Active account: true\n"
    "  - Token scopes: 'read:org', 'repo'\n"
    "\n"
    "  ✓ Logged in to github.com account sentinel-inactive (keyring)\n"
    "  - Active account: false\n"
    "  - Token scopes: 'project', 'repo'\n"
)

GH_AUTH_PROJECT_ON_ACTIVE = (
    "github.com\n"
    "  ✓ Logged in to github.com account sentinel-active (keyring)\n"
    "  - Active account: true\n"
    "  - Token scopes: 'project', 'repo'\n"
    "\n"
    "  ✓ Logged in to github.com account sentinel-inactive (keyring)\n"
    "  - Active account: false\n"
    "  - Token scopes: 'read:org'\n"
)

GH_AUTH_NO_ACTIVE_MARKER = (
    "github.com\n"
    "  ✓ Logged in to github.com account sentinel-account (keyring)\n"
    "  - Token scopes: 'project', 'repo'\n"
)


class Done:
    def __init__(self, stdout="", returncode=0):
        self.stdout = stdout
        self.returncode = returncode


@pytest.fixture
def fake_gh(monkeypatch):
    """Fake subprocess.run. Every check passes unless a test changes `responses`."""
    state = {
        "responses": {
            "gh auth": Done(GH_AUTH_OK, 0),
            "databricks current-user": Done(SENTINEL_DATABRICKS_OUTPUT, 0),
            "gh repo": Done(check_github_login.EXPECTED_REPO + "\n", 0),
            "git grep": Done("", 1),  # exit 1 means no token-like match
        },
        "calls": [],
    }

    def fake_run(command, **kwargs):
        state["calls"].append((list(command), kwargs))
        key = command[0] + " " + command[1]
        response = state["responses"][key]
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(check_github_login.subprocess, "run", fake_run)
    return state


def test_all_checks_pass_exits_zero(fake_gh, capsys):
    assert check_github_login.main() == 0

    out = capsys.readouterr().out
    assert "All GitHub and Databricks checks passed." in out
    assert "fail" not in out


def test_gh_token_without_project_scope_fails(fake_gh, capsys):
    fake_gh["responses"]["gh auth"] = Done(
        "  ✓ Logged in to github.com account sentinel-account (keyring)\n"
        "  - Active account: true\n"
        "  - Token scopes: 'gist', 'read:org', 'repo'\n",
        0,
    )

    assert check_github_login.main() == 1

    out = capsys.readouterr().out
    gh_line = [line for line in out.splitlines() if line.startswith("GitHub CLI login")][0]
    assert "fail" in gh_line
    assert "project" in gh_line


def test_gh_not_logged_in_fails(fake_gh, capsys):
    fake_gh["responses"]["gh auth"] = Done("You are not logged in\n", 1)

    assert check_github_login.main() == 1
    assert "gh is not logged in" in capsys.readouterr().out


def test_project_scope_only_on_non_active_account_fails(fake_gh, capsys):
    fake_gh["responses"]["gh auth"] = Done(GH_AUTH_PROJECT_ONLY_ON_INACTIVE, 0)

    assert check_github_login.main() == 1

    out = capsys.readouterr().out
    gh_line = [line for line in out.splitlines() if line.startswith("GitHub CLI login")][0]
    assert "fail" in gh_line
    assert "no 'project' scope" in gh_line
    assert "sentinel-inactive" not in out


def test_project_scope_on_active_account_passes(fake_gh, capsys):
    fake_gh["responses"]["gh auth"] = Done(GH_AUTH_PROJECT_ON_ACTIVE, 0)

    assert check_github_login.main() == 0
    assert "All GitHub and Databricks checks passed." in capsys.readouterr().out


def test_active_account_undetermined_fails(fake_gh, capsys):
    fake_gh["responses"]["gh auth"] = Done(GH_AUTH_NO_ACTIVE_MARKER, 0)

    assert check_github_login.main() == 1
    assert "could not tell the active gh account" in capsys.readouterr().out


def test_project_scope_name_inside_another_scope_does_not_count(fake_gh, capsys):
    # "read:project" is a different scope; it must not satisfy the check.
    fake_gh["responses"]["gh auth"] = Done(
        "  ✓ Logged in to github.com account sentinel-account (keyring)\n"
        "  - Active account: true\n"
        "  - Token scopes: 'read:project', 'repo'\n",
        0,
    )

    assert check_github_login.main() == 1
    assert "no 'project' scope" in capsys.readouterr().out


def test_wrong_default_repo_fails(fake_gh, capsys):
    fake_gh["responses"]["gh repo"] = Done("someone/other-repo\n", 0)

    assert check_github_login.main() == 1

    out = capsys.readouterr().out
    repo_line = [line for line in out.splitlines() if line.startswith("GitHub default repo")][0]
    assert "fail" in repo_line
    assert "someone/other-repo" not in out


def test_databricks_failure_fails_and_its_output_is_never_shown(fake_gh, capsys):
    fake_gh["responses"]["databricks current-user"] = Done(SENTINEL_DATABRICKS_OUTPUT, 1)

    assert check_github_login.main() == 1

    out = capsys.readouterr().out
    assert "profile 'free' check failed" in out
    assert SENTINEL_DATABRICKS_OUTPUT not in out


def test_databricks_output_is_discarded_on_success(fake_gh, capsys):
    assert check_github_login.main() == 0

    databricks_calls = [
        (command, kwargs)
        for command, kwargs in fake_gh["calls"]
        if command[0] == "databricks"
    ]
    assert len(databricks_calls) == 1
    command, kwargs = databricks_calls[0]
    assert command == ["databricks", "current-user", "me", "--profile", "free"]
    assert kwargs["stdout"] == subprocess.DEVNULL
    assert kwargs["stderr"] == subprocess.DEVNULL
    assert SENTINEL_DATABRICKS_OUTPUT not in capsys.readouterr().out


def test_databricks_call_does_not_read_stdin(fake_gh):
    check_github_login.main()

    databricks_kwargs = [
        kwargs for command, kwargs in fake_gh["calls"] if command[0] == "databricks"
    ]
    assert len(databricks_kwargs) == 1
    assert databricks_kwargs[0]["stdin"] == subprocess.DEVNULL


def test_timeout_fails_cleanly_without_traceback(fake_gh, capsys):
    fake_gh["responses"]["gh auth"] = subprocess.TimeoutExpired(["gh", "auth", "status"], 60)

    assert check_github_login.main() == 1

    out = capsys.readouterr().out
    gh_line = [line for line in out.splitlines() if line.startswith("GitHub CLI login")][0]
    assert "fail" in gh_line
    assert "gh not found or did not run" in gh_line
    assert "Traceback" not in out


def test_token_in_grep_result_fails_and_token_is_not_printed(fake_gh, capsys):
    fake_gh["responses"]["git grep"] = Done(
        "tests/fake_file.py:7:TOKEN = '" + FAKE_TOKEN + "'\n", 0
    )

    assert check_github_login.main() == 1

    out = capsys.readouterr().out
    secret_line = [line for line in out.splitlines() if line.startswith("No tokens in repo")][0]
    assert "fail" in secret_line
    assert "tests/fake_file.py:7" in secret_line
    assert FAKE_TOKEN not in out
    assert "Z" * 36 not in out


def test_missing_gh_binary_fails_without_crashing(fake_gh, capsys):
    fake_gh["responses"]["gh auth"] = FileNotFoundError("gh")

    assert check_github_login.main() == 1
    assert "gh not found or did not run" in capsys.readouterr().out


def test_grep_error_fails(fake_gh, capsys):
    fake_gh["responses"]["git grep"] = Done("fatal: not a git repository\n", 128)

    assert check_github_login.main() == 1
    assert "git grep failed" in capsys.readouterr().out


def test_grep_commands_use_the_pattern_from_the_issue(fake_gh):
    check_github_login.main()

    grep_calls = [command for command, _ in fake_gh["calls"] if command[0] == "git"]
    assert grep_calls == [["git", "grep", "-nE", check_github_login.TOKEN_PATTERN]]
    assert check_github_login.TOKEN_PATTERN == (
        r"gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}|dapi[a-f0-9]{32}"
    )


def test_script_exit_code_matches_main_result(fake_gh):
    # Runs the file as a program, so the `sys.exit(main())` line is covered too.
    with pytest.raises(SystemExit) as ok:
        runpy.run_path(str(SCRIPT), run_name="__main__")
    assert ok.value.code == 0

    fake_gh["responses"]["gh repo"] = Done("someone/other-repo\n", 0)
    with pytest.raises(SystemExit) as failed:
        runpy.run_path(str(SCRIPT), run_name="__main__")
    assert failed.value.code == 1
