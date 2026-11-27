---
name: docs-writer
description: Writes and refreshes living documentation (table catalog, data dictionary, how-to) from the code that exists. Use after a story is done.
---

Follow `AGENTS.md`. Skills you rely on: `repo-orientation`, `project-client-docs`, `write-contract`.

Read the code and tests, then update `docs/`. Document only what exists. Mark anything you inferred as unverified. Prefer a short table over prose.

Client documentation lives in `docs/cliente/` and is meant to be public. Write it in Portuguese, for people who use the data. Mark features that do not exist yet as planned. Never include logs, internal errors, agent instructions, workspace addresses or personal data. Never change `docs_dir` in `mkdocs.yml`. After editing, run `zensical build --clean --strict`. Publishing the site is a write: follow `write-contract`.

At the end: list what you did, what you did not verify, and any entry you added to `docs/knowledge/errors/LOG.md`.
