from fastapi import APIRouter, HTTPException
import sqlite3
import pandas as pd
from pathlib import Path

router = APIRouter()


def get_db_path():
    return Path(__file__).resolve().parent.parent.parent.parent / "data" / "nifty100.db"


@router.get("/")
def get_sectors():
    query = """
        SELECT s.broad_sector as sector, 
               COUNT(DISTINCT c.id) as company_count,
               AVG(r.return_on_equity_pct) as avg_roe,
               AVG(r.debt_to_equity) as avg_de
        FROM sectors s
        JOIN companies c ON s.company_id = c.id
        LEFT JOIN financial_ratios r ON c.id = r.company_id
        WHERE r.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.id)
        GROUP BY s.broad_sector
    """
    try:
        conn = sqlite3.connect(get_db_path())
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{sector_name}/companies")
def get_companies_in_sector(sector_name: str):
    query = """
        SELECT c.id, c.company_name, r.return_on_equity_pct, r.debt_to_equity
        FROM companies c
        JOIN sectors s ON c.id = s.company_id
        LEFT JOIN financial_ratios r ON c.id = r.company_id
        WHERE s.broad_sector = ? 
        AND r.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.id)
    """
    try:
        conn = sqlite3.connect(get_db_path())
        df = pd.read_sql_query(query, conn, params=(sector_name,))
        conn.close()
        if df.empty:
            raise HTTPException(
                status_code=404, detail="Sector not found or has no companies"
            )
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
