# REPO_MAP

Start here. Everything an agent can use is listed below. Keep this file in sync with `python scripts/check_repo_map.py`.

## Instruction files

- `INIT.md`: project initialization steps for the agent (tools, requirements, GitHub, backlog, Databricks).
- `BACKLOG.md`: all project stories, published as issues during initialization.
- `AGENTS.md`: rules for every agent (single source).
- `CLAUDE.md`: imports `AGENTS.md`, adds Claude Code notes.
- `.github/copilot-instructions.md`: points Copilot to `AGENTS.md`.

## Agents (`agents/`)

| Agent | Use it for |
|---|---|
| `requirements-analyst` | Turn an idea into user stories and acceptance criteria as GitHub issues |
| `pipeline-engineer` | Build and test Lakeflow / Spark Declarative Pipelines and transformation code |
| `notebook-engineer` | Develop notebooks and Python modules locally, keep them testable |
| `docs-writer` | Write and refresh living documentation from the code |
| `app-engineer` | Build the Databricks App for data consumers |
| `dashboard-engineer` | Build the operational dashboard: quality, volume, run time, DBUs |
| `data-analyst` | Query data and metadata with read-only SQL |
| `reviewer` | Review a branch or pull request against the rules and tests |
| `harness-improver` | Read the error log, find repeated problems, propose edits to instructions, skills and agents |

## Skills (`skills/<group>/<name>/SKILL.md`)

Grouped by tool. Delete the groups you do not use.

| Group | Skill | What it covers |
|---|---|---|
| core | `environment-setup` | Check and install the tools, logins, fork settings |
| core | `self-improvement` | The error log, learnings and the improvement loop |
| core | `repo-orientation` | How to find your way around this repository |
| core | `write-contract` | Dry-run-first rule for anything that writes |
| databricks | `databricks-cli-auth` | Install the CLI, OAuth login, profiles |
| databricks | `databricks-free-edition` | What works and what does not on Free Edition |
| databricks | `databricks-sql-query` | Read-only SQL on the warehouse, system tables |
| databricks | `project-app` | Project rules for the consumer app |
| databricks | `project-dashboard` | Project rules for the operational dashboard |
| databricks | `project-client-docs` | Project rules for the public documentation site |
| databricks | `databricks-official-skills` | Safe install of official skills and MCP; which rules win |
| databricks | `project-pipelines` | Declarative pipelines and medallion layers |
| databricks | `databricks-bundles-dev` | Asset Bundles with a dev target only |
| github | `github-issues-flow` | Issues as stories, labels, branches |
| github | `github-board-flow` | Agile columns, who moves each card, approval gates |
| github | `github-pr-flow` | Branch, commit, pull request, CI |

## Prompts (`prompts/`)

| Prompt | Use it for |
|---|---|
| `setup` | Initialize the project, following INIT.md |
| `fix-bug` | Fix a bug issue, starting from a failing test |
| `doctor` | Read-only health check of tools and logins |
| `check-harness` | Check that instructions are still true and consistent |
| `retro` | End-of-task review: log errors, update skills |
| `log-error` | Record one error in the log right now |
| `new-skill` | Create a new skill from a repeated task |
| `memory-review` | Clean the knowledge files, mark stale entries |
| `start-story` | Run an issue through the board, calling the agents and moving the card |

## Knowledge (`docs/knowledge/`)

- `docs/knowledge/errors/LOG.md`, `docs/knowledge/decisions/LOG.md`, `docs/knowledge/learnings/`.

## Docs and labs

- `docs/architecture.md`, `docs/no-paid-claude.md`, `docs/shared-memory.md`, `docs/gotchas/databricks.md`.
- `labs/README.md` lists labs 00 to 06.

## Scripts

- `scripts/check_environment.py` (read-only tool check), `scripts/check_github_login.py` (read-only GitHub and Databricks login check), `scripts/dbquery.py` (read-only SQL), `scripts/system_tables_readable.py` (lists the `system` tables that `COUNT(*)` can read, read-only), `scripts/publish_backlog.py` (backlog to issues), `scripts/board.py` (agile board), `scripts/sync_agent_folders.py`, `scripts/check_repo_map.py`, `scripts/quick_validate.py`.
