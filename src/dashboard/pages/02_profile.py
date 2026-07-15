import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from src.dashboard.utils.db import get_companies, get_sectors, get_ratios, get_pl

st.set_page_config(page_title="Company Profile", layout="wide")
st.title("Company Profile 🏢")

# Load baseline data
companies_df = get_companies()
sectors_df = get_sectors()

if companies_df.empty:
    st.error("Database connection error or empty companies table.")
    st.stop()

# Formatting for search dropdown
companies_df['search_key'] = companies_df['id'] + " - " + companies_df['company_name']
search_options = [""] + companies_df['search_key'].tolist()

selected_search = st.selectbox("Search for a company (Ticker or Name):", options=search_options)

if selected_search:
    ticker = selected_search.split(" - ")[0]
    
    company_info = companies_df[companies_df['id'] == ticker].iloc[0]
    sector_info = sectors_df[sectors_df['company_id'] == ticker]
    sector = sector_info['broad_sector'].iloc[0] if not sector_info.empty else "N/A"
    
    # --- COMPANY CARD ---
    with st.container(border=True):
        st.subheader(f"{company_info['company_name']} ({ticker})")
        st.markdown(f"**Sector:** {sector}")
        # Note: 'description' isn't explicitly in our schema, so we provide a clean fallback
        st.markdown(company_info.get('description', 'Fundamental data overview based on recent filings.'))
        
    ratios_df = get_ratios(ticker=ticker)
    
    if not ratios_df.empty:
        latest_ratios = ratios_df.sort_values('year', ascending=False).iloc[0]
        
        # --- KPI TILES ---
        st.markdown("### Key Performance Indicators (Latest Year)")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        col1.metric("ROE", f"{latest_ratios.get('return_on_equity_pct', 0):.1f}%")
        col2.metric("ROCE", f"{latest_ratios.get('roce_pct', 0):.1f}%")
        col3.metric("NPM", f"{latest_ratios.get('net_profit_margin_pct', 0):.1f}%")
        col4.metric("D/E Ratio", f"{latest_ratios.get('debt_to_equity', 0):.2f}")
        col5.metric("Rev CAGR 5yr", f"{latest_ratios.get('revenue_cagr_5yr', 0):.1f}%")
        col6.metric("FCF", f"₹{latest_ratios.get('free_cash_flow_cr', 0):,.0f} Cr")
        
    # --- CHARTS ---
    pl_df = get_pl(ticker=ticker)
    
    if not pl_df.empty:
        pl_df = pl_df.sort_values('year')
        st.markdown("---")
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.markdown("### Revenue & Net Profit (10-Year)")
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(x=pl_df['year'], y=pl_df['sales'], name='Revenue', marker_color='#1f77b4'))
            fig1.add_trace(go.Bar(x=pl_df['year'], y=pl_df['net_profit'], name='Net Profit', marker_color='#2ca02c'))
            fig1.update_layout(barmode='group', margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig1, use_container_width=True)
            
    if not ratios_df.empty:
        ratios_df = ratios_df.sort_values('year')
        with chart_col2:
            st.markdown("### Returns Profile: ROE vs ROCE")
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=ratios_df['year'], y=ratios_df['return_on_equity_pct'], mode='lines+markers', name='ROE %', line=dict(color='#ff7f0e', width=3)))
            fig2.add_trace(go.Scatter(x=ratios_df['year'], y=ratios_df['roce_pct'], mode='lines+markers', name='ROCE %', line=dict(color='#d62728', width=3)))
            fig2.update_layout(margin=dict(t=30, b=0, l=0, r=0), yaxis_title="Percentage (%)")
            st.plotly_chart(fig2, use_container_width=True)
            
    # --- PROS & CONS LOGIC ---
    if not ratios_df.empty:
        st.markdown("---")
        st.markdown("### Strengths & Risks (Algorithmic Flags)")
        
        pc_col1, pc_col2 = st.columns(2)
        
        with pc_col1:
            st.markdown("✅ **Strengths**")
            if latest_ratios.get('return_on_equity_pct', 0) > 15:
                st.success("High Return on Equity (> 15%)")
            if latest_ratios.get('debt_to_equity', 1) < 1:
                st.success("Comfortable Leverage (D/E < 1)")
            if latest_ratios.get('revenue_cagr_5yr', 0) > 10:
                st.success("Strong Revenue Growth (> 10% CAGR)")
                
        with pc_col2:
            st.markdown("❌ **Risks & Concerns**")
            if latest_ratios.get('return_on_equity_pct', 100) < 10:
                st.error("Low Return on Equity (< 10%)")
            if latest_ratios.get('debt_to_equity', 0) > 2:
                st.error("High Debt Burden (D/E > 2)")
            if latest_ratios.get('free_cash_flow_cr', 1) < 0:
                st.error("Negative Free Cash Flow")
