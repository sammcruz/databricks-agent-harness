---
name: handoff-prompt
description: Use when the user asks for a prompt, summary or instructions that another agent in another environment (another fork, machine or workspace) will follow, for example to repeat a story or a load.
---

# Handoff prompt for another environment

The reader is an agent in someone else's fork. It has the code, not this conversation. It should finish with few or no questions.

## Before writing

1. Check the current state, do not trust memory: `git log`, the pull request state, the issue, the board (`board.py status`). A prompt written while a story is in progress goes stale; rewrite it from the merged state.
2. Say what already exists in the repository (paths of code, notebooks, jobs, spec, learnings) and tell the reader to use it, not to rewrite it.
3. Check which results were `verified` (you ran it), `from-docs` or `unverified`.

## What to write

Write in the user's language, as numbered instructions, in this order:

1. Limits: where it runs (for example Free Edition only), what must not be done (no manual upload, no workaround of a block, no unrelated commits).
2. Where the code is and what it does, in a few lines.
3. Steps with the exact commands and what a pass looks like. Put a reference result with its date and say it can change (a live source updates).
4. A stop rule for the likely blocker: what to test first, how to tell a transient error from a real one, what to record, when to stop. State what was seen in another workspace as `unverified` for the reader's own.
5. What is known and not verified.
6. What to report at the end.

## Rules

- Never name the repository, the owner, the user, the machine, a workspace host, a job or run id, or an email. Each person runs it in their own fork. Say "use your own prefix" for schemas and volumes, and take defaults from the skill `databricks-free-edition`.
- Say `python3` only if the machine needs it; otherwise write the command that the repo documents.
- Do not paste secrets, tokens or row content from the data.
- Keep it short enough to read once. Link paths, do not copy files.

Typical errors: a prompt that describes a draft that is now merged; a prompt that makes the reader rebuild code that exists; a stop rule that does not say which host failed.
