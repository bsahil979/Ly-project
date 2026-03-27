import numpy as np
import pandas as pd

def compute_volatility(returns: pd.DataFrame) -> pd.Series:
    """
    Annualized volatility for each stock.
    Higher = riskier.
    """
    daily_vol = returns.std()
    annualized_vol = daily_vol * np.sqrt(252)  # 252 trading days in a year
    return annualized_vol


def compute_var(returns: pd.DataFrame, confidence: float = 0.95) -> pd.Series:
    """
    Value at Risk (VaR) — maximum expected loss on a bad day.
    e.g. VaR 0.95 = worst loss you'd expect 95% of the time
    """
    var = returns.quantile(1 - confidence)
    return var


def compute_cvar(returns: pd.DataFrame, confidence: float = 0.95) -> pd.Series:
    """
    Conditional VaR (CVaR) — average loss in the worst scenarios.
    More conservative than VaR.
    """
    var = compute_var(returns, confidence)
    cvar = returns[returns <= var].mean()
    return cvar


def compute_drawdown(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Drawdown — how far each stock dropped from its peak.
    """
    rolling_max = prices.cummax()
    drawdown = (prices - rolling_max) / rolling_max
    return drawdown


def compute_max_drawdown(prices: pd.DataFrame) -> pd.Series:
    """
    Maximum drawdown — the biggest peak-to-bottom drop ever recorded.
    """
    drawdown = compute_drawdown(prices)
    max_drawdown = drawdown.min()
    return max_drawdown


def get_risk_summary(prices: pd.DataFrame, returns: pd.DataFrame) -> dict:
    """
    Master function — computes all risk metrics in one call.
    """
    volatility = compute_volatility(returns)
    var_95 = compute_var(returns, confidence=0.95)
    cvar_95 = compute_cvar(returns, confidence=0.95)
    max_drawdown = compute_max_drawdown(prices)

    summary = pd.DataFrame({
        "Volatility (Annual)": volatility,
        "VaR (95%)":           var_95,
        "CVaR (95%)":          cvar_95,
        "Max Drawdown":        max_drawdown
    })

    return {
        "summary": summary,
        "drawdown_series": compute_drawdown(prices)
    }