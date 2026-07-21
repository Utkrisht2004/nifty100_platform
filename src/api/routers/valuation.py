from fastapi import APIRouter
import sqlite3
import pandas as pd
from pathlib import Path

router = APIRouter()


def get_db_path():
    return Path(__file__).resolve().parent.parent.parent.parent / "data" / "nifty100.db"


@router.get("/{ticker}")
def get_valuation(ticker: str):
    query = "SELECT * FROM market_cap WHERE company_id = ? ORDER BY year ASC"
    try:
        conn = sqlite3.connect(get_db_path())
        df = pd.read_sql_query(query, conn, params=(ticker,))
        conn.close()
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}
