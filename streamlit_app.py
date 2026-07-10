"""
streamlit_app.py
-----------------
Bonus B2 — Bluestock Fintech Mutual Fund Analytics Capstone

Streamlit web app — alternative to Power BI dashboard.
Covers all 4 dashboard pages with interactive filters.

Usage (run from project root):
    streamlit run streamlit_app.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bluestock Fintech — MF Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent

# ── COLOUR PALETTE ────────────────────────────────────────────────────────────
NAVY   = "#0D2B55"
TEAL   = "#0077B6"
ACCENT = "#00B4D8"
BG     = "#F6F9FC"
CARD   = "#FFFFFF"
GRID   = "#E7EDF3"

# ── Global styling (CSS) ──────────────────────────────────────────────────────
st.markdown(f"""
<style>
    html, body, [class*="css"] {{
        font-family: 'Segoe UI', 'Inter', sans-serif;
    }}
    .main {{
        background-color: {BG};
    }}
    h1 {{
        color: {NAVY};
        font-weight: 700;
        padding-bottom: 0px;
    }}
    h2, h3 {{
        color: {NAVY};
    }}
    div[data-testid="stMetric"] {{
        background-color: {CARD};
        border: 1px solid {GRID};
        border-radius: 10px;
        padding: 14px 16px 10px 16px;
        box-shadow: 0 1px 3px rgba(13, 43, 85, 0.06);
    }}
    div[data-testid="stMetricLabel"] {{
        color: #5A6B85;
        font-weight: 600;
    }}
    div[data-testid="stMetricValue"] {{
        color: {NAVY};
    }}
    div[data-testid="stVerticalBlock"] div[data-testid="stPlotlyChart"],
    div[data-testid="stDataFrame"] {{
        background-color: {CARD};
        border: 1px solid {GRID};
        border-radius: 10px;
        padding: 6px;
    }}
    section[data-testid="stSidebar"] {{
        background-color: {NAVY};
    }}
    section[data-testid="stSidebar"] * {{
        color: #EAF2FB !important;
    }}
    section[data-testid="stSidebar"] div[role="radiogroup"] label {{
        background-color: rgba(255,255,255,0.06);
        border-radius: 8px;
        padding: 8px 10px;
        margin-bottom: 4px;
    }}
    hr {{
        border-color: {GRID};
    }}
