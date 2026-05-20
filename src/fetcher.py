def fetch_basics(info: dict) -> dict:
    """Extrait les infos basiques depuis le dict info yfinance."""
    return {
        "name": info.get("longName") or info.get("shortName"),
        "ticker": info.get("symbol"),
        "price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "currency": info.get("currency"),
    }