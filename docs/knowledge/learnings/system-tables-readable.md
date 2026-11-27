# System tables readable with COUNT(*)

Status: [verified]
Last checked: 2026-11-27

Read-only check. One statement per table: `SELECT COUNT(*) FROM system.<schema>.<table>`.
`system.access.audit` gets counts only (total and last 7 days). No data rows are written here.
The list joins the tables visible in `system.information_schema` with the fixed list from the
Databricks documentation (source column). The documented `system.lakebase.*` wildcard is not listed.

Summary: 48 tables checked, 36 readable, 12 with error.

| Schema | Table | Source | Checked on | Result | Rows | Error |
| --- | --- | --- | --- | --- | --- | --- |
| access | assistant_events | documented+visible | 2026-11-27 | success | 196 |  |
| access | audit | documented+visible | 2026-11-27 | success | total 91257; last 7 days 74701 |  |
| access | clean_room_events | documented+visible | 2026-11-27 | success | 0 |  |
| access | column_lineage | documented+visible | 2026-11-27 | success | 7173 |  |
| access | inbound_network | documented+visible | 2026-11-27 | success | 0 |  |
| access | outbound_network | documented+visible | 2026-11-27 | success | 0 |  |
| access | table_lineage | documented+visible | 2026-11-27 | success | 1278 |  |
| access | workspaces_latest | documented+visible | 2026-11-27 | success | 1 |  |
| ai_gateway | external_model_spend | documented+visible | 2026-11-27 | success | 0 |  |
| ai_gateway | usage | documented+visible | 2026-11-27 | success | 0 |  |
| alert | alert_evaluation_history | documented+visible | 2026-11-27 | success | 0 |  |
| alert | alerts | documented+visible | 2026-11-27 | success | 0 |  |
| billing | account_prices | visible | 2026-11-27 | success | 0 |  |
| billing | cloud_infra_cost | visible | 2026-11-27 | success | 0 |  |
| billing | list_prices | documented+visible | 2026-11-27 | success | 892 |  |
| billing | usage | documented+visible | 2026-11-27 | success | 2283 |  |
| compute | clusters | documented+visible | 2026-11-27 | success | 0 |  |
| compute | instance_events | documented | 2026-11-27 | error | — | Error: query failed: BAD_REQUEST [INSUFFICIENT_PERMISSIONS] Insufficient privileges: |
| compute | instance_pools | documented | 2026-11-27 | error | — | Error: query failed: BAD_REQUEST [INSUFFICIENT_PERMISSIONS] Insufficient privileges: |
| compute | node_timeline | documented+visible | 2026-11-27 | success | 0 |  |
| compute | node_types | documented+visible | 2026-11-27 | success | 652 |  |
| compute | warehouse_events | documented+visible | 2026-11-27 | success | 60 |  |
| compute | warehouses | documented+visible | 2026-11-27 | success | 1 |  |
| data_classification | results | documented | 2026-11-27 | error | — | Error: query failed: BAD_REQUEST [TABLE_OR_VIEW_NOT_FOUND] The table or view `system`.`data_classification`.`results` cannot be found. Verify the spelling and correctness of the schema and catalog. |
| data_quality_monitoring | table_results | documented | 2026-11-27 | error | — | Error: query failed: BAD_REQUEST [TABLE_OR_VIEW_NOT_FOUND] The table or view `system`.`data_quality_monitoring`.`table_results` cannot be found. Verify the spelling and correctness of the schema an... |
| lakeflow | job_run_timeline | documented+visible | 2026-11-27 | success | 4 |  |
| lakeflow | job_task_run_timeline | documented+visible | 2026-11-27 | success | 4 |  |
| lakeflow | job_tasks | documented+visible | 2026-11-27 | success | 6 |  |
| lakeflow | jobs | documented+visible | 2026-11-27 | success | 8 |  |
| lakeflow | pipeline_update_timeline | documented | 2026-11-27 | error | — | Error: query failed: BAD_REQUEST [INSUFFICIENT_PERMISSIONS] Insufficient privileges: |
| lakeflow | pipelines | documented+visible | 2026-11-27 | success | 19 |  |
| lakeflow | zerobus_ingest | documented | 2026-11-27 | error | — | Error: query failed: BAD_REQUEST [INSUFFICIENT_PERMISSIONS] Insufficient privileges: |
| lakeflow | zerobus_stream | documented | 2026-11-27 | error | — | Error: query failed: BAD_REQUEST [INSUFFICIENT_PERMISSIONS] Insufficient privileges: |
| lakeflow_pipeline_events_preview | pipeline_events | documented+visible | 2026-11-27 | success | 2734 |  |
| marketplace | listing_access_events | documented | 2026-11-27 | error | — | Error: query failed: BAD_REQUEST [TABLE_OR_VIEW_NOT_FOUND] The table or view `system`.`marketplace`.`listing_access_events` cannot be found. Verify the spelling and correctness of the schema and ca... |
| marketplace | listing_funnel_events | documented | 2026-11-27 | error | — | Error: query failed: BAD_REQUEST [TABLE_OR_VIEW_NOT_FOUND] The table or view `system`.`marketplace`.`listing_funnel_events` cannot be found. Verify the spelling and correctness of the schema and ca... |
| mlflow | experiments_latest | documented+visible | 2026-11-27 | success | 0 |  |
| mlflow | run_metrics_history | documented+visible | 2026-11-27 | success | 0 |  |
| mlflow | runs_latest | documented+visible | 2026-11-27 | success | 0 |  |
| query | history | documented+visible | 2026-11-27 | success | 1580 |  |
| replication | states | documented | 2026-11-27 | error | — | Error: query failed: BAD_REQUEST [TABLE_OR_VIEW_NOT_FOUND] The table or view `system`.`replication`.`states` cannot be found. Verify the spelling and correctness of the schema and catalog. |
| serving | endpoint_usage | documented+visible | 2026-11-27 | success | 0 |  |
| serving | served_entities | documented+visible | 2026-11-27 | success | 0 |  |
| sharing | materialization_history | documented+visible | 2026-11-27 | success | 0 |  |
| storage | auto_upgrade_operations_history | documented | 2026-11-27 | error | — | Error: query failed: BAD_REQUEST [INSUFFICIENT_PERMISSIONS] Insufficient privileges: |
| storage | predictive_optimization_operations_history | documented+visible | 2026-11-27 | success | 103 |  |
| storage | table_metrics_history | documented | 2026-11-27 | error | — | Error: query failed: BAD_REQUEST [INSUFFICIENT_PERMISSIONS] Insufficient privileges: |
| tags | governed_tags | documented+visible | 2026-11-27 | success | 117 |  |
