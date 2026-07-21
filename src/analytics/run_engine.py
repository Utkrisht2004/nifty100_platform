import sqlite3
import pandas as pd
from pathlib import Path
import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from src.analytics.ratios import (
    calc_net_profit_margin,
    calc_operating_profit_margin,
    calc_return_on_equity,
    calc_return_on_capital_employed,
    calc_debt_to_equity,
    calc_interest_coverage,
    calc_asset_turnover,
)
from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow_kpis import (
    calc_free_cash_flow,
    calc_cfo_quality_score,
    calc_capex_intensity,
    calc_fcf_conversion,
    classify_capital_allocation,
)

# Setup logging
logger = logging.getLogger("ratio_engine")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("output/ratio_edge_cases.log")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
if not logger.handlers:
    logger.addHandler(file_handler)


def main():
    print("\n[+] Starting Financial Ratio Engine...")
    base_dir = Path(__file__).resolve().parent.parent.parent
    db_path = base_dir / "data" / "nifty100.db"

    conn = sqlite3.connect(db_path)

    # 1. Extract and Merge Raw Data
    print("    -> Extracting data from SQLite warehouse...")
    pnl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)
    cf = pd.read_sql_query("SELECT * FROM cashflow", conn)
    companies = pd.read_sql_query(
        "SELECT id, roce_percentage, roe_percentage FROM companies", conn
    )
    sectors = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)

    # Merge tables
    df = pnl.merge(bs, on=["company_id", "year"], how="inner")
    df = df.merge(cf, on=["company_id", "year"], how="inner")
    df = df.merge(sectors, on="company_id", how="left")
    df = df.merge(companies, left_on="company_id", right_on="id", how="left")

    # Sort for CAGR lookbacks
    df = df.sort_values(by=["company_id", "year"]).reset_index(drop=True)

    # 2. Compute 5-Year Lags for CAGR
    df["sales_5yr_ago"] = df.groupby("company_id")["sales"].shift(5)
    df["pat_5yr_ago"] = df.groupby("company_id")["net_profit"].shift(5)
    df["eps_5yr_ago"] = df.groupby("company_id")["eps"].shift(5)

    results = []
    cap_alloc_results = []

    print("    -> Computing 50+ KPIs per company-year...")
    for idx, row in df.iterrows():
        cid = row["company_id"]
        yr = row["year"]
        is_fin = bool(row["broad_sector"] == "Financials")

        # Profitability
        npm = calc_net_profit_margin(row["net_profit"], row["sales"])
        opm = calc_operating_profit_margin(
            row["operating_profit"], row["sales"], row["opm_percentage"], cid, yr
        )
        roe = calc_return_on_equity(
            row["net_profit"], row["equity_capital"], row["reserves"]
        )
        roce = calc_return_on_capital_employed(
            row["operating_profit"],
            row["equity_capital"],
            row["reserves"],
            row["borrowings"],
            is_fin,
        )

        # Cross-check ROCE edge cases (Day 13 logic preemptively logged)
        if roce is not None and pd.notna(row["roce_percentage"]):
            if abs(roce - row["roce_percentage"]) > 5.0:
                logger.warning(
                    f"ROCE Anomaly | {cid} ({yr}): Calc={roce:.2f}%, Source={row['roce_percentage']}%"
                )

        # Leverage & Efficiency
        de_val, high_lev_flag = calc_debt_to_equity(
            row["borrowings"], row["equity_capital"], row["reserves"], is_fin
        )
        icr_val, icr_label, icr_warn = calc_interest_coverage(
            row["operating_profit"], row.get("other_income", 0), row["interest"]
        )
        asset_to = calc_asset_turnover(row["sales"], row["total_assets"])

        # Cash Flow
        fcf = calc_free_cash_flow(row["operating_activity"], row["investing_activity"])
        cfo_score, cfo_label = calc_cfo_quality_score(
            row["operating_activity"], row["net_profit"]
        )
        capex_int, capex_label = calc_capex_intensity(
            row["investing_activity"], row["sales"]
        )
        fcf_conv = calc_fcf_conversion(fcf, row["operating_profit"])

        # Capital Allocation (Day 11 Output)
        cap_pattern = classify_capital_allocation(
            row["operating_activity"],
            row["investing_activity"],
            row["financing_activity"],
            cfo_label,
        )
        cap_alloc_results.append(
            {
                "company_id": cid,
                "year": yr,
                "cfo_sign": "+" if row["operating_activity"] >= 0 else "-",
                "cfi_sign": "+" if row["investing_activity"] >= 0 else "-",
                "cff_sign": "+" if row["financing_activity"] >= 0 else "-",
                "pattern_label": cap_pattern,
            }
        )

        # CAGR (5-Year)
        rev_cagr, rev_flag = calculate_cagr(row["sales_5yr_ago"], row["sales"], 5)
        pat_cagr, pat_flag = calculate_cagr(row["pat_5yr_ago"], row["net_profit"], 5)
        eps_cagr, eps_flag = calculate_cagr(row["eps_5yr_ago"], row["eps"], 5)

        # Compile Row
        results.append(
            {
                "company_id": cid,
                "year": yr,
                "net_profit_margin_pct": npm,
                "operating_profit_margin_pct": opm,
                "return_on_equity_pct": roe,
                "roce_pct": roce,
                "debt_to_equity": de_val,
                "high_leverage_flag": high_lev_flag,
                "interest_coverage": icr_val,
                "icr_label": icr_label,
                "asset_turnover": asset_to,
                "free_cash_flow_cr": fcf,
                "cfo_quality_label": cfo_label,
                "capex_intensity_pct": capex_int,
                "fcf_conversion_pct": fcf_conv,
                "revenue_cagr_5yr": rev_cagr,
                "revenue_cagr_flag": rev_flag,
                "pat_cagr_5yr": pat_cagr,
                "eps_cagr_5yr": eps_cagr,
            }
        )

    # 3. Export Capital Allocation CSV
    df_cap = pd.DataFrame(cap_alloc_results)
    df_cap.to_csv(base_dir / "output" / "capital_allocation.csv", index=False)
    print(f"    -> Generated capital_allocation.csv ({len(df_cap)} rows)")

    # 4. Write to SQLite
    df_results = pd.DataFrame(results)
    df_results.to_sql("financial_ratios", conn, if_exists="replace", index=False)
    print(f"    -> Populated 'financial_ratios' table with {len(df_results)} rows")

    # 5. Verification Count
    count = pd.read_sql_query(
        "SELECT COUNT(*) as cnt FROM financial_ratios", conn
    ).iloc[0]["cnt"]
    print(f"\n[✓] Ratio Engine complete. Total records in DB: {count}")

    conn.close()


if __name__ == "__main__":
    main()
