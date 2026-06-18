import pandas as pd
import numpy as np
import re
import requests

class DataValidator:
    def __init__(self, dfs_dict):
        self.dfs = dfs_dict
        self.failures = []

    def log_failure(self, rule_id, severity, company_id, year, field, issue):
        self.failures.append({
            "rule_id": rule_id, "severity": severity, "company_id": company_id,
            "year": year, "field": field, "issue": issue
        })

    def run_all_rules(self):
        self._check_dq01_company_pk()
        self._check_dq02_annual_pk()
        self._check_dq03_fk_integrity()
        self._check_dq04_bs_balance()
        self._check_dq05_opm_cross_check()
        self._check_dq06_positive_sales()
        self._check_dq07_year_format()
        self._check_dq08_ticker_format()
        self._check_dq09_net_cash_check()
        self._check_dq10_non_negative_fixed_assets()
        self._check_dq11_tax_rate_range()
        self._check_dq12_dividend_payout_cap()
        self._check_dq13_url_validity()
        self._check_dq14_eps_sign_consistency()
        self._check_dq15_bse_nse_balance()
        self._check_dq16_coverage_check()
        
        return pd.DataFrame(self.failures, columns=["rule_id", "severity", "company_id", "year", "field", "issue"])

    def _check_dq01_company_pk(self):
        if 'companies.xlsx' in self.dfs:
            df = self.dfs['companies.xlsx']
            if not df.empty and 'id' in df.columns:
                dupes = df[df.duplicated('id', keep=False)]
                for _, row in dupes.iterrows():
                    self.log_failure("DQ-01", "CRITICAL", row['id'], None, "id", "Duplicate company ticker")

    def _check_dq02_annual_pk(self):
        for table in ['profitandloss.xlsx', 'balancesheet.xlsx', 'cashflow.xlsx']:
            if table in self.dfs:
                df = self.dfs[table]
                if not df.empty and all(c in df.columns for c in ['company_id', 'year']):
                    dupes = df[df.duplicated(['company_id', 'year'], keep=False)]
                    for _, row in dupes.iterrows():
                        self.log_failure("DQ-02", "CRITICAL", row['company_id'], row['year'], "company_id+year", f"Duplicate in {table}")

    def _check_dq03_fk_integrity(self):
        valid_companies = set()
        if 'companies.xlsx' in self.dfs and 'id' in self.dfs['companies.xlsx'].columns:
            valid_companies = set(self.dfs['companies.xlsx']['id'].dropna())

        for table in ['profitandloss.xlsx', 'balancesheet.xlsx', 'cashflow.xlsx']:
            if table in self.dfs:
                df = self.dfs[table]
                if not df.empty and 'company_id' in df.columns:
                    invalid_fks = df[~df['company_id'].isin(valid_companies)]
                    for _, row in invalid_fks.iterrows():
                        self.log_failure("DQ-03", "CRITICAL", row['company_id'], row.get('year'), "company_id", f"Orphan record in {table}")

    def _check_dq04_bs_balance(self):
        if 'balancesheet.xlsx' in self.dfs:
            df = self.dfs['balancesheet.xlsx']
            if not df.empty and all(c in df.columns for c in ['company_id', 'year', 'total_assets', 'total_liabilities']):
                for _, row in df.iterrows():
                    assets = pd.to_numeric(row['total_assets'], errors='coerce')
                    liabs = pd.to_numeric(row['total_liabilities'], errors='coerce')
                    if pd.notna(assets) and pd.notna(liabs):
                        if assets == 0 or abs((assets - liabs) / assets) > 0.01:
                            self.log_failure("DQ-04", "WARNING", row['company_id'], row['year'], "total_assets/liabilities", f"Mismatch: Assets={assets}, Liabs={liabs}")

    def _check_dq05_opm_cross_check(self):
        if 'profitandloss.xlsx' in self.dfs:
            df = self.dfs['profitandloss.xlsx']
            req_cols = ['company_id', 'year', 'operating_profit', 'sales', 'opm_percentage']
            if not df.empty and all(c in df.columns for c in req_cols):
                for _, row in df.iterrows():
                    op, sales, opm = pd.to_numeric(row['operating_profit'], errors='coerce'), pd.to_numeric(row['sales'], errors='coerce'), pd.to_numeric(row['opm_percentage'], errors='coerce')
                    if pd.notna(op) and pd.notna(sales) and pd.notna(opm) and sales != 0:
                        calculated_opm = (op / sales) * 100
                        if abs(calculated_opm - opm) > 1.0:
                            self.log_failure("DQ-05", "WARNING", row['company_id'], row['year'], "opm_percentage", f"Calculated {calculated_opm:.1f} vs Source {opm}")

    def _check_dq06_positive_sales(self):
        if 'profitandloss.xlsx' in self.dfs:
            df = self.dfs['profitandloss.xlsx']
            if not df.empty and all(c in df.columns for c in ['company_id', 'year', 'sales']):
                for _, row in df.iterrows():
                    sales = pd.to_numeric(row['sales'], errors='coerce')
                    if pd.notna(sales) and sales <= 0:
                        self.log_failure("DQ-06", "WARNING", row['company_id'], row['year'], "sales", f"Sales <= 0 ({sales})")

    def _check_dq07_year_format(self):
        for table in ['profitandloss.xlsx', 'balancesheet.xlsx', 'cashflow.xlsx']:
            if table in self.dfs:
                df = self.dfs[table]
                if not df.empty and 'year' in df.columns:
                    invalid_years = df[~df['year'].astype(str).str.match(r"^\d{4}-\d{2}$", na=False)]
                    for _, row in invalid_years.iterrows():
                        self.log_failure("DQ-07", "WARNING", row.get('company_id'), row['year'], "year", f"Invalid format in {table}")

    def _check_dq08_ticker_format(self):
        if 'companies.xlsx' in self.dfs:
            df = self.dfs['companies.xlsx']
            if not df.empty and 'id' in df.columns:
                invalid_tickers = df[df['id'] != df['id'].astype(str).str.strip().str.upper()]
                for _, row in invalid_tickers.iterrows():
                    self.log_failure("DQ-08", "WARNING", row['id'], None, "id", "Unnormalized ticker")

    def _check_dq09_net_cash_check(self):
        if 'cashflow.xlsx' in self.dfs:
            df = self.dfs['cashflow.xlsx']
            req_cols = ['company_id', 'year', 'net_cash_flow', 'operating_activity', 'investing_activity', 'financing_activity']
            if not df.empty and all(c in df.columns for c in req_cols):
                for _, row in df.iterrows():
                    ncf, cfo, cfi, cff = [pd.to_numeric(row[c], errors='coerce') for c in req_cols[2:]]
                    if all(pd.notna(x) for x in [ncf, cfo, cfi, cff]):
                        if abs(ncf - (cfo + cfi + cff)) > 10:
                            self.log_failure("DQ-09", "WARNING", row['company_id'], row['year'], "net_cash_flow", "Cash sum mismatch")

    def _check_dq10_non_negative_fixed_assets(self):
        if 'balancesheet.xlsx' in self.dfs:
            df = self.dfs['balancesheet.xlsx']
            if not df.empty and all(c in df.columns for c in ['company_id', 'year', 'fixed_assets']):
                for _, row in df.iterrows():
                    fa = pd.to_numeric(row['fixed_assets'], errors='coerce')
                    if pd.notna(fa) and fa < 0:
                        self.log_failure("DQ-10", "WARNING", row['company_id'], row['year'], "fixed_assets", "Negative fixed assets")

    def _check_dq11_tax_rate_range(self):
        if 'profitandloss.xlsx' in self.dfs:
            df = self.dfs['profitandloss.xlsx']
            if not df.empty and all(c in df.columns for c in ['company_id', 'year', 'tax_percentage']):
                for _, row in df.iterrows():
                    tax = pd.to_numeric(row['tax_percentage'], errors='coerce')
                    if pd.notna(tax) and (tax < 0 or tax > 60):
                        self.log_failure("DQ-11", "WARNING", row['company_id'], row['year'], "tax_percentage", f"Out of range: {tax}")

    def _check_dq12_dividend_payout_cap(self):
        if 'profitandloss.xlsx' in self.dfs:
            df = self.dfs['profitandloss.xlsx']
            if not df.empty and all(c in df.columns for c in ['company_id', 'year', 'dividend_payout']):
                for _, row in df.iterrows():
                    div = pd.to_numeric(row['dividend_payout'], errors='coerce')
                    if pd.notna(div) and div > 200:
                        self.log_failure("DQ-12", "WARNING", row['company_id'], row['year'], "dividend_payout", f"Cap exceeded: {div}")

    def _check_dq13_url_validity(self):
        if 'documents.xlsx' in self.dfs:
            df = self.dfs['documents.xlsx']
            if not df.empty and all(c in df.columns for c in ['company_id', 'year', 'annual_report']):
                for _, row in df.iterrows():
                    url = str(row['annual_report'])
                    if url.startswith('http'):
                        try:
                            # Use short timeout, ignore actual failures in fast testing
                            res = requests.head(url, timeout=2)
                            if res.status_code >= 400:
                                self.log_failure("DQ-13", "WARNING", row['company_id'], row['year'], "annual_report", f"URL returning {res.status_code}")
                        except:
                            self.log_failure("DQ-13", "WARNING", row['company_id'], row['year'], "annual_report", "URL unreachable")

    def _check_dq14_eps_sign_consistency(self):
        if 'profitandloss.xlsx' in self.dfs:
            df = self.dfs['profitandloss.xlsx']
            if not df.empty and all(c in df.columns for c in ['company_id', 'year', 'net_profit', 'eps']):
                for _, row in df.iterrows():
                    np_val, eps = pd.to_numeric(row['net_profit'], errors='coerce'), pd.to_numeric(row['eps'], errors='coerce')
                    if pd.notna(np_val) and pd.notna(eps):
                        if np_val > 0 and eps <= 0:
                            self.log_failure("DQ-14", "WARNING", row['company_id'], row['year'], "eps", "EPS mismatch with positive net profit")

    def _check_dq15_bse_nse_balance(self):
        if 'balancesheet.xlsx' in self.dfs:
            df = self.dfs['balancesheet.xlsx']
            if not df.empty and all(c in df.columns for c in ['company_id', 'year', 'total_assets', 'total_liabilities']):
                for _, row in df.iterrows():
                    assets, liabs = pd.to_numeric(row['total_assets'], errors='coerce'), pd.to_numeric(row['total_liabilities'], errors='coerce')
                    if pd.notna(assets) and pd.notna(liabs) and assets != liabs:
                        self.log_failure("DQ-15", "INFO", row['company_id'], row['year'], "balance", "Strict balance mismatch")

    def _check_dq16_coverage_check(self):
        for table in ['profitandloss.xlsx', 'balancesheet.xlsx', 'cashflow.xlsx']:
            if table in self.dfs:
                df = self.dfs[table]
                if not df.empty and 'company_id' in df.columns:
                    counts = df['company_id'].value_counts()
                    low_coverage = counts[counts < 5]
                    for comp_id, _ in low_coverage.items():
                        self.log_failure("DQ-16", "WARNING", comp_id, None, "coverage", f"< 5 years data in {table}")

    def export_failures(self, output_path="output/validation_failures.csv"):
        df_failures = pd.DataFrame(self.failures)
        if not df_failures.empty:
            df_failures.to_csv(output_path, index=False)
        return df_failures
