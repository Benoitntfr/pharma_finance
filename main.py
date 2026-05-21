import sys

from src.validator import validate_ticker
from src.fetcher import fetch_identity, fetch_pl, fetch_balance_sheet, fetch_cash_flow
from src.formatter import (
    display_identity,
    display_pl,
    display_balance_sheet,
    display_cash_flow,
    display_ratios,
)
from src.ratios import compute_ratios
from src.exporter import export_to_excel, download_if_colab


def run_analysis(ticker: str) -> None:
    try:
        ticker_obj, info = validate_ticker(ticker)
    except Exception as e:
        print(f"❌ {e}")
        return

    currency = info.get("financialCurrency") or info.get("currency") or ""
    ticker_clean = info.get("symbol", ticker.upper())

    # Bloc 1 — Identity
    identity = None
    try:
        identity = fetch_identity(info)
        display_identity(identity)
    except Exception as e:
        print(f"⚠️ Bloc 1 (Identity) failed: {e}")

    # Bloc 2 — P&L 3Y
    pl_data = None
    try:
        pl_data = fetch_pl(ticker_obj)
        display_pl(pl_data, currency)
    except Exception as e:
        print(f"⚠️ Bloc 2 (P&L 3Y) failed: {e}")

    # Bloc 3 — Balance Sheet
    bs_data = None
    try:
        bs_data = fetch_balance_sheet(ticker_obj)
        display_balance_sheet(bs_data, currency)
    except Exception as e:
        print(f"⚠️ Bloc 3 (Balance Sheet) failed: {e}")

    # Bloc 4 — Cash Flow
    cf_data = None
    try:
        cf_data = fetch_cash_flow(ticker_obj)
        display_cash_flow(cf_data, currency)
    except Exception as e:
        print(f"⚠️ Bloc 4 (Cash Flow) failed: {e}")

    # Bloc 5 — Ratios
    ratios = None
    if pl_data and bs_data and cf_data:
        try:
            ratios = compute_ratios(info, pl_data, bs_data, cf_data)
            display_ratios(ratios, currency)
        except Exception as e:
            print(f"⚠️ Bloc 5 (Ratios) failed: {e}")
    else:
        print("⚠️ Bloc 5 (Ratios) skipped : un des blocs 2/3/4 a échoué.")

    # Export Excel (auto si tous les blocs sont OK)
    if identity and pl_data and bs_data and cf_data and ratios:
        try:
            filepath = export_to_excel(
                ticker_clean, info, identity, pl_data, bs_data, cf_data, ratios, currency
            )
            download_if_colab(filepath)
        except Exception as e:
            print(f"⚠️ Export Excel failed: {e}")
    else:
        print("⚠️ Export Excel skipped : un des blocs a échoué.")


def in_jupyter() -> bool:
    return "ipykernel" in sys.modules


if in_jupyter():
    ticker = input("Ticker : ").strip()
    run_analysis(ticker)
elif __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else input("Ticker : ")
    run_analysis(ticker)