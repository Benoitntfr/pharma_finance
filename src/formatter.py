"""Affichage formaté des blocs dans le notebook."""
import pandas as pd
from IPython.display import display, HTML

from src.utils import format_money


def display_identity(data: dict) -> None:
    """Bloc 1 — Identity. Affichage en 2 parties : tableau + summary."""
    currency = data.get("currency") or ""
    fin_currency = data.get("financial_currency") or currency

    rows = [
        ("Name", data.get("name") or "N/A"),
        ("Ticker", data.get("ticker") or "N/A"),
        ("Market Cap", format_money(data.get("market_cap"), currency)),
        ("Enterprise Value", format_money(data.get("enterprise_value"), currency)),
        ("Country", data.get("country") or "N/A"),
        ("Sector", data.get("sector") or "N/A"),
        ("Industry", data.get("industry") or "N/A"),
        ("Employees", f"{data.get('employees'):,}" if data.get("employees") else "N/A"),
        ("Currency (market)", currency or "N/A"),
        ("Currency (financials)", fin_currency or "N/A"),
    ]
    df = pd.DataFrame(rows, columns=["Field", "Value"])

    display(HTML("<h3>Bloc 1 — Identity</h3>"))
    display(df.style.hide(axis="index"))

    summary = data.get("summary")
    if summary:
        display(HTML(f"<p style='font-size:12px; color:#555;'><b>Summary:</b> {summary}</p>"))