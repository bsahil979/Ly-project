"""
Benchmark engine — compares portfolio performance against benchmarks.

Supports configurable benchmarks (S&P 500, NIFTY 50, NASDAQ-100, custom tickers).
Calculates total return, annualized return, volatility, Sharpe, Sortino,
max drawdown, beta, alpha, tracking error, and information ratio.
"""
import numpy as np
import pandas as pd
from typing import Optional


BENCHMARKS = {
    "S&P 500": "SPY",
    "NASDAQ-100": "QQQ",
    "NIFTY 50": "^NSEI",
    "Russell 2000": "IWM",
    "Dow Jones": "DIA",
    "MSCI Emerging Markets": "EEM",
    "US Aggregate Bonds": "BND",
}


def _safe_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Normalize price data to a DataFrame of daily returns."""
    returns = prices.pct_change().dropna()
    if isinstance(returns, pd.Series):
        returns = returns.to_frame()
    return returns


def _portfolio_returns(returns: pd.DataFrame, weights: np.ndarray) -> pd.Series:
    """Calculate portfolio daily returns from asset returns and weights."""
    aligned = returns.iloc[:, :len(weights)].fillna(0)
    weights_arr = np.array(weights)[:len(aligned.columns)]
    port_ret = aligned @ weights_arr
    return port_ret


def compute_benchmark_comparison(
    prices: pd.DataFrame,
    weights: list[float],
    portfolio_value: float = 100000,
    benchmark_ticker: str = "SPY",
    risk_free_rate: float = 0.02,
) -> dict:
    """
    Compare portfolio against a benchmark.

    Returns a dict of portfolio_vs_benchmark metrics and raw return series.
    """
    weights = np.array(weights, dtype=float)
    weights = weights / weights.sum()

    port_prices = prices.ffill().bfill()
    port_returns_df = _safe_returns(port_prices)

    # Portfolio daily returns
    port_daily = _portfolio_returns(port_returns_df, weights)

    # Benchmark returns — get from same price data if ticker exists in columns
    bench_col = {str(c).upper(): c for c in port_prices.columns}.get(benchmark_ticker.upper())
    if bench_col is not None:
        bench_prices = port_prices[bench_col]
    else:
        # Fetch benchmark separately
        from services.data_fetcher import fetch_price_data
        bench_prices = fetch_price_data([benchmark_ticker],
                                         port_prices.index[0].strftime('%Y-%m-%d'),
                                         port_prices.index[-1].strftime('%Y-%m-%d'))
        if isinstance(bench_prices, pd.DataFrame):
            bench_prices = bench_prices.iloc[:, 0]

    bench_daily = bench_prices.pct_change().dropna()

    # Align dates
    common_idx = port_daily.index.intersection(bench_daily.index)
    port_aligned = port_daily.reindex(common_idx).fillna(0)
    bench_aligned = bench_daily.reindex(common_idx).fillna(0)

    if len(common_idx) < 2:
        return {
            "error": "Insufficient overlapping data for benchmark comparison",
            "benchmark_ticker": benchmark_ticker,
        }

    # --- Performance metrics ---
    port_total = float((1 + port_aligned).prod() - 1)
    bench_total = float((1 + bench_aligned).prod() - 1)

    n_days = len(common_idx)
    n_years = n_days / 252
    port_annualized = float((1 + port_total) ** (1 / n_years) - 1) if n_years > 0 else 0
    bench_annualized = float((1 + bench_total) ** (1 / n_years) - 1) if n_years > 0 else 0

    # --- Risk metrics ---
    port_vol = float(port_aligned.std() * np.sqrt(252))
    bench_vol = float(bench_aligned.std() * np.sqrt(252))

    excess = port_aligned - bench_aligned
    tracking_error = float(excess.std() * np.sqrt(252))

    # Downside deviation (Sortino)
    target = 0
    downside = excess[excess < target]
    downside_dev = float(downside.std() * np.sqrt(252)) if len(downside) > 1 else 0
    sortino = (port_annualized - risk_free_rate) / downside_dev if downside_dev > 0 else 0

    sharpe = (port_annualized - risk_free_rate) / port_vol if port_vol > 0 else 0

    # Beta and Alpha (linear regression)
    beta = float(np.cov(port_aligned, bench_aligned)[0, 1] / np.var(bench_aligned)) if np.var(bench_aligned) > 0 else 0
    alpha_daily = port_aligned.mean() - beta * bench_aligned.mean()
    alpha_annualized = float(alpha_daily * 252)

    # Information ratio
    ir = float(excess.mean() * 252 / tracking_error) if tracking_error > 0 else 0

    # Drawdowns
    port_cum = (1 + port_aligned).cumprod()
    bench_cum = (1 + bench_aligned).cumprod()
    port_dd = float((port_cum / port_cum.cummax() - 1).min())
    bench_dd = float((bench_cum / bench_cum.cummax() - 1).min())

    return {
        "benchmark_ticker": benchmark_ticker,
        "benchmark_display": BENCHMARKS.get(benchmark_ticker, benchmark_ticker),
        "period_days": n_days,
        "portfolio": {
            "total_return": round(port_total, 4),
            "annualized_return": round(port_annualized, 4),
            "volatility": round(port_vol, 4),
            "sharpe_ratio": round(sharpe, 4),
            "sortino_ratio": round(sortino, 4),
            "max_drawdown": round(port_dd, 4),
        },
        "benchmark": {
            "total_return": round(bench_total, 4),
            "annualized_return": round(bench_annualized, 4),
            "volatility": round(bench_vol, 4),
            "max_drawdown": round(bench_dd, 4),
        },
        "comparison": {
            "alpha": round(alpha_annualized, 4),
            "beta": round(beta, 4),
            "tracking_error": round(tracking_error, 4),
            "information_ratio": round(ir, 4),
            "outperformance": round(port_total - bench_total, 4),
            "outperformance_pct": round((port_total - bench_total) * 100, 2),
        },
        "return_series": {
            "portfolio_daily": _clean_series(port_aligned),
            "benchmark_daily": _clean_series(bench_aligned),
        },
    }


def _clean_series(s: pd.Series) -> list:
    """Convert pandas Series to JSON-friendly list for API response."""
    return [
        {"date": idx.strftime('%Y-%m-%d'), "return": float(v)}
        for idx, v in s.items()
    ]


def list_available_benchmarks() -> list[dict]:
    """Return all supported benchmark options."""
    return [{"name": k, "ticker": v} for k, v in BENCHMARKS.items()]
