---
name: github-issues-flow
description: Use when turning an idea into GitHub issues, picking up an issue, or naming a branch for it. Issues are the unit of work.
---

# Issues as stories

The ready project stories are in `BACKLOG.md`. A fork does not copy issues: publish them as described in `INIT.md`, step 5 (dry run first, then `--apply` after a yes). In a fork, pass `--repo` to `gh` so nothing goes to the original repository. To fix a bug issue, use the `fix-bug` prompt.

## Writing a story

Title: `As a <who>, I want <what>, so that <why>`.
Body: context, acceptance criteria (a checklist that can be tested), out of scope, definition of done (tests pass, docs updated, pull request merged).

Keep stories small: one table, one function or one dashboard per issue.

## Working an issue

1. Read the issue and the open entries in `docs/knowledge/errors/LOG.md` that touch the same area.
2. Branch: `feat/<issue-number>-<short-name>` or `fix/<issue-number>-<short-name>`.
3. Post a short plan as a comment before coding, if the user agrees.
4. Link the pull request with `Closes #<number>`.

Creating or editing issues is a write: follow `write-contract` and show the text first. Write the body to a file with the create tool and pass it with `--body-file`; an inline `--body "$(cat <<'EOF' ...)"` breaks on parentheses.
