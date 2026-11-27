import re
import runpy
from pathlib import Path

import pytest

import scripts.check_environment as check_environment

SCRIPT = Path(check_environment.__file__)

FAKE_VERSIONS = {
    "git": "git version 2.45.1",
    "databricks": "Databricks CLI v1.2.0\nToken: sentinel-not-printed-0001",
    "gh": "gh version 2.60.0 (2024-08-01)",
    "uv": "uv 0.5.0",
    "specify": "specify 0.1.0",
}


class Done:
    def __init__(self, stdout="", returncode=0):
        self.stdout = stdout
        self.returncode = returncode


@pytest.fixture
def fake_tools(monkeypatch):
    """Pretend every tool is installed unless a test removes it from `missing`."""
    state = {"missing": set()}

    def fake_which(name):
        return None if name in state["missing"] else "/fake/bin/" + name

    def fake_run(command, **kwargs):
        name = Path(command[0]).name
        if name == "uv":
            return Done(returncode=0)  # `uv python find >=3.11` succeeds
        return Done(FAKE_VERSIONS[name])

    monkeypatch.setattr(check_environment.shutil, "which", fake_which)
    monkeypatch.setattr(check_environment.subprocess, "run", fake_run)
    monkeypatch.setattr(check_environment, "uv_has_python", lambda: True)
    return state


def test_all_tools_ok_exits_zero_and_says_all_found(fake_tools, capsys):
    assert check_environment.main() == 0

    out = capsys.readouterr().out
    assert "All tools found" in out
    assert "Needs attention" not in out
    assert re.search(r"^git\s+ok\s+2\.45\.1$", out, re.MULTILINE)


@pytest.mark.parametrize("missing_command, label", [("gh", "GitHub CLI"), ("specify", "Spec Kit")])
def test_missing_tool_exits_one_and_is_named(fake_tools, capsys, missing_command, label):
    fake_tools["missing"].add(missing_command)

    assert check_environment.main() == 1

    out = capsys.readouterr().out
    assert re.search(r"^" + re.escape(label) + r"\s+missing\s*$", out, re.MULTILINE)
    assert "Needs attention: " + label in out
    assert "All tools found" not in out


def test_output_never_shows_token_like_strings(fake_tools, capsys, monkeypatch):
    monkeypatch.setenv("DATABRICKS_TOKEN", "dapi" + "f" * 32)
    fake_tools["missing"].add("gh")

    check_environment.main()

    out = capsys.readouterr().out
    assert "sentinel-not-printed" not in out
    assert "f" * 32 not in out
    assert "Token" not in out


def test_script_exit_code_matches_main_result(fake_tools, capsys):
    # Runs the file as a program, so the `sys.exit(main())` line is covered too.
    with pytest.raises(SystemExit) as ok:
        runpy.run_path(str(SCRIPT), run_name="__main__")
    assert ok.value.code == 0

    fake_tools["missing"].add("git")
    with pytest.raises(SystemExit) as failed:
        runpy.run_path(str(SCRIPT), run_name="__main__")
    assert failed.value.code == 1
