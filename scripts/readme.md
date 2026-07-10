# scripts/

Production-ready Python scripts (modular and reusable).

## Main Scripts

| Script                        | Purpose |
|------------------------------|--------|
| `data_ingestion.py`          | Fetch latest data from APIs/sources |
| `etl_pipeline.py`            | Full Extract-Transform-Load process |
| `load_to_sqlite.py`          | Load cleaned data into SQLite |
| `compute_metrics.py`         | Calculate risk/return metrics |
| `Markowitz_Efficient_Frontier.py` | Portfolio optimization |
| `Monte_Carlo_simulation.py`  | Risk simulation |
| `recommender.py`             | Fund recommendation engine |
| `live_nav_fetch.py`          | Real-time NAV updates |
| `scheduled_etl.py`           | Scheduled job runner |

**Orchestration:** Use `run_pipeline.py` at root.
