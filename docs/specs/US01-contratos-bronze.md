# Spec and plan: US01, contracts of one year in bronze (issue #2)

Status: **Built in dev (In Progress). Probes C1–C8 done, load and second run done in dev; Spark/Delta tests and the local ijson count still to run on dev.** Decisions taken are in section 8. Stage: In Progress (branch `feat/2-contratos-bronze`, local commit only).
Date: 2026-11-27. Tags: `verified` (I ran it in this pass), `from-docs` (read in the catalog or the story, not re-run here), `unverified` (must be checked).

Decided by the human (not reopened here): record = one contract; source = dataset "Contratos Públicos - Portal Base - IMPIC - Contratos de 2012 a 2026"; probe notebook approved (run only after plan approval); if compute cannot reach the host, the story stops (no manual upload); dev default year = latest year in the catalog.

## 1. Source facts

| Fact | Status | Evidence |
|---|---|---|
| Dataset id `66d72d488ca4b7cb2de28712`, slug `contratos-publicos-portal-base-impic-contratos-de-2012-a-2026`, licence `other-pd`, frequency weekly, last modified 2026-11-22 | verified | `GET https://dados.gov.pt/api/1/datasets/66d72d488ca4b7cb2de28712/` (read-only) |
| 15 zip resources titled `contratos2012.zip` to `contratos2026.zip`; catalog size for 2026 is 71,136,042 bytes, for 2025 77,647,340 bytes (largest) | verified | same API, parsed |
| Each zip has two addresses: `latest` = `https://dados.gov.pt/api/1/datasets/r/<resource id>` and `url` = `https://dados.gov.pt/s/resources/<dataset slug>/<stamp>/<file>.zip` | verified (structure) | same API |
| HEAD on the `url` form from this Mac: 200, `Content-Length` 71136042; the response carries `x-middleware-rewrite: http://host.docker.internal:7000/...` (an internal host). HEAD on the `latest` form: 200 with `application/zip` (no redirect seen) | verified from this Mac only | `curl -sI` |
| The catalog's own link checker recorded HTTP 429 "TOO MANY REQUESTS" and "File too large to download" for the zip and xlsx resources | verified (catalog metadata) | `resources[].extras` |
| `Contratos2026.json` inside the 2026 zip: about 641 MB, one line, a top-level array of flat contract objects, not OCDS | from-docs (story; draft v1 check, not re-run) | story |
| About 217,500 contracts | unverified (draft v1 grep of `"idcontrato"`, approximate) | draft v1 |

Consequence: one record = one contract (`idcontrato` per object). The old OCDS dataset is out of scope: it has no files.

## 2. Open technical checks (answered by the probe, section 6)

| # | Check | Status | Blocks |
|---|---|---|---|
| C1 | Which address works from **serverless compute**: `latest` or the `url` field. Final host after redirect | verified: `latest` HEAD 200, no Content-Length, GET gave all 71,136,042 bytes; `url` HEAD 200 with Content-Length 71136042, but a Range request gave 500 once and 206 once; final host dados.gov.pt | O1 |
| C2 | Behaviour under HTTP 429 from compute | partly verified: 10 catalogue/zip calls from compute, all 200, no 429 seen. The retry path is tested with a local fake server only (not against a real 429) | O9 |
| C3 | Serverless can write the 71 MB zip to a Volume, read it back, and match SHA-256 | verified: 1 MB write/read OK; 71,136,042 bytes stored; SHA-256 re-read equal | storage step |
| C4 | Plain Python can stream-parse the single-line 641 MB JSON within compute limits | verified: 217,517 contracts in 63.6 s, peak RSS about 2,450 MB; the serverless memory limit is not exposed, so the margin is unknown | O6 |
| C5 | Is `idcontrato` unique in the file? | verified for 2026: 217,517 contracts, 217,517 distinct ids, 0 repeats | O12 |
| C6 | Spark's JSON reader cannot split a single 641 MB line | from-docs, reasoned; not re-tested | section 3, step 4 |
| C7 | Volume and schema in dev | verified: created in dev (`workspace.samantha_contratos_pt`, volume `contratos_raw`) by the probe, then `CREATE ... IF NOT EXISTS` in the job | O4 |
| C8 | Free Edition limits: one pipeline slot, one warehouse, storage quota | one pipeline slot not used (job). Storage quota not exposed (P6); the Volume holds the zip plus staging, and staging is cleaned up | O3, O10 |

## 3. Architecture

Each step is one function under `src/` (pure where possible). The job notebook only wires them. Numbers in brackets are the story's criteria, by topic (draft v1 numbering; re-map to the issue's list when the plan is written).

