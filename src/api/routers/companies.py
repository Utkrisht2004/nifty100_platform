from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import sqlite3
import pandas as pd
from typing import Optional
from pathlib import Path

router = APIRouter()


def get_db_path():
    return Path(__file__).resolve().parent.parent.parent.parent / "data" / "nifty100.db"


def get_tearsheet_dir():
    return (
        Path(__file__).resolve().parent.parent.parent.parent / "reports" / "tearsheets"
    )


def execute_query(query: str, params: tuple = ()):
    db_path = get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def get_companies(sector: Optional[str] = None, search: Optional[str] = None):
    query = """
        SELECT c.id, c.company_name, s.broad_sector, s.sub_sector, 
               r.return_on_equity_pct as roe_pct, r.roce_pct
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        LEFT JOIN financial_ratios r ON c.id = r.company_id
        WHERE r.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.id)
    """
    params = []

    if sector:
        query += " AND s.broad_sector = ?"
        params.append(sector)
    if search:
        query += " AND (c.company_name LIKE ? OR c.id LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])

    query += " ORDER BY c.company_name ASC"
    return execute_query(query, tuple(params))


@router.get("/{ticker}")
def get_company_profile(ticker: str):
    query = """
        SELECT c.*, s.broad_sector, s.sub_sector, r.*
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        LEFT JOIN financial_ratios r ON c.id = r.company_id
        WHERE c.id = ? 
        ORDER BY r.year DESC LIMIT 1
    """
    results = execute_query(query, (ticker,))
    if not results:
        raise HTTPException(status_code=404, detail="Company not found")
    return results[0]


@router.get("/{ticker}/pl")
def get_pl_history(
    ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None
):
    query = "SELECT * FROM profitandloss WHERE company_id = ?"
    params = [ticker]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year ASC"
    return execute_query(query, tuple(params))


@router.get("/{ticker}/bs")
def get_bs_history(
    ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None
):
    query = "SELECT * FROM balancesheet WHERE company_id = ?"
    params = [ticker]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year ASC"
    return execute_query(query, tuple(params))


@router.get("/{ticker}/cashflow")
def get_cashflow_history(
    ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None
):
    query = "SELECT * FROM cashflow WHERE company_id = ?"
    params = [ticker]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year ASC"
    return execute_query(query, tuple(params))


@router.get("/{ticker}/ratios")
def get_ratio_history(ticker: str, year: Optional[str] = None):
    query = "SELECT * FROM financial_ratios WHERE company_id = ?"
    params = [ticker]
    if year:
        query += " AND year = ?"
        params.append(year)
    query += " ORDER BY year ASC"
    return execute_query(query, tuple(params))


@router.get("/{ticker}/tearsheet")
def download_tearsheet(ticker: str):
    tearsheet_dir = get_tearsheet_dir()
    file_path = tearsheet_dir / f"{ticker}_tearsheet.pdf"

    if not file_path.exists():
        raise HTTPException(
            status_code=404, detail="Tearsheet PDF not found for this company"
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=f"{ticker}_Financial_Tearsheet.pdf",
    )
