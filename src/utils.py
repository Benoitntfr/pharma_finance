"""Helpers de robustesse pour extraction yfinance."""
import pandas as pd


def safe_get(info: dict, key: str, default=None):
    """Retourne info[key] ou default si absent/None."""
    value = info.get(key)
    return value if value is not None else default


def find_row(df: pd.DataFrame, candidates: list) -> pd.Series | None:
    """
    Cherche une ligne dans df.index parmi une liste de noms candidats.
    Retourne la première trouvée, None sinon.
    yfinance utilise parfois 'Research And Development' ou 'Research Development'.
    """
    if df is None or df.empty:
        return None
    for candidate in candidates:
        if candidate in df.index:
            return df.loc[candidate]
    return None


def format_money(value, currency: str = "") -> str:
    """Formate un montant en M/B selon la magnitude."""
    if value is None or pd.isna(value):
        return "N/A"
    abs_val = abs(value)
    if abs_val >= 1e9:
        return f"{value / 1e9:.2f}B {currency}".strip()
    if abs_val >= 1e6:
        return f"{value / 1e6:.1f}M {currency}".strip()
    return f"{value:,.0f} {currency}".strip()


def format_pct(value) -> str:
    """Formate un ratio en pourcentage."""
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value * 100:.1f}%" if abs(value) < 10 else f"{value:.1f}%"