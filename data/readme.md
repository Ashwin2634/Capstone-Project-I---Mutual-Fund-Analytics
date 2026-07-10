# data/

Central data directory following a standard data engineering structure.

## Subfolders

- **`raw/`** — Original downloaded data (should not be modified)
- **`processed/`** — Cleaned, transformed, and feature-engineered datasets
- **`db/`** — SQLite database (`bluestock_mf.db`)

## Usage

```python
# Example
import pandas as pd
df = pd.read_csv('data/processed/07_scheme_performance.csv')
