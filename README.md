# Nifty 100 Financial Analytics Platform

## Overview
An enterprise-grade data pipeline, analytics engine, and REST API for analyzing the Nifty 100 index constituents. Built using Python, Pandas, SQLite, and FastAPI.

## Setup Instructions
1. Install requirements: `pip install -r requirements.txt`
2. Run ETL: `python src/etl/run_etl.py`
3. Start API: `uvicorn src.api.main:app --port 8000`
4. Start Dashboard: `streamlit run src/dashboard/app.py`

## Architecture
- **Data Layer:** SQLite with composite indexing.
- **Backend:** FastAPI with concurrent request handling.
- **Analytics:** Scikit-learn KMeans clustering and Pandas aggregations.
- **Reporting:** ReportLab PDF generation.
