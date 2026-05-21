import sys

from src.validator import validate_ticker
from src.fetcher import fetch_identity
from src.formatter import display_identity


def run_analysis(ticker: str) -> None:
    """Pipeline complet : validate → fetch → display."""
    try:
        info = validate_ticker(ticker)
    except Exception as e:
        print(f"❌ {e}")
        return

    # Bloc 1 — Identity
    try:
        identity = fetch_identity(info)
        display_identity(identity)
    except Exception as e:
        print(f"⚠️ Bloc 1 (Identity) failed: {e}")


def in_jupyter() -> bool:
    return "ipykernel" in sys.modules


if in_jupyter():
    ticker = input("Ticker : ").strip()
    run_analysis(ticker)
elif __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else input("Ticker : ")
    run_analysis(ticker)