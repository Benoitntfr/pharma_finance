import sys

from src.validator import validate_ticker
from src.fetcher import fetch_identity, fetch_pl, fetch_balance_sheet
from src.formatter import display_identity, display_pl, display_balance_sheet


def run_analysis(ticker: str) -> None:
    try:
        ticker_obj, info = validate_ticker(ticker)
    except Exception as e:
        print(f"❌ {e}")
        return

    currency = info.get("financialCurrency") or info.get("currency") or ""

    # Bloc 1 — Identity
    try:
        identity = fetch_identity(info)
        display_identity(identity)
    except Exception as e:
        print(f"⚠️ Bloc 1 (Identity) failed: {e}")

    # Bloc 2 — P&L 3Y
    try:
        pl_data = fetch_pl(ticker_obj)
        display_pl(pl_data, currency)
    except Exception as e:
        print(f"⚠️ Bloc 2 (P&L 3Y) failed: {e}")

    # Bloc 3 — Balance Sheet N-1, N
    try:
        bs_data = fetch_balance_sheet(ticker_obj)
        display_balance_sheet(bs_data, currency)
    except Exception as e:
        print(f"⚠️ Bloc 3 (Balance Sheet) failed: {e}")


def in_jupyter() -> bool:
    return "ipykernel" in sys.modules


if in_jupyter():
    ticker = input("Ticker : ").strip()
    run_analysis(ticker)
elif __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else input("Ticker : ")
    run_analysis(ticker)