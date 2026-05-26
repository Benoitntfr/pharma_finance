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


def display_cash_flow(cf_data: dict, currency: str = "") -> None:
    """Bloc 4 — Cash Flow 3Y structuré : Start → CFO → CFI → CFF → Net Change."""
    years = cf_data["years"]
    rows = cf_data["rows"]

    def fmt_row(values):
        return [format_money(v, currency) for v in values]

    # Helpers d'agrégation
    def sum_row(*lists):
        """Somme position par position, en ignorant les None."""
        result = []
        for i in range(3):
            vals = [lst[i] for lst in lists if lst[i] is not None]
            result.append(sum(vals) if vals else None)
        return result

    ni = rows["Net Income"]
    da = rows["D&A"]
    sbc = rows["Stock-Based Compensation"]
    def_tax = rows["Deferred Taxes"]
    other_nc = rows["Other Non-Cash"]
    d_rec = rows["Δ Receivables"]
    d_inv = rows["Δ Inventory"]
    d_pay = rows["Δ Payables"]
    d_other_wc = rows["Δ Other WC"]
    total_d_wc = rows["Total Δ WC"]
    cfo = rows["CFO"]

    capex = rows["CapEx"]
    acq = rows["Acquisitions"]
    div_st = rows["Divestitures"]
    net_ma = rows["Net M&A"]
    pinv = rows["Purchase Of Investments"]
    sinv = rows["Sale Of Investments"]
    net_inv = rows["Net Investments"]
    other_inv = rows["Other Investing"]
    cfi = rows["CFI"]

    debt_iss = rows["Debt Issued"]
    debt_rep = rows["Debt Repaid"]
    net_debt = rows["Net Debt Change"]
    eq_iss = rows["Equity Issued"]
    bb = rows["Buybacks"]
    net_cs = rows["Net Common Stock Issuance"]
    div = rows["Dividends Paid"]
    other_fin = rows["Other Financing"]
    cff = rows["CFF"]

    fx = rows["FX Effect"]
    net_change = rows["Net Change In Cash"]
    beg_cash = rows["Beginning Cash"]
    end_cash = rows["Ending Cash"]
    fcf = rows["FCF"]

    # FCF reconstruit
    fcf_calc = [
        (cfo[i] - abs(capex[i])) if (cfo[i] is not None and capex[i] is not None) else None
        for i in range(3)
    ]

    table_rows = [
        ("Net Income", fmt_row(ni)),
        ("", ["", "", ""]),
        ("Non-cash adjustments", ["", "", ""]),
        ("  D&A", fmt_row(da)),
        ("  Stock-Based Compensation", fmt_row(sbc)),
        ("  Deferred Taxes", fmt_row(def_tax)),
        ("  Other Non-Cash", fmt_row(other_nc)),
        ("Working Capital", ["", "", ""]),
        ("  Δ Receivables", fmt_row(d_rec)),
        ("  Δ Inventory", fmt_row(d_inv)),
        ("  Δ Payables", fmt_row(d_pay)),
        ("  Δ Other WC", fmt_row(d_other_wc)),
        ("  Total Δ WC", fmt_row(total_d_wc)),
        ("CFO (Operating Cash Flow)", fmt_row(cfo)),
        ("", ["", "", ""]),
        ("Capital expenditure", ["", "", ""]),
        ("  CapEx", fmt_row(capex)),
        ("Acquisitions & divestitures", ["", "", ""]),
        ("  Acquisitions", fmt_row(acq)),
        ("  Divestitures", fmt_row(div_st)),
        ("  Net M&A", fmt_row(net_ma)),
        ("Investment activities", ["", "", ""]),
        ("  Purchase of investments", fmt_row(pinv)),
        ("  Sale/maturity of investments", fmt_row(sinv)),
        ("  Net investments", fmt_row(net_inv)),
        ("  Other investing", fmt_row(other_inv)),
        ("CFI (Investing Cash Flow)", fmt_row(cfi)),
        ("", ["", "", ""]),
        ("Debt activity", ["", "", ""]),
        ("  Debt issued", fmt_row(debt_iss)),
        ("  Debt repaid", fmt_row(debt_rep)),
        ("  Net debt change", fmt_row(net_debt)),
        ("Equity activity", ["", "", ""]),
        ("  Equity issued", fmt_row(eq_iss)),
        ("  Buybacks", fmt_row(bb)),
        ("  Net common stock", fmt_row(net_cs)),
        ("Distributions", ["", "", ""]),
        ("  Dividends paid", fmt_row(div)),
        ("Other financing", fmt_row(other_fin)),
        ("CFF (Financing Cash Flow)", fmt_row(cff)),
        ("", ["", "", ""]),
        ("FX effect", fmt_row(fx)),
        ("Net change in cash", fmt_row(net_change)),
        ("", ["", "", ""]),
        ("Reconciliation", ["", "", ""]),
        ("  Beginning cash", fmt_row(beg_cash)),
        ("  Ending cash", fmt_row(end_cash)),
        ("", ["", "", ""]),
        ("Free Cash Flow", ["", "", ""]),
        ("  FCF (yfinance)", fmt_row(fcf)),
        ("  FCF reconstruit (CFO - |CapEx|)", fmt_row(fcf_calc)),
    ]

    col_labels = [f"N-2 ({years[0]})", f"N-1 ({years[1]})", f"N ({years[2]})"]
    df = pd.DataFrame(
        [vals for _, vals in table_rows],
        index=[label for label, _ in table_rows],
        columns=col_labels,
    )

    display(HTML(f"<h3>Bloc 4 — Cash Flow 3Y ({currency})</h3>"))
    display(df)

    # Checks
    _display_cf_checks(cf_data, fcf_calc, currency)


