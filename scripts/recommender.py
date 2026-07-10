"""
Mutual Fund Recommender System

A simple rule-based recommender that suggests top mutual funds based on user-specified 
risk level (Low / Moderate / High). 

It uses historical NAV data to compute annualized Sharpe ratios and ranks funds within 
each risk category. The system loads cleaned data from the processed directory and 
provides top-3 recommendations.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path


# ================= FILE PATHS =================
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = SCRIPT_DIR.parent / "data" / "processed"

NAV_PATH = DATA_DIR / "02_nav_history_cleaned.csv"
FUND_PATH = DATA_DIR / "01_fund_master_cleaned.csv"


# ================= LOAD DATA =================
def load_data():
    """Load NAV history and fund master data from processed files."""
    try:
        print("Loading data...")
        
        nav = pd.read_csv(NAV_PATH)
        fund = pd.read_csv(FUND_PATH)

        # Standardize AMFI codes
        nav['amfi_code'] = nav['amfi_code'].astype(str).str.strip()
        fund['amfi_code'] = fund['amfi_code'].astype(str).str.strip()

        print("Data loaded successfully")
        return nav, fund

    except Exception as e:
        print(f"Error loading data: {e}")
        return None, None


# ================= STANDARDIZE RISK CATEGORY =================
def standardize_risk_category(fund):
    """Standardize risk category values into consistent Low/Moderate/High groups."""
    risk_mapping = {
        'Low': ['Low', 'LOW'],
        'Moderate': ['Moderate', 'MODERATE'],
        'High': ['High', 'Very High', 'Moderately High', 'HIGH', 'VERY HIGH']
    }
    
    # Flatten mapping
    flat_mapping = {variant: standard 
                    for standard, variants in risk_mapping.items() 
                    for variant in variants}
    
    fund = fund.copy()
    fund['risk_category'] = fund['risk_category'].map(flat_mapping).fillna('Other').str.capitalize()
    
    return fund


# ================= COMPUTE RETURNS =================
def compute_returns(nav):
    """Compute daily returns for each fund and drop NaN values."""
    nav = nav.copy()
    nav['date'] = pd.to_datetime(nav['date'])
    nav = nav.sort_values(['amfi_code', 'date'])

    nav['return'] = nav.groupby('amfi_code')['nav'].pct_change()
    nav = nav.dropna(subset=['return'])

    return nav


# ================= CALCULATE SHARPE RATIO =================
def calculate_sharpe_ratio(nav):
    """Calculate annualized Sharpe ratio (rf=0) grouped by fund."""
    sharpe_df = nav.groupby('amfi_code')['return'].agg(['mean', 'std']).reset_index()

    # Annualized Sharpe Ratio (rf = 0)
    sharpe_df['sharpe_ratio'] = (sharpe_df['mean'] / sharpe_df['std']) * np.sqrt(252)

    # Convert for consistent merging
    sharpe_df['amfi_code'] = pd.to_numeric(sharpe_df['amfi_code'], errors='coerce').astype('Int64')

    return sharpe_df


# ================= RECOMMENDER =================
def recommend_funds(risk_level, nav, fund):
    """
    Recommend top 3 funds for a given risk level based on Sharpe ratio.
    
    Returns:
        DataFrame with top recommendations or empty DataFrame if none found.
    """
    try:
        risk_level = risk_level.strip().capitalize()
        if risk_level not in ['Low', 'Moderate', 'High']:
            print(f"Warning: Invalid risk level '{risk_level}'. Using 'Moderate'.")
            risk_level = 'Moderate'

        # Ensure consistent data types
        nav = nav.copy()
        fund = fund.copy()
        
        nav['amfi_code'] = nav['amfi_code'].astype(str)
        fund['amfi_code'] = pd.to_numeric(fund['amfi_code'], errors='coerce').astype('Int64')

        # Calculate Sharpe ratios
        sharpe_df = calculate_sharpe_ratio(nav)

        # Merge with fund details
        final_df = sharpe_df.merge(
            fund[['amfi_code', 'scheme_name', 'risk_category']],
            on='amfi_code',
            how='inner'
        )

        # Filter by risk level
        filtered = final_df[final_df['risk_category'].str.lower() == risk_level.lower()]

        if filtered.empty:
            print(f"No funds found for risk level: {risk_level}")
            return pd.DataFrame()

        # Top 3 funds by Sharpe ratio
        top3 = filtered.nlargest(3, 'sharpe_ratio')

        return top3[['amfi_code', 'scheme_name', 'risk_category', 'sharpe_ratio']]

    except Exception as e:
        print(f"Error in recommendation: {e}")
        return pd.DataFrame()


# ================= MAIN =================
if __name__ == "__main__":
    nav, fund = load_data()

    if nav is None or fund is None:
        print("Exiting due to data loading error.")
        exit()

    # Preprocess data
    nav = compute_returns(nav)
    fund = standardize_risk_category(fund)

    print("\n" + "="*60)
    print(" MUTUAL FUND RECOMMENDER")
    print("="*60)
    
    risk_input = input("\nEnter Risk Level (Low / Moderate / High): ").strip()

    recommendations = recommend_funds(risk_input, nav, fund)

    if not recommendations.empty:
        print("\n Top 3 Recommended Funds:\n")
        print(recommendations.to_string(index=False, float_format="{:.4f}".format))
    else:
        print("\n No recommendations available.")

    print("\n" + "="*60)
    print(" Recommender Completed")