"""
Portfolio return attribution engine.

Computes security-level, sector-level, and asset-class-level contribution to
total portfolio returns.  All numbers are mathematically derived from the
portfolio's actual returns, weights, and price changes — no fabrication.
"""
import numpy as np
import pandas as pd
from typing import Optional
from services.portfolio_score import get_asset_category


def compute_attribution(
    tickers: list[str],
    weights: list[float],
    prices: pd.DataFrame,
    portfolio_value: float = 100000,
    currency_symbol: str = "$",
) -> dict:
    """
    Compute portfolio return attribution across multiple dimensions.

    All contribution values are derived from actual price changes and weights.
    """
    weights = np.array(weights, dtype=float)
    tickers_clean = [t.upper().strip() for t in tickers]

    # Align prices with tickers
    prices_aligned = prices.copy()
    col_map = {str(c).upper(): c for c in prices_aligned.columns}
    ticker_cols = []
    for t in tickers_clean:
        if t in col_map:
            ticker_cols.append(col_map[t])
        elif len(prices_aligned.columns) == 1 and t == tickers_clean[0]:
            ticker_cols.append(prices_aligned.columns[0])

    usable_tickers = [t for t, c in zip(tickers_clean, ticker_cols) if c is not None]
    usable_weights = [w for w, c in zip(weights, ticker_cols) if c is not None]
    usable_prices = prices_aligned[ticker_cols] if ticker_cols else prices_aligned.iloc[:, :1]

    if len(usable_tickers) == 0:
        return {"error": "No usable price data for any tickers"}

    # Daily returns
    daily_returns = usable_prices.pct_change().dropna()

    # Period return for each asset (from first to last date)
    first_prices = usable_prices.iloc[0]
    last_prices = usable_prices.iloc[-1]
    total_returns = (last_prices / first_prices - 1)

    # Position values
    position_values = portfolio_value * np.array(usable_weights)
    position_returns = position_values * total_returns.values

    # Portfolio total return
    port_total_return = float(np.average(total_returns.values, weights=usable_weights))

    # --- Security Contribution ---
    security_contrib = []
    for i, ticker in enumerate(usable_tickers):
        w = usable_weights[i]
        r = float(total_returns.iloc[i]) if hasattr(total_returns, 'iloc') else float(total_returns[i])
        contrib = w * r
        security_contrib.append({
            "ticker": ticker,
            "weight": round(float(w), 4),
            "return": round(r, 4),
            "contribution": round(contrib, 4),
            "contribution_pct": round(contrib / port_total_return * 100, 2) if port_total_return != 0 else 0,
            "position_value": round(float(position_values[i]), 2),
            "dollar_pnl": round(float(position_returns[i]), 2),
            "category": get_asset_category(ticker),
        })

    # --- Sector Contribution ---
    sector_data = {}
    for i, ticker in enumerate(usable_tickers):
        cat = get_asset_category(ticker)
        if cat not in sector_data:
            sector_data[cat] = {"weight": 0, "return": 0, "contrib": 0, "tickers": []}
        sector_data[cat]["weight"] += usable_weights[i]
        sector_data[cat]["return"] += usable_weights[i] * (
            float(total_returns.iloc[i]) if hasattr(total_returns, 'iloc') else float(total_returns[i])
        )
        sector_data[cat]["contrib"] += usable_weights[i] * (
            float(total_returns.iloc[i]) if hasattr(total_returns, 'iloc') else float(total_returns[i])
        )
        sector_data[cat]["tickers"].append(ticker)

    sector_contrib = []
    for cat, data in sorted(sector_data.items(), key=lambda x: -x[1]["contrib"]):
        sector_contrib.append({
            "category": cat,
            "weight": round(data["weight"], 4),
            "return": round(data["return"] / data["weight"], 4) if data["weight"] > 0 else 0,
            "contribution": round(data["contrib"], 4),
            "contribution_pct": round(data["contrib"] / port_total_return * 100, 2) if port_total_return != 0 else 0,
            "tickers": data["tickers"],
        })

    # --- Asset Class Contribution (broad buckets) ---
    def _asset_class(cat: str) -> str:
        if "ETF" in cat or cat in ("Equity", "Technology", "Communication", "Consumer", "Financial", "Healthcare", "Energy", "Utilities", "Industrials", "Basic Materials"):
            if "Cash" in cat or cat == "Other":
                return "Cash"
            if "Financial" in cat:
                return "Financials"
            if "Technology" in cat:
                return "Technology"
            if "Health" in cat:
                return "Healthcare"
            if "Consumer" in cat:
                return "Consumer"
            if "Energy" in cat or "Utilities" in cat:
                return "Energy/Utilities"
            if "Industries" in cat:
                return "Industrials"
            if "Materials" in cat:
                return "Materials"
            return cat
        return cat

    asset_class_data = {}
    for i, ticker in enumerate(usable_tickers):
        cat = get_asset_category(ticker)
        ac = _asset_class(cat)
        if ac not in asset_class_data:
            asset_class_data[ac] = {"weight": 0, "contrib": 0, "tickers": []}
        asset_class_data[ac]["weight"] += usable_weights[i]
        asset_class_data[ac]["contrib"] += usable_weights[i] * (
            float(total_returns.iloc[i]) if hasattr(total_returns, 'iloc') else float(total_returns[i])
        )
        asset_class_data[ac]["tickers"].append(ticker)

    asset_class_contrib = []
    for ac, data in sorted(asset_class_data.items(), key=lambda x: -x[1]["contrib"]):
        asset_class_contrib.append({
            "asset_class": ac,
            "weight": round(data["weight"], 4),
            "contribution": round(data["contrib"], 4),
            "contribution_pct": round(data["contrib"] / port_total_return * 100, 2) if port_total_return != 0 else 0,
            "tickers": data["tickers"],
        })

    # --- Period info ---
    first_date = usable_prices.index[0]
    last_date = usable_prices.index[-1]

    return {
        "period": {
            "start": first_date.strftime('%Y-%m-%d') if hasattr(first_date, 'strftime') else str(first_date),
            "end": last_date.strftime('%Y-%m-%d') if hasattr(last_date, 'strftime') else str(last_date),
        },
        "portfolio_total_return": round(port_total_return, 4),
        "portfolio_value": float(portfolio_value),
        "currency": currency_symbol,
        "security_contribution": security_contrib,
        "sector_contribution": sector_contrib,
        "asset_class_contribution": asset_class_contrib,
    }
