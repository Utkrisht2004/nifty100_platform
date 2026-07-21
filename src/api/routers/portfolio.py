from fastapi import APIRouter, HTTPException
import pandas as pd
from pathlib import Path

router = APIRouter()


@router.get("/stats")
def get_portfolio_stats():
    stats_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "output"
        / "portfolio_stats.csv"
    )
    if not stats_path.exists():
        raise HTTPException(
            status_code=404, detail="Portfolio stats not generated yet."
        )

    df = pd.read_csv(stats_path)
    return df.to_dict(orient="records")
