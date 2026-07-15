import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from src.dashboard.utils.db import get_db_connection

st.set_page_config(page_title="Peer Comparison", layout="wide")
st.title("Sector Peer Comparison 🏢")

# --- LOAD DATA ---
@st.cache_data(ttl=600)
def load_peer_data():
    conn = get_db_connection()
    # Get all percentiles
    pct_df = pd.read_sql_query("SELECT * FROM peer_percentiles", conn)
    # Get raw ratios for the table
    ratios_df = pd.read_sql_query("""
        SELECT r.*, p.peer_group_name 
        FROM financial_ratios r
        JOIN (SELECT DISTINCT company_id, peer_group_name FROM peer_percentiles) p
          ON r.company_id = p.company_id
        WHERE r.year = (SELECT MAX(year) FROM financial_ratios r2 WHERE r.company_id = r2.company_id)
    """, conn)
    conn.close()
    return pct_df, ratios_df

pct_df, ratios_df = load_peer_data()

if pct_df.empty:
    st.error("No peer percentile data found. Please ensure Day 18 script ran.")
    st.stop()

# --- UI CONTROLS ---
groups = sorted(pct_df['peer_group_name'].dropna().unique())
selected_group = st.selectbox("Select Peer Group", groups)

group_pct_df = pct_df[pct_df['peer_group_name'] == selected_group]
group_ratios_df = ratios_df[ratios_df['peer_group_name'] == selected_group]

companies = sorted(group_pct_df['company_id'].unique())
selected_company = st.selectbox("Select Benchmark Company", companies)

st.markdown("---")
col_chart, col_table = st.columns([1, 1.2])

# --- RADAR CHART ---
with col_chart:
    st.subheader(f"{selected_company} vs {selected_group} Average")
    
    comp_data = group_pct_df[group_pct_df['company_id'] == selected_company]
    
    if not comp_data.empty:
        # We use standard 8 metrics for the radar
        metrics = ['return_on_equity_pct', 'roce_pct', 'net_profit_margin_pct', 'debt_to_equity', 
                   'free_cash_flow_cr', 'pat_cagr_5yr', 'revenue_cagr_5yr', 'asset_turnover']
        
        labels = ['ROE', 'ROCE', 'NPM', 'D/E (Inv)', 'FCF', 'PAT CAGR', 'Rev CAGR', 'Asset Turn']
        
        comp_vals = []
        for m in metrics:
            val = comp_data[comp_data['metric'] == m]['percentile_rank']
            comp_vals.append(val.iloc[0] if not val.empty else 50)
            
        # Peer average for percentiles is inherently ~50th percentile
        peer_vals = [50] * len(labels)
        
        # Close loops
        comp_vals += comp_vals[:1]
        peer_vals += peer_vals[:1]
        labels += labels[:1]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=peer_vals, theta=labels, fill='none', name='Group Median', line=dict(color='grey', dash='dash')))
        fig.add_trace(go.Scatterpolar(r=comp_vals, theta=labels, fill='toself', name=selected_company, line=dict(color='#1f77b4')))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            margin=dict(t=30, b=30, l=30, r=30)
        )
        st.plotly_chart(fig, use_container_width=True)

# --- KPI TABLE ---
with col_table:
    st.subheader(f"{selected_group} Raw Metrics")
    st.markdown("Row highlighted in **Gold** represents the highest ROE in the group.")
    
    display_cols = ['company_id', 'return_on_equity_pct', 'net_profit_margin_pct', 'debt_to_equity', 'revenue_cagr_5yr', 'pat_cagr_5yr']
    table_df = group_ratios_df[display_cols].copy()
    table_df = table_df.rename(columns={
        'company_id': 'Ticker', 'return_on_equity_pct': 'ROE (%)', 'net_profit_margin_pct': 'NPM (%)',
        'debt_to_equity': 'D/E', 'revenue_cagr_5yr': 'Rev CAGR', 'pat_cagr_5yr': 'PAT CAGR'
    })
    
    # Sort by ROE descending
    table_df = table_df.sort_values('ROE (%)', ascending=False).reset_index(drop=True)
    
    # Apply pandas Styler to highlight the first row (Max ROE)
    def highlight_benchmark(x):
        df1 = pd.DataFrame('', index=x.index, columns=x.columns)
        if not df1.empty:
            df1.iloc[0] = 'background-color: rgba(255, 215, 0, 0.2)' # Subtle Gold
        return df1
        
    st.dataframe(table_df.style.apply(highlight_benchmark, axis=None).format(precision=2), use_container_width=True, hide_index=True)
