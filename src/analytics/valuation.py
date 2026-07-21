import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path
import os


def generate_valuation():
    print("\n--- DAY 26: VALUATION ENGINE ---")
    base_dir = Path(__file__).resolve().parent.parent.parent
    db_path = base_dir / "data" / "nifty100.db"
    output_dir = base_dir / "output"
    os.makedirs(output_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)

    # 1. Fetch Latest Data (REMOVED r.ev_ebitda to prevent SQL crash)
    query = """
    SELECT r.company_id, r.free_cash_flow_cr,
           m.pe_ratio, m.pb_ratio, m.market_cap_crore, m.year,
           s.broad_sector as sector,
           c.company_name
    FROM financial_ratios r
    JOIN market_cap m ON r.company_id = m.company_id AND r.year = m.year
    JOIN sectors s ON r.company_id = s.company_id
    JOIN companies c ON r.company_id = c.id
    WHERE r.year = (SELECT MAX(year) FROM financial_ratios r2 WHERE r.company_id = r2.company_id)
    """
    df = pd.read_sql_query(query, conn)

    # Fetch 5-year median PE
    pe_query = "SELECT company_id, pe_ratio FROM market_cap WHERE pe_ratio IS NOT NULL"
    pe_history = pd.read_sql_query(pe_query, conn)
    median_pe_df = pe_history.groupby("company_id")["pe_ratio"].median().reset_index()
    median_pe_df.rename(columns={"pe_ratio": "5yr_median_PE"}, inplace=True)

    conn.close()

    if df.empty:
        print("[!] No data found in the database for valuation.")
        return

    # Merge 5yr median PE
    df = pd.merge(df, median_pe_df, on="company_id", how="left")

    # 2. Computations
    print("Calculating Valuation Metrics & Sector Flags...")

    # FCF Yield = (FCF / Market Cap) * 100
    df["FCF_yield_pct"] = (df["free_cash_flow_cr"] / df["market_cap_crore"]) * 100

    # Sector Median P/E
    sector_medians = df.groupby("sector")["pe_ratio"].median().reset_index()
    sector_medians.rename(columns={"pe_ratio": "sector_median_PE"}, inplace=True)
    df = pd.merge(df, sector_medians, on="sector", how="left")

    # PE vs Sector Median Pct
    df["PE_vs_sector_median_pct"] = (
        (df["pe_ratio"] / df["sector_median_PE"]) - 1
    ) * 100

    # 3. Flags (Caution > 1.5x, Discount < 0.7x)
    def assign_flag(row):
        if pd.isna(row["pe_ratio"]) or pd.isna(row["sector_median_PE"]):
            return "Unknown"
        if row["pe_ratio"] > (row["sector_median_PE"] * 1.5):
            return "Caution"
        elif row["pe_ratio"] < (row["sector_median_PE"] * 0.7):
            return "Discount"
        else:
            return "Fair"

    df["flag"] = df.apply(assign_flag, axis=1)

    # 4. Formatting Output
    out_cols = [
        "company_id",
        "company_name",
        "sector",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "FCF_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
        "flag",
    ]

    # Defensive programming: gracefully fill any missing columns (like ev_ebitda) with NaN
    for col in out_cols:
        if col not in df.columns:
            df[col] = np.nan

    final_df = df[out_cols].copy()

    # Clean up massive float decimals before export
    float_cols = [
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "FCF_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
    ]
    for col in float_cols:
        final_df[col] = final_df[col].round(2)

    final_df = final_df.sort_values(by=["sector", "flag"])

    # 5. Exports
    excel_path = output_dir / "valuation_summary.xlsx"
    final_df.to_excel(excel_path, index=False)
    print(f"[✓] Generated {excel_path} ({len(final_df)} companies)")

    csv_path = output_dir / "valuation_flags.csv"
    flagged_df = final_df[final_df["flag"].isin(["Caution", "Discount"])]
    flagged_df.to_csv(csv_path, index=False)
    print(f"[✓] Generated {csv_path} ({len(flagged_df)} flagged opportunities)")


if __name__ == "__main__":
    generate_valuation()
