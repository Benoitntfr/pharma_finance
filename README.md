# pharma_finance

Mini-outil d'analyse financière d'entreprises cotées (P&L 3Y, Balance Sheet, Cash Flow, Ratios + checks de cohérence + export Excel).

## Usage Colab — copier-coller ces 6 lignes

```python
%cd /content
!rm -rf pharma_finance
!git clone https://github.com/Benoitntfr/pharma_finance.git
%cd pharma_finance
!pip install -q -r requirements.txt
%run main.py
```

Entrer le ticker au prompt (ex: `TEM`, `PFE`, `SAN.PA`). Output inline + fichier Excel téléchargé automatiquement.

## Sources

- yfinance (Yahoo Finance) — market data, états financiers
- SEC EDGAR — non utilisé (réservé pour évolutions futures)

## Blocs

1. **Identity** — nom, ticker, market cap, EV, secteur, employés
2. **P&L 3Y** — revenue, GP, R&D, SG&A, EBIT, EBITDA, NI + marges
3. **Balance Sheet** — N-1, N + checks équation comptable
4. **Cash Flow 3Y** — CFO, CFI, CFF, CapEx, FCF, dividends, buybacks
5. **Ratios** — CAGR, FCF/NI, ND/EBITDA, GW/TA, EV reconciliation

Excel Number Format: "_($* #\ ##0_);_($* (#\ ##0);_($* "-"_);_(@_)"
