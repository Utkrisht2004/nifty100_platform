import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
)
from src.dashboard.utils.db import get_db_connection

st.set_page_config(page_title="Sector Analysis", layout="wide")
st.title("Sector Analysis & Positioning 🏢")


# --- LOAD SECTOR DATA ---
@st.cache_data(ttl=600)
def load_sector_data():
    conn = get_db_connection()
    query = """
    SELECT r.company_id, r.return_on_equity_pct, r.net_profit_margin_pct, r.debt_to_equity,
           pl.sales, s.broad_sector, s.sub_sector, m.market_cap_crore
    FROM financial_ratios r
    JOIN profitandloss pl ON r.company_id = pl.company_id AND r.year = pl.year
    JOIN sectors s ON r.company_id = s.company_id
    LEFT JOIN market_cap m ON r.company_id = m.company_id AND r.year = m.year
    WHERE r.year = (SELECT MAX(year) FROM financial_ratios r2 WHERE r.company_id = r2.company_id)
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


df = load_sector_data()

if df.empty:
    st.error("Sector data could not be loaded.")
    st.stop()

# --- UI ---
sectors = sorted(df["broad_sector"].dropna().unique())
selected_sector = st.selectbox("Select a Broad Sector to Analyze:", sectors)

sector_df = df[df["broad_sector"] == selected_sector].copy()

# Fill missing market cap with a baseline so bubbles render
sector_df["market_cap_crore"] = sector_df["market_cap_crore"].fillna(
    sector_df["market_cap_crore"].median() or 5000
)

st.markdown("---")
st.subheader(f"{selected_sector} Landscape")
st.markdown(
    "X-Axis: Revenue (Size) | Y-Axis: ROE (Quality) | Bubble Size: Market Cap | Color: Sub-Sector"
)

# --- BUBBLE CHART ---
fig = px.scatter(
    sector_df,
    x="sales",
    y="return_on_equity_pct",
    size="market_cap_crore",
    color="sub_sector",
    hover_name="company_id",
    log_x=True,  # Log scale for revenue handles massive differences (e.g., Reliance vs peers)
    size_max=60,
    labels={
        "sales": "Revenue (₹ Cr) [Log Scale]",
        "return_on_equity_pct": "Return on Equity (%)",
        "sub_sector": "Sub Sector",
    },
)
fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=500)
st.plotly_chart(fig, use_container_width=True)

# --- SECTOR MEDIANS ---
st.markdown("### Sub-Sector Median KPIs")
medians = (
    sector_df.groupby("sub_sector")[
        ["return_on_equity_pct", "net_profit_margin_pct", "debt_to_equity"]
    ]
    .median()
    .reset_index()
)

bar_fig = px.bar(
    medians,
    x="sub_sector",
    y="return_on_equity_pct",
    title="Median ROE by Sub-Sector",
    labels={"return_on_equity_pct": "Median ROE (%)", "sub_sector": ""},
    color="return_on_equity_pct",
    color_continuous_scale="Viridis",
)
bar_fig.update_layout(showlegend=False, margin=dict(t=40, b=20, l=20, r=20))
st.plotly_chart(bar_fig, use_container_width=True)
