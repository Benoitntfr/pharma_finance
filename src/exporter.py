"""Export Excel des 5 blocs, mis en forme."""
import os
from datetime import datetime

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment

from src.excel_styles import (
    FONT_TITLE, FONT_SUBTITLE, FONT_HEADER, FONT_SECTION, FONT_VALUE,
    FONT_RATIO, FONT_TOTAL,
    FONT_CHECK_OK, FONT_CHECK_WARN, FONT_CHECK_NEUTRAL,
    FILL_TITLE, FILL_SECTION, FILL_TOTAL,
    ALIGN_LEFT, ALIGN_RIGHT, ALIGN_CENTER,
    BORDER_TOTAL_TOP,
    get_money_format, PCT_FORMAT, RATIO_FORMAT,
)
from src.utils import safe_div


# Échelle d'affichage : on divise par 1000 → "thousands"
SCALE = 1000


def _scale(v):
    return v / SCALE if v is not None else None


def export_to_excel(
    ticker: str,
    info: dict,
    identity: dict,
    pl_data: dict,
    bs_data: dict,
    cf_data: dict,
    ratios: dict,
    currency: str,
) -> str:
    """Génère un Excel formaté avec 5 onglets. Retourne le chemin."""
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{ticker}_{date_str}.xlsx"
    os.makedirs("exports", exist_ok=True)
    filepath = os.path.join("exports", filename)

    wb = Workbook()
    wb.remove(wb.active)  # remove default sheet

    company_name = identity.get("name", "")
    exchange = info.get("exchange", "")
    money_fmt = get_money_format(currency)

    _create_identity_sheet(wb, identity, company_name, exchange, currency)
    _create_pl_sheet(wb, pl_data, company_name, exchange, ticker, currency, money_fmt)
    _create_bs_sheet(wb, bs_data, company_name, exchange, ticker, currency, money_fmt)
    _create_cf_sheet(wb, cf_data, company_name, exchange, ticker, currency, money_fmt)
    _create_ratios_sheet(wb, ratios, company_name, exchange, ticker, currency, money_fmt)

    wb.save(filepath)
    return filepath


# ============================================================
# Helpers communs
# ============================================================

def _setup_sheet(ws, title_text: str, subtitle_text: str, num_cols: int):
    """Header standard : titre bleu marine + sous-titre gris + grille off."""
    ws.sheet_view.showGridLines = False

    # Ligne 1 : titre
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=num_cols)
    cell = ws.cell(row=1, column=1, value=title_text)
    cell.font = FONT_TITLE
    cell.fill = FILL_TITLE
    cell.alignment = ALIGN_LEFT
    ws.row_dimensions[1].height = 22

    # Ligne 2 : sous-titre
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=num_cols)
    cell = ws.cell(row=2, column=1, value=subtitle_text)
    cell.font = FONT_SUBTITLE
    cell.alignment = ALIGN_LEFT

    # Ligne 3 : vide
    ws.row_dimensions[3].height = 8


def _write_section_header(ws, row: int, label: str, num_cols: int):
    """Bandeau bleu clair, gras."""
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=num_cols)
    cell = ws.cell(row=row, column=1, value=label)
    cell.font = FONT_SECTION
    cell.fill = FILL_SECTION
    cell.alignment = ALIGN_LEFT


def _write_col_headers(ws, row: int, headers: list):
    """Headers de colonnes (FY2023, FY2024, ...) sur fond bleu clair."""
    for i, h in enumerate(headers):
        cell = ws.cell(row=row, column=i + 1, value=h)
        cell.font = FONT_HEADER
        cell.fill = FILL_SECTION
        cell.alignment = ALIGN_RIGHT if i > 0 else ALIGN_LEFT


