"""
Mutual Fund Performance Metrics Calculator

Computes key risk-return metrics (CAGR, Sharpe, Sortino, Alpha/Beta, Drawdown),
builds a composite scorecard, updates the database, and generates benchmark charts.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
from scipy import stats
from sqlalchemy import create_engine
import matplotlib.pyplot as plt

def get_db_connection(db_path="data/db/bluestock_mf.db"):
    """Return a SQLite connection to the mutual fund database."""
    return sqlite3.connect(db_path)

def compute_performance_metrics(db_path="data/db/bluestock_mf.db", processed_dir="data/processed", reports_dir="reports/images"):
    """
    Main function: Compute performance metrics, scorecard, update DB, and generate charts.

    Args:
        db_path (str): Path to SQLite database.
        processed_dir (str): Output directory for CSVs.
        reports_dir (str): Output directory for charts.
    """
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)
    
    conn = get_db_connection(db_path)
    
    # 1. Load Fund Master and NAV History
    df_funds = pd.read_sql("SELECT amfi_code, scheme_name, fund_house, category, plan, expense_ratio_pct, aum_crore, morningstar_rating, risk_grade FROM fact_performance", conn)
    df_nav_all = pd.read_sql("SELECT amfi_code, date, nav, daily_return_pct FROM fact_nav", conn)
    df_nav_all['date'] = pd.to_datetime(df_nav_all['date'])
    
    # 2. Load Benchmark NAV (NIFTY100)
    df_bench = pd.read_sql("SELECT date, close_value FROM fact_benchmark WHERE index_name = 'NIFTY100'", conn)
    df_bench['date'] = pd.to_datetime(df_bench['date'])
    df_bench = df_bench.sort_values('date')
    df_bench['bench_return'] = df_bench['close_value'].pct_change()
    df_bench = df_bench.dropna()
    
    metrics_list = []
    
    # Let's compute metrics for each fund
    for idx, row in df_funds.iterrows():
        code = row['amfi_code']
        df_sub = df_nav_all[df_nav_all['amfi_code'] == code].sort_values('date').copy()
        
        if len(df_sub) < 5:
            print(f"Skipping scheme {code} due to insufficient data.")
            continue
            
        navs = df_sub['nav'].values
        dates = df_sub['date'].values
        daily_returns = (df_sub['daily_return_pct'].values / 100.0)  # Convert back to decimal
        
        # A. CAGR Calculations (1Yr = 252 trading days, 3Yr = 756, 5Yr = 1260)
        n = len(navs)
        
        # 1-Year CAGR
        n_1y = min(252, n)
        cagr_1y = (navs[-1] / navs[-n_1y]) ** (252.0 / n_1y) - 1 if n_1y > 1 else 0.0
        
        # 3-Year CAGR
        n_3y = min(756, n)
        cagr_3y = (navs[-1] / navs[-n_3y]) ** (252.0 / n_3y) - 1 if n_3y > 1 else 0.0
        
        # 5-Year CAGR
        n_5y = min(1260, n)
        cagr_5y = (navs[-1] / navs[-n_5y]) ** (252.0 / n_5y) - 1 if n_5y > 1 else 0.0
        
        # B. Sharpe and Sortino Ratios (Rf = 6.5% = 0.065)
        rf_daily = 0.065 / 252.0
        excess_returns = daily_returns - rf_daily
        
        mean_excess = np.mean(excess_returns)
        std_daily = np.std(daily_returns)
        
        # Annualized values
        ann_return = np.mean(daily_returns) * 252.0
        ann_std = std_daily * np.sqrt(252.0)
        
        sharpe = (ann_return - 0.065) / ann_std if ann_std > 0 else 0.0
        
        # Downside Std (Sortino)
        negative_returns = daily_returns[daily_returns < 0]
        downside_std = np.sqrt(np.mean(negative_returns ** 2)) if len(negative_returns) > 0 else 0.0001
        ann_downside_std = downside_std * np.sqrt(252.0)
        sortino = (ann_return - 0.065) / ann_downside_std if ann_downside_std > 0 else 0.0
        
        # C. Alpha and Beta (Regression vs Nifty 100)
        # Align on dates
        df_fund_ret = df_sub[['date', 'daily_return_pct']].copy()
        df_fund_ret['fund_return'] = df_fund_ret['daily_return_pct'] / 100.0
        df_aligned = pd.merge(df_fund_ret, df_bench[['date', 'bench_return']], on='date', how='inner')
        
        if len(df_aligned) > 30:
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                df_aligned['bench_return'].values, 
                df_aligned['fund_return'].values
            )
            beta = slope
            alpha = intercept * 252.0  # Annualized Alpha
        else:
            beta = 1.0
            alpha = 0.0
            
        # D. Maximum Drawdown and Worst Drawdown Date Range
        running_max = np.maximum.accumulate(navs)
        drawdowns = (navs / running_max) - 1.0
        max_dd = np.min(drawdowns)
        
        worst_idx = np.argmin(drawdowns)
        # Find peak before worst drawdown
        peak_idx = np.argmax(navs[:worst_idx + 1])
        
        peak_date = str(dates[peak_idx])[:10]
        bottom_date = str(dates[worst_idx])[:10]
        
        metrics_list.append({
            'amfi_code': code,
            'scheme_name': row['scheme_name'],
            'fund_house': row['fund_house'],
            'category': row['category'],
            'plan': row['plan'],
            'return_1yr_pct': cagr_1y * 100.0,
            'return_3yr_pct': cagr_3y * 100.0,
            'return_5yr_pct': cagr_5y * 100.0,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'alpha': alpha * 100.0,  # in %
            'beta': beta,
            'max_drawdown_pct': max_dd * 100.0,
            'worst_dd_start': peak_date,
            'worst_dd_end': bottom_date,
            'expense_ratio_pct': row['expense_ratio_pct'],
            'std_dev_ann_pct': ann_std * 100.0,
            'aum_crore': row['aum_crore'],
            'morningstar_rating': row['morningstar_rating'],
            'risk_grade': row['risk_grade']
        })
        
    df_metrics = pd.DataFrame(metrics_list)
    
    # 3. Build Fund Scorecard (0-100)
    # Composite: 30% * 3yr Return Rank + 25% * Sharpe Rank + 20% * Alpha Rank + 15% * Expense Rank (inv) + 10% * Max DD Rank (inv)
    # We will use rank percentile (0 to 100 scale)
    
    df_metrics['rank_ret_3yr'] = df_metrics['return_3yr_pct'].rank(pct=True) * 100.0
    df_metrics['rank_sharpe'] = df_metrics['sharpe_ratio'].rank(pct=True) * 100.0
    df_metrics['rank_alpha'] = df_metrics['alpha'].rank(pct=True) * 100.0
    
    # Inverse metrics: lower is better, so smaller expense ratio gets higher rank
    df_metrics['rank_expense'] = df_metrics['expense_ratio_pct'].rank(ascending=False, pct=True) * 100.0
    # lower max drawdown (more negative) is worse, so less negative / higher max drawdown is better.
    df_metrics['rank_max_dd'] = df_metrics['max_drawdown_pct'].rank(pct=True) * 100.0
    
    df_metrics['composite_score'] = (
        0.30 * df_metrics['rank_ret_3yr'] +
        0.25 * df_metrics['rank_sharpe'] +
        0.20 * df_metrics['rank_alpha'] +
        0.15 * df_metrics['rank_expense'] +
        0.10 * df_metrics['rank_max_dd']
    )
    
    # Round columns for readability
    round_cols = ['return_1yr_pct', 'return_3yr_pct', 'return_5yr_pct', 'sharpe_ratio', 'sortino_ratio', 'alpha', 'beta', 'max_drawdown_pct', 'composite_score', 'std_dev_ann_pct']
    for col in round_cols:
        df_metrics[col] = df_metrics[col].round(3)
        
    # Save scorecard to processed csv
    scorecard_path = os.path.join(processed_dir, "fund_scorecard.csv")
    df_metrics.to_csv(scorecard_path, index=False)
    print(f"Fund scorecard saved to {scorecard_path}")
    
    # Save alpha_beta csv
    ab_path = os.path.join(processed_dir, "alpha_beta.csv")
    df_metrics[['amfi_code', 'scheme_name', 'alpha', 'beta']].to_csv(ab_path, index=False)
    print(f"Alpha Beta report saved to {ab_path}")
    
    # Load back to sqlite to update fact_performance
    print("Updating SQLite table 'fact_performance'...")
    engine = create_engine(f"sqlite:///{db_path}")
    # Load df_metrics to fact_performance
    df_metrics_db = df_metrics.drop(columns=['rank_ret_3yr', 'rank_sharpe', 'rank_alpha', 'rank_expense', 'rank_max_dd'])
    df_metrics_db.to_sql('fact_performance', engine, if_exists='replace', index=False)
    
    # 4. Generate Benchmark comparison chart (Top 5 funds vs Nifty 50 and Nifty 100 over 3 years)
    print("Generating Benchmark Comparison Chart...")
    # Get top 5 funds by composite score
    top_5_codes = df_metrics.sort_values('composite_score', ascending=False).head(5)['amfi_code'].tolist()
    
    plt.figure(figsize=(12, 6))
    
    # Plot top 5 funds growth
    min_common_date = pd.to_datetime('2023-01-01')
    
    for code in top_5_codes:
        sub = df_nav_all[(df_nav_all['amfi_code'] == code) & (df_nav_all['date'] >= min_common_date)].sort_values('date')
        if not sub.empty:
            # Base value at start
            start_val = sub.iloc[0]['nav']
            scheme_name = df_metrics.set_index('amfi_code').loc[code, 'scheme_name']
            plt.plot(sub['date'], (sub['nav'] / start_val) * 100.0, label=scheme_name, linewidth=1.5)
            
    # Plot benchmarks NIFTY50 and NIFTY100
    df_nifty50 = pd.read_sql("SELECT date, close_value FROM fact_benchmark WHERE index_name = 'NIFTY50' AND date >= '2023-01-01'", conn)
    df_nifty50['date'] = pd.to_datetime(df_nifty50['date'])
    df_nifty50 = df_nifty50.sort_values('date')
    if not df_nifty50.empty:
        plt.plot(df_nifty50['date'], (df_nifty50['close_value'] / df_nifty50.iloc[0]['close_value']) * 100.0, label='Nifty 50', color='black', linestyle='--', linewidth=2)
        
    df_nifty100 = pd.read_sql("SELECT date, close_value FROM fact_benchmark WHERE index_name = 'NIFTY100' AND date >= '2023-01-01'", conn)
    df_nifty100['date'] = pd.to_datetime(df_nifty100['date'])
    df_nifty100 = df_nifty100.sort_values('date')
    if not df_nifty100.empty:
        plt.plot(df_nifty100['date'], (df_nifty100['close_value'] / df_nifty100.iloc[0]['close_value']) * 100.0, label='Nifty 100', color='grey', linestyle=':', linewidth=2)
        
    plt.title("Performance Comparison: Top 5 Funds vs. Benchmarks (Normalized to 100 at Jan 2023)")
    plt.xlabel("Date")
    plt.ylabel("Relative Value")
    plt.legend(loc='upper left', fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(reports_dir, "benchmark_chart.png"), dpi=150)
    plt.close()
    
    # Compute Tracking Error vs Nifty 100 for the top 5
    print("\n--- Tracking Error vs Nifty 100 (Annualized) ---")
    for code in top_5_codes:
        sub = df_nav_all[df_nav_all['amfi_code'] == code].sort_values('date').copy()
        sub['fund_return'] = sub['nav'].pct_change()
        df_align = pd.merge(sub[['date', 'fund_return']], df_bench[['date', 'bench_return']], on='date', how='inner')
        if len(df_align) > 10:
            diff = df_align['fund_return'] - df_align['bench_return']
            tracking_error = diff.std() * np.sqrt(252.0)
            print(f"Fund: {code} | {df_metrics.set_index('amfi_code').loc[code, 'scheme_name'][:40]:<40} | Tracking Error: {tracking_error*100:.2f}%")
            
    conn.close()

if __name__ == "__main__":
    compute_performance_metrics()