1. **Resolve the file (catalog API, at load time).** `resolve_recurso(ano)` reads the dataset from the catalog and finds the resource whose title is `contratos<ANO>.zip`. It returns the address (O1), title, `last_modified` and `filesize`. The year is a required parameter; in dev it defaults to the largest year in the titles. Missing year: `E_ANO_AUSENTE`. No match: `E_SEM_ARQUIVO`. Only the dataset id is configured (bundle variable). [source, year]
2. **Download to local disk (not the Volume).** Streamed in 8 MB chunks; connect and read timeout 60 s; SHA-256 computed while writing. HTTP 429 or 5xx: retry with exponential backoff, capped attempts (O9). Checks: HTTP 200; bytes = `Content-Length` when sent; `zipfile` opens it and `testzip()` passes. Errors: `E_HTTP`, `E_TIMEOUT`, `E_ZIP_TRUNCADO`, `E_ZIP_INVALIDO`. Temp file deleted on any error. [download failures]
3. **Store in the Volume unchanged.** Copy the validated file to `/Volumes/<catalogo>/<schema>/<volume>/contratos/<ANO>/<AAAA-MM-DD>_contratos<ANO>.zip` (date = catalog `last_modified`). Re-read the copy; its SHA-256 must equal the download's, else `E_HASH_DIVERGE`. A new publication adds a new dated file; the previous file for the year stays in the Volume. Zero-byte file: `E_ARQUIVO_VAZIO`. [stored file, keep previous]
4. **Stream the JSON; never load it whole.** `zipfile.open()` gives a binary stream of the one JSON line. A splitter reads the top-level array and yields one contract object at a time, using bounded buffers. Each object is parsed with `json.loads(parse_float=str, parse_int=str)`, so numbers keep their literal text (`9000.00` stays `9000.00`). Rules: strings as they are; `null` stays null; booleans become `"true"`/`"false"`; nested objects and arrays are stored as JSON text (O5). Rows are written as NDJSON to `staging/<ANO>/` in the Volume, in batches (for example 10,000 contracts). Zero contracts: `E_ARQUIVO_VAZIO` (O8). Choice of splitter vs `ijson`: O6, decided by probe C4. [fields as text, big file]
5. **Bronze load.** Spark reads the staging NDJSON with an explicit all-`StringType` schema (no inference). Metadata columns added: `_source_url` (the address used), `_source_modified` (catalog `last_modified`), `_ingested_at` (run start, UTC), `_file_sha256` (of the stored zip), and `_source_year` (O2). All are required and non-null. Write: Delta `replaceWhere _source_year = <ANO>` into `bronze_contratos` (created if absent). [metadata, count]
6. **Idempotency.** The same file gives the same SHA-256. Each run replaces the whole year in one Delta write, so the count and the keys stay the same (O12 defines the key rule). Multiple years and reloads are US03. [idempotent]
7. **Errors.** One error type with fields `passo` and `causa`. The message is Portuguese and names the step and the cause, for example: `Falha no download de contratos2026.zip (passo: download). Causa: tempo esgotado após 60 s. Nenhum arquivo foi salvo e a bronze não mudou.` On any error, partial files are removed and nothing is written to bronze. [errors]
8. **Logs.** Only step names, year, byte counts, hashes, counts and durations. Never row values, never record text. [logs]
9. **Independent count.** A reader that is not the loader (for example a separate `ijson` count script; not the loader's splitter) counts the contracts in the stored zip. It must equal `count(*)` of the bronze year. [count]

Layout: `contratos/<ANO>/<date>_contratos<ANO>.zip` in the Volume; staging NDJSON under `staging/<ANO>/`, deleted after a successful write.

## 4. Tests first, one per criterion

Write each test before its function (project-pipelines). Tests live in `tests/`, need no network (a local HTTP server serves generated zips), and call only functions in `src/`. Spark tests use a local session and Delta (O7).

| Topic | Test (name) | Where it runs | What it asserts |
|---|---|---|---|
| Source address | `test_endereco_vem_da_api_do_catalogo` and `test_nenhum_endereco_fixo_no_codigo` | local, mocked catalog JSON; grep of `src/` | address comes from the payload; no literal host or path in `src/` |
| Stored file | `test_arquivo_guardado_igual_ao_baixado` | local, temp Volume folder | stored bytes = served bytes; SHA-256 equal; name has the date |
| Text fields | `test_campos_da_fonte_ficam_como_texto` | local Spark | all source columns are string; `9000.00` kept; `1e5` kept; `null` stays null; `""` stays `""` |
| Metadata | `test_metadados_presentes_e_nao_nulos` | local Spark | `_source_url`, `_source_modified`, `_ingested_at`, `_file_sha256`, `_source_year` exist and are never null |
| Count | `test_contagem_igual_ao_leitor_independente` | local Spark + independent reader | bronze count = contracts counted by the other reader, on a generated zip with known count |
| Idempotency | `test_duas_cargas_mesmo_arquivo_nao_duplicam` | local Spark, Delta | after two runs: same count; keys as O12 defines |
| Download failures | `test_falha_de_download_mensagem_e_sem_arquivo_parcial` (parametrized: HTTP 500, HTTP 429 after retries, timeout, truncated zip, invalid zip) | local HTTP server | Portuguese message with step and cause; no file in Volume folder; bronze unchanged |
| Year and empty file | `test_ano_ausente_e_arquivo_vazio_falham_com_mensagem` | local | clear error for a missing year, a zero-byte file, and a zero-contract file |
| Streaming | `test_leitura_em_streaming_com_memoria_limitada` | local, `tracemalloc` on a generated ~50 MB single-line JSON | peak memory far below file size (threshold in the test, for example 20 MB) |
| Logs | `test_logs_sem_conteudo_de_linha` | local, `caplog` | a sentinel value from the data never appears in any log line |

Dev acceptance (after deploy, after a yes): the real 2026 file. Compare the independent count with the bronze count, run twice, check nulls in the metadata columns, and watch peak memory on serverless. Use skill `databricks-sql-query` (read-only) or `data-analyst`.

Gates: `python -m pytest` and `ruff check` locally (AGENTS.md). `databricks bundle validate --strict -t dev` and `bundle plan -t dev` before any deploy.

## 5. Files that would change (In Progress stage, not now)

- New `src/us01/` package: `catalogo.py` (resolve), `download.py` (download, retry, hash, zip checks), `volume.py` (store, re-hash), `stream.py` (splitter to text rows), `bronze.py` (metadata, replaceWhere), `erros.py` (Portuguese messages). Independent counter as a separate module or script.
- New `tests/test_us01_*.py` and a generator for small test zips.
- `databricks.yml`: variables for catalog, schema, Volume and dataset id. A `resources/` job for US01, dev target only.
- Thin job notebook `notebooks/us01_bronze_contratos.py` (widget: year, default = latest in catalog in dev).
- `requirements-dev.txt`: `delta-spark` (if O7 = yes); `ijson` only if O6 chooses it.
- Not changed: `prod`, any pipeline, silver, gold.

## 6. Probe plan (dev only; runs after plan approval and a yes; write-contract applies)

The probe is a one-off notebook on serverless compute, uploaded to dev and deleted at the end. Each step records status, timing and error text, and prints no row content.

| Step | What it does | Pass when | Answers |
|---|---|---|---|
| P1 Reachability | HEAD, then `Range: bytes=0-99`, on the `latest` address and on the `url` address of `contratos2026.zip`. Print the final host after redirects | 200 or 206 on at least one address; `Content-Length` 71136042 | C1, O1 |
| P2 Rate limit | Call the catalog API and the zip address about 10 times, spaced; log statuses. Then run the retry code path (backoff) | any 429 is retried and ends in 200 within the cap; no tight loop | C2, O9 |
| P3 Volume write | Create a 1 MB test file and then the 71 MB zip in a test folder of the dev Volume; read back; compare SHA-256; delete both | hashes equal; files removed | C3 |
| P4 Streaming parse | On the 2026 zip from P3: stream the single JSON line with the candidate splitter; count contracts; record peak memory (`resource`/`tracemalloc`) and time. Count again with an independent reader (`ijson` if available) | counts equal; peak memory under the serverless limit (limit to be read from the workspace or docs); time acceptable for a weekly run | C4, C5, O6 |
| P5 Packages | Import `ijson` and `delta` on serverless | import works, or O6 = splitter | O6, O7 |
| P6 Storage | Read the Volume quota (read-only) | quota known; room for 15 zips (about 641 MB total) or a decision on O10 | C8, O10 |
| P7 Cleanup | Delete test files and the probe notebook; record the result in `docs/knowledge/learnings/free-edition.md` | nothing left in dev | — |

If P1 fails from compute: stop the story (decided). Log the error in `docs/knowledge/errors/LOG.md` and the limit in the learnings file. No manual upload.

## 7. Docs to update (at the end of In Progress)

- `docs/specs/US01-contratos-bronze.md`: status and the results of C1 to C8.
- `docs/architecture.md`: the bronze flow and the Volume layout.
- `docs/knowledge/learnings/free-edition.md`: probe results, each marked `verified` or `unverified`.
- `docs/gotchas/databricks.md`: a single-line 641 MB JSON cannot be read by one Spark JSON read; the workaround. Only after P4 is verified.
- `docs/knowledge/decisions/LOG.md`: one entry per decided open item (append only).
- `docs/knowledge/errors/LOG.md`: entries for every failure met in implementation.
- Attribution: source IMPIC, Portal BASE; licence `other-pd` as published (O11).
- `REPO_MAP.md` when new folders appear (`python scripts/check_repo_map.py`).

## 7. Decisions still needed from the human

Removed from v1: the OCDS source question and the "one record = one OCDS release" rule (replaced by one record = one contract, decided). Also decided and no longer open: the probe approval (run after plan approval), the stop-on-block fallback, the default dev year, and keeping every publication in the Volume.

| # | Open decision | My recommendation | Why it matters |
|---|---|---|---|
| O1 | Which address to use: `latest` (catalog resource API) or the `url` field | the one that P1 shows works from compute; prefer `latest` if both work (stable id; the `url` form returns an internal rewrite header) | address rule in step 1 |
| O2 | Add a fifth metadata column `_source_year` (needed by `replaceWhere`; the story lists four) | yes | schema beyond the four in the story |
| O3 | Job notebook (recommended) or Lakeflow pipeline | job: keeps the one pipeline slot free; download is not a declarative step | Free Edition: one active pipeline per type |
| O4 | Dev names: schema (for example `samantha_agents`, catalog `workspace`) and Volume (for example `contratos_raw`) | yes | created by the bundle in dev after a yes |
| O5 | Nested fields (`adjudicante`, `CPV`, ...) stored as JSON text, with numbers inside them kept as text | yes; flattening would be a conversion (US04) | affects every later story |
| O6 | Splitter (hand-written, no new dependency) or `ijson` (needs a serverless dependency) | splitter if P4 is fast and within memory; `ijson` only if the splitter fails P4 | streaming design |
| O7 | Local tests with Delta (`delta-spark`) or a test double for the write | `delta-spark`: it tests the real `replaceWhere` | idempotency test is not honest without it |
| O8 | A file with zero contracts: error (`E_ARQUIVO_VAZIO`, bronze unchanged) | yes | the story asks for a clear error on an empty file |
| O9 | Retry policy for HTTP 429: attempts and backoff (proposal: 5 attempts, starting at 10 s, doubling) | confirm after P2 | download step; the catalog reported 429 |
| O10 | Storage: keep every publication. Free Edition quota unknown; all 15 zips are about 0.9 GB together | keep all; check quota (P6); if blocked, ask again | may block the next year |
| O11 | Attribution text for the docs (IMPIC, Portal BASE, licence `other-pd`) | show source and licence as published | legal and client docs |
| O12 | Key rule: is `idcontrato` the key, and what if it repeats in the file (C5)? | keep every contract row so the count equals the JSON count; report repeated keys in the log and in the acceptance check; no silent deletion | idempotency criterion ("keeps count and keys") |

## 8. Decisions taken and results (In Progress)

Decisions taken with the spec's recommendation unless noted:

| # | Decision taken |
|---|---|
| O1 | `latest` address (C1). `url` kept only as a fallback field in the code |
| O2 | Yes: `_source_year` is the fifth metadata column |
| O3 | Job with a notebook (`resources/us01_bronze.yml`), not a Lakeflow pipeline |
| O4 | Dev names: catalog `workspace`, schema `samantha_contratos_pt`, Volume `contratos_raw`, table `bronze_contratos`. Deviation: the schema and Volume are created by the job notebook with `CREATE ... IF NOT EXISTS`, not as bundle resources (they already existed from the probe, and a bind would add a manual step) |
| O5 | Nested fields stored as JSON text, numbers inside kept as text |
| O6 | Hand-written splitter for the load (C4 passed). `ijson` only in the check job's environment, for the independent count |
| O7 | `delta-spark` for the Spark tests. Those tests need a JDK: they skip locally and must run on dev |
| O8 | Zero contracts: `E_ARQUIVO_VAZIO`, bronze unchanged |
| O9 | 5 attempts, 10 s starting delay doubling, 60 s timeout, no retry on timeout |
| O10 | Keep every publication in the Volume (the previous zip stays with its date) |
| O11 | Attribution as published: IMPIC, Portal BASE, licence `other-pd` |
| O12 | Keep every row; repeated `idcontrato` values are counted and reported (0 in 2026) |

Dev objects: job `[dev samantha] us01_bronze_contratos` (serverless, two tasks: `carregar_ano`, `contar_independente`); schema `workspace.samantha_contratos_pt`; Volume `workspace.samantha_contratos_pt.contratos_raw`; table `workspace.samantha_contratos_pt.bronze_contratos`.

Dev results (2026, latest catalogue year):

| Run | Rows in bronze | Independent count | Repeats | Null metadata | Check |
|---|---|---|---|---|---|
| 1 | 217,517 | 217,517 | 0 | 0 | equal |
| 2 (idempotency) | 217,517 | 217,517 | 0 | 0 | equal; same SHA-256 `02a0a96d…` |

Not yet verified on dev: the Spark/Delta tests (`tests/test_us01_bronze.py`) and the local ijson count test (`tests/test_us01_contagem.py`). The load itself was checked by the job's own count step.
