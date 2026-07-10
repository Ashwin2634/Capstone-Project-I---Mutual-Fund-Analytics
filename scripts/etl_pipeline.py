"""
Mutual Fund ETL Pipeline Orchestrator
=====================================

This script orchestrates the complete ETL (Extract, Transform, Load) pipeline
for the Mutual Fund dataset using the provided scripts and notebook logic.

Pipeline Stages:
1. EXTRACT  → Ingest raw CSVs + profiling (data_ingestion.py)
2. TRANSFORM → Comprehensive data cleaning (consolidated from notebook)
3. LOAD     → Star schema into SQLite (load_to_sqlite.py)

Run with: python etl_pipeline.py
"""

import os
import sys
import subprocess
from pathlib import Path
import pandas as pd
import numpy as np
import shutil

# ====================== CONFIGURATION ======================
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = SCRIPT_DIR.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DB_DIR = PROJECT_ROOT / "data" / "db"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"

for dir_path in [PROCESSED_DIR, DB_DIR, REPORTS_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ====================== HELPER FUNCTIONS ======================

def run_ingestion():
    """Stage 1: Extract + Profiling"""
    print("=" * 80)
    print("ETL STAGE 1: DATA INGESTION & PROFILING")
    print("=" * 80)
    
    ingestion_script = SCRIPT_DIR / "data_ingestion.py"
    if not ingestion_script.exists():
        print("❌ data_ingestion.py not found!")
        sys.exit(1)
    
    result = subprocess.run([sys.executable, str(ingestion_script)], 
                          capture_output=True, text=True, cwd=SCRIPT_DIR)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode == 0:
        print("✅ Ingestion & Profiling completed successfully.")
    else:
        print("⚠️ Ingestion completed with warnings.")
    return result.returncode == 0


def clean_all_datasets():
    """Stage 2: Transform - Consolidated cleaning logic"""
    print("\n" + "=" * 80)
    print("ETL STAGE 2: DATA CLEANING & TRANSFORMATION")
    print("=" * 80)
    
    # Ensure processed directory is clean
    for f in PROCESSED_DIR.glob("*.csv"):
        f.unlink()
    
    # Load raw data
    dfs = {}
    for file in RAW_DIR.glob("*.csv"):
        name = file.stem
        dfs[name] = pd.read_csv(file)
        print(f"Loaded {name}: {dfs[name].shape}")
    
    # ================== CLEANING FUNCTIONS ==================
    
    def clean_nav_history(df):
        """Comprehensive NAV cleaning"""
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'], format='mixed', errors='coerce')
        df = df.sort_values(['amfi_code', 'date'])
        df = df[df['nav'] > 0].drop_duplicates()
        
        # Forward fill gaps
        start_date = df['date'].min()
        end_date = df['date'].max()
        full_dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        def forward_fill_scheme(group):
            group = group.set_index('date')
            group = group.reindex(full_dates)
            group['nav'] = group['nav'].ffill()
            group['amfi_code'] = group['amfi_code'].ffill()
            return group.reset_index().rename(columns={'index': 'date'})
        
        df = df.groupby('amfi_code', group_keys=False).apply(forward_fill_scheme)
        df = df[['amfi_code', 'date', 'nav']]
        return df
    
    def clean_investor_transactions(df):
        """Transaction cleaning"""
        df = df.copy()
        # Standardize transaction types
        mapping = {
            'SIP': ['SIP', 'sip', 'systematic'],
            'Lumpsum': ['Lumpsum', 'lump sum', 'purchase'],
            'Redemption': ['Redemption', 'redeem', 'withdrawal']
        }
        flat_map = {v: k for k, vals in mapping.items() for v in vals}
        df['transaction_type'] = df['transaction_type'].map(flat_map).fillna('Other').str.upper()
        
        df = df[df['amount_inr'] > 0]
        valid_kyc = ['Verified', 'Pending', 'Rejected']
        df = df[df['kyc_status'].isin(valid_kyc)]
        
        df['date'] = pd.to_datetime(df['transaction_date'], format='mixed', errors='coerce')
        return df.drop(columns=['transaction_date'], errors='ignore')
    
    def clean_fund_master(df):
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'], errors='coerce')  # launch_date
        return df.rename(columns={'date': 'launch_date'})
    
    def clean_other(df, date_col='date' if 'date' in df.columns else 'month'):
        df = df.copy()
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        return df.drop_duplicates()
    
    # Apply cleaning
    cleaned = {}
    cleaned['01_fund_master'] = clean_fund_master(dfs.get('01_fund_master', pd.DataFrame()))
    cleaned['02_nav_history'] = clean_nav_history(dfs.get('02_nav_history', pd.DataFrame()))
    cleaned['08_investor_transactions'] = clean_investor_transactions(dfs.get('08_investor_transactions', pd.DataFrame()))
    
    for name, df in dfs.items():
        if name not in ['01_fund_master', '02_nav_history', '08_investor_transactions']:
            cleaned[name] = clean_other(df)
    
    # Save cleaned files
    for name, df in cleaned.items():
        out_path = PROCESSED_DIR / f"{name}_cleaned.csv"
        df.to_csv(out_path, index=False)
        print(f"✅ Saved cleaned: {out_path.name} ({len(df):,} rows)")
    
    print("✅ All datasets cleaned and saved to processed/ directory.")
    return True


def run_loading():
    """Stage 3: Load to SQLite"""
    print("\n" + "=" * 80)
    print("ETL STAGE 3: LOAD TO SQLITE STAR SCHEMA")
    print("=" * 80)
    
    load_script = SCRIPT_DIR / "load_to_sqlite.py"
    if not load_script.exists():
        print("❌ load_to_sqlite.py not found!")
        return False
    
    result = subprocess.run([sys.executable, str(load_script)], 
                          capture_output=True, text=True, cwd=SCRIPT_DIR)
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode == 0:
        print("✅ Database load completed successfully.")
        return True
    else:
        print("❌ Database load failed.")
        return False


def generate_pipeline_report():
    """Generate final ETL report"""
    report_path = REPORTS_DIR / "etl_pipeline_summary.txt"
    with open(report_path, "w") as f:
        f.write("MUTUAL FUND ETL PIPELINE SUMMARY\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Run Date: {pd.Timestamp.now()}\n")
        f.write(f"Raw Files: {len(list(RAW_DIR.glob('*.csv')))}\n")
        f.write(f"Processed Files: {len(list(PROCESSED_DIR.glob('*.csv')))}\n")
        f.write(f"Database: {DB_DIR / 'bluestock_mf.db'}\n")
        f.write("\nPipeline Stages: [EXTRACT] → [TRANSFORM] → [LOAD] ✓\n")
    print(f"\n📊 Pipeline report saved: {report_path}")


# ====================== MAIN PIPELINE ======================

def main():
    """Run full ETL pipeline"""
    print("🚀 Starting Mutual Fund ETL Pipeline...\n")
    
    success = True
    success &= run_ingestion()
    success &= clean_all_datasets()
    success &= run_loading()
    
    generate_pipeline_report()
    
    if success:
        print("\n🎉 ETL PIPELINE COMPLETED SUCCESSFULLY!")
    else:
        print("\n⚠️ ETL completed with some issues. Check logs.")
    
    print(f"Database ready at: {DB_DIR / 'bluestock_mf.db'}")


if __name__ == "__main__":
    main()