def _write_value_row(ws, row: int, label: str, values: list, num_fmt: str,
                     is_total: bool = False, is_ratio: bool = False):
    """Ligne valeur ou ratio."""
    label_cell = ws.cell(row=row, column=1, value=label)
    if is_total:
        label_cell.font = FONT_TOTAL
        label_cell.fill = FILL_TOTAL
        label_cell.border = BORDER_TOTAL_TOP
    elif is_ratio:
        label_cell.font = FONT_RATIO
    else:
        label_cell.font = FONT_VALUE
    label_cell.alignment = ALIGN_LEFT

    for i, v in enumerate(values):
        cell = ws.cell(row=row, column=i + 2, value=v)
        cell.number_format = num_fmt
        cell.alignment = ALIGN_RIGHT
        if is_total:
            cell.font = FONT_TOTAL
            cell.fill = FILL_TOTAL
            cell.border = BORDER_TOTAL_TOP
        elif is_ratio:
            cell.font = FONT_RATIO
        else:
            cell.font = FONT_VALUE


def _set_col_widths(ws, label_width: int = 38, value_width: int = 16, num_value_cols: int = 3):
    ws.column_dimensions["A"].width = label_width
    for i in range(num_value_cols):
        ws.column_dimensions[get_column_letter(i + 2)].width = value_width


def _write_checks(ws, start_row: int, checks: list, num_cols: int) -> int:
    """Écrit une section 'Checks de cohérence' à la fin de l'onglet."""
    start_row += 2
    _write_section_header(ws, start_row, "Checks de cohérence", num_cols)
    start_row += 1
    for status, text in checks:
        cell = ws.cell(row=start_row, column=1, value=text)
        if status == "ok":
            cell.font = FONT_CHECK_OK
        elif status == "warn":
            cell.font = FONT_CHECK_WARN
        else:
            cell.font = FONT_CHECK_NEUTRAL
        ws.merge_cells(start_row=start_row, start_column=1, end_row=start_row, end_column=num_cols)
        start_row += 1
    return start_row


# ============================================================
# Onglets
# ============================================================

def _create_identity_sheet(wb, identity, company_name, exchange, currency):
    ws = wb.create_sheet("Identity")
    title = f"{company_name} ({exchange}: {identity.get('ticker', '')}) - Identity"
    _setup_sheet(ws, title, f"All figures in {currency}.", 2)
    _set_col_widths(ws, label_width=30, value_width=40, num_value_cols=1)

    def fmt_employees(n):
        return f"{n:,}" if n else "N/A"

    def fmt_money_raw(v):
        if v is None:
            return "N/A"
        if abs(v) >= 1e9:
            return f"{v/1e9:.2f}B {currency}"
        if abs(v) >= 1e6:
            return f"{v/1e6:.1f}M {currency}"
        return f"{v:,.0f} {currency}"

    rows = [
        ("Name", identity.get("name") or "N/A"),
        ("Ticker", identity.get("ticker") or "N/A"),
        ("Market Cap", fmt_money_raw(identity.get("market_cap"))),
        ("Enterprise Value", fmt_money_raw(identity.get("enterprise_value"))),
        ("Country", identity.get("country") or "N/A"),
        ("Sector", identity.get("sector") or "N/A"),
        ("Industry", identity.get("industry") or "N/A"),
        ("Employees", fmt_employees(identity.get("employees"))),
        ("Currency (market)", identity.get("currency") or "N/A"),
        ("Currency (financials)", identity.get("financial_currency") or "N/A"),
    ]

    row = 4
    _write_col_headers(ws, row, ["Field", "Value"])
    row += 1
    for label, value in rows:
        ws.cell(row=row, column=1, value=label).font = FONT_VALUE
        ws.cell(row=row, column=1).alignment = ALIGN_LEFT
        ws.cell(row=row, column=2, value=value).font = FONT_VALUE
        ws.cell(row=row, column=2).alignment = ALIGN_LEFT
        row += 1

    # Summary en bas
    summary = identity.get("summary")
    if summary:
        row += 2
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
        cell = ws.cell(row=row, column=1, value="Business summary")
        cell.font = FONT_SECTION
        cell.fill = FILL_SECTION
        row += 1
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
        cell = ws.cell(row=row, column=1, value=summary)
        cell.font = FONT_SUBTITLE
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.row_dimensions[row].height = 80


