import sqlite3
import pandas as pd
from pathlib import Path

# FIX: Added one more .parent to correctly reach the root directory
db_path = Path(__file__).resolve().parent.parent.parent / 'data' / 'nifty100.db'
conn = sqlite3.connect(db_path)

print("\n--- DAY 06 MANUAL QA REVIEW ---")

# 1. Verify strict relational integrity
fk_issues = pd.read_sql_query("PRAGMA foreign_key_check;", conn)
print(f"Foreign Key Violations: {len(fk_issues)}")

# 2. Sample 5 random companies to check their P&L history
query = """
SELECT company_id, COUNT(year) as years_of_data 
FROM profitandloss 
GROUP BY company_id 
ORDER BY RANDOM() LIMIT 5;
"""
print("\nRandom 5 Company Year Coverage:")
print(pd.read_sql_query(query, conn).to_string(index=False))

# 3. Check for any companies with low historical data (< 5 years)
low_coverage = pd.read_sql_query("SELECT company_id, COUNT(year) as years FROM profitandloss GROUP BY company_id HAVING years < 5;", conn)
print(f"\nCompanies with < 5 years history: {len(low_coverage)}")

conn.close()