def _display_cf_checks(cf_data: dict, fcf_calc: list, currency: str) -> None:
    """Checks Cash Flow : CFO articulation, FCF reconstruction, Cash reconciliation."""
    rows = cf_data["rows"]
    ni = rows["Net Income"][2]
    da = rows["D&A"][2]
    sbc = rows["Stock-Based Compensation"][2]
    def_tax = rows["Deferred Taxes"][2]
    other_nc = rows["Other Non-Cash"][2]
    total_d_wc = rows["Total Δ WC"][2]
    cfo_yf = rows["CFO"][2]
    fcf_yf = rows["FCF"][2]
    cfi_n = rows["CFI"][2]
    cff_n = rows["CFF"][2]
    fx_n = rows["FX Effect"][2]
    beg_cash = rows["Beginning Cash"][2]
    end_cash = rows["Ending Cash"][2]

    checks_html = "<h4 style='margin-top:12px;'>Checks de cohérence (N)</h4><ul style='font-size:13px;'>"

    # Check 1 : NI + non-cash + ΔWC ≈ CFO
    components = [ni, da, sbc, def_tax, other_nc, total_d_wc]
    known = [v for v in components if v is not None]
    if cfo_yf is not None and len(known) >= 3:
        sum_known = sum(known)
        diff_pct = abs(cfo_yf - sum_known) / abs(cfo_yf) if cfo_yf != 0 else 0
        if diff_pct < 0.05:
            checks_html += (
                f"<li style='color:green;'>✓ CFO articulation : NI + ajustements ≈ CFO "
                f"(écart {diff_pct*100:.1f}%)</li>"
            )
        else:
            checks_html += (
                f"<li style='color:orange;'>⚠ CFO articulation : "
                f"somme connue = {format_money(sum_known, currency)} vs CFO yf = "
                f"{format_money(cfo_yf, currency)} "
                f"(écart {diff_pct*100:.1f}% — lignes 'Other' non détaillées par yfinance)</li>"
            )
    else:
        checks_html += "<li style='color:gray;'>⊘ CFO articulation : données insuffisantes</li>"

    # Check 2 : FCF reconstruit vs FCF yfinance
    fcf_calc_n = fcf_calc[2]
    if fcf_yf is not None and fcf_calc_n is not None:
        diff_pct = abs(fcf_yf - fcf_calc_n) / abs(fcf_yf) if fcf_yf != 0 else 0
        if diff_pct < 0.01:
            checks_html += (
                f"<li style='color:green;'>✓ FCF yfinance ≈ FCF reconstruit "
                f"(écart {diff_pct*100:.2f}%)</li>"
            )
        else:
            checks_html += (
                f"<li style='color:orange;'>⚠ FCF yfinance vs FCF reconstruit : "
                f"écart {diff_pct*100:.2f}%</li>"
            )
    else:
        checks_html += "<li style='color:gray;'>⊘ FCF check : données manquantes</li>"

    # Check 3 : Cash reconciliation
    if (
        beg_cash is not None and end_cash is not None
        and cfo_yf is not None and cfi_n is not None and cff_n is not None
    ):
        fx_val = fx_n if fx_n is not None else 0
        calc_end = beg_cash + cfo_yf + cfi_n + cff_n + fx_val
        diff_pct = abs(calc_end - end_cash) / abs(end_cash) if end_cash != 0 else 0
        if diff_pct < 0.01:
            checks_html += (
                f"<li style='color:green;'>✓ Cash reconciliation : "
                f"Beg + CFO + CFI + CFF + FX ≈ Ending Cash "
                f"(écart {diff_pct*100:.2f}%)</li>"
            )
        else:
            checks_html += (
                f"<li style='color:orange;'>⚠ Cash reconciliation : "
                f"calcul = {format_money(calc_end, currency)} vs reported = "
                f"{format_money(end_cash, currency)} "
                f"(écart {diff_pct*100:.2f}%)</li>"
            )
    else:
        checks_html += "<li style='color:gray;'>⊘ Cash reconciliation : Beginning/Ending Cash absents</li>"

    checks_html += "</ul>"
    display(HTML(checks_html))

