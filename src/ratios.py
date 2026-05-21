"""Bloc 5 — Ratios dérivés et checks cross-bloc."""
from src.utils import safe_div


def compute_ratios(info: dict, pl_data: dict, bs_data: dict, cf_data: dict) -> dict:
    """
    Calcule les ratios dérivés du Bloc 5.
    Retourne un dict avec valeurs + métadonnées pour affichage.
    """
    rev = pl_data["rows"]["Revenue"]
    rd = pl_data["rows"]["R&D"]
    ebit = pl_data["rows"]["EBIT"]
    ebitda = pl_data["rows"]["EBITDA"]
    ni = pl_data["rows"]["Net Income"]
    fcf = cf_data["rows"]["FCF"]

    # Index 1 = N-1, 2 = N pour Balance Sheet (2 années)
    ta_n = bs_data["rows"]["Total Assets"][1]
    gw_n = bs_data["rows"]["Goodwill"][1]
    debt_n = bs_data["rows"]["Total Debt"][1]
    cash_n = bs_data["rows"]["Cash & ST Investments"][1]

    # Revenue CAGR 3Y : (rev_N / rev_N-2)^(1/2) - 1
    cagr = None
    if rev[0] and rev[2] and rev[0] > 0:
        cagr = (rev[2] / rev[0]) ** (1 / 2) - 1

    # R&D / Revenue trend (3 valeurs)
    rd_trend = [safe_div(rd[i], rev[i]) for i in range(3)]

    # EBIT margin trend (3 valeurs)
    ebit_trend = [safe_div(ebit[i], rev[i]) for i in range(3)]

    # FCF conversion N : N/M si NI ou FCF < 0
    fcf_conv = None
    fcf_conv_nm = False
    if ni[2] is not None and fcf[2] is not None:
        if ni[2] < 0 or fcf[2] < 0:
            fcf_conv_nm = True
        else:
            fcf_conv = safe_div(fcf[2], ni[2])

    # Net Debt / EBITDA N : drop si EBITDA absent ou négatif
    nd_ebitda = None
    nd_ebitda_nm = False
    net_debt_n = None
    if debt_n is not None and cash_n is not None:
        net_debt_n = debt_n - cash_n
    if net_debt_n is not None and ebitda[2] is not None:
        if ebitda[2] <= 0:
            nd_ebitda_nm = True
        else:
            nd_ebitda = net_debt_n / ebitda[2]

    # Goodwill / Total Assets N
    gw_ta = safe_div(gw_n, ta_n)

    # Market Cap
    mcap = info.get("marketCap")
    ev_info = info.get("enterpriseValue")

    # EV reconstruit = Market Cap + Total Debt - Cash
    ev_calc = None
    if mcap is not None and debt_n is not None and cash_n is not None:
        ev_calc = mcap + debt_n - cash_n

    # EV / Revenue calculé
    ev_rev_calc = safe_div(ev_calc, rev[2])
    ev_rev_info = info.get("enterpriseToRevenue")

    # EV / EBITDA calculé
    ev_ebitda_calc = None
    if ev_calc is not None and ebitda[2] is not None and ebitda[2] > 0:
        ev_ebitda_calc = ev_calc / ebitda[2]
    ev_ebitda_info = info.get("enterpriseToEbitda")

    return {
        "cagr": cagr,
        "rd_trend": rd_trend,
        "ebit_trend": ebit_trend,
        "fcf_conv": fcf_conv,
        "fcf_conv_nm": fcf_conv_nm,
        "nd_ebitda": nd_ebitda,
        "nd_ebitda_nm": nd_ebitda_nm,
        "gw_ta": gw_ta,
        "ev_calc": ev_calc,
        "ev_info": ev_info,
        "ev_rev_calc": ev_rev_calc,
        "ev_rev_info": ev_rev_info,
        "ev_ebitda_calc": ev_ebitda_calc,
        "ev_ebitda_info": ev_ebitda_info,
        "years": pl_data["years"],
    }