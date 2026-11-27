---
description: Fix a bug issue, starting from a failing test.
---

Fix the bug in issue $ARGUMENTS. Keep its card up to date (skill `github-board-flow`, bug path).

1. Read the issue (use `gh issue view` with `--repo` set to my fork) and the related entries in `docs/knowledge/errors/LOG.md`.
2. Find the code and reproduce the problem. If you cannot, say so and ask; do not guess a fix.
3. Show the cause and a short plan. Wait for my yes.
4. Create a branch `fix/<issue-number>-<short-name>`. Write a test that fails for the reported reason and show it failing.
5. Make the smallest fix. Run all tests and lint. Do not change or delete existing tests to make them pass.
6. Ask before pushing. Open a pull request in my fork with `Closes #<number>`, explaining cause, fix and what you did not verify.