def display_ratios(ratios: dict, currency: str = "") -> None:
    """Bloc 5 — Ratios dérivés + checks cross-bloc."""
    years = ratios["years"]

    def fmt_pct_or_na(v):
        return format_pct(v) if v is not None else "N/A"

    def fmt_ratio_or_na(v, nm_flag=False):
        if nm_flag:
            return "N/M"
        if v is None:
            return "N/A"
        return f"{v:.2f}x"

    # Lignes ratios
    rows = [
        ("Revenue CAGR 3Y", fmt_pct_or_na(ratios["cagr"])),
        (
            f"R&D / Revenue ({years[0]} → {years[2]})",
            " → ".join(fmt_pct_or_na(v) for v in ratios["rd_trend"]),
        ),
        (
            f"EBIT margin ({years[0]} → {years[2]})",
            " → ".join(fmt_pct_or_na(v) for v in ratios["ebit_trend"]),
        ),
        (
            "FCF / Net Income (N)",
            fmt_ratio_or_na(ratios["fcf_conv"], ratios["fcf_conv_nm"]),
        ),
        (
            "Net Debt / EBITDA (N)",
            fmt_ratio_or_na(ratios["nd_ebitda"], ratios["nd_ebitda_nm"]),
        ),
        ("Goodwill / Total Assets (N)", fmt_pct_or_na(ratios["gw_ta"])),
        (
            f"ROIC (N) — tax {ratios['tax_rate_source']}",
            "N/M" if ratios["roic_nm"] else fmt_pct_or_na(ratios["roic"]),
        ),
    ]

    df = pd.DataFrame(rows, columns=["Ratio", "Value"])

    display(HTML("<h3>Bloc 5 — Ratios dérivés</h3>"))
    display(df.style.hide(axis="index"))

    # Checks cross-bloc
    _display_ratio_checks(ratios, currency)


def _display_ratio_checks(r: dict, currency: str) -> None:
    """Checks cross-bloc : EV reconstruit, EV/Rev, EV/EBITDA."""
    checks_html = "<h4 style='margin-top:12px;'>Checks cross-bloc (N)</h4><ul style='font-size:13px;'>"

    # Check 1 : EV reconstruit vs EV info
    if r["ev_calc"] is not None and r["ev_info"] is not None:
        diff_pct = abs(r["ev_calc"] - r["ev_info"]) / r["ev_info"] if r["ev_info"] != 0 else 0
        color = "green" if diff_pct < 0.05 else "orange"
        symbol = "✓" if diff_pct < 0.05 else "⚠"
        checks_html += (
            f"<li style='color:{color};'>{symbol} EV reconstruit "
            f"({format_money(r['ev_calc'], currency)}) "
            f"vs EV yfinance ({format_money(r['ev_info'], currency)}) "
            f": écart {diff_pct*100:.1f}%</li>"
        )
    else:
        checks_html += "<li style='color:gray;'>⊘ EV check : données manquantes</li>"

    # Check 2 : EV/Revenue calculé vs info
    if r["ev_rev_calc"] is not None and r["ev_rev_info"] is not None:
        diff_pct = abs(r["ev_rev_calc"] - r["ev_rev_info"]) / r["ev_rev_info"] if r["ev_rev_info"] != 0 else 0
        color = "green" if diff_pct < 0.05 else "orange"
        symbol = "✓" if diff_pct < 0.05 else "⚠"
        checks_html += (
            f"<li style='color:{color};'>{symbol} EV/Revenue calculé "
            f"({r['ev_rev_calc']:.2f}x) vs yfinance ({r['ev_rev_info']:.2f}x) "
            f": écart {diff_pct*100:.1f}%</li>"
        )
    else:
        checks_html += "<li style='color:gray;'>⊘ EV/Revenue check : données manquantes</li>"

    # Check 3 : EV/EBITDA calculé vs info
    if r["ev_ebitda_calc"] is not None and r["ev_ebitda_info"] is not None:
        diff_pct = abs(r["ev_ebitda_calc"] - r["ev_ebitda_info"]) / r["ev_ebitda_info"] if r["ev_ebitda_info"] != 0 else 0
        color = "green" if diff_pct < 0.05 else "orange"
        symbol = "✓" if diff_pct < 0.05 else "⚠"
        checks_html += (
            f"<li style='color:{color};'>{symbol} EV/EBITDA calculé "
            f"({r['ev_ebitda_calc']:.2f}x) vs yfinance ({r['ev_ebitda_info']:.2f}x) "
            f": écart {diff_pct*100:.1f}%</li>"
        )
    else:
        checks_html += "<li style='color:gray;'>⊘ EV/EBITDA check : EBITDA négatif ou données manquantes</li>"

    checks_html += "</ul>"
    display(HTML(checks_html))