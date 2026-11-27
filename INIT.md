# Inicialização do projeto

Este documento é para o **agente** executar, com você a aprovar. Depois do fork e do clone, abra a pasta no VS Code e peça:

> Inicialize o projeto seguindo o INIT.md

(No Claude Code ou no Copilot também há o comando `/setup`.)

## Como começar (para você)

Escreva no chat do agente, com a pasta do seu fork aberta:

| Quando | O que pedir |
|---|---|
| Primeira vez | `Inicialize o projeto seguindo o INIT.md. Antes de mudar qualquer coisa, mostre o plano.` |
| Só ver o que falta | `Verifique o INIT.md sem alterar nada e diga o que está pendente.` |
| Parou a meio ou fez um login | `Continue a inicialização do INIT.md a partir do que falta.` |
| Algo falhou | `Este passo falhou. Explique a causa, registe o erro e não contorne bloqueios.` |

No Claude Code e no Copilot, `/setup` equivale ao primeiro pedido. O agente pede o seu "sim" antes de criar ou instalar, e diz quando é a sua vez de fazer um login.

Depois de inicializar:

| O que quer fazer | O que pedir |
|---|---|
| Ver o quadro | `Mostre o estado do quadro.` |
| Refinar uma história | `Use o requirements-analyst para refinar a issue #N.` |
| Implementar uma história (o agente coordena os agentes e move o cartão) | `/start-story N` ou `Siga o prompt start-story para a issue #N.` |
| Corrigir um bug | `/fix-bug N` |
| Ver se está tudo a funcionar | `/doctor` |
| Rever as instruções do harness | `/check-harness` |

## Antes de pedir (feito por você)

- Conta no GitHub e no Databricks Free Edition.
- Git, VS Code e um agente (ver `docs/no-paid-claude.md`).
- Fork deste repositório na sua conta, clonado no computador.

O fork de um repositório público também é público. Nunca grave credenciais, endereços do seu workspace ou notas privadas.

## Regras para o agente

1. Execute os passos por ordem. Cada um tem uma **verificação**; se ela já passar, não repita o passo.
2. Antes de começar, verifique tudo sem alterar nada e mostre um plano único: o que já está feito, o que vai instalar ou criar e onde. Espere um "sim". Peça novo "sim" se o plano mudar.
3. Os logins e autorizações no navegador são do aluno. Nunca peça, mostre ou grave tokens.
4. Se algo estiver bloqueado, pare e explique. Não contorne bloqueios (skill `environment-setup`).
5. Registe cada falha em `docs/knowledge/errors/LOG.md`.
6. Não faça commit nem push durante a inicialização.

## Passo 1: ferramentas

Siga a skill `environment-setup`, secções 1 e 2.

**Verificação:** `python3 scripts/check_environment.py` (Windows: `py scripts/check_environment.py`) mostra tudo `ok`. O verificador também encontra o Spec Kit em `~/.local/bin` (instalação com `uv tool install`), mesmo que essa pasta não esteja no PATH.

**No Windows:** um terminal que já estava aberto não vê as ferramentas acabadas de instalar, e atualizar o PATH no terminal do agente **não muda o do aluno**. Depois de as instalações terminarem e **antes de qualquer login**:

1. O aluno corre no seu terminal PowerShell:
   ```
   $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User")
   gh --version
   ```
2. Se `gh` continuar sem ser reconhecido, fechar **todas** as janelas do VS Code, voltar a abrir e testar num terminal novo. Se não resolver, reiniciar o computador.
3. Se ainda falhar, siga a secção "Windows: refresh PATH" da skill `environment-setup`.

Só avance para os logins quando os comandos funcionarem no terminal do aluno.

## Passo 2: ambiente Python e dependências

```
uv venv --python 3.12
uv pip install -r requirements-dev.txt -r requirements-docs.txt
```

Ative com `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`). Não recrie um `.venv` que já funciona.

**Verificação:** `pytest` e `ruff check .` passam.

## Passo 3: logins (o aluno executa)

```
gh auth login
gh auth refresh -s project
databricks auth login --host https://<seu-workspace> --profile free
```

**Para o agente:** verifique primeiro o que já está feito. Peça um comando de cada vez, num terminal do VS Code (menu Terminal, New Terminal), explique o que vai aparecer e espere o aluno dizer que terminou.

