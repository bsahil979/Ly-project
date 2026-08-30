"""
Risk budgeting engine — decomposes portfolio-level risk into per-asset contributions.

Calculates marginal contribution to risk (MCR), component contribution to risk (CCR),
and percentage contribution to total portfolio risk (PCR).

All values are mathematically derived from the portfolio's return covariance matrix
and weight vector — no approximations or fabricated inputs.
"""
import numpy as np
import pandas as pd


def compute_risk_budget(
    tickers: list[str],
    weights: list[float],
    returns: pd.DataFrame,
    portfolio_value: float = 100000,
    confidence_level: float = 0.95,
) -> dict:
    """
    Compute risk contribution analysis for the portfolio.

    Returns marginal, component, and percentage risk contributions based on
    the analytical portfolio volatility formula:

        σ_p = √(wᵀ Σ w)

        MCR_i = (Σ w)_i / σ_p          (marginal contribution to risk)
        CCR_i = w_i * MCR_i            (component contribution to risk)
        PCR_i = CCR_i / σ_p            (percentage contribution to total risk)
    """
    weights = np.array(weights, dtype=float)
    weights = weights / weights.sum()

    tickers_clean = [t.upper().strip() for t in tickers]

    # Align returns with tickers
    ret = returns.copy()
    col_map = {str(c).upper(): c for c in ret.columns}
    usable_cols = [col_map[t] for t in tickers_clean if t in col_map]
    usable_tickers = [t for t in tickers_clean if t in col_map]
    usable_weights = weights[:len(usable_cols)]

    if len(usable_cols) == 0 or len(ret) < 2:
        return {"error": "Insufficient data or no matching tickers in returns"}

    ret_aligned = ret[usable_cols].dropna()
    if len(ret_aligned) < 2:
        return {"error": "Insufficient overlapping returns after alignment"}

    # Covariance matrix (annualized)
    cov_matrix = ret_aligned.cov().values * 252

    # Portfolio volatility (annualized)
    port_var = float(usable_weights @ cov_matrix @ usable_weights)
    port_vol = float(np.sqrt(port_var)) if port_var > 0 else 0.0

    if port_vol == 0:
        return {"error": "Portfolio volatility is zero — cannot compute risk contributions"}

    # Marginal contribution to risk: d(σ_p)/d(w_i) = (Σw)_i / σ_p
    marginal = (cov_matrix @ usable_weights) / port_vol

    # Component contribution to risk: w_i * MCR_i
    component = usable_weights * marginal

    # Percentage contribution to risk: CCR_i / σ_p
    percentage = component / port_vol

    # VaR and CVaR
    port_daily_returns = ret_aligned @ usable_weights
    port_annual_returns = port_daily_returns * 252
    var_threshold = float(np.percentile(port_daily_returns, (1 - confidence_level) * 100))
    var_annual = var_threshold * np.sqrt(252)
    cvar = float(port_daily_returns[port_daily_returns <= var_threshold].mean()) * 252 if len(port_daily_returns[port_daily_returns <= var_threshold]) > 0 else 0

    risk_contributions = []
    for i, ticker in enumerate(usable_tickers):
        risk_contributions.append({
            "ticker": ticker,
            "weight": round(float(usable_weights[i]), 4),
            "marginal_contribution_to_risk": round(float(marginal[i]), 6),
            "component_contribution_to_risk": round(float(component[i]), 6),
            "percentage_contribution_to_risk": round(float(percentage[i] * 100), 2),
            "volatility": round(float(np.sqrt(cov_matrix[i, i])), 4),
            "value_at_risk": round(var_annual, 4),
        })

    # Sort by risk contribution descending
    risk_contributions.sort(key=lambda x: -x["percentage_contribution_to_risk"])

    # Diversification ratio
    weighted_avg_vol = float(np.average(
        [np.sqrt(cov_matrix[i, i]) for i in range(len(usable_cols))],
        weights=usable_weights
    ))
    diversification_ratio = weighted_avg_vol / port_vol if port_vol > 0 else 0

    # Herfindahl-Hirschman Index for risk concentration
    pcr_values = np.array([r["percentage_contribution_to_risk"] / 100 for r in risk_contributions])
    hhi = float(np.sum(pcr_values ** 2))

    return {
        "portfolio_volatility": round(port_vol, 4),
        "portfolio_value": float(portfolio_value),
        "currency": None,  # Set by caller
        "confidence_level": confidence_level,
        "var_95": round(var_annual, 4),
        "cvar_95": round(cvar, 4),
        "diversification_ratio": round(diversification_ratio, 4),
        "herfindahl_index": round(hhi, 4),
        "risk_concentration": _interpret_hhi(hhi),
        "risk_contributions": risk_contributions,
    }


def _interpret_hhi(hhi: float) -> str:
    """Classify risk concentration level based on HHI."""
    if hhi > 0.25:
        return "highly_concentrated"
    elif hhi > 0.15:
        return "moderately_concentrated"
    elif hhi > 0.08:
        return "moderately_diversified"
    else:
        return "well_diversified"


def compute_correlation_matrix(tickers: list[str], returns: pd.DataFrame) -> dict:
    """Return the pairwise correlation matrix for the portfolio's tickers."""
    tickers_clean = [t.upper().strip() for t in tickers]
    col_map = {str(c).upper(): c for c in returns.columns}
    usable_cols = [col_map[t] for t in tickers_clean if t in col_map]
    usable_tickers = [t for t in tickers_clean if t in col_map]

    if not usable_cols:
        return {"error": "No matching tickers in returns data"}

    corr = returns[usable_cols].dropna().corr()
    matrix = []
    for i, t1 in enumerate(usable_tickers):
        row = []
        for j, t2 in enumerate(usable_tickers):
            row.append(round(float(corr.iloc[i, j]), 4))
        matrix.append(row)

    return {
        "tickers": usable_tickers,
        "matrix": matrix,
    }
