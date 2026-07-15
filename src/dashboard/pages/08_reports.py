import streamlit as st
import pandas as pd
import requests
import sys
import os
import concurrent.futures

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from src.dashboard.utils.db import get_companies

st.set_page_config(page_title="Annual Reports", layout="wide")
st.title("Annual Reports Library 📚")
st.markdown("Direct links to BSE / NSE PDF filings for Nifty 100 companies.")

companies = get_companies()

if companies.empty:
    st.error("Database connection error.")
    st.stop()

companies['search_key'] = companies['id'] + " - " + companies['company_name']
selected_search = st.selectbox("Search for a company to view filings:", options=[""] + companies['search_key'].tolist())

def check_url(url):
    """Pings the URL to see if it returns a 200 OK or 404."""
    try:
        # Use a short timeout so the UI doesn't hang forever
        res = requests.head(url, timeout=1.5)
        return res.status_code < 400
    except requests.RequestException:
        return False

if selected_search:
    ticker = selected_search.split(" - ")[0]
    st.subheader(f"Available Documents for {ticker}")
    st.markdown("---")
    
    # We will check the last 3 years
    years = [2023, 2022, 2021]
    
    for year in years:
        col1, col2 = st.columns([1, 4])
        
        # Constructing a generic mock BSE structure for the sake of the exercise
        url = f"https://www.bseindia.com/bseplus/AnnualReport/{ticker}/{ticker}_{year}.pdf"
        
        with col1:
            st.markdown(f"**FY {year}-{str(year+1)[-2:]}**")
            
        with col2:
            with st.spinner("Checking availability..."):
                is_valid = check_url(url)
            
            if is_valid:
                st.markdown(f"✅ [Download {year} Annual Report (PDF)]({url})")
            else:
                st.markdown(f"🚨 <span style='color:red; font-weight:bold; border: 1px solid red; padding: 2px 6px; border-radius: 4px;'>Report Unavailable (404)</span>", unsafe_allow_html=True)
                
        st.markdown("") # Spacing
