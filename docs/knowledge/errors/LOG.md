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
