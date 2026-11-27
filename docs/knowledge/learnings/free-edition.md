# Databricks Free Edition: what US01 verified in dev

Measured in the DEV Free Edition workspace (profile `free`), serverless compute, for issue #2 (US01).
Status tags: **verified** = run in dev and the output was checked; **unverified** = not run, or run without a check.

## Probe results (P1–P7, spec section 6)

| # | Probe | Result | Status |
|---|---|---|---|
| P1 | Reach the catalogue and the zip from compute | `latest` HEAD 200, no Content-Length; `url` HEAD 200, Content-Length 71136042; a Range request gave 500 once and 206 once. Chosen: `latest`. Final host dados.gov.pt | verified (P1 check was too strict at first; fixed to test reachability and size only) |
| P2 | Repeated calls (rate limit) | 10 calls, all 200, no 429 seen | verified for 10 calls; a real 429 was not reproduced |
| P3a | Write and read the Volume | 1 MB write and read OK | verified |
| P3-download | Download the zip to compute | 71,136,042 bytes in 13.7 s | verified |
| P3b | Store and re-hash | SHA-256 re-read equal | verified |
| P4 | Stream-parse the 641 MB single-line JSON | 217,517 contracts, 217,517 distinct ids, 0 repeats, 63.6 s, peak RSS about 2,450 MB | verified; the serverless memory limit is not exposed, so the margin is unknown |
| P4-count | Independent count with ijson | could not run: ijson not importable in the probe | unverified in the probe; the check job installs `ijson` as an environment dependency and passed in dev (217,517 = 217,517) |
| P5-ijson | Import ijson on serverless (probe) | not importable in the probe environment | verified as absent in the probe; the check job's environment dependency is what made it work |
| P5-delta | Delta write from a notebook | works | verified (the load writes Delta `replaceWhere`) |
| P6 | Storage quota | no quota exposed; the probe wrote about 72 MB | unverified (quota not visible) |
| P7 | Cleanup | probe folder deleted from the workspace | verified |

## Things that cost time (keep these)

- **`dbutils.notebook.exit` is required** for one-off job runs to return a value. Printed output is not returned by `jobs get-run-output`.
- **An uncaught `SystemExit` shows as job SUCCESS.** Use `raise` (or `dbutils.notebook.exit` with a status) so a failed probe does not look green.
- **`databricks jobs submit --json`** needs the environment spec with `client: "2"` for serverless. The run's notebook output is on the task run id (`get-run` → `tasks[0].run_id` → `get-run-output`).
- **`workspace import-dir`** copies `__pycache__` and stray files too. Import only the files you need.
- **Serverless does not have `ijson` by default.** Declare it as a job environment dependency (`environments: spec: dependencies: [ijson]`) when a task needs it. Verified in dev.
- **The macOS `/usr/bin/java` stub** exists without a JDK: `shutil.which("java")` finds it. Check `java -version` returns 0 before running Spark tests.
- **PyPI returned HTTP 503 from the Mac** during the build, and `uv` failed on TLS. Local installs of `ijson` failed; the test that needs it skips locally.

## Limits met

- Single-line JSON: Spark's JSON reader cannot split it, so the load streams it in plain Python first (see spec section 3). Peak memory about 2.4 GB for a 641 MB file.
- One warehouse and one active pipeline slot: the load is a job, so the pipeline slot is not used.
