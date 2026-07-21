from fastapi import APIRouter, HTTPException, Query
import sqlite3
import pandas as pd
import json
from typing import Optional
from pathlib import Path

router = APIRouter()


def get_db_path():
    return Path(__file__).resolve().parent.parent.parent.parent / "data" / "nifty100.db"


def execute_query(query: str, params: tuple = ()):
    try:
        # CONCURRENCY FIX: Add timeout and disable same_thread check for high-traffic API hits
        conn = sqlite3.connect(get_db_path(), timeout=15.0, check_same_thread=False)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        return json.loads(df.to_json(orient="records"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def screen_companies(
    min_roe: Optional[float] = Query(None, description="Minimum Return on Equity (%)"),
    max_de: Optional[float] = Query(None, description="Maximum Debt to Equity"),
    min_fcf: Optional[float] = Query(None, description="Minimum Free Cash Flow (Cr)"),
    sector: Optional[str] = Query(None, description="Filter by Broad Sector"),
    min_rev_cagr_5yr: Optional[float] = Query(
        None, description="Minimum 5Y Revenue CAGR"
    ),
    min_pat_cagr_5yr: Optional[float] = Query(None, description="Minimum 5Y PAT CAGR"),
):
    query = """
        SELECT c.id, c.company_name, s.broad_sector, r.*
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        JOIN financial_ratios r ON c.id = r.company_id
        WHERE r.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.id)
    """
    params = []

    if min_roe is not None:
        query += " AND r.return_on_equity_pct >= ?"
        params.append(min_roe)
    if max_de is not None:
        query += " AND r.debt_to_equity <= ?"
        params.append(max_de)
    if min_fcf is not None:
        query += " AND r.free_cash_flow_cr >= ?"
        params.append(min_fcf)
    if sector:
        query += " AND s.broad_sector = ?"
        params.append(sector)
    if min_rev_cagr_5yr is not None:
        query += " AND r.revenue_cagr_5yr >= ?"
        params.append(min_rev_cagr_5yr)
    if min_pat_cagr_5yr is not None:
        query += " AND r.pat_cagr_5yr >= ?"
        params.append(min_pat_cagr_5yr)

    query += " ORDER BY r.return_on_equity_pct DESC"
    return execute_query(query, tuple(params))
