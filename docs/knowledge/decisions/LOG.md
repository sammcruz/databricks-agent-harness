# Decision log

Append only. One entry per decision that changes how we work.

```
## YYYY-MM-DD · <title>
- Decision:
- Why:
- Alternatives rejected:
- Revisit when:
```

## 2026-11-28 · US01 bronze: streaming splitter, job with notebook, all rows kept
- Decision: the load streams the single-line JSON with a hand-written splitter (no `ijson` in the load); the load is a serverless job with a notebook (not a Lakeflow pipeline); every contract row is kept and repeated `idcontrato` values are reported; the year is replaced with Delta `replaceWhere` on `_source_year`. The independent count uses `ijson` only in the check job.
- Why: probe P4 measured 217,517 contracts with no repeats in 63.6 s and about 2.4 GB peak memory; the job keeps the single pipeline slot free; keeping every row keeps the count equal to the JSON.
- Alternatives rejected: `ijson` in the load (not needed while the splitter passes); Lakeflow pipeline (download is not a declarative step; pipeline slot); dropping repeated keys (silent data loss).
- Revisit when: the serverless memory limit is known and a file gets close to it, or the source starts repeating `idcontrato` values.
