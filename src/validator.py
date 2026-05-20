import yfinance as yf
from curl_cffi import requests as curl_requests

_session = curl_requests.Session(impersonate="chrome")


def validate_ticker(ticker: str) -> dict:
    """Retourne le dict info yfinance si ticker valide, raise ValueError sinon."""
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("Ticker vide.")

    info = yf.Ticker(ticker, session=_session).info

    has_name = bool(info.get("longName") or info.get("shortName"))
    has_price = bool(info.get("currentPrice") or info.get("regularMarketPrice"))

    if not (has_name and has_price):
        raise ValueError(f"Ticker '{ticker}' introuvable ou données indisponibles.")

    return info