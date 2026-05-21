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