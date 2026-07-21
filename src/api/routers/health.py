from fastapi import APIRouter
import sqlite3
import time
from pathlib import Path

router = APIRouter()
START_TIME = time.time()


@router.get("/health")
def health_check():
    db_path = (
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "nifty100.db"
    )
    row_counts = {}

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall() if t[0] != "sqlite_sequence"]

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_counts[table] = cursor.fetchone()[0]

        conn.close()
    except Exception as e:
        row_counts = {"error": str(e)}

    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "version": "1.0.0",
        "db_row_counts": row_counts,
    }
