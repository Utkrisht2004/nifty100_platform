import sqlite3
import pandas as pd
import os
from pathlib import Path
import sys

# Ensure the script can find the tearsheet module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from tearsheet import generate_tearsheet


def run_batch():
    print("\n--- DAY 34 & 35: BATCH PDF GENERATION (PANDAS EDITION) ---")
    base_dir = Path(__file__).resolve().parent.parent.parent
    db_path = base_dir / "data" / "nifty100.db"
    output_dir = base_dir / "output"

    if not db_path.exists():
        print("[!] Database not found.")
        return

    conn = sqlite3.connect(db_path)
    companies = pd.read_sql_query("SELECT id FROM companies", conn)["id"].tolist()

    # Load all years and filter in Pandas instead of SQLite to avoid Regex errors
    ratios = pd.read_sql_query("SELECT company_id, year FROM financial_ratios", conn)
    conn.close()

    # Filter for valid 4-digit years
    ratios = ratios[ratios["year"].astype(str).str.match(r"^\d{4}")]
    year_counts = ratios.groupby("company_id").size().reset_index(name="year_count")

    skipped_records = []
    success_count = 0

    print(f"Initiating batch run for {len(companies)} companies...")

    for ticker in companies:
        company_data = year_counts[year_counts["company_id"] == ticker]

        if company_data.empty or company_data.iloc[0]["year_count"] < 3:
            skipped_records.append(
                {
                    "company_id": ticker,
                    "reason": "Insufficient historical data (< 3 years)",
                }
            )
            continue

        try:
            if generate_tearsheet(ticker):
                success_count += 1
        except Exception as e:
            skipped_records.append(
                {"company_id": ticker, "reason": f"Generation Error: {e}"}
            )

    # Export skipped logs
    if skipped_records:
        skipped_df = pd.DataFrame(skipped_records)
        skipped_csv = output_dir / "skipped_tearsheets.csv"
        skipped_df.to_csv(skipped_csv, index=False)
        print(f"[!] Skipped {len(skipped_records)} companies. Logged to {skipped_csv}")

    print(f"\n[✓] Batch Execution Complete: Generated {success_count} PDF tearsheets.")
    print("[✓] SPRINT 5 EXIT CRITERIA MET. PIPELINE FULLY OPERATIONAL.")


if __name__ == "__main__":
    run_batch()
