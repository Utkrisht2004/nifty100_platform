import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path

# Locate DB relative to this file: src/dashboard/utils/db.py -> ../../../data/nifty100.db
DB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "nifty100.db"


def get_db_connection():
    """Returns a fresh SQLite connection."""
    return sqlite3.connect(DB_PATH)


@st.cache_data(ttl=600)
def get_companies():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM companies", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_sectors():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM sectors", conn)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_ratios(ticker=None, year=None):
    conn = get_db_connection()
    query = "SELECT * FROM financial_ratios WHERE 1=1"
    params = []
    if ticker:
        query += " AND company_id = ?"
        params.append(ticker)
    if year:
        query += " AND year = ?"
        params.append(year)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_pl(ticker):
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT * FROM profitandloss WHERE company_id = ?", conn, params=(ticker,)
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_bs(ticker):
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT * FROM balancesheet WHERE company_id = ?", conn, params=(ticker,)
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_cf(ticker):
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT * FROM cashflow WHERE company_id = ?", conn, params=(ticker,)
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_peers(group_name):
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT * FROM peer_percentiles WHERE peer_group_name = ?",
        conn,
        params=(group_name,),
    )
    conn.close()
    return df


@st.cache_data(ttl=600)
def get_valuation(ticker):
    # Placeholder for Day 26 Valuation module
    pass
