"""Affichage formaté des blocs dans le notebook."""
import pandas as pd
from IPython.display import display, HTML

from src.utils import format_money, format_pct, safe_div


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


def display_pl(pl_data: dict, currency: str = "") -> None:
    """Bloc 2 — P&L 3Y. Table alternée valeur + ratio."""
    years = pl_data["years"]
    rows = pl_data["rows"]

    rev = rows["Revenue"]
    gp = rows["Gross Profit"]
    rd = rows["R&D"]
    sga = rows["SG&A"]
    ebit = rows["EBIT"]
    ebitda = rows["EBITDA"]
    ni = rows["Net Income"]

    def fmt_row(values):
        return [format_money(v, currency) for v in values]

    def fmt_pct_row(values):
        return [format_pct(v) for v in values]

    # YoY revenue
    yoy = [
        None,
        (rev[1] / rev[0] - 1) if (rev[0] and rev[1]) else None,
        (rev[2] / rev[1] - 1) if (rev[1] and rev[2]) else None,
    ]

    # Marges
    gm = [safe_div(gp[i], rev[i]) for i in range(3)]
    rd_pct = [safe_div(rd[i], rev[i]) for i in range(3)]
    sga_pct = [safe_div(sga[i], rev[i]) for i in range(3)]
    ebit_m = [safe_div(ebit[i], rev[i]) for i in range(3)]
    ebitda_m = [safe_div(ebitda[i], rev[i]) for i in range(3)]
    ni_m = [safe_div(ni[i], rev[i]) for i in range(3)]

    has_ebitda = any(v is not None for v in ebitda)

    table_rows = [
        ("Revenue", fmt_row(rev)),
        ("  YoY %", fmt_pct_row(yoy)),
        ("Gross Profit", fmt_row(gp)),
        ("  Gross Margin", fmt_pct_row(gm)),
        ("R&D", fmt_row(rd)),
        ("  % Revenue", fmt_pct_row(rd_pct)),
        ("SG&A", fmt_row(sga)),
        ("  % Revenue ", fmt_pct_row(sga_pct)),
        ("EBIT", fmt_row(ebit)),
        ("  EBIT Margin", fmt_pct_row(ebit_m)),
    ]
    if has_ebitda:
        table_rows.append(("EBITDA", fmt_row(ebitda)))
        table_rows.append(("  EBITDA Margin", fmt_pct_row(ebitda_m)))
    table_rows.append(("Net Income", fmt_row(ni)))
    table_rows.append(("  Net Margin", fmt_pct_row(ni_m)))

    col_labels = [f"N-2 ({years[0]})", f"N-1 ({years[1]})", f"N ({years[2]})"]
    df = pd.DataFrame(
        [vals for _, vals in table_rows],
        index=[label for label, _ in table_rows],
        columns=col_labels,
    )

    display(HTML(f"<h3>Bloc 2 — P&L 3Y ({currency})</h3>"))
    display(df)

    if not has_ebitda:
        display(HTML("<p style='font-size:11px; color:#888;'>EBITDA non disponible directement dans income_stmt.</p>"))