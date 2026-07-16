import streamlit as st
import pandas as pd
import urllib.parse
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from src.dashboard.utils.db import get_companies

st.set_page_config(page_title="Annual Reports", layout="wide")
st.title("Annual Reports Library 📚")
st.markdown("Direct portal links and search operators for Nifty 100 company filings.")

companies = get_companies()

if companies.empty:
    st.error("Database connection error.")
    st.stop()

companies['search_key'] = companies['id'] + " - " + companies['company_name']
selected_search = st.selectbox("Search for a company to view filings:", options=[""] + companies['search_key'].tolist())

if selected_search:
    ticker = selected_search.split(" - ")[0]
    company_name = selected_search.split(" - ")[1]
    
    st.subheader(f"Document Portals for {company_name} ({ticker})")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔍 Direct PDF Search")
        st.markdown("BSE and NSE block automated downloads. Click below to fetch the official PDFs directly via web search operators.")
        
        for year in [2024, 2023, 2022]:
            # Creates a URL that automatically searches for the exact PDF
            query = urllib.parse.quote(f'"{company_name}" OR "{ticker}" "Annual Report" {year} filetype:pdf')
            google_url = f"https://www.google.com/search?q={query}"
            st.markdown(f"📄 **FY {year}:** [Find Official PDF]({google_url})")
            
    with col2:
        st.markdown("### 🏢 Financial Aggregators")
        st.markdown("View all historical annual reports, concall transcripts, and investor presentations.")
        
        screener_url = f"https://www.screener.in/company/{ticker}/consolidated/#documents"
        st.markdown(f"🔗 **Screener.in:** [View All Documents]({screener_url})")
        
        nse_url = f"https://www.nseindia.com/get-quotes/equity?symbol={ticker}"
        st.markdown(f"🔗 **NSE India:** [Corporate Disclosures]({nse_url})")
