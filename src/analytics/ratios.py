import logging

# Setup basic logging for the ratio engine edge cases
logger = logging.getLogger("ratio_engine")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("output/ratio_edge_cases.log")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(file_handler)

# --- DAY 08: Profitability Ratios ---
def calc_net_profit_margin(net_profit, sales):
    if not sales or sales == 0: return None
    return (net_profit / sales) * 100

def calc_operating_profit_margin(operating_profit, sales, source_opm=None, company_id=None, year=None):
    if not sales or sales == 0: return None
    calculated_opm = (operating_profit / sales) * 100
    if source_opm is not None and abs(calculated_opm - source_opm) > 1.0:
        logger.info(f"OPM Mismatch | {company_id} ({year}): Calc={calculated_opm:.2f}%, Source={source_opm}%")
    return calculated_opm

def calc_return_on_equity(net_profit, equity_capital, reserves):
    denominator = equity_capital + reserves
    if denominator <= 0: return None
    return (net_profit / denominator) * 100

def calc_return_on_capital_employed(ebit, equity_capital, reserves, borrowings, is_financial=False):
    denominator = equity_capital + reserves + borrowings
    if denominator == 0: return None
    return (ebit / denominator) * 100

def calc_return_on_assets(net_profit, total_assets):
    if not total_assets or total_assets == 0: return None
    return (net_profit / total_assets) * 100


# --- DAY 09: Leverage & Efficiency Ratios ---
def calc_debt_to_equity(borrowings, equity_capital, reserves, is_financial=False):
    """Returns (D/E ratio, high_leverage_flag)"""
    if borrowings == 0 or not borrowings:
        return 0.0, False  # Debt-free
    
    denominator = equity_capital + reserves
    if denominator <= 0:
        return None, False
        
    de_ratio = borrowings / denominator
    high_leverage_flag = (de_ratio > 5.0) and not is_financial
    return de_ratio, high_leverage_flag

def calc_interest_coverage(operating_profit, other_income, interest):
    """Returns (ICR, label, warning_flag)"""
    if not interest or interest == 0:
        return None, "Debt Free", False
        
    icr = (operating_profit + (other_income or 0)) / interest
    warning_flag = icr < 1.5
    label = "At Risk" if warning_flag else "Healthy"
    return icr, label, warning_flag

def calc_net_debt(borrowings, investments):
    borr = borrowings or 0
    inv = investments or 0
    return borr - inv

def calc_asset_turnover(sales, total_assets):
    if not total_assets or total_assets == 0: return None
    return sales / total_assets
