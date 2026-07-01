import pytest
import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.analytics.ratios import (
    calc_net_profit_margin, calc_operating_profit_margin, calc_return_on_equity, 
    calc_return_on_capital_employed, calc_return_on_assets,
    calc_debt_to_equity, calc_interest_coverage_ratio, calc_net_debt, calc_asset_turnover
)

# --- DAY 08 TESTS ---
def test_npm_normal_case():
    assert calc_net_profit_margin(net_profit=20, sales=100) == 20.0
def test_npm_zero_denominator():
    assert calc_net_profit_margin(net_profit=20, sales=0) is None
def test_opm_normal_case():
    assert calc_operating_profit_margin(operating_profit=25, sales=100) == 25.0
def test_opm_cross_check_mismatch(caplog):
    with caplog.at_level(logging.INFO):
        res = calc_operating_profit_margin(operating_profit=30, sales=100, source_opm=25.0, company_id="TCS", year="2023")
        assert res == 30.0
        assert "OPM Mismatch" in caplog.text
def test_roe_normal_case():
    assert calc_return_on_equity(net_profit=15, equity_capital=10, reserves=40) == 30.0
def test_roe_negative_equity():
    assert calc_return_on_equity(net_profit=15, equity_capital=10, reserves=-20) is None
def test_roce_normal_case():
    assert calc_return_on_capital_employed(ebit=20, equity_capital=10, reserves=40, borrowings=50) == 20.0
def test_roa_normal_case():
    assert calc_return_on_assets(net_profit=10, total_assets=200) == 5.0
def test_roa_zero_assets():
    assert calc_return_on_assets(net_profit=10, total_assets=0) is None


# --- DAY 09 TESTS ---
def test_de_normal_case():
    de, flag = calc_debt_to_equity(borrowings=100, equity_capital=10, reserves=40)
    assert de == 2.0
    assert flag is False

def test_de_debt_free_returns_zero():
    de, flag = calc_debt_to_equity(borrowings=0, equity_capital=10, reserves=40)
    assert de == 0.0
    assert flag is False

def test_de_high_leverage_flag():
    de, flag = calc_debt_to_equity(borrowings=600, equity_capital=10, reserves=90)
    assert de == 6.0
    assert flag is True

def test_de_financial_suppresses_flag():
    de, flag = calc_debt_to_equity(borrowings=600, equity_capital=10, reserves=90, is_financial=True)
    assert de == 6.0
    assert flag is False

def test_icr_normal_case():
    icr, label, flag = calc_interest_coverage_ratio(operating_profit=50, other_income=10, interest=20)
    assert icr == 3.0
    assert label == "Healthy"
    assert flag is False

def test_icr_interest_zero_returns_none_debt_free():
    icr, label, flag = calc_interest_coverage_ratio(operating_profit=50, other_income=10, interest=0)
    assert icr is None
    assert label == "Debt Free"
    assert flag is False

def test_icr_warning_flag():
    icr, label, flag = calc_interest_coverage_ratio(operating_profit=10, other_income=2, interest=10)
    assert icr == 1.2
    assert label == "At Risk"
    assert flag is True

def test_net_debt():
    assert calc_net_debt(borrowings=100, investments=40) == 60

def test_asset_turnover():
    assert calc_asset_turnover(sales=500, total_assets=250) == 2.0
    assert calc_asset_turnover(sales=500, total_assets=0) is None
