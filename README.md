# Databricks agent harness (template)

A starter kit for doing data engineering on Databricks with an AI agent in VS Code. It gives the agent instructions, skills, roles and reusable prompts, and it makes the agent log its errors and improve the harness over time.

Individual and hands-on: your VS Code, your Databricks Free Edition, your GitHub repository.

## Comece aqui

1. Faça o fork deste repositório, clone o seu fork e abra a pasta no VS Code.
2. No chat do seu agente, escreva:
   > Inicialize o projeto seguindo o INIT.md. Antes de mudar qualquer coisa, mostre o plano.

   (No Claude Code ou no Copilot, `/setup` faz o mesmo.)
3. O agente guia os logins e permissões (que são feitos por você), instala o que falta, cria as issues e o quadro e prepara o Databricks, com o seu "sim".
4. Siga os labs.

Todos os pedidos que pode fazer ao agente, antes e depois, estão no início do `INIT.md`.

### Conferir os logins

Para checar se os logins e o repositório padrão estão prontos, rode na raiz do projeto:

```
python3 scripts/check_github_login.py
```

Ele faz quatro checagens: login no GitHub CLI com a permissão `project` na conta ativa; login no Databricks (perfil `free`); repositório padrão do `gh` igual ao deste projeto; e nenhum token escrito nos arquivos do repositório. Ele é somente leitura e não mostra tokens nem dados de conta. Sai com código 0 se tudo passou e 1 se algo falhou.

## What is inside

- `AGENTS.md`: the rules every agent follows, including the improvement protocol.
- `skills/<tool>/`: procedures by tool (`core`, `databricks`, `github`).
- `agents/`: roles. `prompts/`: reusable commands (`/retro`, `/log-error`, `/new-skill`, `/memory-review`, `/start-story`, `/setup`, `/fix-bug`).
- `INIT.md`: project initialization, run by your agent.
- `BACKLOG.md`: all the project issues.
- `docs/knowledge/`: error log, decision log, learnings.
- `.claude/` and `.github/`: generated copies for each tool. Edit the sources, then run `python scripts/sync_agent_folders.py`.
- `docs/`: architecture, options without paid Claude, shared team memory.

## Which agent can I use?

Genie Code (in Databricks), GitHub Copilot in VS Code, or Claude Code. See `docs/no-paid-claude.md`.

## Status

Written to be tested. Anything marked `from-docs` or `unverified` has not been run on every setup. Your job in the labs is to verify it and update the files.

Based on the structure of the public DataEngAgents repository (Fabric and Azure DevOps).
