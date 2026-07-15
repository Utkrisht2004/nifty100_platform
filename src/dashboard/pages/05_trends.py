import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from src.dashboard.utils.db import get_companies, get_ratios, get_pl

st.set_page_config(page_title="Trend Analysis", layout="wide")
st.title("Time-Series Trend Analysis 📈")
st.markdown("Overlay multiple fundamental metrics to visualize 10-year structural business trends.")

# --- LOAD BASE DATA ---
companies = get_companies()
if companies.empty:
    st.error("Database connection error.")
    st.stop()

companies['search_key'] = companies['id'] + " - " + companies['company_name']
selected_search = st.selectbox("Search for a company:", options=[""] + companies['search_key'].tolist())

if selected_search:
    ticker = selected_search.split(" - ")[0]
    
    # Fetch Data
    ratios = get_ratios(ticker=ticker)
    pl = get_pl(ticker=ticker)
    
    if not ratios.empty and not pl.empty:
        # Merge on year for a unified timeseries dataset
        df = pd.merge(pl, ratios, on=['company_id', 'year'], how='inner')
        df = df.sort_values('year')
        
        # Define available metrics for the dropdown
        metric_options = {
            'Revenue (Cr)': 'sales',
            'Net Profit (Cr)': 'net_profit',
            'Operating Profit (Cr)': 'operating_profit',
            'ROE (%)': 'return_on_equity_pct',
            'ROCE (%)': 'roce_pct',
            'Debt to Equity': 'debt_to_equity',
            'Operating Margin (%)': 'operating_profit_margin_pct'
        }
        
        st.markdown("---")
        selected_metrics = st.multiselect(
            "Select up to 3 metrics to overlay:", 
            options=list(metric_options.keys()),
            default=['Revenue (Cr)', 'Net Profit (Cr)'],
            max_selections=3
        )
        
        if selected_metrics:
            fig = go.Figure()
            
            # Map colors to ensure contrast
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
            
            for i, metric_label in enumerate(selected_metrics):
                col_name = metric_options[metric_label]
                
                # Calculate YoY change for annotations
                df[f'{col_name}_yoy'] = df[col_name].pct_change() * 100
                
                # Create hover text
                hover_text = df.apply(
                    lambda row: f"{row['year']}<br>Value: {row[col_name]:.2f}<br>YoY: {row[f'{col_name}_yoy']:.1f}%" 
                    if pd.notna(row[f'{col_name}_yoy']) else f"{row['year']}<br>Value: {row[col_name]:.2f}",
                    axis=1
                )
                
                fig.add_trace(go.Scatter(
                    x=df['year'], 
                    y=df[col_name],
                    mode='lines+markers',
                    name=metric_label,
                    line=dict(color=colors[i], width=3),
                    marker=dict(size=8),
                    text=hover_text,
                    hoverinfo='text+name'
                ))
            
            fig.update_layout(
                title=f"10-Year Fundamental Trends for {ticker}",
                xaxis_title="Financial Year",
                yaxis_title="Value",
                hovermode="x unified",
                margin=dict(t=50, b=30, l=30, r=30),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Show raw data below
            with st.expander("View Raw Time-Series Data"):
                display_df = df[['year'] + [metric_options[m] for m in selected_metrics]].copy()
                st.dataframe(display_df.set_index('year').sort_index(ascending=False), use_container_width=True)
    else:
        st.warning("Insufficient time-series data available for this company.")
