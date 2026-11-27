---
date: 2026-11-27 12:03
area: environment-setup
status: open
seen: 1
---

# PowerShell quoting broke an exploratory GitHub status check

- Symptom: The notebook engineer reported a PowerShell quoting error in the first GitHub status check.
- Cause: unknown; exact shell error was not included in the report.
- Fix: A later filtered `gh auth status` and fork-settings check passed.
- Prevention: Update `agents/notebook-engineer.md` to prefer simple PowerShell commands and verify quoting before running composed status checks.
