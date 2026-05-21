"""Extraction des données yfinance par bloc."""
from src.utils import safe_get


def fetch_identity(info: dict) -> dict:
    """Bloc 1 — Identity. Tout depuis info."""
    return {
        "name": safe_get(info, "longName") or safe_get(info, "shortName"),
        "ticker": safe_get(info, "symbol"),
        "market_cap": safe_get(info, "marketCap"),
        "enterprise_value": safe_get(info, "enterpriseValue"),
        "country": safe_get(info, "country"),
        "sector": safe_get(info, "sector"),
        "industry": safe_get(info, "industry"),
        "employees": safe_get(info, "fullTimeEmployees"),
        "currency": safe_get(info, "currency"),
        "financial_currency": safe_get(info, "financialCurrency"),
        "summary": safe_get(info, "longBusinessSummary"),
    }

import yfinance as yf
from src.utils import find_row, get_col_value, safe_div


# Mapping des lignes P&L : nom métrique → liste de candidats yfinance
PL_ROWS = {
    "Revenue": ["Total Revenue"],
    "COGS": ["Cost Of Revenue"],
    "Gross Profit": ["Gross Profit"],
    "R&D": ["Research And Development", "Research Development"],
    "SG&A": [
        "Selling General And Administration",
        "Selling General And Administrative Expense",
        "Selling General And Administrative",
    ],
    "EBIT": ["Operating Income", "EBIT"],
    "EBITDA": ["EBITDA"],
    "Net Income": ["Net Income", "Net Income Common Stockholders"],
    "Tax Provision": ["Tax Provision", "Income Tax Expense"],
    "Pretax Income": ["Pretax Income", "Income Before Tax"],
}


def fetch_pl(ticker_obj) -> dict:
    """
    Bloc 2 — P&L 3Y.
    Retourne dict avec :
    - 'years' : liste de 3 dates (les 3 plus récentes)
    - 'rows' : dict {metric_name: [val_N-2, val_N-1, val_N]}
    """
    income_stmt = ticker_obj.income_stmt
    if income_stmt is None or income_stmt.empty:
        raise ValueError("Income statement indisponible.")

    # yfinance ordonne les colonnes de la plus récente à la plus ancienne
    # On prend les 3 premières (= 3 dernières années), puis on inverse pour N-2, N-1, N
    cols = income_stmt.columns[:3][::-1]
    years = [c.year for c in cols]

    rows = {}
    for metric, candidates in PL_ROWS.items():
        series = find_row(income_stmt, candidates)
        if series is None:
            rows[metric] = [None, None, None]
        else:
            # Réordonner selon cols (inversé)
            rows[metric] = [series.get(c) for c in cols]

    return {"years": years, "rows": rows}

# Mapping Balance Sheet : nom métrique → candidats yfinance
BS_ROWS = {
    "Total Assets": ["Total Assets"],
    "Current Assets": ["Current Assets", "Total Current Assets"],
    "Non-Current Assets": [
        "Total Non Current Assets",
        "Non Current Assets",
    ],
    "Total Liabilities": [
        "Total Liabilities Net Minority Interest",
        "Total Liabilities",
    ],
    "Current Liabilities": ["Current Liabilities", "Total Current Liabilities"],
    "Non-Current Liabilities": [
        "Total Non Current Liabilities Net Minority Interest",
        "Total Non Current Liabilities",
        "Non Current Liabilities",
    ],
    "Total Equity": [
        "Stockholders Equity",
        "Total Equity Gross Minority Interest",
        "Common Stock Equity",
    ],
    "Cash & ST Investments": [
        "Cash Cash Equivalents And Short Term Investments",
        "Cash And Cash Equivalents",
    ],
    "Current Debt": ["Current Debt", "Current Debt And Capital Lease Obligation"],
    "Long-Term Debt": [
        "Long Term Debt",
        "Long Term Debt And Capital Lease Obligation",
    ],
    "Total Debt": ["Total Debt"],
    "Goodwill": ["Goodwill"],
    "Intangible Assets": ["Other Intangible Assets", "Intangible Assets"],
}


def fetch_balance_sheet(ticker_obj) -> dict:
    """
    Bloc 3 — Balance Sheet N-1, N.
    Retourne dict avec years (2 dates) et rows {metric: [val_N-1, val_N]}.
    """
    bs = ticker_obj.balance_sheet
    if bs is None or bs.empty:
        raise ValueError("Balance sheet indisponible.")

    # 2 dernières années, ordre N-1, N
    cols = bs.columns[:2][::-1]
    years = [c.year for c in cols]

    rows = {}
    for metric, candidates in BS_ROWS.items():
        series = find_row(bs, candidates)
        if series is None:
            rows[metric] = [None, None]
        else:
            rows[metric] = [series.get(c) for c in cols]

    return {"years": years, "rows": rows}

# Mapping Cash Flow : nom métrique → candidats yfinance
CF_ROWS = {
    "CFO": ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"],
    "CFI": ["Investing Cash Flow", "Cash Flow From Continuing Investing Activities"],
    "CFF": ["Financing Cash Flow", "Cash Flow From Continuing Financing Activities"],
    "CapEx": ["Capital Expenditure", "Capital Expenditures"],
    "FCF": ["Free Cash Flow"],
    "D&A": [
        "Depreciation And Amortization",
        "Depreciation Amortization Depletion",
        "Reconciled Depreciation",
    ],
    "Dividends Paid": ["Cash Dividends Paid", "Common Stock Dividend Paid"],
    "Buybacks": [
        "Repurchase Of Capital Stock",
        "Common Stock Payments",
    ],
}


def fetch_cash_flow(ticker_obj) -> dict:
    """Bloc 4 — Cash Flow 3Y. Retourne dict avec years (3 dates) et rows."""
    cf = ticker_obj.cashflow
    if cf is None or cf.empty:
        raise ValueError("Cash flow statement indisponible.")

    cols = cf.columns[:3][::-1]
    years = [c.year for c in cols]

    rows = {}
    for metric, candidates in CF_ROWS.items():
        series = find_row(cf, candidates)
        if series is None:
            rows[metric] = [None, None, None]
        else:
            rows[metric] = [series.get(c) for c in cols]

    return {"years": years, "rows": rows}