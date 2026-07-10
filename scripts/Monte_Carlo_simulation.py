"""
scripts/monte_carlo.py
-----------------------
Bonus B3 — Bluestock Fintech Mutual Fund Analytics Capstone
Monte Carlo simulation projecting NAV growth over 5 years (1,260 trading
days) with uncertainty bands for 5 selected mutual fund schemes.

Method: Geometric Brownian Motion (GBM)
  NAV_t = NAV_0 * exp((mu - 0.5*sigma^2)*t + sigma*sqrt(t)*Z)
  where Z ~ N(0,1), mu and sigma estimated from historical daily returns.

Outputs:
  - reports/monte_carlo_simulation.png — fan chart with 10th/50th/90th
    percentile bands for each fund
  - reports/monte_carlo_summary.csv — summary statistics per fund

Usage (run from project root):
    python scripts/monte_carlo.py
"""

from pathlib import Path
import argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Set up paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED = BASE_DIR / "data" / "processed"
RAW = BASE_DIR / "data" / "raw"
REPORTS = BASE_DIR / "reports"
REPORTS.mkdir(exist_ok=True)

# Reproducibility
np.random.seed(42)

def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load NAV and fund master data."""
    nav_path = PROCESSED / "02_nav_history_cleaned.csv"
    fm_path = PROCESSED / "01_fund_master_cleaned.csv"
    
    if not nav_path.exists():
        raise FileNotFoundError(f"Processed NAV data not found at {nav_path}")
    if not fm_path.exists():
        raise FileNotFoundError(f"Fund master data not found at {fm_path}")
    
    nav = pd.read_csv(nav_path, parse_dates=["date"])
    nav = nav.sort_values(["amfi_code", "date"]).copy()
    nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()
    
    fm = pd.read_csv(fm_path)
    return nav, fm


def estimate_gbm_params(returns: pd.Series) -> tuple[float, float]:
    """
    Estimate drift (mu) and volatility (sigma) for GBM from historical
    daily log returns.
    """
    log_returns = np.log(1 + returns.dropna())
    mu = log_returns.mean()
    sigma = log_returns.std()
    return mu, sigma


def simulate_paths(nav_0: float, mu: float, sigma: float,
                   n_days: int, n_sims: int) -> np.ndarray:
    """
    Simulate n_sims price paths over n_days using GBM (vectorized).
    Returns array of shape (n_days+1, n_sims).
    """
    dt = 1.0
    drift = (mu - 0.5 * sigma**2) * dt
    diffusion = sigma * np.sqrt(dt)
    
    # Vectorized simulation
    Z = np.random.standard_normal((n_days, n_sims))
    daily_changes = np.exp(drift + diffusion * Z)
    
    paths = np.ones((n_days + 1, n_sims))
    paths[0] = nav_0
    # Cumulative product is much faster than loop
    paths[1:] = nav_0 * np.cumprod(daily_changes, axis=0)
    
    return paths


def run_monte_carlo(n_simulations: int = 1000, n_trading_days: int = 1260) -> pd.DataFrame:
    """Run full Monte Carlo simulation and generate outputs."""
    nav_df, fm = load_data()
    
    # Simulation parameters
    TRADING_DAYS_PER_YEAR = 252
    CONFIDENCE_BANDS = [10, 50, 90]
    
    # Selected funds: diverse across risk categories
    SELECTED_CODES = [119551, 119598, 119120, 120503, 100016]
    COLORS = ["#0077B6", "#E63946", "#2DC653", "#F4A261", "#9B5DE5"]
    
    summary_rows = []
    
    # Create figure with subplots
    n_funds = len(SELECTED_CODES)
    fig, axes = plt.subplots(1, n_funds, figsize=(18, 7), sharey=False)
    if n_funds == 1:
        axes = [axes]
    
    fig.suptitle(
        f"Monte Carlo NAV Projection — 5 Years ({n_trading_days:,} Trading Days)\n"
        f"{n_simulations:,} Simulations per Fund | GBM Model | 10th/50th/90th Percentile Bands",
        fontsize=13, fontweight="bold", y=1.02
    )
    
    for idx, (code, ax, color) in enumerate(zip(SELECTED_CODES, axes, COLORS)):
        fund_nav = nav_df[nav_df["amfi_code"] == code].copy()
        if fund_nav.empty:
            print(f"Warning: No data for fund code {code}")
            continue
            
        returns = fund_nav["daily_return"].dropna()
        if len(returns) < 30:  # Minimum history requirement
            print(f"Warning: Insufficient data for fund code {code}")
            continue
            
        nav_0 = fund_nav["nav"].iloc[-1]  # Start from last known NAV
        fund_name = fm[fm["amfi_code"] == code]["scheme_name"].iloc[0]
        short_name = fund_name.split(" - ")[0].replace("Fund", "").strip()[:25]
        
        mu, sigma = estimate_gbm_params(returns)
        paths = simulate_paths(nav_0, mu, sigma, n_trading_days, n_simulations)
        
        # Time in years for x-axis
        t = np.arange(n_trading_days + 1) / TRADING_DAYS_PER_YEAR
        
        # Calculate percentiles
        p10 = np.percentile(paths, 10, axis=1)
        p50 = np.percentile(paths, 50, axis=1)
        p90 = np.percentile(paths, 90, axis=1)
        p25 = np.percentile(paths, 25, axis=1)
        p75 = np.percentile(paths, 75, axis=1)
        
        # Plot fan chart
        ax.fill_between(t, p10, p90, alpha=0.2, color=color, label="10th–90th percentile")
        ax.fill_between(t, p25, p75, alpha=0.35, color=color, label="25th–75th percentile")
        ax.plot(t, p50, color=color, linewidth=2.5, label="Median (50th)")
        ax.plot(t, p10, color=color, linewidth=1, linestyle="--", alpha=0.7)
        ax.plot(t, p90, color=color, linewidth=1, linestyle="--", alpha=0.7)
        
        # Starting NAV reference
        ax.axhline(nav_0, color="black", linewidth=1, linestyle=":", alpha=0.6,
                   label=f"Current NAV: ₹{nav_0:,.0f}")
        
        ax.set_title(short_name, fontsize=11, fontweight="bold", pad=10)
        ax.set_xlabel("Years", fontsize=10)
        if idx == 0:
            ax.set_ylabel("NAV (₹)", fontsize=10)
        ax.legend(fontsize=8, loc="upper left")
        ax.grid(True, alpha=0.3)
        
        # Summary stats
        median_5yr = p50[-1]
        expected_cagr = (median_5yr / nav_0) ** (1 / 5) - 1
        
        summary_rows.append({
            "amfi_code": code,
            "scheme_name": fund_name,
            "nav_start": round(nav_0, 2),
            "mu_daily": round(mu, 6),
            "sigma_daily": round(sigma, 6),
            "ann_volatility_pct": round(sigma * np.sqrt(252) * 100, 2),
            "p10_5yr_nav": round(p10[-1], 2),
            "p50_5yr_nav": round(median_5yr, 2),
            "p90_5yr_nav": round(p90[-1], 2),
            "expected_cagr_pct": round(expected_cagr * 100, 2),
            "prob_positive_5yr_pct": round((paths[-1] > nav_0).mean() * 100, 1),
            "n_historical_days": len(returns),
        })
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # Save outputs
    out_path = REPORTS / "monte_carlo_simulation.png"
    fig.savefig(out_path, bbox_inches="tight", dpi=120)
    plt.close()
    print(f"✅ Chart saved: {out_path.relative_to(BASE_DIR)}")
    
    summary_df = pd.DataFrame(summary_rows)
    csv_path = REPORTS / "monte_carlo_summary.csv"
    summary_df.to_csv(csv_path, index=False)
    print(f"✅ Summary saved: {csv_path.relative_to(BASE_DIR)}")
    
    # Pretty print key results
    print("\n" + "="*80)
    print("MONTE CARLO SUMMARY")
    print("="*80)
    print(summary_df[["scheme_name", "expected_cagr_pct", 
                      "prob_positive_5yr_pct", "p50_5yr_nav", 
                      "ann_volatility_pct"]].round(2).to_string(index=False))
    
    return summary_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monte Carlo NAV Projection")
    parser.add_argument("--n_sims", type=int, default=1000, help="Number of simulations")
    parser.add_argument("--n_days", type=int, default=1260, help="Number of trading days")
    args = parser.parse_args()
    
    print("=" * 75)
    print("MONTE CARLO SIMULATION — 5-Year NAV Projection (GBM)")
    print("=" * 75)
    print(f"Simulations: {args.n_sims:,} | Days: {args.n_days}")
    
    run_monte_carlo(n_simulations=args.n_sims, n_trading_days=args.n_days)