def _create_pl_sheet(wb, pl_data, company_name, exchange, ticker, currency, money_fmt):
    ws = wb.create_sheet("P&L")
    years = pl_data["years"]
    rows = pl_data["rows"]
    title = f"{company_name} ({exchange}: {ticker}) - Profit & Loss"
    _setup_sheet(ws, title, f"All figures in {currency} thousands unless noted.", 4)
    _set_col_widths(ws, label_width=38, value_width=16, num_value_cols=3)

    rev = [_scale(v) for v in rows["Revenue"]]
    gp = [_scale(v) for v in rows["Gross Profit"]]
    rd = [_scale(v) for v in rows["R&D"]]
    sga = [_scale(v) for v in rows["SG&A"]]
    ebit = [_scale(v) for v in rows["EBIT"]]
    ebitda = [_scale(v) for v in rows["EBITDA"]]
    ni = [_scale(v) for v in rows["Net Income"]]

    yoy = [
        None,
        (rev[1] / rev[0] - 1) if (rev[0] and rev[1]) else None,
        (rev[2] / rev[1] - 1) if (rev[1] and rev[2]) else None,
    ]
    gm = [safe_div(gp[i], rev[i]) for i in range(3)]
    rd_pct = [safe_div(rd[i], rev[i]) for i in range(3)]
    sga_pct = [safe_div(sga[i], rev[i]) for i in range(3)]
    ebit_m = [safe_div(ebit[i], rev[i]) for i in range(3)]
    ebitda_m = [safe_div(ebitda[i], rev[i]) for i in range(3)]
    ni_m = [safe_div(ni[i], rev[i]) for i in range(3)]

    has_ebitda = any(v is not None for v in ebitda)

    row = 4
    _write_col_headers(ws, row, ["", f"FY{years[0]}", f"FY{years[1]}", f"FY{years[2]}"])
    row += 1

    _write_section_header(ws, row, "Revenue", 4); row += 1
    _write_value_row(ws, row, "Total Revenue", rev, money_fmt, is_total=True); row += 1
    _write_value_row(ws, row, "  YoY %", yoy, PCT_FORMAT, is_ratio=True); row += 1

    _write_section_header(ws, row, "Profitability", 4); row += 1
    _write_value_row(ws, row, "Gross Profit", gp, money_fmt); row += 1
    _write_value_row(ws, row, "  Gross Margin", gm, PCT_FORMAT, is_ratio=True); row += 1
    _write_value_row(ws, row, "EBIT", ebit, money_fmt); row += 1
    _write_value_row(ws, row, "  EBIT Margin", ebit_m, PCT_FORMAT, is_ratio=True); row += 1
    if has_ebitda:
        _write_value_row(ws, row, "EBITDA", ebitda, money_fmt); row += 1
        _write_value_row(ws, row, "  EBITDA Margin", ebitda_m, PCT_FORMAT, is_ratio=True); row += 1
    _write_value_row(ws, row, "Net Income", ni, money_fmt, is_total=True); row += 1
    _write_value_row(ws, row, "  Net Margin", ni_m, PCT_FORMAT, is_ratio=True); row += 1

    _write_section_header(ws, row, "Operating expenses", 4); row += 1
    _write_value_row(ws, row, "R&D", rd, money_fmt); row += 1
    _write_value_row(ws, row, "  % Revenue", rd_pct, PCT_FORMAT, is_ratio=True); row += 1
    _write_value_row(ws, row, "SG&A", sga, money_fmt); row += 1
    _write_value_row(ws, row, "  % Revenue", sga_pct, PCT_FORMAT, is_ratio=True); row += 1


