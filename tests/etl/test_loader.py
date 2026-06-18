import pytest
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.etl.loader import clean_data_for_db

def test_cleaner_removes_duplicate_companies():
    dfs = {'companies.xlsx': pd.DataFrame({'id': ['TCS', 'TCS']})}
    cleaned = clean_data_for_db(dfs)
    assert len(cleaned['companies.xlsx']) == 1

def test_cleaner_drops_junk_id_column():
    dfs = {'companies.xlsx': pd.DataFrame({'id': ['TCS']}), 
           'profitandloss.xlsx': pd.DataFrame({'id': [1, 2], 'company_id': ['TCS', 'TCS'], 'year': ['2023', '2024'], 'sales': [100, 200], 'expenses': [50, 100], 'operating_profit': [50, 100]})}
    cleaned = clean_data_for_db(dfs)
    assert 'id' not in cleaned['profitandloss.xlsx'].columns

def test_cleaner_enforces_fk_integrity():
    dfs = {'companies.xlsx': pd.DataFrame({'id': ['TCS']}), 
           'profitandloss.xlsx': pd.DataFrame({'company_id': ['TCS', 'ORPHAN'], 'year': ['2023', '2023'], 'sales': [100, 200], 'expenses': [50, 100], 'operating_profit': [50, 100]})}
    cleaned = clean_data_for_db(dfs)
    assert len(cleaned['profitandloss.xlsx']) == 1

def test_cleaner_removes_duplicate_annual_rows():
    dfs = {'companies.xlsx': pd.DataFrame({'id': ['TCS']}), 
           'profitandloss.xlsx': pd.DataFrame({'company_id': ['TCS', 'TCS'], 'year': ['2023', '2023'], 'sales': [100, 200], 'expenses': [50, 100], 'operating_profit': [50, 100]})}
    cleaned = clean_data_for_db(dfs)
    assert len(cleaned['profitandloss.xlsx']) == 1

def test_cleaner_coerces_negative_fixed_assets():
    dfs = {'companies.xlsx': pd.DataFrame({'id': ['TCS']}), 
           'balancesheet.xlsx': pd.DataFrame({'company_id': ['TCS'], 'year': ['2023'], 'fixed_assets': [-50]})}
    cleaned = clean_data_for_db(dfs)
    assert cleaned['balancesheet.xlsx'].iloc[0]['fixed_assets'] == 0

def test_cleaner_preserves_positive_fixed_assets():
    dfs = {'companies.xlsx': pd.DataFrame({'id': ['TCS']}), 
           'balancesheet.xlsx': pd.DataFrame({'company_id': ['TCS'], 'year': ['2023'], 'fixed_assets': [100]})}
    cleaned = clean_data_for_db(dfs)
    assert cleaned['balancesheet.xlsx'].iloc[0]['fixed_assets'] == 100

def test_cleaner_drops_null_pnl_constraints():
    dfs = {'companies.xlsx': pd.DataFrame({'id': ['TCS']}), 
           'profitandloss.xlsx': pd.DataFrame({'company_id': ['TCS', 'TCS'], 'year': ['2023', '2024'], 'sales': [100, None], 'expenses': [50, 50], 'operating_profit': [50, 50]})}
    cleaned = clean_data_for_db(dfs)
    assert len(cleaned['profitandloss.xlsx']) == 1

def test_cleaner_handles_empty_dataframes():
    # Empty DataFrame but with the 'id' column initialized
    dfs = {'companies.xlsx': pd.DataFrame({'id': pd.Series(dtype='str')})}
    cleaned = clean_data_for_db(dfs)
    assert cleaned['companies.xlsx'].empty

def test_cleaner_sectors_deduplication():
    dfs = {'companies.xlsx': pd.DataFrame({'id': ['TCS']}), 
           'sectors.xlsx': pd.DataFrame({'company_id': ['TCS', 'TCS']})}
    cleaned = clean_data_for_db(dfs)
    assert len(cleaned['sectors.xlsx']) == 1

def test_cleaner_stock_prices_deduplication():
    dfs = {'companies.xlsx': pd.DataFrame({'id': ['TCS']}), 
           'stock_prices.xlsx': pd.DataFrame({'company_id': ['TCS', 'TCS'], 'date': ['2023-01-01', '2023-01-01']})}
    cleaned = clean_data_for_db(dfs)
    assert len(cleaned['stock_prices.xlsx']) == 1
