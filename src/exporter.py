"""Export Excel des 5 blocs."""
import os
from datetime import datetime

import pandas as pd

from src.utils import format_money, format_pct, safe_div


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
    """
    Génère un fichier Excel avec 5 onglets.
    Retourne le chemin du fichier créé.
    """
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{ticker}_{date_str}.xlsx"

    # Créer le dossier exports/ s'il n'existe pas
    os.makedirs("exports", exist_ok=True)
    filepath = os.path.join("exports", filename)

    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        _write_identity_sheet(writer, identity, currency)
        _write_pl_sheet(writer, pl_data, currency)
        _write_bs_sheet(writer, bs_data, currency)
        _write_cf_sheet(writer, cf_data, currency)
        _write_ratios_sheet(writer, ratios, currency)

    return filepath


def _write_identity_sheet(writer, identity: dict, currency: str) -> None:
    rows = [
        ("Name", identity.get("name") or "N/A"),
        ("Ticker", identity.get("ticker") or "N/A"),
        ("Market Cap", format_money(identity.get("market_cap"), currency)),
        ("Enterprise Value", format_money(identity.get("enterprise_value"), currency)),
        ("Country", identity.get("country") or "N/A"),
        ("Sector", identity.get("sector") or "N/A"),
        ("Industry", identity.get("industry") or "N/A"),
        ("Employees", identity.get("employees") or "N/A"),
        ("Currency (market)", identity.get("currency") or "N/A"),
        ("Currency (financials)", identity.get("financial_currency") or "N/A"),
        ("Summary", identity.get("summary") or "N/A"),
    ]
    df = pd.DataFrame(rows, columns=["Field", "Value"])
    df.to_excel(writer, sheet_name="Identity", index=False)


def _write_pl_sheet(writer, pl_data: dict, currency: str) -> None:
    years = pl_data["years"]
    rows = pl_data["rows"]

    rev = rows["Revenue"]
    gp = rows["Gross Profit"]
    rd = rows["R&D"]
    sga = rows["SG&A"]
    ebit = rows["EBIT"]
    ebitda = rows["EBITDA"]
    ni = rows["Net Income"]

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

    table_rows = [
        ("Revenue", rev),
        ("  YoY %", yoy),
        ("Gross Profit", gp),
        ("  Gross Margin", gm),
        ("R&D", rd),
        ("  % Revenue", rd_pct),
        ("SG&A", sga),
        ("  % Revenue ", sga_pct),
        ("EBIT", ebit),
        ("  EBIT Margin", ebit_m),
    ]
    if has_ebitda:
        table_rows.append(("EBITDA", ebitda))
        table_rows.append(("  EBITDA Margin", ebitda_m))
    table_rows.append(("Net Income", ni))
    table_rows.append(("  Net Margin", ni_m))

    col_labels = [f"N-2 ({years[0]})", f"N-1 ({years[1]})", f"N ({years[2]})"]
    df = pd.DataFrame(
        [vals for _, vals in table_rows],
        index=[label for label, _ in table_rows],
        columns=col_labels,
    )
    df.to_excel(writer, sheet_name="P&L 3Y")


def _write_bs_sheet(writer, bs_data: dict, currency: str) -> None:
    years = bs_data["years"]
    rows = bs_data["rows"]

    ta = rows["Total Assets"]
    debt = rows["Total Debt"]
    cash = rows["Cash & ST Investments"]
    gw = rows["Goodwill"]

    net_debt = [
        (debt[i] - cash[i]) if (debt[i] is not None and cash[i] is not None) else None
        for i in range(2)
    ]
    gw_ratio = [safe_div(gw[i], ta[i]) for i in range(2)]

    table_rows = [
        ("Total Assets", ta),
        ("  Current Assets", rows["Current Assets"]),
        ("  Non-Current Assets", rows["Non-Current Assets"]),
        ("Total Liabilities", rows["Total Liabilities"]),
        ("  Current Liabilities", rows["Current Liabilities"]),
        ("  Non-Current Liabilities", rows["Non-Current Liabilities"]),
        ("Total Equity", rows["Total Equity"]),
        ("Cash & ST Investments", cash),
        ("Current Debt", rows["Current Debt"]),
        ("Long-Term Debt", rows["Long-Term Debt"]),
        ("Total Debt", debt),
        ("Net Debt", net_debt),
        ("Goodwill", gw),
        ("  GW / Total Assets", gw_ratio),
        ("Intangible Assets", rows["Intangible Assets"]),
    ]

    col_labels = [f"N-1 ({years[0]})", f"N ({years[1]})"]
    df = pd.DataFrame(
        [vals for _, vals in table_rows],
        index=[label for label, _ in table_rows],
        columns=col_labels,
    )
    df.to_excel(writer, sheet_name="Balance Sheet")


def _write_cf_sheet(writer, cf_data: dict, currency: str) -> None:
    years = cf_data["years"]
    rows = cf_data["rows"]

    cfo = rows["CFO"]
    capex = rows["CapEx"]
    fcf_calc = [
        (cfo[i] - abs(capex[i])) if (cfo[i] is not None and capex[i] is not None) else None
        for i in range(3)
    ]

    table_rows = [
        ("CFO (Operating)", cfo),
        ("CFI (Investing)", rows["CFI"]),
        ("CFF (Financing)", rows["CFF"]),
        ("CapEx", capex),
        ("D&A", rows["D&A"]),
        ("FCF (yfinance)", rows["FCF"]),
        ("FCF reconstruit", fcf_calc),
        ("Dividends Paid", rows["Dividends Paid"]),
        ("Buybacks", rows["Buybacks"]),
    ]

    col_labels = [f"N-2 ({years[0]})", f"N-1 ({years[1]})", f"N ({years[2]})"]
    df = pd.DataFrame(
        [vals for _, vals in table_rows],
        index=[label for label, _ in table_rows],
        columns=col_labels,
    )
    df.to_excel(writer, sheet_name="Cash Flow")


def _write_ratios_sheet(writer, ratios: dict, currency: str) -> None:
    years = ratios["years"]

    def fmt_pct_or_na(v):
        return format_pct(v) if v is not None else "N/A"

    def fmt_ratio_or_na(v, nm_flag=False):
        if nm_flag:
            return "N/M"
        if v is None:
            return "N/A"
        return f"{v:.2f}x"

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
        ("---", "---"),
        ("EV reconstruit", format_money(ratios["ev_calc"], currency)),
        ("EV yfinance", format_money(ratios["ev_info"], currency)),
        ("EV/Revenue calculé", f"{ratios['ev_rev_calc']:.2f}x" if ratios["ev_rev_calc"] else "N/A"),
        ("EV/Revenue yfinance", f"{ratios['ev_rev_info']:.2f}x" if ratios["ev_rev_info"] else "N/A"),
        ("EV/EBITDA calculé", f"{ratios['ev_ebitda_calc']:.2f}x" if ratios["ev_ebitda_calc"] else "N/A"),
        ("EV/EBITDA yfinance", f"{ratios['ev_ebitda_info']:.2f}x" if ratios["ev_ebitda_info"] else "N/A"),
    ]

    df = pd.DataFrame(rows, columns=["Ratio / Check", "Value"])
    df.to_excel(writer, sheet_name="Ratios", index=False)


def download_if_colab(filepath: str) -> None:
    """Sur Colab, déclenche le téléchargement automatique. Sinon affiche le chemin."""
    try:
        from google.colab import files
        files.download(filepath)
    except ImportError:
        print(f"📁 Fichier exporté : {filepath}")