---
name: write-contract
description: Use before any action that creates, changes or deletes something outside the local working tree, such as a Databricks object, a bundle deployment, a GitHub issue, a branch push or a pull request.
---

# Write contract

Anything that writes outside the local checkout follows four steps.

1. Permission: say what you are about to do and wait for a yes. A yes covers only what you described.
2. Dry run: show the plan first. Examples: `databricks bundle validate`, `databricks bundle deploy --dry-run` if available (check `--help`), the SQL you will run, the issue text you will post. For a long text (issue or pull request body), write it to a file and pass `--body-file`.
3. Safety pattern: dev target only; create new objects rather than overwrite; never delete without naming each object; never touch objects you did not create in this session.
4. Rerun safety: the action must be safe to run twice. If it is not, say so and ask.

After the action, report what changed and how to undo it. If something went wrong, log it (skill `self-improvement`).
