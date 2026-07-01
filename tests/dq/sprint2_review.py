import sqlite3
import pandas as pd
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent
db_path = base_dir / 'data' / 'nifty100.db'
conn = sqlite3.connect(db_path)

print("\n--- SPRINT 2: FINAL REVIEW & SCREENER (PER-COMPANY LATEST YEAR) ---")

# 1. Manual Spot Check (Latest year per company)
query_spot = """
SELECT company_id, year, ROUND(return_on_equity_pct, 2) as ROE_pct, ROUND(revenue_cagr_5yr, 2) as Rev_CAGR_5yr
FROM financial_ratios r1
WHERE company_id IN ('TCS', 'RELIANCE', 'HDFCBANK') 
  AND year = (SELECT MAX(year) FROM financial_ratios r2 WHERE r1.company_id = r2.company_id)
"""
print("\n[1] Spot Check (ROE & 5-Yr Rev CAGR):")
print(pd.read_sql_query(query_spot, conn).to_string(index=False))

# 2. Screener Preview (ROE > 15% and D/E < 1 for the latest year per company)
query_screen = """
SELECT company_id, ROUND(return_on_equity_pct, 2) as ROE_pct, ROUND(debt_to_equity, 2) as D_E
FROM financial_ratios r1
WHERE return_on_equity_pct > 15 
  AND (debt_to_equity < 1 OR debt_to_equity IS NULL)
  AND year = (SELECT MAX(year) FROM financial_ratios r2 WHERE r1.company_id = r2.company_id)
ORDER BY ROE_pct DESC
"""
screener_df = pd.read_sql_query(query_screen, conn)
print(f"\n[2] Screener Preview Result Count: {len(screener_df)} companies (Target: 15-50)")
print("Top 5 Screener Candidates:")
print(screener_df.head().to_string(index=False))

conn.close()
