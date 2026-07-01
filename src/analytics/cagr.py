def calculate_cagr(start_val, end_val, periods):
    """
    Calculates CAGR and returns a tuple: (cagr_value, flag_label).
    Formula: ((end/start)^(1/n) - 1) * 100
    """
    if periods is None or periods <= 0:
        return None, "INSUFFICIENT"
        
    if start_val == 0:
        return None, "ZERO_BASE"
        
    if start_val < 0 and end_val < 0:
        return None, "BOTH_NEGATIVE"
        
    if start_val < 0 and end_val > 0:
        return None, "TURNAROUND"
        
    if start_val > 0 and end_val < 0:
        return None, "DECLINE_TO_LOSS"
        
    # Normal case (Positive to Positive, or Positive to Positive-Decline)
    cagr = ((end_val / start_val) ** (1 / periods) - 1) * 100
    return cagr, None
