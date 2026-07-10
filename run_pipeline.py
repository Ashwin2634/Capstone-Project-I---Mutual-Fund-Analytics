"""
Bluestock Mutual Fund Capstone Pipeline Runner

This script orchestrates the entire data processing and analytics pipeline for the
Bluestock Mutual Fund Capstone project. It sequentially executes various stages
including data ingestion, database loading, analytics computation, advanced
modeling, and report generation.

The pipeline uses a helper function to run each step with real-time output
logging and error handling.

Usage:
    python run_pipeline.py

Outputs:
    - Processed data in processed/ directory
    - SQLite database in db/
    - Reports and newsletters in reports/
"""


import subprocess
import sys
import time

def run_step(command, description):
    """
    Execute a pipeline step as a subprocess and monitor its output in real-time.

    This function runs the given shell command, prints a header for the step,
    streams the stdout/stderr in real-time to the console, measures execution
    time, and handles success/error states. On failure, it exits the entire
    pipeline with the subprocess's return code.

    Args:
        command (str): The shell command to execute (e.g., 'python script.py').
        description (str): Human-readable name/description of the step for logging.

    Returns:
        None: Function exits on error or continues on success.

    Raises:
        SystemExit: If the subprocess returns a non-zero exit code.
    """
    print(f"\n==================================================")
    print(f"STEP: {description}")
    print(f"Running: {command}")
    print(f"==================================================")
    start_time = time.time()
    
    # Run process
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='ignore')
    
    # Print output in real-time
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())
            
    rc = process.poll()
    elapsed = time.time() - start_time
    
    if rc == 0:
        print(f"SUCCESS: {description} completed in {elapsed:.2f} seconds.")
    else:
        print(f"ERROR: {description} failed with exit code {rc} after {elapsed:.2f} seconds.")
        sys.exit(rc)

if __name__ == "__main__":
    print("Starting Bluestock Mutual Fund Capstone Pipeline...")
    total_start = time.time()
    
    # 1. Project Setup and Data Ingestion
    run_step("python scripts/data_ingestion.py.py", "Data Ingestion & Folder Setup")
    run_step("python scripts/live_nav_fetch.py", "Fetch Live Scheme NAVs")
    
    # 2. Database Creation and Clean Loading
    run_step("python scripts/load_to_sqlite.py", "SQLite Database Table Init")
    run_step("python scripts/etl_pipeline.py", "ETL Data Cleaning & SQLite Loading")
    
    # 3. Compute Risk and Performance Analytics
    run_step("python scripts/compute_metrics.py", "Performance Analytics & Scorecard Calculation")
    
    # 4. Advanced Portfolio Risk & Optimization Models
    run_step("jupyter notebook notebooks/05_advanced_analytics.ipynb", "Advanced Analytics (VaR, Cohorts, HHI, Frontier, MC)")
    
    # 5. Compile final deliverables and weekly reports
    run_step("python email_report.py", "Weekly HTML Newsletter Compiler")
    
    total_elapsed = time.time() - total_start
    print(f"\n==================================================")
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {total_elapsed:.2f} SECONDS!")
    print(f"All deliverables are ready in processed/, db/, and reports/ directories.")
    print(f"==================================================")