# Bluestock Mutual Fund Analytics Platform

## Data Dictionary

### Dataset: 01_fund_master.csv

| Column Name        | Data Type | Description                                              |
| ------------------ | --------- | -------------------------------------------------------- |
| amfi_code          | INTEGER   | Unique AMFI scheme identifier                            |
| fund_house         | TEXT      | Asset Management Company (AMC) name                      |
| scheme_name        | TEXT      | Official mutual fund scheme name                         |
| category           | TEXT      | Fund category (Equity, Debt, Hybrid, etc.)               |
| sub_category       | TEXT      | Scheme sub-category (Large Cap, Small Cap, Liquid, etc.) |
| plan               | TEXT      | Direct or Regular plan                                   |
| launch_date        | DATE      | Scheme launch date                                       |
| benchmark          | TEXT      | Benchmark index                                          |
| expense_ratio_pct  | REAL      | Annual expense ratio (%)                                 |
| exit_load_pct      | REAL      | Exit load percentage                                     |
| min_sip_amount     | REAL      | Minimum SIP investment amount                            |
| min_lumpsum_amount | REAL      | Minimum lumpsum investment amount                        |
| fund_manager       | TEXT      | Fund manager name                                        |
| risk_category      | TEXT      | Risk classification                                      |
| sebi_category_code | TEXT      | SEBI category code                                       |

---

### Dataset: 02_nav_history.csv

| Column Name | Data Type | Description                   |
| ----------- | --------- | ----------------------------- |
| amfi_code   | INTEGER   | Mutual fund scheme identifier |
| date        | DATE      | NAV date                      |
| nav         | REAL      | Net Asset Value               |

---

### Dataset: 03_aum_by_fund_house.csv

| Column Name    | Data Type | Description                           |
| -------------- | --------- | ------------------------------------- |
| date           | DATE      | Reporting date                        |
| fund_house     | TEXT      | Asset Management Company              |
| aum_lakh_crore | REAL      | Assets Under Management in lakh crore |
| aum_crore      | REAL      | Assets Under Management in crore      |
| num_schemes    | INTEGER   | Number of schemes managed             |

---

### Dataset: 07_scheme_performance.csv

| Column Name        | Data Type | Description                      |
| ------------------ | --------- | -------------------------------- |
| amfi_code          | INTEGER   | Scheme identifier                |
| scheme_name        | TEXT      | Mutual fund scheme name          |
| fund_house         | TEXT      | AMC name                         |
| category           | TEXT      | Fund category                    |
| plan               | TEXT      | Direct/Regular                   |
| return_1yr_pct     | REAL      | 1-Year Return (%)                |
| return_3yr_pct     | REAL      | 3-Year CAGR (%)                  |
| return_5yr_pct     | REAL      | 5-Year CAGR (%)                  |
| benchmark_3yr_pct  | REAL      | Benchmark 3-Year Return (%)      |
| alpha              | REAL      | Excess return over benchmark     |
| beta               | REAL      | Market sensitivity               |
| sharpe_ratio       | REAL      | Risk-adjusted performance metric |
| sortino_ratio      | REAL      | Downside-risk-adjusted return    |
| std_dev_ann_pct    | REAL      | Annualized standard deviation    |
| max_drawdown_pct   | REAL      | Maximum drawdown (%)             |
| aum_crore          | REAL      | Scheme AUM in crore              |
| expense_ratio_pct  | REAL      | Expense ratio (%)                |
| morningstar_rating | INTEGER   | Morningstar rating (1–5)        |
| risk_grade         | TEXT      | Risk level                       |

---

### Dataset: 08_investor_transactions.csv

| Column Name        | Data Type | Description                       |
| ------------------ | --------- | --------------------------------- |
| investor_id        | TEXT      | Unique investor identifier        |
| transaction_date   | DATE      | Transaction date                  |
| amfi_code          | INTEGER   | Fund scheme identifier            |
| transaction_type   | TEXT      | SIP, Lumpsum, Redemption          |
| amount_inr         | REAL      | Transaction amount in INR         |
| state              | TEXT      | Investor state                    |
| city               | TEXT      | Investor city                     |
| city_tier          | TEXT      | T30 or B30 classification         |
| age_group          | TEXT      | Investor age bracket              |
| gender             | TEXT      | Investor gender                   |
| annual_income_lakh | REAL      | Annual income (₹ lakh)           |
| payment_mode       | TEXT      | UPI, Net Banking, Mandate, Cheque |
| kyc_status         | TEXT      | Verified or Pending               |

---

## Data Sources

* AMFI India
* mfapi.in
* NSE India
* BSE India
* Bluestock Fintech Capstone Dataset Pack

## Prepared For

Bluestock Fintech Pvt. Ltd.
Mutual Fund Analytics Platform Capstone Project
