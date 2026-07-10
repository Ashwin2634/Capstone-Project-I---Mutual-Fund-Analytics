
"""
Mutual Fund Data Loader - Star Schema ETL Pipeline
==================================================

This script performs ETL operations to load cleaned mutual fund datasets 
into a SQLite database using a star schema design.
"""

import pandas as pd
from sqlalchemy import create_engine
import os
from pathlib import Path


# ====================== CONFIGURATION ======================
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"
SCHEMA_DIR = SCRIPT_DIR.parent / "sql"
DB_DIR = SCRIPT_DIR.parent / "data" / "db"
REPORTS_DIR = SCRIPT_DIR.parent / "reports"

DB_PATH = DB_DIR / "bluestock_mf.db"

# Ensure directories exist
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)


# ====================== HELPER FUNCTIONS ======================

def build_date_dimension(nav_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate date dimension table covering the full range of NAV history.
    """
    start_date = nav_df["date"].min()
    end_date = nav_df["date"].max()
    
    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    
    dim_date = pd.DataFrame({
        "date_id": dates.strftime("%Y-%m-%d")
    })
    
    dim_date["year"] = dates.year
    dim_date["month"] = dates.month
    dim_date["quarter"] = dates.quarter
    dim_date["day_of_week"] = dates.dayofweek
    dim_date["is_weekday"] = (dates.dayofweek < 5).astype(int)
    
    return dim_date


def calculate_daily_returns(nav_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute daily percentage returns grouped by fund.
    """
    df = nav_df.sort_values(["amfi_code", "date"]).copy()
    df["daily_return_pct"] = (
        df.groupby("amfi_code")["nav"].pct_change() * 100
    ).round(4)
    return df


def load_table(df: pd.DataFrame, table_name: str, engine) -> int:
    """Load DataFrame into target table and return row count."""
    df.to_sql(table_name, engine, if_exists="append", index=False)
    return len(df)


# ====================== MAIN ETL PIPELINE ======================

def main() -> None:
    """Execute the complete ETL process for mutual fund star schema."""
    print("=" * 80)
    print("MUTUAL FUND STAR SCHEMA ETL PIPELINE")
    print("Loading data into bluestock_mf.db")
    print("=" * 80)

    # Clean rebuild
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"[INFO] Removed existing database for clean rebuild: {DB_PATH.name}")

    engine = create_engine(f"sqlite:///{DB_PATH}")

    # Apply schema
    schema_sql = (SCHEMA_DIR / "schema.sql").read_text(encoding="utf-8")
    with engine.raw_connection() as conn:
        conn.executescript(schema_sql)
        conn.commit()
    
    print("[SUCCESS] Database schema applied")

    verification_records = []

    # --------------------- Dimension Tables ---------------------
    # dim_fund
    fund_master = pd.read_csv(DATA_DIR / "01_fund_master_cleaned.csv")
    fund_master = fund_master.rename(columns={"date": "launch_date"})
    
    row_count = load_table(fund_master, "dim_fund", engine)
    verification_records.append(("dim_fund", "01_fund_master_cleaned.csv", 
                                len(fund_master), row_count))
    print(f"[OK] dim_fund loaded: {row_count:,} rows")

    # --------------------- Fact Tables ---------------------
    # fact_nav + dim_date
    nav_history = pd.read_csv(
        DATA_DIR / "02_nav_history_cleaned.csv", 
        parse_dates=["date"]
    )
    
    dim_date = build_date_dimension(nav_history)
    load_table(dim_date, "dim_date", engine)
    print(f"[OK] dim_date generated: {len(dim_date):,} rows "
          f"({nav_history['date'].min().date()} to {nav_history['date'].max().date()})")
    
    nav_with_returns = calculate_daily_returns(nav_history)
    nav_out = nav_with_returns.copy()
    nav_out["date"] = nav_out["date"].dt.strftime("%Y-%m-%d")
    nav_out = nav_out.rename(columns={"date": "nav_date"})
    
    nav_cols = ["amfi_code", "nav_date", "nav", "daily_return_pct"]
    row_count = load_table(nav_out[nav_cols], "fact_nav", engine)
    verification_records.append(("fact_nav", "02_nav_history_cleaned.csv",
                                len(nav_history), row_count))
    print(f"[OK] fact_nav loaded: {row_count:,} rows")

    # fact_transactions
    tx = pd.read_csv(DATA_DIR / "08_investor_transactions_cleaned.csv")
    tx["transaction_type"] = tx["transaction_type"].replace({
        "REDEMPTION": "Redemption",
        "LUMPSUM": "Lumpsum",
        "SIP": "SIP"
    })
    
    tx_out = tx.rename(columns={"date": "transaction_date"})
    tx_cols = ["investor_id", "transaction_date", "amfi_code", "transaction_type",
               "amount_inr", "state", "city", "city_tier", "age_group", "gender",
               "annual_income_lakh", "payment_mode", "kyc_status"]
    
    row_count = load_table(tx_out[tx_cols], "fact_transactions", engine)
    verification_records.append(("fact_transactions", 
                                "08_investor_transactions_cleaned.csv",
                                len(tx), row_count))
    print(f"[OK] fact_transactions loaded: {row_count:,} rows")

    # fact_performance
    perf = pd.read_csv(DATA_DIR / "07_scheme_performance_cleaned.csv")
    perf_cols = ["amfi_code", "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
                 "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio", "sortino_ratio",
                 "std_dev_ann_pct", "max_drawdown_pct", "aum_crore", "expense_ratio_pct",
                 "morningstar_rating", "risk_grade"]
    
    row_count = load_table(perf[perf_cols], "fact_performance", engine)
    verification_records.append(("fact_performance", 
                                "07_scheme_performance_cleaned.csv",
                                len(perf), row_count))
    print(f"[OK] fact_performance loaded: {row_count:,} rows")

    # fact_aum
    aum = pd.read_csv(DATA_DIR / "03_aum_by_fund_house_cleaned.csv")
    aum_out = aum.rename(columns={"date": "report_date"})
    row_count = load_table(aum_out, "fact_aum", engine)
    verification_records.append(("fact_aum", "03_aum_by_fund_house_cleaned.csv",
                                len(aum), row_count))
    print(f"[OK] fact_aum loaded: {row_count:,} rows")

    # ====================== VERIFICATION ======================
    print("\n" + "=" * 80)
    print("DATA INTEGRITY VERIFICATION")
    print("=" * 80)
    
    verification_df = pd.DataFrame(
        verification_records,
        columns=["table_name", "source_file", "source_rows", "loaded_rows"]
    )
    verification_df["match"] = verification_df["source_rows"] == verification_df["loaded_rows"]
    
    print(verification_df.to_string(index=False))
    
    if verification_df["match"].all():
        print("\n[SUCCESS] All row counts match source files.")
    else:
        print("\n[WARNING] Some row counts do not match source files!")

    # Save verification report
    report_path = REPORTS_DIR / "day2_SqliteDB_load_verification_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("MUTUAL FUND ETL LOAD VERIFICATION REPORT\n")
        f.write("=" * 70 + "\n\n")
        f.write(verification_df.to_string(index=False))
        f.write(f"\n\nDatabase Path : {DB_PATH.relative_to(SCRIPT_DIR.parent)}\n")
        f.write(f"Database Size : {DB_PATH.stat().st_size / 1024:.1f} KB\n")
        f.write(f"Status        : {'SUCCESS' if verification_df['match'].all() else 'WARNING'}\n")
    
    print(f"\n[INFO] Verification report saved: {report_path.relative_to(SCRIPT_DIR.parent)}")
    print(f"[INFO] Database created successfully at: {DB_PATH.relative_to(SCRIPT_DIR.parent)}")


if __name__ == "__main__":
    main()