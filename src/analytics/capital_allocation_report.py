import sqlite3
import pandas as pd
import os
from pathlib import Path

def run_capital_allocation():
    print("\n--- DAY 32: CAPITAL ALLOCATION REPORT ---")
    base_dir = Path(__file__).resolve().parent.parent.parent
    db_path = base_dir / 'data' / 'nifty100.db'
    output_dir = base_dir / 'output'
    intel_path = output_dir / 'cashflow_intelligence.xlsx'
    
    if not db_path.exists():
        print("[!] Database not found.")
        return
        
    conn = sqlite3.connect(db_path)
    
    query = """
    SELECT r.company_id, r.year, r.return_on_equity_pct, r.debt_to_equity, c.company_name 
    FROM financial_ratios r
    JOIN companies c ON r.company_id = c.id
    ORDER BY r.company_id, r.year ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Filter for valid years
    df = df[df['year'].astype(str).str.match(r'^\d{4}')].copy()
    
    def classify_pattern(row):
        roe = row.get('return_on_equity_pct', 0)
        de = row.get('debt_to_equity', 0)
        
        roe = 0 if pd.isna(roe) else roe
        de = 0 if pd.isna(de) else de
        
        if roe > 20 and de < 0.5: return "Efficient Compounders"
        if de == 0: return "Cash Hoarders (Debt-Free)"
        if de > 2: return "Leveraged (Paying down Debt)"
        if roe < 10: return "Value Traps / Stagnant"
        if roe > 15: return "Growth / Heavy Reinvestment"
        return "Balanced Allocators"

    df['allocation_pattern'] = df.apply(classify_pattern, axis=1)
    
    print("Analyzing year-over-year pattern shifts...")
    changes = []
    latest_patterns = {}
    
    grouped = df.groupby('company_id')
    for cid, group in grouped:
        if len(group) < 2:
            latest_patterns[cid] = group.iloc[-1]['allocation_pattern'] if len(group) > 0 else "Balanced Allocators"
            continue
            
        prev = group.iloc[-2]['allocation_pattern']
        curr = group.iloc[-1]['allocation_pattern']
        latest_patterns[cid] = curr
        
        if prev != curr:
            changes.append({
                'company_id': cid,
                'company_name': group.iloc[-1]['company_name'],
                'previous_pattern': prev,
                'current_pattern': curr
            })
            
    # 1. Generate Pattern Changes CSV
    changes_df = pd.DataFrame(changes)
    changes_path = output_dir / 'pattern_changes.csv'
    if not changes_df.empty:
        changes_df.to_csv(changes_path, index=False)
        print(f"[✓] Documented {len(changes_df)} companies with shifting allocation strategies -> {changes_path}")
    else:
        pd.DataFrame(columns=['company_id', 'company_name', 'previous_pattern', 'current_pattern']).to_csv(changes_path, index=False)
        print(f"[✓] Zero pattern shifts detected year-over-year.")

    # 2. Update cashflow_intelligence.xlsx
    if intel_path.exists():
        intel_df = pd.read_excel(intel_path)
        intel_df['capital_allocation_label'] = intel_df['company_id'].map(latest_patterns).fillna("Balanced Allocators")
        intel_df.to_excel(intel_path, index=False)
        print(f"[✓] Successfully injected capital allocation labels into {intel_path}")
    else:
        print(f"[!] Warning: {intel_path} not found. Run Day 31 first.")

if __name__ == "__main__":
    run_capital_allocation()
