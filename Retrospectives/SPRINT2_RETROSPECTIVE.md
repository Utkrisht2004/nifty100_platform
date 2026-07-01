## Sprint 2 Retrospective: Financial Ratio Engine

### 1. Sprint Goals Summary
* **Objective:** Architect a scalable mathematical engine to compute 50+ financial KPIs across 92 Nifty 100 companies, handling all accounting edge cases.
* **Outcome:** `financial_ratios` table populated with over 1,100 rows of clean, calculated metrics. Screener successfully identifies high-ROE/low-Debt candidates.

### 2. Key Technical Achievements
* **Mathematical Integrity:** Engineered robust Python functions (`ratios.py`, `cagr.py`, `cashflow_kpis.py`) that strictly handle zero-division, negative bases, and missing variables.
* **Capital Allocation Classifier:** Built an 8-pattern cash flow logic engine to categorize companies by financial maturity (e.g., Reinvestor, Cash Accumulator, Distress Signal).
* **Dynamic Year Querying:** Solved a critical fiscal calendar anomaly (where companies report ending months differently) using correlated subqueries in SQLite to ensure cross-company screening always utilizes the latest available data.

### 3. Edge Cases Handled
* **CAGR Anomalies:** Trapped 6 distinct edge cases, including negative-to-positive turnarounds and zero-base anomalies, outputting specific flags instead of mathematical crashes.
* **Financial Sector Exemption:** Built logic to exempt banking and NBFC institutions from standard high-leverage D/E warnings, as high debt is structurally normal for these entities.
* **Data Discrepancies:** Generated an automated edge-case log capturing 782 expected anomalies where strict formulaic calculation of OPM/ROCE deviated from the raw source provider's approximations.

### 4. Sprint Metrics
* **Tests:** 37/37 Unit Tests passing cleanly.
* **Output:** Generated `capital_allocation.csv` and fully populated SQLite `financial_ratios` table.
