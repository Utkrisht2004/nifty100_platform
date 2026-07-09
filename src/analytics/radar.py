import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import pi
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.screener.scoring import calculate_composite_score

def create_radar_chart(company_id, company_data, peer_avg_data, metrics, output_dir, is_standalone=False):
    """Generates and saves a radar chart for a single company."""
    N = len(metrics)
    
    # Calculate angles for each axis
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1] # Close the loop
    
    # Prepare data arrays (close the loop)
    values = company_data.tolist()
    values += values[:1]
    
    peer_values = peer_avg_data.tolist()
    peer_values += peer_values[:1]
    
    # Setup plot
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    
    # Draw one axe per variable and add labels
    plt.xticks(angles[:-1], metrics, size=10, weight='bold')
    
    # Draw ylabels
    ax.set_rlabel_position(0)
    plt.yticks([25, 50, 75], ["25th", "Median", "75th"], color="grey", size=8)
    plt.ylim(0, 100)
    
    # Plot Peer Average (Dashed outline)
    label_text = "Nifty 100 Average" if is_standalone else "Peer Group Average"
    ax.plot(angles, peer_values, linewidth=2, linestyle='dashed', color='grey', label=label_text)
    
    # Plot Company (Filled Polygon)
    ax.plot(angles, values, linewidth=2, linestyle='solid', color='#1f77b4', label=company_id)
    ax.fill(angles, values, '#1f77b4', alpha=0.25)
    
    # Add title and legend
    title_suffix = "(Standalone - No Peer Group)" if is_standalone else "(vs Peers)"
    plt.title(f"{company_id} Financial Profile {title_suffix}", size=14, weight='bold', y=1.1)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    # Save file
    plt.tight_layout()
    file_path = output_dir / f"{company_id}_radar.png"
    plt.savefig(file_path, dpi=150, bbox_inches='tight')
    plt.close()

def main():
    print("\n--- DAY 19: RADAR CHART GENERATOR ---")
    base_dir = Path(__file__).resolve().parent.parent.parent
    db_path = base_dir / 'data' / 'nifty100.db'
    output_dir = base_dir / 'reports' / 'radar_charts'
    
    conn = sqlite3.connect(db_path)
    
    # 1. Load data
    print("Loading data and calculating Composite Scores...")
    query = """
    SELECT r.*, s.broad_sector
    FROM financial_ratios r
    LEFT JOIN sectors s ON r.company_id = s.company_id
    WHERE r.year = (SELECT MAX(year) FROM financial_ratios r2 WHERE r.company_id = r2.company_id)
    """
    df_latest = pd.read_sql_query(query, conn)
    
    # Calculate composite score on the fly (since we didn't save it to SQLite on Day 17)
    df_scored = calculate_composite_score(df_latest)
    
    # Load Percentiles
    pct_df = pd.read_sql_query("SELECT * FROM peer_percentiles", conn)
    conn.close()
    
    # 2. Prepare the 8 specific axes requested
    # We will use Percentiles where available, and scaled 0-100 scores for the rest to ensure the chart makes sense
    metrics = [
        'ROE', 'ROCE', 'Net Profit Margin', 'D/E (Lower=Better)', 
        'FCF', 'PAT CAGR 5yr', 'Rev CAGR 5yr', 'Composite Score'
    ]
    
    db_metric_map = {
        'ROE': 'return_on_equity_pct',
        'ROCE': 'roce_pct',
        'Net Profit Margin': 'net_profit_margin_pct',
        'D/E (Lower=Better)': 'debt_to_equity',
        'FCF': 'free_cash_flow_cr',
        'PAT CAGR 5yr': 'pat_cagr_5yr',
        'Rev CAGR 5yr': 'revenue_cagr_5yr'
    }

    # Calculate global averages for standalone companies
    print("Generating 92 radar charts (this may take a moment)...")
    
    generated_count = 0
    for idx, row in df_scored.iterrows():
        cid = row['company_id']
        
        # Get percentiles for this company
        company_pcts = pct_df[pct_df['company_id'] == cid]
        
        company_values = []
        peer_values = []
        is_standalone = False
        
        if company_pcts.empty:
            is_standalone = True
            
        for metric_label in metrics:
            if metric_label == 'Composite Score':
                # Use the 0-100 score we just calculated
                company_values.append(row['composite_quality_score'])
                if is_standalone:
                    peer_values.append(df_scored['composite_quality_score'].median())
                else:
                    peer_group = company_pcts.iloc[0]['peer_group_name']
                    peer_df = df_scored[df_scored['broad_sector'] == peer_group]
                    peer_values.append(peer_df['composite_quality_score'].median() if not peer_df.empty else 50)
            else:
                db_metric = db_metric_map[metric_label]
                if is_standalone:
                    # Fallback to percentile rank against the entire Nifty 100
                    val = df_scored[db_metric].rank(pct=True).loc[idx] * 100
                    if metric_label == 'D/E (Lower=Better)': val = 100 - val
                    company_values.append(val)
                    peer_values.append(50.0) # Median is always 50th percentile
                else:
                    # Get specific peer percentile
                    pct_val = company_pcts[company_pcts['metric'] == db_metric]['percentile_rank'].values
                    company_values.append(pct_val[0] if len(pct_val) > 0 else 50.0)
                    peer_values.append(50.0) # Peer median is the 50th percentile

        # Generate the visual
        create_radar_chart(
            cid, 
            np.array(company_values), 
            np.array(peer_values), 
            metrics, 
            output_dir, 
            is_standalone
        )
        generated_count += 1

    print(f"[✓] Successfully exported {generated_count} radar charts to reports/radar_charts/")

if __name__ == "__main__":
    main()
