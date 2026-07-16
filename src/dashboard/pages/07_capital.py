import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from src.dashboard.utils.db import get_ratios, get_companies, get_sectors, get_db_connection

st.set_page_config(page_title="Capital Allocation", layout="wide")
st.title("Capital Allocation Map 🧩")
st.markdown("Visualizing how the Nifty 100 deploys capital using fundamental algorithmic signatures.")

@st.cache_data(ttl=600)
def load_capital_data():
    conn = get_db_connection()
    ratios = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    conn.close()
    
    if ratios.empty: return pd.DataFrame()
    
    ratios['year_str'] = ratios['year'].astype(str)
    
    # THE FIX: Use regex to extract only valid 4-digit years, convert to int to find the true max, then back to string
    valid_years = ratios['year_str'].str.extract(r'^(\d{4})')[0].dropna()
    if not valid_years.empty:
        latest_year_base = str(valid_years.astype(int).max())
        # Filter rows that start with the true maximum year (e.g., '2023' or '2024')
        ratios = ratios[ratios['year_str'].str.startswith(latest_year_base)]
    
    companies = get_companies()
    sectors = get_sectors()
    
    df = pd.merge(ratios, companies[['id', 'company_name']], left_on='company_id', right_on='id', how='left')
    df = pd.merge(df, sectors, on='company_id', how='left')
    
    # --- ALGORITHMIC CLASSIFIER ---
    def classify_allocation(row):
        div = row.get('dividend_payout_ratio_pct', 0)
        fcf = row.get('free_cash_flow_cr', 0)
        de = row.get('debt_to_equity', 1)
        gro = row.get('revenue_cagr_5yr', 0)
        roe = row.get('return_on_equity_pct', 0)
        
        div = 0 if pd.isna(div) else div
        fcf = 0 if pd.isna(fcf) else fcf
        de = 0 if pd.isna(de) else de
        gro = 0 if pd.isna(gro) else gro
        
        if div > 40 and fcf > 0: return "Aggressive Dividend Payers"
        if de == 0 and fcf > 1000: return "Cash Hoarders (Debt-Free)"
        if gro > 15 and fcf < 0: return "Growth / Heavy Reinvestment"
        if de > 2 and fcf > 0: return "Leveraged (Paying down Debt)"
        if de > 2 and fcf <= 0: return "Distressed / Highly Leveraged"
        if roe > 20 and fcf > 0 and div <= 40: return "Efficient Compounders"
        if roe < 10 and fcf > 0: return "Value Traps / Stagnant"
        return "Balanced Allocators"

    df['allocation_pattern'] = df.apply(classify_allocation, axis=1)
    df['weight'] = 1 
    
    return df

df = load_capital_data()

if df.empty:
    st.error("Data not available.")
    st.stop()

# --- TREEMAP CHART ---
fig = px.treemap(
    df,
    path=['allocation_pattern', 'company_id'],
    values='weight',
    color='allocation_pattern',
    hover_data=['company_name', 'broad_sector', 'return_on_equity_pct'],
    color_discrete_sequence=px.colors.qualitative.Set2
)
fig.update_layout(margin=dict(t=20, l=10, r=10, b=10), height=600)
st.plotly_chart(fig, use_container_width=True)

# --- DETAILED VIEW ---
st.markdown("### View Pattern Components")
patterns = sorted(df['allocation_pattern'].unique())
selected_pattern = st.selectbox("Select a pattern to view companies:", patterns)

pattern_df = df[df['allocation_pattern'] == selected_pattern]
display_cols = ['company_id', 'company_name', 'broad_sector', 'return_on_equity_pct', 'debt_to_equity', 'free_cash_flow_cr']
st.dataframe(pattern_df[display_cols].sort_values('return_on_equity_pct', ascending=False), hide_index=True, use_container_width=True)
