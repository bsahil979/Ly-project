import pandas as pd

# Risk thresholds for decision making
VOLATILITY_THRESHOLD_HIGH = 0.35
VOLATILITY_THRESHOLD_LOW  = 0.20
VAR_THRESHOLD_HIGH        = -0.03
DRAWDOWN_THRESHOLD_HIGH   = -0.30


def assess_portfolio_risk(risk_summary: pd.DataFrame) -> str:
    """
    Assesses overall portfolio risk level.
    Returns: "HIGH", "MEDIUM", or "LOW"
    """
    avg_volatility  = risk_summary["Volatility (Annual)"].mean()
    avg_var         = risk_summary["VaR (95%)"].mean()
    avg_drawdown    = risk_summary["Max Drawdown"].mean()

    high_flags = 0
    if avg_volatility > VOLATILITY_THRESHOLD_HIGH:
        high_flags += 1
    if avg_var < VAR_THRESHOLD_HIGH:
        high_flags += 1
    if avg_drawdown < DRAWDOWN_THRESHOLD_HIGH:
        high_flags += 1

    if high_flags >= 2:
        return "HIGH"
    elif high_flags == 1:
        return "MEDIUM"
    else:
        return "LOW"


def generate_decision_options(
    tickers:          list,
    weights:          list,
    risk_summary:     pd.DataFrame,
    regime_summary:   pd.DataFrame,
    stress_results:   dict,
    portfolio_value:  float = 100000,
    currency_symbol:  str = "$"
) -> list:
    """
    Generates 3 decision options based on risk analysis.
    Each option includes allocation, reasoning, and trade-offs.
    """

    risk_level   = assess_portfolio_risk(risk_summary)
    worst_loss   = stress_results["worst_loss"]
    worst_scene  = stress_results["worst_scenario"]
    worst_pct    = stress_results["worst_loss_pct"]

    # Get current regime — supports both old DataFrame and new HMM dict formats
    if isinstance(regime_summary, dict):
        # New HMM format: {'current_regime': '...', 'state_id': ..., 'confidence': ...}
        dominant_regime = regime_summary.get("current_regime", "Unknown")
    elif isinstance(regime_summary, pd.DataFrame):
        # Legacy DataFrame format
        current_regimes = regime_summary["Current Regime"].values
        regime_counts   = pd.Series(current_regimes).value_counts()
        dominant_regime = regime_counts.index[0]
    else:
        dominant_regime = str(regime_summary)

    options = []

    # ─────────────────────────────────────────
    # OPTION 1 — CONSERVATIVE
    # ─────────────────────────────────────────
    conservative_weights = []
    for w in weights:
        conservative_weights.append(round(w * 0.5, 2))  # cut equity by 50%
    bonds_allocation = round(1.0 - sum(conservative_weights), 2)

    options.append({
        "option":       "Conservative",
        "emoji":        "🛡️",
        "description":  "Reduce equity exposure, shift capital to bonds/cash",
        "allocations":  {
            **{t: f"{round(w*100)}%" for t, w in zip(tickers, conservative_weights)},
            "Bonds/Cash": f"{round(bonds_allocation*100)}%"
        },
        "expected_return":    "6% - 9% annually",
        "downside_risk":      f"{currency_symbol}{worst_loss * 0.4:,.2f} in worst case ({worst_pct * 0.4:.1f}%)",
        "reasoning": [
            f"Portfolio risk level is {risk_level}",
            f"Current market regime is {dominant_regime}",
            f"Worst case scenario ({worst_scene}) could cause {worst_pct}% loss",
            "Reducing equity by 50% and moving to bonds limits downside significantly",
            "Best for capital preservation during uncertain market conditions"
        ],
        "best_for":     "Risk-averse investors or near-term capital needs"
    })

    # ─────────────────────────────────────────
    # OPTION 2 — BALANCED
    # ─────────────────────────────────────────
    balanced_weights = []
    for w in weights:
        balanced_weights.append(round(w * 0.75, 2))  # cut equity by 25%
    bonds_allocation_balanced = round(1.0 - sum(balanced_weights), 2)

    options.append({
        "option":       "Balanced",
        "emoji":        "⚖️",
        "description":  "Maintain core positions, add moderate diversification",
        "allocations":  {
            **{t: f"{round(w*100)}%" for t, w in zip(tickers, balanced_weights)},
            "Bonds/Cash": f"{round(bonds_allocation_balanced*100)}%"
        },
        "expected_return":    "10% - 14% annually",
        "downside_risk":      f"{currency_symbol}{worst_loss * 0.7:,.2f} in worst case ({worst_pct * 0.7:.1f}%)",
        "reasoning": [
            f"Portfolio risk level is {risk_level}",
            f"Market is currently in {dominant_regime} regime",
            "Reducing equity by 25% provides moderate protection",
            "Maintaining majority of positions preserves upside potential",
            "Bond allocation acts as a buffer during market shocks"
        ],
        "best_for":     "Investors seeking growth with moderate risk protection"
    })

    # ─────────────────────────────────────────
    # OPTION 3 — AGGRESSIVE
    # ─────────────────────────────────────────
    options.append({
        "option":       "Aggressive",
        "emoji":        "🚀",
        "description":  "Hold or increase current positions for maximum growth",
        "allocations":  {
            **{t: f"{round(w*100)}%" for t, w in zip(tickers, weights)},
        },
        "expected_return":    "15% - 22% annually",
        "downside_risk":      f"{currency_symbol}{worst_loss:,.2f} in worst case ({worst_pct}%)",
        "reasoning": [
            f"Portfolio risk level is {risk_level} but long-term outlook is positive",
            f"Market regime is {dominant_regime} — volatility can mean opportunity",
            "Full equity exposure maximizes participation in market recovery",
            "Historical data shows tech stocks recover strongly after crashes",
            "Suitable only if investment horizon is 5+ years"
        ],
        "best_for":     "Long-term investors comfortable with high volatility"
    })

    return options


def print_decision_options(options: list):
    """
    Prints decision options in a clean, readable format.
    """
    print("\n" + "="*60)
    print("       SMART PORTFOLIO ADVISOR — DECISION OPTIONS")
    print("="*60)

    for opt in options:
        print(f"\n{opt['emoji']}  OPTION: {opt['option'].upper()}")
        print(f"   {opt['description']}")
        print(f"\n   📊 Allocations:")
        for asset, alloc in opt["allocations"].items():
            print(f"      {asset}: {alloc}")
        print(f"\n   📈 Expected Return : {opt['expected_return']}")
        print(f"   📉 Downside Risk   : {opt['downside_risk']}")
        print(f"\n   🧠 Reasoning:")
        for reason in opt["reasoning"]:
            print(f"      • {reason}")
        print(f"\n   👤 Best For: {opt['best_for']}")
        print("-"*60)