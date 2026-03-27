from services.data_fetcher import get_portfolio_data
from services.risk_metrics import get_risk_summary
from services.regime_detector import get_regime_summary
from services.stress_tester import get_stress_summary
from services.momentum import get_momentum_summary
from agents.decision_engine import generate_decision_options, print_decision_options

if __name__ == "__main__":
    tickers         = ["AAPL", "MSFT", "GOOGL"]
    weights         = [0.4, 0.3, 0.3]
    portfolio_value = 100000
    start           = "2020-01-01"
    end             = "2024-01-01"

    # Step 2 - Fetch data
    data    = get_portfolio_data(tickers, start, end)
    prices  = data["prices"]
    returns = data["returns"]

    # Step 3 - Risk metrics
    risk = get_risk_summary(prices, returns)
    print("=== RISK SUMMARY ===")
    print(risk["summary"].round(4))

    # Step 4 - Market regime detection
    print("\n=== MARKET REGIME DETECTION ===")
    regime_summary = get_regime_summary(returns)
    print(regime_summary)

    # Step 5 - Stress testing
    print("\n=== STRESS TEST RESULTS ===")
    stress = get_stress_summary(tickers, weights, portfolio_value)
    print(stress["stress_table"].to_string())
    print(f"\n⚠️  Worst Scenario : {stress['worst_scenario']}")
    print(f"💸  Maximum Loss   : ${stress['worst_loss']:,.2f}")
    print(f"📉  Loss %         : {stress['worst_loss_pct']}%")

    # Step 6 - Momentum & Performance Ratios
    print("\n=== MOMENTUM SIGNALS ===")
    momentum = get_momentum_summary(prices, returns)
    print(momentum["momentum_signals"].to_string())
    print("\n=== PERFORMANCE RATIOS ===")
    print(momentum["performance"].to_string())

    # Step 7 - Decision engine
    options = generate_decision_options(
        tickers         = tickers,
        weights         = weights,
        risk_summary    = risk["summary"],
        regime_summary  = regime_summary,
        stress_results  = stress,
        portfolio_value = portfolio_value
    )
    print_decision_options(options)