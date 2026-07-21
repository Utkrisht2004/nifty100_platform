import sqlite3
from pathlib import Path


def optimise_db():
    print("\n--- DAY 43: SQLITE OPTIMISATION ---")
    db_path = Path(__file__).resolve().parent.parent / "data" / "nifty100.db"

    if not db_path.exists():
        print("[!] Database not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = ["financial_ratios", "profitandloss", "balancesheet", "cashflow"]
    print("[*] Creating composite indexes on (company_id, year)...")

    for table in tables:
        try:
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{table}_comp_year ON {table}(company_id, year)"
            )
            print(f"  [✓] Index created for {table}")
        except Exception as e:
            print(f"  [!] Could not index {table}: {e}")

    conn.commit()
    conn.close()
    print(
        "[✓] Database optimisation complete. Queries will now execute exponentially faster."
    )


if __name__ == "__main__":
    optimise_db()