</style>
""", unsafe_allow_html=True)

# ── Consistent chart theme ────────────────────────────────────────────────────
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = [TEAL, NAVY, ACCENT, "#2DC653", "#F4A300"]

def style_fig(fig):
    """Apply a shared, understated look to every chart."""
    fig.update_layout(
        font=dict(family="Segoe UI, sans-serif", color=NAVY, size=12),
        title_font=dict(color=NAVY),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=NAVY)),
        plot_bgcolor=CARD,
        paper_bgcolor=CARD,
        margin=dict(t=30, b=20, l=10, r=10),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False,
                      tickfont=dict(color=NAVY), title_font=dict(color=NAVY))
    fig.update_yaxes(gridcolor=GRID, zeroline=False,
                      tickfont=dict(color=NAVY), title_font=dict(color=NAVY))
    fig.update_coloraxes(colorbar=dict(tickfont=dict(color=NAVY),
                                         title_font=dict(color=NAVY)))
    return fig

# ── Load data (cached) ────────────────────────────────────────────────────────
@st.cache_data
def load_all():
    raw = BASE_DIR / "data" / "raw"
    processed = BASE_DIR / "data" / "processed"

    fm = pd.read_csv(processed / "01_fund_master_cleaned.csv")
    nav = pd.read_csv(processed / "02_nav_history_cleaned.csv", parse_dates=["date"])
    aum = pd.read_csv(processed / "03_aum_by_fund_house_cleaned.csv", parse_dates=["date"])
    sip = pd.read_csv(processed / "04_monthly_sip_inflows_cleaned.csv")
    sip["month_dt"] = pd.to_datetime(sip["date"], format="%Y-%m", errors='coerce')
    cat = pd.read_csv(processed / "05_category_inflows_cleaned.csv")
    folio = pd.read_csv(processed / "06_industry_folio_count_cleaned.csv")
    folio["month_dt"] = pd.to_datetime(folio["date"], format="%Y-%m", errors='coerce')
    tx = pd.read_csv(processed / "08_investor_transactions_cleaned.csv",
                      parse_dates=["date"])
    perf = pd.read_csv(processed / "07_scheme_performance_cleaned.csv")
    holdings = pd.read_csv(processed / "09_portfolio_holdings_cleaned.csv")
    bench = pd.read_csv(processed / "10_benchmark_indices_cleaned.csv", parse_dates=["date"])
    sc = pd.read_csv(processed / "fund_scorecard.csv")
    var_df = pd.read_csv(processed / "var_cvar_report.csv")

    nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()
    return fm, nav, aum, sip, cat, folio, tx, perf, holdings, bench, sc, var_df

fm, nav, aum, sip, cat, folio, tx, perf, holdings, bench, sc, var_df = load_all()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.image("https://img.shields.io/badge/Bluestock-Fintech-0077B6?style=for-the-badge",
                  use_container_width=True)
st.sidebar.title("📊 MF Analytics Platform")
st.sidebar.markdown("**Bluestock Fintech | Capstone 2026**")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigate",
    ["🏭 Industry Overview",
     "📈 Fund Performance",
     "👥 Investor Analytics",
     "💹 SIP & Market Trends"],
    index=0
)

st.sidebar.divider()
st.sidebar.caption("Data: AMFI India | mfapi.in | Jan 2022 – May 2026")
st.sidebar.caption("Built by Pavan Kumar Koti | Intern Cohort 2025")


# ============================================================================
# PAGE 1 — INDUSTRY OVERVIEW
# ============================================================================
if page == "🏭 Industry Overview":
    st.title("🏭 Industry Overview")
    st.caption("Indian Mutual Fund Industry — Key Metrics & Trends (2022-2025)")

    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total AUM",       f"Rs. {aum['aum_crore'].sum()/1e5:.1f}L Cr",  "from all fund houses")
    c2.metric("Latest SIP Inflow", f"Rs. {sip['sip_inflow_crore'].iloc[-1]:,.0f} Cr", f"Month: {sip['date'].iloc[-1]}")
    c3.metric("Total Folios",    f"{folio['total_folios_crore'].iloc[-1]:.2f} Cr", "crore investor accounts")
    c4.metric("Active SIP Accounts", f"{sip['active_sip_accounts_crore'].iloc[-1]:.2f} Cr", "crore accounts")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📈 Industry AUM Trend")
        aum_trend = aum.groupby("date", as_index=False)["aum_crore"].sum()
        fig = px.line(aum_trend, x="date", y="aum_crore",
                       labels={"aum_crore": "Total AUM (Rs. crore)", "date": "Date"},
                       color_discrete_sequence=[TEAL])
        fig.update_layout(height=350, margin=dict(t=20, b=20))
        st.plotly_chart(style_fig(fig), use_container_width=True, theme=None)

    with col2:
        st.subheader("🏦 AUM by Fund House (Latest)")
        latest_date = aum["date"].max()
        aum_latest = aum[aum["date"] == latest_date].sort_values("aum_crore", ascending=True)
        fig = px.bar(aum_latest, x="aum_crore", y="fund_house", orientation="h",
                      labels={"aum_crore": "AUM (Rs. crore)", "fund_house": ""},
                      color="aum_crore", color_continuous_scale="Blues")
        fig.update_layout(height=350, margin=dict(t=20, b=20), showlegend=False)
        st.plotly_chart(style_fig(fig), use_container_width=True, theme=None)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("💰 Monthly SIP Inflows")
        fig = px.line(sip, x="month_dt", y="sip_inflow_crore",
                       labels={"sip_inflow_crore": "SIP Inflow (Rs. crore)", "month_dt": "Month"},
                       color_discrete_sequence=[ACCENT])
        peak = sip.loc[sip["sip_inflow_crore"].idxmax()]
        fig.add_annotation(x=peak["month_dt"], y=peak["sip_inflow_crore"],
                            text=f"ATH: Rs.{peak['sip_inflow_crore']:,} Cr",
                            showarrow=True, arrowhead=2, ay=-30)
        fig.update_layout(height=320, margin=dict(t=20, b=20))
        st.plotly_chart(style_fig(fig), use_container_width=True, theme=None)

    with col4:
        st.subheader("📊 Total Folio Count Growth")
        fig = px.line(folio, x="month_dt", y="total_folios_crore",
                       labels={"total_folios_crore": "Folios (crore)", "month_dt": "Month"},
                       color_discrete_sequence=["#2DC653"])
        fig.update_layout(height=320, margin=dict(t=20, b=20))
        st.plotly_chart(style_fig(fig), use_container_width=True, theme=None)


# ============================================================================
# PAGE 2 — FUND PERFORMANCE
# ============================================================================
elif page == "📈 Fund Performance":
    st.title("📈 Fund Performance Analytics")

    # Slicers
    col1, col2, col3 = st.columns(3)
    with col1:
        sel_house = st.multiselect("Fund House", sorted(fm["fund_house"].unique()),
                                    default=sorted(fm["fund_house"].unique()))
    with col2:
        sel_cat = st.multiselect("Category", sorted(fm["category"].unique()),
                                  default=sorted(fm["category"].unique()))
    with col3:
        sel_plan = st.multiselect("Plan", sorted(fm["plan"].unique()),
                                   default=sorted(fm["plan"].unique()))

    filtered_fm = fm[
        fm["fund_house"].isin(sel_house) &
        fm["category"].isin(sel_cat) &
        fm["plan"].isin(sel_plan)
    ]
    filtered_sc = sc[sc["amfi_code"].isin(filtered_fm["amfi_code"])]

    st.divider()
    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.subheader("🎯 Return vs Risk Scatter")
        fig = px.scatter(filtered_sc, x="3Y CAGR (%)", y="Sharpe Ratio",
                          size="Final_Score (0-100)", color="Final_Score (0-100)",
                          hover_name="Scheme Name",
                          labels={"3Y CAGR (%)": "3Y CAGR (%)",
                                   "Sharpe Ratio": "Sharpe Ratio",
                                   "Final_Score (0-100)": "Final_Score (0-100)"},
                          color_continuous_scale="Blues", size_max=25)
        fig.update_layout(height=380, margin=dict(t=20, b=20))
        st.plotly_chart(style_fig(fig), use_container_width=True, theme=None)

    with col2:
        st.subheader("🏆 Fund Scorecard")
        display_cols = ["Scheme Name", "Final_Score (0-100)", "3Y CAGR (%)", "Sharpe Ratio", "Max Drawdown (%)"]
        st.dataframe(
            filtered_sc[display_cols].rename(columns={
                "Scheme Name": "Fund", "Final_Score (0-100)": "Score",
                "3Y CAGR (%)": "3yr CAGR%", "Sharpe Ratio": "Sharpe",
                "Max Drawdown (%)": "Max DD%"
            }).round(2),
            use_container_width=True, height=380
        )

    st.subheader("📉 NAV History — Fund vs Benchmark")
    sel_fund_name = st.selectbox("Select Fund",
                                   sorted(filtered_fm["scheme_name"].tolist()), index=0)
    sel_fund_code = filtered_fm[filtered_fm["scheme_name"] == sel_fund_name]["amfi_code"].values[0]
    sel_bench = st.selectbox("Select Benchmark",
                               sorted(bench["index_name"].unique()), index=1)

    fund_nav_filtered = nav[nav["amfi_code"] == sel_fund_code].sort_values("date")
    bench_filtered = bench[bench["index_name"] == sel_bench].sort_values("date")

    if not fund_nav_filtered.empty and not bench_filtered.empty:
        nav_norm = fund_nav_filtered["nav"] / fund_nav_filtered["nav"].iloc[0] * 100
        bench_norm = bench_filtered["close_value"] / bench_filtered["close_value"].iloc[0] * 100

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=fund_nav_filtered["date"], y=nav_norm,
                                  name=sel_fund_name[:35], line=dict(color=TEAL, width=2)))
        fig.add_trace(go.Scatter(x=bench_filtered["date"], y=bench_norm,
                                  name=sel_bench, line=dict(color="gray", width=1.5, dash="dash")))
        fig.update_layout(height=320, margin=dict(t=20, b=20),
                           yaxis_title="Normalized Value (Start=100)",
                           xaxis_title="Date")
        st.plotly_chart(style_fig(fig), use_container_width=True, theme=None)


# ============================================================================
# PAGE 3 — INVESTOR ANALYTICS
# ============================================================================
elif page == "👥 Investor Analytics":
    st.title("👥 Investor Analytics")

    # Slicers
    col1, col2, col3 = st.columns(3)
    with col1:
        sel_state = st.multiselect("State", sorted(tx["state"].unique()),
                                    default=sorted(tx["state"].unique()))
    with col2:
        sel_age = st.multiselect("Age Group", sorted(tx["age_group"].unique()),
                                  default=sorted(tx["age_group"].unique()))
    with col3:
        sel_tier = st.multiselect("City Tier", sorted(tx["city_tier"].unique()),
                                   default=sorted(tx["city_tier"].unique()))

    filtered_tx = tx[
        tx["state"].isin(sel_state) &
        tx["age_group"].isin(sel_age) &
        tx["city_tier"].isin(sel_tier)
    ]

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🗺️ SIP Amount by State")
        sip_state = (filtered_tx[filtered_tx["transaction_type"] == "SIP"]
                      .groupby("state", as_index=False)["amount_inr"].sum()
                      .sort_values("amount_inr"))
        fig = px.bar(sip_state, x="amount_inr", y="state", orientation="h",
                      labels={"amount_inr": "Total SIP Amount (Rs.)", "state": ""},
                      color="amount_inr", color_continuous_scale="Blues")
        fig.update_layout(height=370, margin=dict(t=20, b=20), showlegend=False)
        st.plotly_chart(style_fig(fig), use_container_width=True, theme=None)

    with col2:
        st.subheader("🍩 Transaction Type Split")
        tx_split = filtered_tx.groupby("transaction_type")["amount_inr"].sum().reset_index()
        fig = px.pie(tx_split, values="amount_inr", names="transaction_type",
                      hole=0.45, color_discrete_sequence=[NAVY, TEAL, ACCENT])
        fig.update_layout(height=370, margin=dict(t=20, b=20))
        st.plotly_chart(style_fig(fig), use_container_width=True, theme=None)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("👤 Avg SIP by Age Group")
        age_sip = (filtered_tx[filtered_tx["transaction_type"] == "SIP"]
                    .groupby("age_group", as_index=False)["amount_inr"].mean()
                    .sort_values("age_group"))
        fig = px.bar(age_sip, x="age_group", y="amount_inr",
                      labels={"amount_inr": "Avg SIP Amount (Rs.)", "age_group": "Age Group"},
                      color="amount_inr", color_continuous_scale="Blues")
        fig.update_layout(height=320, margin=dict(t=20, b=20), showlegend=False)
        st.plotly_chart(style_fig(fig), use_container_width=True, theme=None)

    with col4:
        st.subheader("📅 Monthly Transaction Volume")
        tx_monthly = (filtered_tx.groupby(
            filtered_tx["date"].dt.to_period("M"))
            .size().reset_index(name="count"))
        tx_monthly["month"] = tx_monthly["date"].astype(str)
        fig = px.line(tx_monthly, x="month", y="count",
                       labels={"count": "Transaction Count", "month": "Month"},
                       color_discrete_sequence=[ACCENT])
        fig.update_layout(height=320, margin=dict(t=20, b=20))
        st.plotly_chart(style_fig(fig), use_container_width=True, theme=None)


# ============================================================================
# PAGE 4 — SIP & MARKET TRENDS
# ============================================================================
elif page == "💹 SIP & Market Trends":
    st.title("💹 SIP & Market Trends")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 SIP Inflow vs Nifty 50")
        nifty50 = bench[bench["index_name"] == "NIFTY50"].sort_values("date")
        sip_plot = sip.sort_values("month_dt")

        fig = go.Figure()
        fig.add_trace(go.Bar(x=sip_plot["month_dt"], y=sip_plot["sip_inflow_crore"],
                              name="SIP Inflow (Cr)", marker_color=TEAL, opacity=0.8))
        fig.add_trace(go.Scatter(x=nifty50["date"], y=nifty50["close_value"],
                                  name="Nifty 50", yaxis="y2",
                                  line=dict(color="orange", width=2)))
        fig.update_layout(
            yaxis=dict(title="SIP Inflow (Rs. crore)"),
            yaxis2=dict(title="Nifty 50", overlaying="y", side="right"),
            height=370, margin=dict(t=20, b=20),
            legend=dict(x=0.01, y=0.99)
        )
        st.plotly_chart(style_fig(fig), use_container_width=True, theme=None)

    with col2:
        st.subheader("🌡️ Category Inflow Heatmap")
        pivot = cat.pivot(index="category", columns="date", values="net_inflow_crore").fillna(0)
        fig = px.imshow(pivot, aspect="auto", color_continuous_scale="RdYlGn",
                         labels={"color": "Net Inflow (Cr)"})
        fig.update_layout(height=370, margin=dict(t=20, b=20))
        st.plotly_chart(style_fig(fig), use_container_width=True, theme=None)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("🏆 Top 5 Categories by Net Inflow FY25")
        top_cat = cat.groupby("category", as_index=False)["net_inflow_crore"].sum()
        top_cat = top_cat.nlargest(5, "net_inflow_crore").sort_values("net_inflow_crore")
        fig = px.bar(top_cat, x="net_inflow_crore", y="category", orientation="h",
                      labels={"net_inflow_crore": "Net Inflow (Rs. crore)", "category": ""},
                      color="net_inflow_crore", color_continuous_scale="Blues")
        fig.update_layout(height=320, margin=dict(t=20, b=20), showlegend=False)
        st.plotly_chart(style_fig(fig), use_container_width=True, theme=None)

    with col4:
        st.subheader("📈 Active SIP Accounts Growth")
        fig = px.line(sip, x="month_dt", y="active_sip_accounts_crore",
                       labels={"active_sip_accounts_crore": "Active SIP Accounts (crore)",
                                "month_dt": "Month"},
                       color_discrete_sequence=["#2DC653"])
        fig.update_layout(height=320, margin=dict(t=20, b=20))
        st.plotly_chart(style_fig(fig), use_container_width=True, theme=None)