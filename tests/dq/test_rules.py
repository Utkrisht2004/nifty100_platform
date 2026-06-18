import pytest
import pandas as pd
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.etl.validator import DataValidator

def test_dq01_company_pk():
    validator = DataValidator({'companies.xlsx': pd.DataFrame({'id': ['TCS', 'TCS']})})
    validator._check_dq01_company_pk()
    assert validator.failures[0]['rule_id'] == 'DQ-01'

def test_dq02_annual_pk():
    validator = DataValidator({'profitandloss.xlsx': pd.DataFrame({'company_id': ['TCS', 'TCS'], 'year': ['2023-03', '2023-03']})})
    validator._check_dq02_annual_pk()
    assert validator.failures[0]['rule_id'] == 'DQ-02'

def test_dq03_fk_integrity():
    validator = DataValidator({'companies.xlsx': pd.DataFrame({'id': ['TCS']}), 'profitandloss.xlsx': pd.DataFrame({'company_id': ['ORPHAN']})})
    validator._check_dq03_fk_integrity()
    assert validator.failures[0]['rule_id'] == 'DQ-03'

def test_dq04_bs_balance():
    validator = DataValidator({'balancesheet.xlsx': pd.DataFrame({'company_id': ['TCS'], 'year': ['2023-03'], 'total_assets': [1000], 'total_liabilities': [1020]})})
    validator._check_dq04_bs_balance()
    assert validator.failures[0]['rule_id'] == 'DQ-04'

def test_dq05_opm_cross_check():
    validator = DataValidator({'profitandloss.xlsx': pd.DataFrame({'company_id': ['TCS'], 'year': ['2023-03'], 'operating_profit': [20], 'sales': [100], 'opm_percentage': [25]})})
    validator._check_dq05_opm_cross_check()
    assert validator.failures[0]['rule_id'] == 'DQ-05'

def test_dq06_zero_sales():
    validator = DataValidator({'profitandloss.xlsx': pd.DataFrame({'company_id': ['TCS'], 'year': ['2023-03'], 'sales': [0]})})
    validator._check_dq06_positive_sales()
    assert validator.failures[0]['rule_id'] == 'DQ-06'

def test_dq07_year_format():
    validator = DataValidator({'profitandloss.xlsx': pd.DataFrame({'company_id': ['TCS'], 'year': ['Mar-23']})})
    validator._check_dq07_year_format()
    assert validator.failures[0]['rule_id'] == 'DQ-07'

def test_dq08_ticker_format():
    validator = DataValidator({'companies.xlsx': pd.DataFrame({'id': [' tcs ']})})
    validator._check_dq08_ticker_format()
    assert validator.failures[0]['rule_id'] == 'DQ-08'

def test_dq09_net_cash_check():
    validator = DataValidator({'cashflow.xlsx': pd.DataFrame({'company_id': ['TCS'], 'year': ['2023-03'], 'net_cash_flow': [100], 'operating_activity': [50], 'investing_activity': [10], 'financing_activity': [10]})})
    validator._check_dq09_net_cash_check()
    assert validator.failures[0]['rule_id'] == 'DQ-09'

def test_dq10_non_negative_fixed_assets():
    validator = DataValidator({'balancesheet.xlsx': pd.DataFrame({'company_id': ['TCS'], 'year': ['2023-03'], 'fixed_assets': [-50]})})
    validator._check_dq10_non_negative_fixed_assets()
    assert validator.failures[0]['rule_id'] == 'DQ-10'

def test_dq11_tax_rate_range():
    validator = DataValidator({'profitandloss.xlsx': pd.DataFrame({'company_id': ['TCS'], 'year': ['2023-03'], 'tax_percentage': [65]})})
    validator._check_dq11_tax_rate_range()
    assert validator.failures[0]['rule_id'] == 'DQ-11'

def test_dq12_dividend_payout_cap():
    validator = DataValidator({'profitandloss.xlsx': pd.DataFrame({'company_id': ['TCS'], 'year': ['2023-03'], 'dividend_payout': [250]})})
    validator._check_dq12_dividend_payout_cap()
    assert validator.failures[0]['rule_id'] == 'DQ-12'

@patch('requests.head')
def test_dq13_url_validity(mock_head):
    mock_head.return_value.status_code = 404
    validator = DataValidator({'documents.xlsx': pd.DataFrame({'company_id': ['TCS'], 'year': ['2023-03'], 'annual_report': ['http://bad-url.com']})})
    validator._check_dq13_url_validity()
    assert validator.failures[0]['rule_id'] == 'DQ-13'

def test_dq14_eps_sign_consistency():
    validator = DataValidator({'profitandloss.xlsx': pd.DataFrame({'company_id': ['TCS'], 'year': ['2023-03'], 'net_profit': [100], 'eps': [-2.5]})})
    validator._check_dq14_eps_sign_consistency()
    assert validator.failures[0]['rule_id'] == 'DQ-14'

def test_dq15_bse_nse_balance():
    validator = DataValidator({'balancesheet.xlsx': pd.DataFrame({'company_id': ['TCS'], 'year': ['2023-03'], 'total_assets': [1000.5], 'total_liabilities': [1000.4]})})
    validator._check_dq15_bse_nse_balance()
    assert validator.failures[0]['rule_id'] == 'DQ-15'

def test_dq16_coverage_check():
    validator = DataValidator({'profitandloss.xlsx': pd.DataFrame({'company_id': ['TCS']*4, 'year': ['2020', '2021', '2022', '2023']})})
    validator._check_dq16_coverage_check()
    assert validator.failures[0]['rule_id'] == 'DQ-16'
