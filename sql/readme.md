# sql/

SQL assets for the SQLite database.

## Files

- `schema.sql` — Database schema, table creation, and indexes
- `queries.sql` — Common analytical queries (performance, AUM, investor trends, etc.)

## Usage

```sql
-- Example
SELECT * FROM scheme_performance 
WHERE sharpe_ratio > 1.5 
ORDER BY return_3yr_pct DESC;
