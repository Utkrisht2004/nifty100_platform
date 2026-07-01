def calc_free_cash_flow(operating_activity, investing_activity):
    """FCF: CFO + CFI (Investing is typically negative, so addition nets it out)"""
    return operating_activity + investing_activity

def calc_cfo_quality_score(cfo, pat):
    """CFO / PAT. Evaluates how much paper profit translates to cash."""
    if not pat or pat == 0:
        return None, None
        
    score = cfo / pat
    if score > 1.0:
        label = "High Quality"
    elif score >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"
        
    return score, label

def calc_capex_intensity(cfi, sales):
    """abs(CFI) / Sales * 100"""
    if not sales or sales == 0:
        return None, None
        
    intensity = (abs(cfi) / sales) * 100
    if intensity < 3.0:
        label = "Asset Light"
    elif intensity <= 8.0:
        label = "Moderate"
    else:
        label = "Capital Intensive"
        
    return intensity, label

def calc_fcf_conversion(fcf, operating_profit):
    """FCF / Operating Profit * 100"""
    if not operating_profit or operating_profit == 0:
        return None
    return (fcf / operating_profit) * 100

def classify_capital_allocation(cfo, cfi, cff, cfo_quality_label=None):
    """Classifies cash flow patterns into 8 distinct strategic behaviors."""
    sign_cfo = "+" if cfo >= 0 else "-"
    sign_cfi = "+" if cfi >= 0 else "-"
    sign_cff = "+" if cff >= 0 else "-"
    
    pattern = (sign_cfo, sign_cfi, sign_cff)
    
    if pattern == ("+", "-", "-"):
        if cfo_quality_label == "High Quality":
            return "Shareholder Returns"
        return "Reinvestor"
    elif pattern == ("+", "+", "-"):
        return "Liquidating Assets"
    elif pattern == ("-", "+", "+"):
        return "Distress Signal"
    elif pattern == ("-", "-", "+"):
        return "Growth Funded by Debt"
    elif pattern == ("+", "+", "+"):
        return "Cash Accumulator"
    elif pattern == ("-", "-", "-"):
        return "Pre-Revenue"
    else: # Includes (+, -, +)
        return "Mixed"
