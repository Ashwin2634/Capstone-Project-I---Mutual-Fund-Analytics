"""
scripts/Markowitz_Efficient_Frontier.py
------------------------------
Bonus B4 — Bluestock Fintech Mutual Fund Analytics Capstone

Markowitz Mean-Variance Portfolio Optimisation for 5 selected mutual
fund schemes. Generates the Efficient Frontier — the set of portfolios
offering the maximum expected return for each level of risk.

Run it with::
    python scripts/efficient_frontier.py
"""


from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # For non-interactive plotting
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / 'data' / 'processed'
OUTPUT_DIR = PROJECT_ROOT / 'reports'
OUTPUT_DIR.mkdir(exist_ok=True)

# Constants
RISK_FREE_RATE = 0.065
TRADING_DAYS_PER_YEAR = 252
NUM_RANDOM_PORTFOLIOS = 5000

np.random.seed(42)

# Selected fund codes - picked these for diversity
FUND_CODES = [119551, 119598, 119120, 120503, 100016]


def get_daily_returns():
    """Load NAV data and compute daily returns for selected funds."""
    nav_data = pd.read_csv(DATA_DIR / '02_nav_history_cleaned.csv', parse_dates=['date'])
    fund_info = pd.read_csv(DATA_DIR / '01_fund_master_cleaned.csv')
    
    # Filter to our funds
    nav_data = nav_data[nav_data['amfi_code'].isin(FUND_CODES)]
    nav_data = nav_data.sort_values(['amfi_code', 'date'])
    
    # Calculate returns
    nav_data['daily_ret'] = nav_data.groupby('amfi_code')['nav'].pct_change()
    
    # Pivot to wide format
    returns_wide = nav_data.pivot(
        index='date', 
        columns='amfi_code', 
        values='daily_ret'
    ).dropna()
    
    # Clean column names
    clean_names = []
    for code in returns_wide.columns:
        name = fund_info[fund_info['amfi_code'] == code]['scheme_name'].iloc[0]
        short_name = name.split(' - ')[0].strip()[:18]
        clean_names.append(short_name)
    
    returns_wide.columns = clean_names
    return returns_wide, clean_names


def calc_portfolio_stats(weights, avg_returns, cov_mat):
    """Calculate annualized return, volatility and Sharpe ratio."""
    annual_ret = np.dot(weights, avg_returns) * TRADING_DAYS_PER_YEAR
    annual_vol = np.sqrt(np.dot(weights.T, np.dot(cov_mat * TRADING_DAYS_PER_YEAR, weights)))
    sharpe_ratio = (annual_ret - RISK_FREE_RATE) / annual_vol if annual_vol > 0 else 0
    return annual_ret, annual_vol, sharpe_ratio


def generate_random_portfolios(avg_returns, cov_mat, num_port=NUM_RANDOM_PORTFOLIOS):
    """Simulate many random portfolios."""
    num_funds = len(avg_returns)
    portfolio_results = np.zeros((3, num_port))
    all_weights = []
    
    for i in range(num_port):
        # Random weights that sum to 1
        weights = np.random.dirichlet(np.ones(num_funds))
        
        ret, vol, sharpe = calc_portfolio_stats(weights, avg_returns, cov_mat)
        
        portfolio_results[0, i] = ret
        portfolio_results[1, i] = vol
        portfolio_results[2, i] = sharpe
        all_weights.append(weights)
    
    return portfolio_results, all_weights


def find_min_variance_portfolio(avg_returns, cov_mat):
    """Optimize for the portfolio with lowest risk."""
    num_funds = len(avg_returns)
    
    def objective(w):
        return calc_portfolio_stats(w, avg_returns, cov_mat)[1]
    
    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    bounds = [(0, 1) for _ in range(num_funds)]
    initial_guess = np.ones(num_funds) / num_funds
    
    result = minimize(
        objective, initial_guess,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )
    return result


def find_max_sharpe_portfolio(avg_returns, cov_mat):
    """Optimize for the highest Sharpe ratio."""
    num_funds = len(avg_returns)
    
    def objective(w):
        return -calc_portfolio_stats(w, avg_returns, cov_mat)[2]
    
    constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1}]
    bounds = [(0, 1) for _ in range(num_funds)]
    initial_guess = np.ones(num_funds) / num_funds
    
    result = minimize(
        objective, initial_guess,
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )
    return result


def build_efficient_frontier(avg_returns, cov_mat, points=100):
    """Generate points along the efficient frontier."""
    min_ret = avg_returns.min() * TRADING_DAYS_PER_YEAR * 1.05
    max_ret = avg_returns.max() * TRADING_DAYS_PER_YEAR * 0.95
    target_returns = np.linspace(min_ret, max_ret, points)
    
    num_funds = len(avg_returns)
    vols = []
    
    for target in target_returns:
        def objective(w):
            return calc_portfolio_stats(w, avg_returns, cov_mat)[1]
        
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},
            {'type': 'eq', 'fun': lambda w: calc_portfolio_stats(w, avg_returns, cov_mat)[0] - target}
        ]
        bounds = [(0, 1) for _ in range(num_funds)]
        initial_guess = np.ones(num_funds) / num_funds
        
        opt_result = minimize(
            objective, initial_guess,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )
        
        if opt_result.success:
            vols.append(opt_result.fun)
        else:
            vols.append(np.nan)
    
    return target_returns, np.array(vols)