def _create_bs_sheet(wb, bs_data, company_name, exchange, ticker, currency, money_fmt):
    ws = wb.create_sheet("Balance Sheet")
    years = bs_data["years"]
    rows = bs_data["rows"]
    title = f"{company_name} ({exchange}: {ticker}) - Balance Sheet"
    _setup_sheet(ws, title, f"All figures in {currency} thousands.", 3)
    _set_col_widths(ws, label_width=38, value_width=18, num_value_cols=2)

    ta = [_scale(v) for v in rows["Total Assets"]]
    ca = [_scale(v) for v in rows["Current Assets"]]
    nca = [_scale(v) for v in rows["Non-Current Assets"]]
    tl = [_scale(v) for v in rows["Total Liabilities"]]
    cl = [_scale(v) for v in rows["Current Liabilities"]]
    ncl = [_scale(v) for v in rows["Non-Current Liabilities"]]
    eq = [_scale(v) for v in rows["Total Equity"]]
    cash = [_scale(v) for v in rows["Cash & ST Investments"]]
    cdebt = [_scale(v) for v in rows["Current Debt"]]
    ltdebt = [_scale(v) for v in rows["Long-Term Debt"]]
    debt = [_scale(v) for v in rows["Total Debt"]]
    gw = [_scale(v) for v in rows["Goodwill"]]
    intang = [_scale(v) for v in rows["Intangible Assets"]]

    net_debt = [
        (debt[i] - cash[i]) if (debt[i] is not None and cash[i] is not None) else None
        for i in range(2)
    ]
    gw_ratio = [safe_div(gw[i], ta[i]) for i in range(2)]

    row = 4
    _write_col_headers(ws, row, ["", f"FY{years[0]}", f"FY{years[1]}"])
    row += 1

    _write_section_header(ws, row, "Assets", 3); row += 1
    _write_value_row(ws, row, "  Current Assets", ca, money_fmt); row += 1
    _write_value_row(ws, row, "  Non-Current Assets", nca, money_fmt); row += 1
    _write_value_row(ws, row, "Total Assets", ta, money_fmt, is_total=True); row += 1

    _write_section_header(ws, row, "Liabilities & Equity", 3); row += 1
    _write_value_row(ws, row, "  Current Liabilities", cl, money_fmt); row += 1
    _write_value_row(ws, row, "  Non-Current Liabilities", ncl, money_fmt); row += 1
    _write_value_row(ws, row, "Total Liabilities", tl, money_fmt, is_total=True); row += 1
    _write_value_row(ws, row, "Total Equity", eq, money_fmt, is_total=True); row += 1

    _write_section_header(ws, row, "Debt & Cash", 3); row += 1
    _write_value_row(ws, row, "Cash & ST Investments", cash, money_fmt); row += 1
    _write_value_row(ws, row, "Current Debt", cdebt, money_fmt); row += 1
    _write_value_row(ws, row, "Long-Term Debt", ltdebt, money_fmt); row += 1
    _write_value_row(ws, row, "Total Debt", debt, money_fmt, is_total=True); row += 1
    _write_value_row(ws, row, "Net Debt", net_debt, money_fmt); row += 1

    _write_section_header(ws, row, "Intangibles", 3); row += 1
    _write_value_row(ws, row, "Goodwill", gw, money_fmt); row += 1
    _write_value_row(ws, row, "  GW / Total Assets", gw_ratio, PCT_FORMAT, is_ratio=True); row += 1
    _write_value_row(ws, row, "Intangible Assets", intang, money_fmt); row += 1

    # Checks
    checks = _build_bs_checks(ta[1], tl[1], eq[1], gw[1])
    _write_checks(ws, row, checks, 3)


def _build_bs_checks(ta, tl, eq, gw):
    checks = []
    if ta is not None and tl is not None and eq is not None:
        sum_le = tl + eq
        diff_pct = abs(ta - sum_le) / ta if ta != 0 else 0
        if diff_pct < 0.01:
            checks.append(("ok", f"✓ Total Assets = L + E (écart {diff_pct*100:.2f}%)"))
        else:
            checks.append(("warn", f"✗ Total Assets ≠ L + E (écart {diff_pct*100:.2f}%)"))
    if gw is not None and ta is not None and ta != 0:
        ratio = gw / ta
        if ratio > 0.40:
            checks.append(("warn", f"⚠ Goodwill / Total Assets = {ratio*100:.1f}% > 40%"))
        else:
            checks.append(("ok", f"✓ Goodwill / Total Assets = {ratio*100:.1f}% (sous 40%)"))
    return checks


