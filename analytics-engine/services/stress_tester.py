import numpy as np
import pandas as pd

# Define historical stress scenarios
SCENARIOS = {
    "2008 Financial Crisis": {
        "AAPL":  -0.40,
        "MSFT":  -0.45,
        "GOOGL": -0.55,
        "default": -0.40
    },
    "COVID Crash 2020": {
        "AAPL":  -0.30,
        "MSFT":  -0.30,
        "GOOGL": -0.31,
        "default": -0.30
    },
    "Tech Sector Crash": {
        "AAPL":  -0.35,
        "MSFT":  -0.38,
        "GOOGL": -0.40,
        "default": -0.35
    },
    "Rate Hike Shock": {
        "AAPL":  -0.15,
        "MSFT":  -0.18,
        "GOOGL": -0.20,
        "default": -0.15
    }
}


def run_stress_test(
    tickers: list,
    weights: list,
    portfolio_value: float = 100000
) -> pd.DataFrame:
    """
    Simulates portfolio loss under each stress scenario.

    Args:
        tickers:          e.g. ["AAPL", "MSFT", "GOOGL"]
        weights:          e.g. [0.4, 0.3, 0.3] — must sum to 1.0
        portfolio_value:  total portfolio value in USD (default $100,000)

    Returns:
        DataFrame showing loss per scenario
    """

    if round(sum(weights), 5) != 1.0:
        raise ValueError(f"Weights must sum to 1.0, got {sum(weights)}")

    results = []

    for scenario_name, shocks in SCENARIOS.items():
        portfolio_loss = 0.0
        ticker_losses = {}

        for ticker, weight in zip(tickers, weights):
            # Get shock for this ticker, use default if not defined
            shock = shocks.get(ticker, shocks["default"])

            # Calculate dollar loss for this position
            position_value = portfolio_value * weight
            loss = position_value * shock
            portfolio_loss += loss
            ticker_losses[ticker] = round(loss, 2)

        results.append({
            "Scenario":             scenario_name,
            "Portfolio Loss":       round(portfolio_loss, 2),
            "Portfolio Loss (%)":   round((portfolio_loss / portfolio_value) * 100, 2),
            "Remaining Value":      round(portfolio_value + portfolio_loss, 2),
            **ticker_losses
        })

    return pd.DataFrame(results).set_index("Scenario")


def get_worst_scenario(stress_results: pd.DataFrame) -> str:
    """
    Returns the name of the worst scenario.
    """
    return stress_results["Portfolio Loss"].idxmin()


def get_stress_summary(
    tickers: list,
    weights: list,
    portfolio_value: float = 100000
) -> dict:
    """
    Master function — runs stress test and returns full summary.
    """
    results = run_stress_test(tickers, weights, portfolio_value)
    worst = get_worst_scenario(results)

    return {
        "stress_table": results,
        "worst_scenario": worst,
        "worst_loss": results.loc[worst, "Portfolio Loss"],
        "worst_loss_pct": results.loc[worst, "Portfolio Loss (%)"]
    }