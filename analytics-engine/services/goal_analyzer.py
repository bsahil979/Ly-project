"""
Goal-based portfolio analysis engine.

Computes required return, expected return, probability of achieving a financial
goal using Monte Carlo simulation, and the monthly contribution needed to reach
the target.

All simulation logic reuses numpy for path generation — no hardcoded scenarios.
"""
import numpy as np
import pandas as pd
from typing import Optional


def compute_goal_analysis(
    tickers: list[str],
    weights: list[float],
    current_capital: float,
    monthly_contribution: float,
    target_amount: float,
    time_horizon_years: float,
    returns: pd.DataFrame,
    num_sims: int = 1000,
    risk_free_rate: float = 0.02,
) -> dict:
    """
    Analyze whether the user's current plan will achieve their financial goal.

    Uses Monte Carlo simulation on historical returns to estimate:
    - Required annual return (CAGR needed to hit target)
    - Expected annual return (from historical data)
    - Probability of achieving goal
    - Shortfall probability
    - Required monthly contribution (if current contributions are insufficient)
    - Final portfolio distribution
    """
    weights = np.array(weights, dtype=float)
    weights = weights / weights.sum()

    tickers_clean = [t.upper().strip() for t in tickers]
    col_map = {str(c).upper(): c for c in returns.columns}
    usable_cols = [col_map[t] for t in tickers_clean if t in col_map]
    usable_weights = weights[:len(usable_cols)]

    if len(usable_cols) < 1 or len(returns) < 30:
        return {"error": "Insufficient data for Monte Carlo simulation"}

    ret_aligned = returns[usable_cols].dropna()
    mean_returns = ret_aligned.mean().values * 252
    cov_matrix = ret_aligned.cov().values * 252

    n_assets = len(mean_returns)

    # Cholesky for correlated sampling
    try:
        L = np.linalg.cholesky(cov_matrix)
    except np.linalg.LinAlgError:
        L = np.diag(np.sqrt(np.maximum(np.diag(cov_matrix), 1e-8)))

    # Required CAGR to reach target
    n_years = time_horizon_years
    periods_per_year = 12  # monthly contributions
    n_months = int(n_years * periods_per_year)

    required_cagr = float((target_amount / current_capital) ** (1 / n_years) - 1) if current_capital > 0 else 0

    # Expected portfolio return
    expected_portfolio_return = float(np.dot(usable_weights, mean_returns))

    # Run Monte Carlo
    rng = np.random.default_rng(42)
    dt = 1 / periods_per_year
    final_values = np.zeros(num_sims)
    trajectory_10 = np.zeros(n_months)
    trajectory_50 = np.zeros(n_months)
    trajectory_90 = np.zeros(n_months)

    all_trajectories = []

    for sim in range(num_sims):
        # Sample annual returns with correlation
        Z = rng.standard_normal((n_months, n_assets))
        correlated = Z @ L.T
        # GBM: monthly return = annual_mean * dt + annual_vol * sqrt(dt) * Z
        # where dt = 1/months_per_year
        monthly_returns_per_asset = expected_portfolio_return * dt + correlated * np.sqrt(dt)
        # Portfolio monthly return = weighted average of per-asset monthly returns
        portfolio_monthly = monthly_returns_per_asset @ usable_weights

        # Build path with contributions
        balance = current_capital
        path = [balance]
        for ret in portfolio_monthly:
            balance = balance * (1 + float(ret)) + monthly_contribution
            path.append(balance)
        final_values[sim] = balance
        all_trajectories.append(path)

    trajectories = np.array(all_trajectories)

    # Percentile trajectories for charting
    trajectory_10 = np.percentile(trajectories, 10, axis=0).tolist()
    trajectory_50 = np.percentile(trajectories, 50, axis=0).tolist()
    trajectory_90 = np.percentile(trajectories, 90, axis=0).tolist()

    # Probability of goal achievement
    success_mask = final_values >= target_amount
    success_rate = float(np.mean(success_mask) * 100)
    shortfall_rate = float(np.mean(~success_mask) * 100)
    expected_shortfall = float(np.mean(final_values[~success_mask]) - target_amount) if np.any(~success_mask) else 0

    # Required monthly contribution
    # Solve: target = current * (1+r)^n + contribution * [((1+r)^n - 1) / r/12]
    # where r is the expected annual return
    r_monthly = expected_portfolio_return / periods_per_year
    growth_factor = (1 + r_monthly) ** n_months
    if r_monthly > 0:
        required_monthly = (target_amount - current_capital * growth_factor) / (
            (growth_factor - 1) / r_monthly if growth_factor != 1 else n_months
        )
    else:
        required_monthly = (target_amount - current_capital) / n_months

    required_monthly = max(0, float(required_monthly))

    # Summary
    return {
        "goal": {
            "current_capital": float(current_capital),
            "monthly_contribution": float(monthly_contribution),
            "target_amount": float(target_amount),
            "time_horizon_years": float(n_years),
            "risk_free_rate": float(risk_free_rate),
        },
        "analysis": {
            "required_return_cagr": round(required_cagr, 4),
            "expected_annual_return": round(expected_portfolio_return, 4),
            "return_gap": round(required_cagr - expected_portfolio_return, 4),
            "probability_of_success_pct": round(success_rate, 2),
            "probability_of_shortfall_pct": round(shortfall_rate, 2),
            "expected_shortfall": round(expected_shortfall, 2),
            "current_plan_on_track": success_rate >= 85,
            "required_monthly_contribution": round(required_monthly, 2),
            "additional_monthly_needed": round(max(0, required_monthly - monthly_contribution), 2),
            "num_simulations": num_sims,
        },
        "distribution": {
            "mean_final": round(float(np.mean(final_values)), 2),
            "median_final": round(float(np.median(final_values)), 2),
            "p10": round(float(np.percentile(final_values, 10)), 2),
            "p25": round(float(np.percentile(final_values, 25)), 2),
            "p75": round(float(np.percentile(final_values, 75)), 2),
            "p90": round(float(np.percentile(final_values, 90)), 2),
        },
        "trajectory": {
            "p10": [round(v, 2) for v in trajectory_10],
            "p50": [round(v, 2) for v in trajectory_50],
            "p90": [round(v, 2) for v in trajectory_90],
        },
    }