- `gh auth login`: escolher GitHub.com, HTTPS e login pelo navegador.
- `gh auth refresh -s project`: dá ao `gh` a permissão de **ler e alterar os seus projetos do GitHub**, necessária para criar o quadro e mover cartões. Explique isto antes de pedir. Para retirar depois: `gh auth refresh -h github.com --remove-scopes project`.
- Em ambos: o terminal mostra um código de uso único; cole-o **apenas na página do GitHub**, nunca no chat, confirme a conta e autorize.
- Databricks: abre o navegador. Como descobrir o host: skill `databricks-cli-auth`.

**Verificação:** `gh auth status` mostra a sua conta com o escopo `project`; `databricks current-user me --profile free` funciona. Não copie a saída para ficheiros.

## Passo 4: apontar o GitHub para o seu fork

Descubra o nome com `git remote get-url origin`. Confirme que o dono é a conta do aluno. Se for outra, pare.

```
gh repo set-default <aluno>/<fork>
gh repo edit <aluno>/<fork> --enable-issues --enable-projects
```

Peça ao aluno para abrir o separador **Actions** do fork e ativar os workflows, se o GitHub pedir. Num fork podem estar desligados.

**Verificação:** `gh repo set-default --view` mostra o fork; `gh repo view <aluno>/<fork> --json hasIssuesEnabled,hasProjectsEnabled,isFork,visibility`.

## Passo 5: issues, quadro e colunas

Todas as issues estão em `BACKLOG.md`. Mostre primeiro o plano:

```
python scripts/publish_backlog.py --repo <aluno>/<fork> --project "Contratos PT"
```

Depois do "sim", o mesmo comando com `--apply`. O script cria etiquetas, issues e o quadro, e não duplica o que já existe. Não altera issues existentes.

Depois configure as colunas e a vista do quadro (skill `github-board-flow`). Mostre o plano e, após o "sim", aplique:

```
python scripts/board.py setup --repo <aluno>/<fork>
python scripts/board.py setup --repo <aluno>/<fork> --apply
```

Peça ao aluno para abrir o quadro, em `...`, **Workflows**, e confirmar no navegador: "Item added to project" define **Backlog**; "Item closed" e "Pull request merged" definem **Done**; "Pull request linked to issue" deve estar desligado ou definir **In Review**.

**Verificação:** `gh issue list --repo <aluno>/<fork> --state all --limit 100` mostra as histórias de `US00` a `US17`, uma vez cada, e `python scripts/board.py status --repo <aluno>/<fork>` mostra as oito colunas.

## Passo 6: Databricks

1. Confirme o catálogo com `python scripts/dbquery.py "SHOW CATALOGS"`. No Free Edition usamos `workspace`, se existir; se não, pergunte.
2. Verifique o que existe: `python scripts/dbquery.py "SHOW SCHEMAS IN workspace"`.
3. Se faltar, mostre estes comandos e espere o "sim" (skill `write-contract`):
   ```
   databricks schemas create contratos_pt workspace --profile free
   databricks volumes create workspace contratos_pt landing MANAGED --profile free
   ```
   Se o schema já existir e não tiver sido criado para este projeto, não o reutilize sem perguntar.
4. Valide o bundle: `databricks bundle validate -t dev --profile free`. **Não faça deploy** na inicialização. O host vem do perfil: não o escreva no `databricks.yml`.

**Verificação:** `python scripts/dbquery.py "SHOW VOLUMES IN workspace.contratos_pt"` mostra `landing`, e o bundle valida.

## Passo 7: skills oficiais do Databricks

Siga a skill `databricks-official-skills`: sempre com escopo do projeto e agente indicado. Mostre o comando e espere o "sim". Para Claude Code:

```
databricks aitools install --scope project --agents claude-code --skills-only --skills databricks-core,databricks-pipelines,databricks-dabs
```

Para outro agente, confirme o nome em `databricks aitools install --help`; ainda não foi testado. As regras do projeto prevalecem sobre estas skills. Não faça commit dos ficheiros. No fim, peça ao aluno para abrir uma sessão nova do agente.

**Verificação:** `databricks aitools list --scope project` mostra as três instaladas e `git status` não mostra os ficheiros delas.

## Passo 8: relatório

Mostre uma tabela com cada passo (`feito`, `já existia`, `bloqueado`, `pendente`), os endereços das issues e do quadro, e o que não foi verificado. Indique a primeira história: `US00`.

## Fora da inicialização

- **Spec Kit:** a ferramenta é instalada, mas **não execute `specify init`**. Ele escreve nas pastas dos agentes e pode substituir ficheiros; isso tem de ser tratado numa alteração revista.
- GitHub Pages (história `US15`), pipelines, job, dashboard, app e deploy: são histórias do backlog.