def _create_cf_sheet(wb, cf_data, company_name, exchange, ticker, currency, money_fmt):
    ws = wb.create_sheet("Cash Flow")
    years = cf_data["years"]
    rows = cf_data["rows"]
    title = f"{company_name} ({exchange}: {ticker}) - Cash Flow"
    _setup_sheet(ws, title, f"All figures in {currency} thousands.", 4)
    _set_col_widths(ws, label_width=38, value_width=16, num_value_cols=3)

    cfo = [_scale(v) for v in rows["CFO"]]
    cfi = [_scale(v) for v in rows["CFI"]]
    cff = [_scale(v) for v in rows["CFF"]]
    capex = [_scale(v) for v in rows["CapEx"]]
    fcf = [_scale(v) for v in rows["FCF"]]
    da = [_scale(v) for v in rows["D&A"]]
    div = [_scale(v) for v in rows["Dividends Paid"]]
    bb = [_scale(v) for v in rows["Buybacks"]]

    fcf_calc = [
        (cfo[i] - abs(capex[i])) if (cfo[i] is not None and capex[i] is not None) else None
        for i in range(3)
    ]

    row = 4
    _write_col_headers(ws, row, ["", f"FY{years[0]}", f"FY{years[1]}", f"FY{years[2]}"])
    row += 1

    _write_section_header(ws, row, "Operating", 4); row += 1
    _write_value_row(ws, row, "CFO", cfo, money_fmt, is_total=True); row += 1
    _write_value_row(ws, row, "D&A", da, money_fmt); row += 1

    _write_section_header(ws, row, "Investing", 4); row += 1
    _write_value_row(ws, row, "CapEx", capex, money_fmt); row += 1
    _write_value_row(ws, row, "CFI", cfi, money_fmt, is_total=True); row += 1

    _write_section_header(ws, row, "Financing", 4); row += 1
    _write_value_row(ws, row, "Dividends Paid", div, money_fmt); row += 1
    _write_value_row(ws, row, "Buybacks", bb, money_fmt); row += 1
    _write_value_row(ws, row, "CFF", cff, money_fmt, is_total=True); row += 1

    _write_section_header(ws, row, "Free Cash Flow", 4); row += 1
    _write_value_row(ws, row, "FCF (yfinance)", fcf, money_fmt); row += 1
    _write_value_row(ws, row, "FCF reconstruit (CFO - |CapEx|)", fcf_calc, money_fmt); row += 1

    # Check
    checks = _build_cf_checks(fcf[2], fcf_calc[2])
    _write_checks(ws, row, checks, 4)


def _build_cf_checks(fcf_yf, fcf_calc):
    if fcf_yf is None or fcf_calc is None:
        return [("neutral", "⊘ FCF check : données manquantes")]
    diff_pct = abs(fcf_yf - fcf_calc) / abs(fcf_yf) if fcf_yf != 0 else 0
    if diff_pct < 0.01:
        return [("ok", f"✓ FCF yfinance ≈ FCF reconstruit (écart {diff_pct*100:.2f}%)")]
    return [("warn", f"⚠ FCF yfinance ≠ FCF reconstruit (écart {diff_pct*100:.2f}%)")]


