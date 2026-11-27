---
name: github-pr-flow
description: Use when committing, pushing, opening or updating a pull request, or when CI fails on a pull request.
---

# Branch, commit, pull request

1. Never commit to `main`. Work on a branch.
2. Before committing run the same checks as CI (`.github/workflows/ci.yml`), with the same commands:
   - `ruff check .`
   - `pytest` (not `python -m pytest`: it can hide import errors)
   - `python scripts/sync_agent_folders.py --check`
   - `python scripts/check_repo_map.py`
   - `python scripts/quick_validate.py skills/<group>/<name>` for each changed skill
3. Read `git diff` and `git status` before committing: no debug output, unrelated files, secrets or personal data.
4. Commit small and often. Message: imperative sentence saying what and why.
5. Push the branch and open a pull request in the user's fork (`--repo`). Fill every section of `.github/pull_request_template.md`, briefly. State honestly how AI was used.
6. Wait for CI. If CI fails, read the log, fix the cause, push again. Do not disable a check to get green.
7. A human reviews and merges. You do not merge your own pull request.
8. When the story ends (merged), delete its branch, local and remote (`git push origin --delete <branch>`, `git branch -d <branch>`). Only after the merge is confirmed.

Typical lint failures: unused import, unsorted imports, missing newline at end of file, line too long. `ruff check --fix` solves most of them; review the diff afterwards.

Pushing and opening a pull request are writes: follow `write-contract`.
