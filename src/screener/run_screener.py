import sqlite3
import pandas as pd
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from src.screener.engine import ScreenerEngine
from src.screener.scoring import calculate_composite_score
from src.screener.exporter import export_to_excel

base_dir = Path(__file__).resolve().parent.parent.parent
db_path = base_dir / "data" / "nifty100.db"

# 1. Load Data
conn = sqlite3.connect(db_path)
query = """
SELECT r.*, s.broad_sector, m.pe_ratio, m.pb_ratio, m.market_cap_crore, m.dividend_yield_pct
FROM financial_ratios r
LEFT JOIN sectors s ON r.company_id = s.company_id
LEFT JOIN market_cap m ON r.company_id = m.company_id AND r.year = m.year
WHERE r.year = (SELECT MAX(year) FROM financial_ratios r2 WHERE r.company_id = r2.company_id)
"""
df_latest = pd.read_sql_query(query, conn)
conn.close()

# 2. Score Data
print("Calculating Composite Scores...")
df_scored = calculate_composite_score(df_latest)

# 3. Filter via Presets
engine = ScreenerEngine()
presets = engine.config.get("presets", {})
preset_results = {}

print("Applying Filters...")
for preset_name, filters in presets.items():
    filtered_df = engine.apply_filters(df_scored, filters)
    preset_results[preset_name] = filtered_df
    print(f"  -> {preset_name}: {len(filtered_df)} companies")

# 4. Export to Excel
export_to_excel(preset_results)
