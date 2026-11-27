# Error log

Append only. Newest at the bottom. Format and rules: skill `self-improvement`.
Do not store secrets or personal data here.

Entry template:

```
## YYYY-MM-DD HH:MM · <skill or area> · <open|fixed>
- Symptom:
- Cause:
- Fix:
- Prevention: (which file should change)
- Status: open | fixed-in-skill | wont-fix
- Seen: 1
```

---

## 2026-11-27 00:00 · example · fixed
- Symptom: `databricks: command not found` right after installing the CLI.
- Cause: the terminal was opened before the install, so PATH was stale.
- Fix: open a new terminal.
- Prevention: `skills/databricks/databricks-cli-auth` lists it under typical errors.
- Status: fixed-in-skill
- Seen: 1

## 2026-11-27 19:00 · environment-setup · open
- Symptom: on Windows, `gh : The term 'gh' is not recognized as the name of a cmdlet, function, script file, or operable program.` It continued after the agent reported a successful install.
- Cause: not confirmed. Likely the student's terminal kept the old PATH; the agent refreshing PATH in its own shell does not change it.
- Fix: not confirmed yet.
- Prevention: `skills/core/environment-setup` and `INIT.md` now ask to refresh PATH in the student's terminal, or restart VS Code, before any login.
- Status: open
- Seen: 1

## 2026-11-27 15:10 · scripts (system_tables_readable) · open
- Symptom: `python scripts/system_tables_readable.py --show-statements` fails with `ModuleNotFoundError: No module named 'scripts'`, because the script imports `scripts.dbquery` and running a file directly puts `scripts/` on the path, not the repo root.
- Cause: a script in `scripts/` that imports a sibling module through the `scripts` package.
- Fix: run it as a module from the repo root: `python -m scripts.system_tables_readable`. The docstring shows this.
- Prevention: not yet in a skill. Scripts in `scripts/` that import each other must be run with `python -m scripts.<name>`; the skill that documents the script should say so.
- Status: open
- Seen: 1

## 2026-11-27 15:30 · python command (AGENTS.md, skill databricks-sql-query, scripts) · open
- Symptom: `python scripts/dbquery.py --help` fails with `/bin/bash: python: command not found` on the macOS machine. `python3` exists and runs.
- Cause: `python` is not on PATH on this machine. AGENTS.md and the skills write `python scripts/...` and `python -m pytest` as if `python` always exists.
- Fix: use `python3` on macOS, or install a `python` alias. Not changed in this run.
- Prevention: `docs/gotchas/databricks.md` or `environment-setup` should say which command the machine has (`python` or `python3`). Check with `python3 scripts/check_environment.py` first.
- Status: open
- Seen: 1

## 2026-11-28 · US01 probe · SystemExit reported as job SUCCESS
- Symptom: a serverless one-off probe (`databricks jobs submit`) showed SUCCESS while its check had failed; `raise SystemExit(1)` was the only signal.
- Cause: an uncaught `SystemExit` ends the notebook task with a success state.
- Fix: the probe now uses `dbutils.notebook.exit(json)` for results and `raise` for failures. Output is read with `get-run` → `tasks[0].run_id` → `get-run-output`.
- Prevention: the probe skill and `databricks-free-edition` should say this. Not yet in a skill.
- Status: fixed in this story (learnings: `docs/knowledge/learnings/free-edition.md`)
- Seen: 1

## 2026-11-28 · US01 probe · ijson not on serverless
- Symptom: `import ijson` fails on serverless in the probe (P5); the independent count could not run.
- Cause: serverless has no `ijson` by default.
- Fix: the check job declares `ijson` as an environment dependency (`environments.spec.dependencies`). The dev check then ran and matched (217,517).
- Prevention: any job that needs a PyPI package must declare it in its environment spec. Not yet in a skill.
- Status: fixed in this story
- Seen: 1

## 2026-11-28 · US01 build · macOS java stub makes Spark tests error
- Symptom: `tests/test_us01_bronze.py` errored at setup with `JAVA_GATEWAY_EXITED` on the Mac.
- Cause: `/usr/bin/java` exists as a stub without a JDK, so `shutil.which("java")` finds it.
- Fix: the skip check runs `java -version` and needs return code 0.
- Prevention: check the JDK with `java -version`, not `which java`, in any Spark test skip.
- Status: fixed in this story
- Seen: 1

## 2026-11-28 · US01 build · PyPI unreachable from the Mac
- Symptom: `pip install ijson` returned HTTP 503 from PyPI; `uv` failed with a TLS error.
- Cause: the network from this Mac to PyPI (not a project problem). Not diagnosed further.
- Fix: the ijson test skips locally with a reason; it runs in dev through the job's environment.
- Prevention: when a local install fails, run the check in dev. Not yet in a skill.
- Status: open (local only)
- Seen: 1

## 2026-11-28 · US01 probe · url address returns 500 on a Range request
- Symptom: the `url` address of dataset resource returned HTTP 500 on one Range request and 206 on another (P1).
- Cause: not diagnosed; intermittent on the server side.
- Fix: the download uses `latest` (no Range needed; full GET works). `url` is kept only as a fallback field.
- Prevention: do not depend on Range requests for this source; the download checks the byte count instead.
- Status: open (upstream)
- Seen: 1

## 2026-11-28 · US01 build · process: spec appended with a bash heredoc
- Symptom: the decisions and results section was appended to `docs/specs/US01-contratos-bronze.md` with `cat >> ... <<'EOF'`.
- Cause: a shortcut; the file-change rule says new or changed files go through create and edit only.
- Fix: none yet; the content is correct. Future edits use edit/create only.
- Prevention: check the file-change rule before writing docs from bash.
- Status: open
- Seen: 1
