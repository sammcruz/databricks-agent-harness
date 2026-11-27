---
date: 2026-11-27 12:03
area: databricks-cli-auth
status: open
seen: 1
---

# Guessed Databricks volume command was unavailable

- Symptom: The notebook engineer reported that `databricks volumes get` failed; the corrected `databricks volumes read` check passed.
- Cause: The CLI command name was guessed instead of checked against its help.
- Fix: Use the supported `databricks volumes read` command, or the project's read-only SQL wrapper for existence checks.
- Prevention: Update `agents/notebook-engineer.md` to inspect `databricks volumes --help` before invoking unfamiliar CLI subcommands.
