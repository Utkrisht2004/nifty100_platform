import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
)
from src.dashboard.utils.db import get_db_connection, get_companies
from src.screener.scoring import calculate_composite_score

st.set_page_config(page_title="Screener", layout="wide")
st.title("Interactive Stock Screener 🔎")


# --- LOAD LATEST DATA ---
@st.cache_data(ttl=600)
def load_screener_data():
    conn = get_db_connection()
    # Fetch latest year data with market metrics
    query = """
    SELECT r.*, s.broad_sector, m.pe_ratio, m.pb_ratio, m.dividend_yield_pct
    FROM financial_ratios r
    LEFT JOIN sectors s ON r.company_id = s.company_id
    LEFT JOIN market_cap m ON r.company_id = m.company_id AND r.year = m.year
    WHERE r.year = (SELECT MAX(year) FROM financial_ratios r2 WHERE r.company_id = r2.company_id)
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    companies = get_companies()
    df = pd.merge(
        df,
        companies[["id", "company_name"]],
        left_on="company_id",
        right_on="id",
        how="left",
    )
    df = calculate_composite_score(df)
    return df


df = load_screener_data()

if df.empty:
    st.error("Screener data could not be loaded.")
    st.stop()

# --- PRESET LOGIC (SESSION STATE) ---
presets = {
    "Quality Compounder": {
        "roe": 15.0,
        "de": 1.0,
        "fcf": 0.0,
        "rev_cagr": 10.0,
        "pat_cagr": 0.0,
        "opm": 0.0,
        "pe": 100.0,
        "pb": 20.0,
        "div": 0.0,
        "icr": 0.0,
    },
    "Value Pick": {
        "roe": 0.0,
        "de": 2.0,
        "fcf": -1000.0,
        "rev_cagr": 0.0,
        "pat_cagr": 0.0,
        "opm": 0.0,
        "pe": 20.0,
        "pb": 3.0,
        "div": 1.0,
        "icr": 0.0,
    },
    "Growth Accelerator": {
        "roe": 0.0,
        "de": 2.0,
        "fcf": -1000.0,
        "rev_cagr": 15.0,
        "pat_cagr": 20.0,
        "opm": 0.0,
        "pe": 100.0,
        "pb": 20.0,
        "div": 0.0,
        "icr": 0.0,
    },
    "Dividend Champion": {
        "roe": 0.0,
        "de": 5.0,
        "fcf": 0.0,
        "rev_cagr": 0.0,
        "pat_cagr": 0.0,
        "opm": 0.0,
        "pe": 100.0,
        "pb": 20.0,
        "div": 2.0,
        "icr": 0.0,
    },
    "Debt-Free Blue Chip": {
        "roe": 12.0,
        "de": 0.0,
        "fcf": -1000.0,
        "rev_cagr": 0.0,
        "pat_cagr": 0.0,
        "opm": 0.0,
        "pe": 100.0,
        "pb": 20.0,
        "div": 0.0,
        "icr": 0.0,
    },
    "Reset Filters": {
        "roe": -50.0,
        "de": 10.0,
        "fcf": -50000.0,
        "rev_cagr": -50.0,
        "pat_cagr": -50.0,
        "opm": -50.0,
        "pe": 200.0,
        "pb": 50.0,
        "div": 0.0,
        "icr": -10.0,
    },
}


def set_preset(preset_name):
    for key, val in presets[preset_name].items():
        st.session_state[key] = val


# Initialize session state if empty
if "roe" not in st.session_state:
    set_preset("Reset Filters")

# --- SIDEBAR UI ---
st.sidebar.header("Strategy Presets")
preset_cols = st.sidebar.columns(2)
for i, (p_name, p_vals) in enumerate(presets.items()):
    preset_cols[i % 2].button(p_name, on_click=set_preset, args=(p_name,))

st.sidebar.markdown("---")
st.sidebar.header("Custom Metrics")

# Sliders bound to session_state keys
st.sidebar.slider("Min ROE (%)", -50.0, 50.0, key="roe", step=1.0)
st.sidebar.slider("Max D/E Ratio", 0.0, 10.0, key="de", step=0.1)
st.sidebar.slider("Min FCF (Cr)", -50000.0, 50000.0, key="fcf", step=100.0)
st.sidebar.slider("Min Rev CAGR (%)", -50.0, 50.0, key="rev_cagr", step=1.0)
st.sidebar.slider("Min PAT CAGR (%)", -50.0, 50.0, key="pat_cagr", step=1.0)
st.sidebar.slider("Min OPM (%)", -50.0, 50.0, key="opm", step=1.0)
st.sidebar.slider("Max P/E Ratio", 0.0, 200.0, key="pe", step=1.0)
st.sidebar.slider("Max P/B Ratio", 0.0, 50.0, key="pb", step=0.5)
st.sidebar.slider("Min Dividend Yield (%)", 0.0, 10.0, key="div", step=0.1)
st.sidebar.slider("Min ICR", -10.0, 50.0, key="icr", step=1.0)

# --- APPLY FILTERS ---
filtered_df = df.copy()

# Fill NAs temporarily for filtering
filtered_df["pe_ratio"] = filtered_df["pe_ratio"].fillna(999)
filtered_df["pb_ratio"] = filtered_df["pb_ratio"].fillna(999)
filtered_df["dividend_yield_pct"] = filtered_df["dividend_yield_pct"].fillna(0)

# Math filters
filtered_df = filtered_df[
    (filtered_df["return_on_equity_pct"] >= st.session_state.roe)
    & (filtered_df["free_cash_flow_cr"] >= st.session_state.fcf)
    & (filtered_df["revenue_cagr_5yr"] >= st.session_state.rev_cagr)
    & (filtered_df["pat_cagr_5yr"] >= st.session_state.pat_cagr)
    & (filtered_df["operating_profit_margin_pct"] >= st.session_state.opm)
    & (filtered_df["pe_ratio"] <= st.session_state.pe)
    & (filtered_df["pb_ratio"] <= st.session_state.pb)
    & (filtered_df["dividend_yield_pct"] >= st.session_state.div)
]

# Edge case: D/E ignores Financials
filtered_df = filtered_df[
    (filtered_df["debt_to_equity"] <= st.session_state.de)
    | (filtered_df["broad_sector"] == "Financials")
    | (filtered_df["debt_to_equity"].isna())
]

# Edge case: ICR allows Debt Free
filtered_df = filtered_df[
    (filtered_df["interest_coverage"] >= st.session_state.icr)
    | (filtered_df["icr_label"] == "Debt Free")
    | (filtered_df["interest_coverage"].isna())
]

# --- DISPLAY RESULTS ---
st.subheader(f"Results: {len(filtered_df)} companies match your filters")

display_cols = [
    "company_id",
    "company_name",
    "broad_sector",
    "composite_quality_score",
    "return_on_equity_pct",
    "debt_to_equity",
    "free_cash_flow_cr",
    "pe_ratio",
]
clean_df = filtered_df[
    [c for c in display_cols if c in filtered_df.columns]
].sort_values("composite_quality_score", ascending=False)

st.dataframe(clean_df, use_container_width=True, hide_index=True)

# --- CSV DOWNLOAD ---
csv = clean_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Download Results as CSV",
    data=csv,
    file_name="screener_results.csv",
    mime="text/csv",
)
