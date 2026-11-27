# System table access

- [verified] `system.lakeflow.pipelines` is queryable through `python scripts/dbquery.py`. On 2026-11-27, a read-only count returned 27 rows. This confirms table read access, not pipeline freshness, configuration, or historical completeness.
- [verified] Safe discovery sequence: `SHOW SCHEMAS IN system`, `SHOW TABLES IN system.lakeflow`, `SHOW TABLES IN system.billing`, `SHOW TABLES IN system.compute`, then `DESCRIBE TABLE system.lakeflow.pipelines` before selecting.
- [verified] Query used: `SELECT COUNT(*) AS pipeline_row_count FROM system.lakeflow.pipelines`. It returned only an aggregate and did not expose identities or row-level data. Last checked: 2026-11-27
