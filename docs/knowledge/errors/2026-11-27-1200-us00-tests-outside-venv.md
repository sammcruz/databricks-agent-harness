---
date: 2026-11-27 12:00
area: environment-setup
status: open
seen: 1
---

# US00 checks ran outside the project virtual environment

- Symptom: The notebook engineer reported `pytest` and `ruff` were not recognized when run directly, despite the project `.venv` containing both tools.
- Cause: The commands were run without activating `.venv` or using its `Scripts` executables.
- Fix: Re-run through `.venv\Scripts\pytest.exe` and `.venv\Scripts\ruff.exe`.
- Prevention: Update `agents/notebook-engineer.md` to activate or explicitly use the project virtual environment before running checks.