def _create_ratios_sheet(wb, ratios, company_name, exchange, ticker, currency, money_fmt):
    ws = wb.create_sheet("Ratios")
    title = f"{company_name} ({exchange}: {ticker}) - Ratios"
    _setup_sheet(ws, title, "Derived ratios and cross-bloc checks.", 2)
    _set_col_widths(ws, label_width=42, value_width=22, num_value_cols=1)

    years = ratios["years"]

    def fmt_pct(v):
        return f"{v*100:.1f}%" if v is not None else "N/A"

    def fmt_ratio(v, nm=False):
        if nm:
            return "N/M"
        return f"{v:.2f}x" if v is not None else "N/A"

    def fmt_money(v):
        if v is None:
            return "N/A"
        if abs(v) >= 1e9:
            return f"{v/1e9:.2f}B {currency}"
        if abs(v) >= 1e6:
            return f"{v/1e6:.1f}M {currency}"
        return f"{v:,.0f} {currency}"

    row = 4
    _write_col_headers(ws, row, ["Ratio / Indicator", "Value"])
    row += 1

    _write_section_header(ws, row, "Growth & profitability", 2); row += 1
    pairs = [
        ("Revenue CAGR 3Y", fmt_pct(ratios["cagr"])),
        (f"R&D / Revenue ({years[0]} → {years[2]})",
         " → ".join(fmt_pct(v) for v in ratios["rd_trend"])),
        (f"EBIT margin ({years[0]} → {years[2]})",
         " → ".join(fmt_pct(v) for v in ratios["ebit_trend"])),
    ]
    for label, value in pairs:
        ws.cell(row=row, column=1, value=label).font = FONT_VALUE
        ws.cell(row=row, column=1).alignment = ALIGN_LEFT
        ws.cell(row=row, column=2, value=value).font = FONT_VALUE
        ws.cell(row=row, column=2).alignment = ALIGN_RIGHT
        row += 1

    _write_section_header(ws, row, "Capital structure & cash generation", 2); row += 1
    pairs = [
        ("FCF / Net Income (N)", fmt_ratio(ratios["fcf_conv"], ratios["fcf_conv_nm"])),
        ("Net Debt / EBITDA (N)", fmt_ratio(ratios["nd_ebitda"], ratios["nd_ebitda_nm"])),
        ("Goodwill / Total Assets (N)", fmt_pct(ratios["gw_ta"])),
    ]
    for label, value in pairs:
        ws.cell(row=row, column=1, value=label).font = FONT_VALUE
        ws.cell(row=row, column=1).alignment = ALIGN_LEFT
        ws.cell(row=row, column=2, value=value).font = FONT_VALUE
        ws.cell(row=row, column=2).alignment = ALIGN_RIGHT
        row += 1

    _write_section_header(ws, row, "EV reconciliation", 2); row += 1
    pairs = [
        ("EV reconstruit (Mcap + Debt - Cash)", fmt_money(ratios["ev_calc"])),
        ("EV yfinance", fmt_money(ratios["ev_info"])),
        ("EV/Revenue calculé",
         f"{ratios['ev_rev_calc']:.2f}x" if ratios["ev_rev_calc"] else "N/A"),
        ("EV/Revenue yfinance",
         f"{ratios['ev_rev_info']:.2f}x" if ratios["ev_rev_info"] else "N/A"),
        ("EV/EBITDA calculé",
         f"{ratios['ev_ebitda_calc']:.2f}x" if ratios["ev_ebitda_calc"] else "N/A"),
        ("EV/EBITDA yfinance",
         f"{ratios['ev_ebitda_info']:.2f}x" if ratios["ev_ebitda_info"] else "N/A"),
    ]
    for label, value in pairs:
        ws.cell(row=row, column=1, value=label).font = FONT_VALUE
        ws.cell(row=row, column=1).alignment = ALIGN_LEFT
        ws.cell(row=row, column=2, value=value).font = FONT_VALUE
        ws.cell(row=row, column=2).alignment = ALIGN_RIGHT
        row += 1

    # Checks
    checks = _build_ratio_checks(ratios)
    _write_checks(ws, row, checks, 2)


def _build_ratio_checks(r):
    checks = []
    if r["ev_calc"] is not None and r["ev_info"] is not None and r["ev_info"] != 0:
        d = abs(r["ev_calc"] - r["ev_info"]) / r["ev_info"]
        status = "ok" if d < 0.05 else "warn"
        sym = "✓" if d < 0.05 else "⚠"
        checks.append((status, f"{sym} EV reconstruit vs yfinance : écart {d*100:.1f}%"))
    if r["ev_rev_calc"] is not None and r["ev_rev_info"] is not None and r["ev_rev_info"] != 0:
        d = abs(r["ev_rev_calc"] - r["ev_rev_info"]) / r["ev_rev_info"]
        status = "ok" if d < 0.05 else "warn"
        sym = "✓" if d < 0.05 else "⚠"
        checks.append((status, f"{sym} EV/Revenue calculé vs yfinance : écart {d*100:.1f}%"))
    if r["ev_ebitda_calc"] is not None and r["ev_ebitda_info"] is not None and r["ev_ebitda_info"] != 0:
        d = abs(r["ev_ebitda_calc"] - r["ev_ebitda_info"]) / r["ev_ebitda_info"]
        status = "ok" if d < 0.05 else "warn"
        sym = "✓" if d < 0.05 else "⚠"
        checks.append((status, f"{sym} EV/EBITDA calculé vs yfinance : écart {d*100:.1f}%"))
    else:
        checks.append(("neutral", "⊘ EV/EBITDA : EBITDA négatif ou données manquantes"))
    return checks


def download_if_colab(filepath: str) -> None:
    """Sur Colab, déclenche le téléchargement automatique."""
    try:
        from google.colab import files
        files.download(filepath)
    except ImportError:
        print(f"📁 Fichier exporté : {filepath}")