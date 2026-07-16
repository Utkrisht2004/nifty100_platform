import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from src.dashboard.utils.db import get_ratios, get_sectors, get_companies, get_db_connection
from src.screener.scoring import calculate_composite_score

st.set_page_config(page_title="Home - Nifty 100", layout="wide")

st.title("Market Overview 📊")
st.markdown("Macro-level fundamentals and sector distribution for the Nifty 100 universe.")

# --- FOOLPROOF YEAR SELECTOR ---
@st.cache_data(ttl=600)
def get_available_years():
    conn = get_db_connection()
    df_years = pd.read_sql_query("SELECT DISTINCT year FROM financial_ratios", conn)
    conn.close()
    
    valid_years = []
    for y in df_years['year'].dropna():
        y_str = str(y).strip()
        if y_str.isdigit() and len(y_str) == 4:
            valid_years.append(y_str)
        elif y_str.endswith('.0') and y_str[:-2].isdigit():
            valid_years.append(y_str[:-2])
            
    return sorted(list(set(valid_years)), reverse=True)

available_years = get_available_years()

st.sidebar.header("Global Filters")
if not available_years:
    available_years = ['2023', '2022', '2021']

selected_year = st.sidebar.selectbox("Select Financial Year", options=available_years)

# --- DATA LOADING (BULLETPROOF PANDAS FILTER) ---
@st.cache_data(ttl=600)
def load_home_data(year):
    conn = get_db_connection()
    ratios = pd.read_sql_query("SELECT * FROM financial_ratios", conn)
    conn.close()
    
    # THE FIX: Match any row where the year string STARTS WITH the 4-digit year from the dropdown
    ratios['year_str'] = ratios['year'].astype(str)
    ratios = ratios[ratios['year_str'].str.startswith(str(year))]
    
    sectors = get_sectors()
    companies = get_companies()
    
    if not ratios.empty:
        df = pd.merge(ratios, sectors, on='company_id', how='left')
        df = pd.merge(df, companies[['id', 'company_name']], left_on='company_id', right_on='id', how='left')
        df = calculate_composite_score(df)
        return df
    return pd.DataFrame()

df = load_home_data(selected_year)

st.warning(f"DEBUG: Dataframe has {len(df)} rows.")
st.write("DEBUG RAW DATA:", df.head())

if df.empty:
    st.warning(f"No fundamental data available for the year {selected_year}.")
else:
    # --- KPI TILES ---
    st.subheader(f"Nifty 100 Snapshot ({selected_year})")
    
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)
    
    avg_roe = df['return_on_equity_pct'].mean()
    median_de = df['debt_to_equity'].median()
    median_rev_cagr = df['revenue_cagr_5yr'].median()
    total_companies = len(df)
    debt_free_count = len(df[df['icr_label'] == 'Debt Free']) if 'icr_label' in df.columns else 0
    median_pe = df['pe_ratio'].median() if 'pe_ratio' in df.columns else None
    
    col1.metric("Average ROE", f"{avg_roe:.1f}%" if pd.notna(avg_roe) else "N/A")
    col2.metric("Median D/E", f"{median_de:.2f}" if pd.notna(median_de) else "N/A")
    col3.metric("Median Rev CAGR (5yr)", f"{median_rev_cagr:.1f}%" if pd.notna(median_rev_cagr) else "N/A")
    col4.metric("Total Companies Tracked", total_companies)
    col5.metric("Debt-Free Companies", debt_free_count)
    col6.metric("Median P/E", f"{median_pe:.1f}" if pd.notna(median_pe) else "N/A")
    
    st.markdown("---")
    
    # --- CHARTS & TABLES ---
    col_chart, col_table = st.columns([1, 1.2])
    
    with col_chart:
        st.subheader("Sector Breakdown")
        sector_counts = df['broad_sector'].value_counts().reset_index()
        sector_counts.columns = ['Sector', 'Count']
        
        fig = px.pie(sector_counts, names='Sector', values='Count', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
        
    with col_table:
        st.subheader("Top 5 Quality Compounders")
        st.markdown("Ranked by internal Composite Quality Score.")
        
        top_5 = df.nlargest(5, 'composite_quality_score')
        display_cols = {
            'company_id': 'Ticker',
            'company_name': 'Company',
            'broad_sector': 'Sector',
            'composite_quality_score': 'Quality Score (0-100)',
            'return_on_equity_pct': 'ROE (%)'
        }
        
        st.dataframe(top_5[list(display_cols.keys())].rename(columns=display_cols).set_index('Ticker'), use_container_width=True)
