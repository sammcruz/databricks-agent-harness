---
date: 2026-11-27 12:03
area: environment-setup
status: open
seen: 1
---

# Optional pip check was unavailable in the uv virtual environment

- Symptom: `.venv\Scripts\python.exe -m pip check` failed because `pip` is not installed in the environment.
- Cause: The project virtual environment is managed with uv and does not include the `pip` module.
- Fix: The declared dev/docs packages were validated by import checks; project tests and Ruff passed.
- Prevention: Update `agents/notebook-engineer.md` to use the project's uv and test commands instead of assuming `python -m pip` exists.
