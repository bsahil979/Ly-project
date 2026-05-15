import pandas as pd
import numpy as np

def compute_momentum_signals(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Computes momentum signals over multiple time horizons.
    Inspired by Lim et al. (2020) Deep Momentum Networks.
    
    Returns normalized returns over:
    - 1 month  (21 trading days)
    - 3 months (63 trading days)
    - 6 months (126 trading days)
    - 1 year   (252 trading days)
    """
    signals = {}

    for ticker in prices.columns:
        p = prices[ticker]

        # Compute returns over different horizons
        mom_1m  = (p.iloc[-1] - p.iloc[-21])  / p.iloc[-21]  if len(p) >= 21  else None
        mom_3m  = (p.iloc[-1] - p.iloc[-63])  / p.iloc[-63]  if len(p) >= 63  else None
        mom_6m  = (p.iloc[-1] - p.iloc[-126]) / p.iloc[-126] if len(p) >= 126 else None
        mom_12m = (p.iloc[-1] - p.iloc[-252]) / p.iloc[-252] if len(p) >= 252 else None

        # Signal direction: +1 = bullish, -1 = bearish, 0 = neutral
        def signal(m):
            if m is None:
                return "N/A"
            elif m > 0.02:
                return "[+] Bullish"
            elif m < -0.02:
                return "[-] Bearish"
            else:
                return "[~] Neutral"

        signals[ticker] = {
            "1M Return":       f"{round(mom_1m  * 100, 2)}%" if mom_1m  is not None else "N/A",
            "3M Return":       f"{round(mom_3m  * 100, 2)}%" if mom_3m  is not None else "N/A",
            "6M Return":       f"{round(mom_6m  * 100, 2)}%" if mom_6m  is not None else "N/A",
            "12M Return":      f"{round(mom_12m * 100, 2)}%" if mom_12m is not None else "N/A",
            "1M Signal":       signal(mom_1m),
            "3M Signal":       signal(mom_3m),
            "6M Signal":       signal(mom_6m),
            "12M Signal":      signal(mom_12m),
            "Overall Trend":   _overall_trend(mom_1m, mom_3m, mom_6m, mom_12m)
        }

    return pd.DataFrame(signals).T


def _overall_trend(m1, m3, m6, m12) -> str:
    """
    Determines overall trend based on momentum signals.
    """
    signals = [m for m in [m1, m3, m6, m12] if m is not None]
    if not signals:
        return "N/A"

    positive = sum(1 for m in signals if m > 0.02)
    negative = sum(1 for m in signals if m < -0.02)

    if positive >= 3:
        return "[+] Strong Uptrend"
    elif positive == 2:
        return "[+] Moderate Uptrend"
    elif negative >= 3:
        return "[-] Strong Downtrend"
    elif negative == 2:
        return "[-] Moderate Downtrend"
    else:
        return "[~] Sideways / Mixed"


def compute_sharpe_ratio(returns: pd.DataFrame, risk_free_rate: float = 0.05) -> pd.Series:
    """
    Computes annualized Sharpe Ratio for each ticker.
    Inspired by Lim et al. (2020) who optimize directly for Sharpe ratio.
    
    Args:
        returns:        daily returns DataFrame
        risk_free_rate: annual risk free rate (default 5%)
    """
    daily_rf = risk_free_rate / 252
    excess_returns = returns - daily_rf
    sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
    return sharpe.round(4)


def compute_calmar_ratio(returns: pd.DataFrame, prices: pd.DataFrame) -> pd.Series:
    """
    Computes Calmar Ratio = Annualized Return / Max Drawdown.
    Used in Paper 1 as a key performance metric.
    """
    annual_return = returns.mean() * 252
    rolling_max   = prices.cummax()
    drawdown      = (prices - rolling_max) / rolling_max
    max_drawdown  = drawdown.min().abs()
    calmar        = annual_return / max_drawdown
    return calmar.round(4)


def get_momentum_summary(prices: pd.DataFrame, returns: pd.DataFrame) -> dict:
    """
    Master function — computes all momentum metrics in one call.
    """
    momentum_signals = compute_momentum_signals(prices)
    sharpe           = compute_sharpe_ratio(returns)
    calmar           = compute_calmar_ratio(returns, prices)

    performance = pd.DataFrame({
        "Sharpe Ratio": sharpe,
        "Calmar Ratio": calmar
    })

    return {
        "momentum_signals": momentum_signals,
        "performance":      performance
    }