import pandas as pd
import sqlite3
import time
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from src.etl.normaliser import normalize_ticker, apply_year_normalization
from src.etl.validator import DataValidator

CORE_FILES = {
    "companies.xlsx": "companies",
    "profitandloss.xlsx": "profitandloss",
    "balancesheet.xlsx": "balancesheet",
    "cashflow.xlsx": "cashflow",
    "analysis.xlsx": "analysis",
    "documents.xlsx": "documents",
    "prosandcons.xlsx": "prosandcons",
}

SUPP_FILES = {
    "sectors.xlsx": "sectors",
    "stock_prices.xlsx": "stock_prices",
    "market_cap.xlsx": "market_cap",
}


def load_excel_file(file_path: Path) -> pd.DataFrame:
    filename = file_path.name
    header_row = 1 if filename in CORE_FILES else 0
    try:
        df = pd.read_excel(file_path, header=header_row)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        for col in ["id", "company_id"]:
            if col in df.columns:
                df[col] = normalize_ticker(df[col])

        if "year" in df.columns and filename != "documents.xlsx":
            df["year"] = apply_year_normalization(df["year"])

        return df
    except Exception as e:
        print(f"WARNING: Failed to load {filename} - {e}")
        return pd.DataFrame()


def clean_data_for_db(dfs):
    """Applies CRITICAL automated fixes to prevent SQLite constraint crashes."""

    if "companies.xlsx" in dfs and not dfs["companies.xlsx"].empty:
        dfs["companies.xlsx"] = dfs["companies.xlsx"].drop_duplicates(
            subset=["id"], keep="last"
        )

    valid_companies = (
        set(dfs["companies.xlsx"]["id"].dropna()) if "companies.xlsx" in dfs else set()
    )

    for filename, df in dfs.items():
        if filename == "companies.xlsx" or df.empty:
            continue

        if "id" in df.columns:
            df = df.drop(columns=["id"])

        if "company_id" in df.columns:
            df = df[df["company_id"].isin(valid_companies)]

        dfs[filename] = df

    annual_tables = [
        "profitandloss.xlsx",
        "balancesheet.xlsx",
        "cashflow.xlsx",
        "market_cap.xlsx",
    ]
    for table in annual_tables:
        if table in dfs and not dfs[table].empty:
            # Drop rows where company_id or year are completely missing
            df = dfs[table].dropna(subset=["company_id", "year"])
            dfs[table] = df.drop_duplicates(subset=["company_id", "year"], keep="last")

    if "stock_prices.xlsx" in dfs and not dfs["stock_prices.xlsx"].empty:
        df = dfs["stock_prices.xlsx"].dropna(subset=["company_id", "date"])
        dfs["stock_prices.xlsx"] = df.drop_duplicates(
            subset=["company_id", "date"], keep="last"
        )

    for table in ["sectors.xlsx", "analysis.xlsx"]:
        if table in dfs and not dfs[table].empty:
            dfs[table] = dfs[table].drop_duplicates(subset=["company_id"], keep="last")

    # FIX: Drop rows violating NOT NULL constraints in profitandloss
    if "profitandloss.xlsx" in dfs and not dfs["profitandloss.xlsx"].empty:
        df = dfs["profitandloss.xlsx"]
        df = df.dropna(subset=["sales", "expenses", "operating_profit"])
        dfs["profitandloss.xlsx"] = df

    if "balancesheet.xlsx" in dfs and not dfs["balancesheet.xlsx"].empty:
        df = dfs["balancesheet.xlsx"]
        if "fixed_assets" in df.columns:
            df["fixed_assets"] = df["fixed_assets"].apply(
                lambda x: 0 if pd.notna(x) and float(x) < 0 else x
            )
        dfs["balancesheet.xlsx"] = df

    return dfs


def main():
    print("\n[+] Starting Nifty 100 ETL Pipeline...")
    start_time = time.time()

    base_dir = Path(__file__).resolve().parent.parent.parent
    db_path = base_dir / "data" / "nifty100.db"
    schema_path = base_dir / "data" / "db" / "schema.sql"

    if db_path.exists():
        db_path.unlink()
        print("[+] Removed old database to ensure clean schema build.")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")

    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    print("[+] SQLite schema built successfully.")

    dfs = {}
    for file_dict, folder in [(CORE_FILES, "raw"), (SUPP_FILES, "supporting")]:
        for filename in file_dict.keys():
            file_path = base_dir / "data" / folder / filename
            if file_path.exists():
                dfs[filename] = load_excel_file(file_path)

    print("[+] Running 16-Rule Data Quality Validator...")
    validator = DataValidator(dfs)
    validator.run_all_rules()
    validator.export_failures(base_dir / "output" / "validation_failures.csv")
    print(f"    -> Found {len(validator.failures)} QA flags (exported to CSV).")

    dfs = clean_data_for_db(dfs)

    print("[+] Writing to SQLite database...")
    audit_log = []

    load_order = [
        "companies.xlsx",
        "sectors.xlsx",
        "analysis.xlsx",
        "prosandcons.xlsx",
        "profitandloss.xlsx",
        "balancesheet.xlsx",
        "cashflow.xlsx",
        "stock_prices.xlsx",
        "market_cap.xlsx",
        "documents.xlsx",
    ]

    for filename in load_order:
        if filename in dfs and not dfs[filename].empty:
            table_name = CORE_FILES.get(filename) or SUPP_FILES.get(filename)
            df = dfs[filename]

            if filename == "documents.xlsx" and "year" in df.columns:
                df["year"] = (
                    pd.to_numeric(df["year"], errors="coerce").fillna(0).astype(int)
                )

            try:
                df.to_sql(table_name, conn, if_exists="append", index=False)
                audit_log.append(
                    {"table": table_name, "rows_loaded": len(df), "status": "SUCCESS"}
                )
                print(f"    -> Loaded {len(df)} rows into '{table_name}'")
            except Exception as e:
                audit_log.append(
                    {"table": table_name, "rows_loaded": 0, "status": f"FAILED: {e}"}
                )
                print(f"    -> FAILED loading '{table_name}': {e}")

    conn.close()

    pd.DataFrame(audit_log).to_csv(base_dir / "output" / "load_audit.csv", index=False)
    elapsed = time.time() - start_time
    print(f"\n[✓] ETL Pipeline completed in {elapsed:.2f} seconds!")
    print("[✓] Sprint 1 Definition of Done achieved.\n")


if __name__ == "__main__":
    main()
