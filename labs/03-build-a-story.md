# Lab 03: build one story end to end

Use your own data idea. If you have none, extend `src/clean_orders.py` with an aggregation (orders per day).

1. Ask the `requirements-analyst` agent for one small story. Approve its text, then create the issue.
2. `/start-story <issue number>`. The agent calls the right agent at each stage and moves the card. Read before you approve the story and the plan.
3. Test first, then the function in `src/`. Run `pytest`.
4. Optional, if your workspace allows: wire the function into a notebook and run it in dev. Use `skills/databricks/project-pipelines`.
5. Run `ruff check .`, commit, push the branch, open the pull request.
6. Ask the `reviewer` agent to review it. Fix what it finds.
7. Merge when CI is green, then delete the branch, local and remote. A story ends with its branch deleted.
8. Run `/retro`.

Done when: the issue is closed by a merged pull request.
