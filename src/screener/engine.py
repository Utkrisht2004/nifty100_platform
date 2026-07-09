import yaml
import pandas as pd

class ScreenerEngine:
    def __init__(self, config_path="config/screener_config.yaml"):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)

    def apply_filters(self, df, filters=None):
        if filters is None:
            filters = self.config.get('global_filters', {})
            
        filtered_df = df.copy()

        # 1. Profitability & Returns
        if 'roe_min' in filters:
            filtered_df = filtered_df[filtered_df['return_on_equity_pct'] >= filters['roe_min']]
        if 'opm_min' in filters:
            filtered_df = filtered_df[filtered_df['operating_profit_margin_pct'] >= filters['opm_min']]
        if 'net_profit_min' in filters:
            filtered_df = filtered_df[filtered_df['net_profit'] >= filters['net_profit_min']]

        # 2. Leverage
        if 'de_max' in filters:
            filtered_df = filtered_df[
                (filtered_df['debt_to_equity'] <= filters['de_max']) | 
                (filtered_df['broad_sector'] == 'Financials')
            ]
        if 'icr_min' in filters:
            filtered_df = filtered_df[
                (filtered_df['interest_coverage'] >= filters['icr_min']) | 
                (filtered_df['icr_label'] == 'Debt Free')
            ]

        # 3. Cash Flow
        if 'fcf_min' in filters:
            filtered_df = filtered_df[filtered_df['free_cash_flow_cr'] >= filters['fcf_min']]

        # 4. Growth
        if 'rev_cagr_5yr_min' in filters:
            filtered_df = filtered_df[filtered_df['revenue_cagr_5yr'] >= filters['rev_cagr_5yr_min']]
        if 'pat_cagr_5yr_min' in filters:
            filtered_df = filtered_df[filtered_df['pat_cagr_5yr'] >= filters['pat_cagr_5yr_min']]
        if 'eps_cagr_min' in filters:
            filtered_df = filtered_df[filtered_df['eps_cagr_5yr'] >= filters['eps_cagr_min']]

        # 5. Valuation & Dividends
        if 'pe_max' in filters:
            filtered_df = filtered_df[filtered_df['pe_ratio'] <= filters['pe_max']]
        if 'pb_max' in filters:
            filtered_df = filtered_df[filtered_df['pb_ratio'] <= filters['pb_max']]
        if 'div_yield_min' in filters:
            filtered_df = filtered_df[filtered_df['dividend_yield_pct'] >= filters['div_yield_min']]
            
        # FIX: Defensive programming - only filter if the column exists in the database
        if 'div_payout_max' in filters:
            if 'dividend_payout_ratio_pct' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['dividend_payout_ratio_pct'] <= filters['div_payout_max']]

        if 'market_cap_min' in filters:
            filtered_df = filtered_df[filtered_df['market_cap_crore'] >= filters['market_cap_min']]
            
        # 6. Efficiency
        if 'asset_turnover_min' in filters:
            filtered_df = filtered_df[filtered_df['asset_turnover'] >= filters['asset_turnover_min']]
        
        if 'sales_min' in filters:
            filtered_df = filtered_df[filtered_df['market_cap_crore'] >= filters['sales_min']]

        if 'composite_quality_score' not in filtered_df.columns:
            filtered_df['composite_quality_score'] = 0.0
            
        filtered_df = filtered_df.sort_values(by='composite_quality_score', ascending=False)
        
        return filtered_df
