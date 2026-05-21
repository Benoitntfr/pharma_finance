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

def display_balance_sheet(bs_data: dict, currency: str = "") -> None:
    """Bloc 3 — Balance Sheet N-1, N. Avec checks de cohérence."""
    years = bs_data["years"]
    rows = bs_data["rows"]

    def fmt_row(values):
        return [format_money(v, currency) for v in values]

    def fmt_pct_row(values):
        return [format_pct(v) for v in values]

    # Calculs dérivés
    ta = rows["Total Assets"]
    tl = rows["Total Liabilities"]
    eq = rows["Total Equity"]
    cash = rows["Cash & ST Investments"]
    debt = rows["Total Debt"]
    gw = rows["Goodwill"]

    # Net Debt = Total Debt - Cash
    net_debt = [
        (debt[i] - cash[i]) if (debt[i] is not None and cash[i] is not None) else None
        for i in range(2)
    ]

    # Goodwill / Total Assets
    gw_ratio = [safe_div(gw[i], ta[i]) for i in range(2)]

    table_rows = [
        ("Total Assets", fmt_row(ta)),
        ("  Current Assets", fmt_row(rows["Current Assets"])),
        ("  Non-Current Assets", fmt_row(rows["Non-Current Assets"])),
        ("Total Liabilities", fmt_row(tl)),
        ("  Current Liabilities", fmt_row(rows["Current Liabilities"])),
        ("  Non-Current Liabilities", fmt_row(rows["Non-Current Liabilities"])),
        ("Total Equity", fmt_row(eq)),
        ("Cash & ST Investments", fmt_row(cash)),
        ("Current Debt", fmt_row(rows["Current Debt"])),
        ("Long-Term Debt", fmt_row(rows["Long-Term Debt"])),
        ("Total Debt", fmt_row(debt)),
        ("Net Debt", fmt_row(net_debt)),
        ("Goodwill", fmt_row(gw)),
        ("  GW / Total Assets", fmt_pct_row(gw_ratio)),
        ("Intangible Assets", fmt_row(rows["Intangible Assets"])),
    ]

    col_labels = [f"N-1 ({years[0]})", f"N ({years[1]})"]
    df = pd.DataFrame(
        [vals for _, vals in table_rows],
        index=[label for label, _ in table_rows],
        columns=col_labels,
    )

    display(HTML(f"<h3>Bloc 3 — Balance Sheet ({currency})</h3>"))
    display(df)

    # Checks de cohérence (sur N)
    _display_bs_checks(ta[1], tl[1], eq[1], gw[1], currency)


def _display_bs_checks(ta, tl, eq, gw, currency: str) -> None:
    """Checks intra-Bloc 3 sur la dernière année."""
    checks_html = "<h4 style='margin-top:12px;'>Checks de cohérence (N)</h4><ul style='font-size:13px;'>"

    # Check 1 : A = L + E
    if ta is not None and tl is not None and eq is not None:
        sum_le = tl + eq
        diff_pct = abs(ta - sum_le) / ta if ta != 0 else 0
        if diff_pct < 0.01:
            checks_html += (
                f"<li style='color:green;'>✓ Equation comptable : "
                f"Total Assets = {format_money(ta, currency)} ≈ "
                f"L+E = {format_money(sum_le, currency)} "
                f"(écart {diff_pct*100:.2f}%)</li>"
            )
        else:
            checks_html += (
                f"<li style='color:red;'>✗ Equation comptable : "
                f"Total Assets = {format_money(ta, currency)} ≠ "
                f"L+E = {format_money(sum_le, currency)} "
                f"(écart {diff_pct*100:.2f}%)</li>"
            )
    else:
        checks_html += "<li style='color:gray;'>⊘ Equation comptable : données manquantes</li>"

    # Check 2 : Goodwill / Total Assets > 40%
    if gw is not None and ta is not None and ta != 0:
        gw_ratio = gw / ta
        if gw_ratio > 0.40:
            checks_html += (
                f"<li style='color:red;'>⚠ Goodwill / Total Assets = "
                f"{gw_ratio*100:.1f}% > 40% (entreprise construite par M&A, "
                f"risque impairment)</li>"
            )
        else:
            checks_html += (
                f"<li style='color:green;'>✓ Goodwill / Total Assets = "
                f"{gw_ratio*100:.1f}% (sous le seuil 40%)</li>"
            )
    else:
        checks_html += "<li style='color:gray;'>⊘ Goodwill / Total Assets : pas de goodwill ou données manquantes</li>"

    checks_html += "</ul>"
    display(HTML(checks_html))