def create_visualization(returns_df, fund_names, rand_results, mvp, msr, ef_rets, ef_vols):
    """Create the two-panel plot."""
    fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(16, 7))
    
    # Random portfolios scatter
    scatter = ax_left.scatter(
        rand_results[1], rand_results[0],
        c=rand_results[2], cmap='viridis',
        alpha=0.5, s=10, label='Random Portfolios'
    )
    plt.colorbar(scatter, ax=ax_left, label='Sharpe Ratio')
    
    # Efficient frontier line
    valid_mask = ~np.isnan(ef_vols)
    ax_left.plot(
        ef_vols[valid_mask], ef_rets[valid_mask],
        'b-', linewidth=3, label='Efficient Frontier'
    )
    
    # Optimal points
    mvp_ret, mvp_vol, mvp_sr = calc_portfolio_stats(mvp.x, returns_df.mean().values, returns_df.cov().values)
    msr_ret, msr_vol, msr_sr = calc_portfolio_stats(msr.x, returns_df.mean().values, returns_df.cov().values)
    
    ax_left.scatter(mvp_vol, mvp_ret, marker='*', color='gold', s=350, 
                   label=f'Min Risk (Sharpe: {mvp_sr:.2f})', zorder=10)
    ax_left.scatter(msr_vol, msr_ret, marker='*', color='red', s=350, 
                   label=f'Best Sharpe (Sharpe: {msr_sr:.2f})', zorder=10)
    
    ax_left.set_xlabel('Annualized Risk (Volatility)', fontsize=12)
    ax_left.set_ylabel('Annualized Expected Return', fontsize=12)
    ax_left.set_title('Efficient Frontier for Selected Mutual Funds', fontsize=13, fontweight='bold')
    ax_left.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x*100:.1f}%'))
    ax_left.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x*100:.1f}%'))
    ax_left.legend(fontsize=10)
    ax_left.grid(True, alpha=0.25)
    
    # Weights bar chart
    n_funds = len(fund_names)
    equal_weights = np.ones(n_funds) / n_funds
    weights_matrix = np.array([equal_weights, mvp.x, msr.x])
    
    labels = ['Equal Weight', 'Min Variance', 'Max Sharpe']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    bottom = np.zeros(3)
    for idx, (fund, color) in enumerate(zip(fund_names, colors)):
        ax_right.bar(labels, weights_matrix[:, idx], bottom=bottom, 
                    color=color, label=fund[:15], edgecolor='white')
        bottom += weights_matrix[:, idx]
    
    ax_right.set_title('Portfolio Allocations', fontsize=13, fontweight='bold')
    ax_right.set_ylabel('Weight (%)', fontsize=12)
    ax_right.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x*100:.0f}%'))
    ax_right.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax_right.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    save_path = OUTPUT_DIR / 'Markowitz_Efficient_Frontier.png'
    fig.savefig(save_path, dpi=120, bbox_inches='tight')
    plt.close()
    print(f'📊 Plot saved to: {save_path}')


def main():
    print('🔍 Starting Portfolio Optimization Analysis...')
    print('=' * 60)
    
    # Load data
    returns_data, fund_names = get_daily_returns()
    mean_rets = returns_data.mean().values
    cov_matrix = returns_data.cov().values
    
    print(f'\nFunds analyzed: {fund_names}')
    print(f'Period: {returns_data.index.min().date()} to {returns_data.index.max().date()}')
    print(f'Daily observations: {len(returns_data)}')
    
    # Generate random portfolios
    print(f'\nGenerating {NUM_RANDOM_PORTFOLIOS:,} random portfolios...')
    random_results, _ = generate_random_portfolios(mean_rets, cov_matrix)
    
    # Find optimal portfolios
    print('Optimizing portfolios...')
    min_var_opt = find_min_variance_portfolio(mean_rets, cov_matrix)
    max_sharpe_opt = find_max_sharpe_portfolio(mean_rets, cov_matrix)
    
    # Build frontier
    print('Building efficient frontier...')
    frontier_returns, frontier_vols = build_efficient_frontier(mean_rets, cov_matrix)
    
    # Create plot
    create_visualization(returns_data, fund_names, random_results, 
                        min_var_opt, max_sharpe_opt, frontier_returns, frontier_vols)
    
    # Save weights to CSV
    equal_w = np.ones(len(fund_names)) / len(fund_names)
    weight_records = []
    for i, fund in enumerate(fund_names):
        weight_records.append({
            'fund_name': fund,
            'equal_weight': round(equal_w[i] * 100, 2),
            'min_var_weight': round(min_var_opt.x[i] * 100, 2),
            'max_sharpe_weight': round(max_sharpe_opt.x[i] * 100, 2)
        })
    
    weights_table = pd.DataFrame(weight_records)
    csv_path = OUTPUT_DIR / 'efficient_frontier_weights.csv'
    weights_table.to_csv(csv_path, index=False)
    print(f'💾 Weights saved to: {csv_path}')
    
    # Print summary
    mvp_r, mvp_v, mvp_s = calc_portfolio_stats(min_var_opt.x, mean_rets, cov_matrix)
    msr_r, msr_v, msr_s = calc_portfolio_stats(max_sharpe_opt.x, mean_rets, cov_matrix)
    
    print('\n' + '='*50)
    print('📈 OPTIMIZATION RESULTS')
    print('='*50)
    print(f'Minimum Variance Portfolio: Return {mvp_r*100:.1f}% | Risk {mvp_v*100:.1f}% | Sharpe {mvp_s:.3f}')
    print(f'Max Sharpe Portfolio:       Return {msr_r*100:.1f}% | Risk {msr_v*100:.1f}% | Sharpe {msr_s:.3f}')
    print('\nDetailed Weights:')
    print(weights_table.to_string(index=False))


if __name__ == '__main__':
    main()