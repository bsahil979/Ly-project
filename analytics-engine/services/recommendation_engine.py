"""
Recommendation engine — central decision layer that combines signals from
portfolio analytics, risk engine, benchmark comparison, attribution, risk
budgeting, ML forecasts, HMM regime, stress tests, and optimization.

Each recommendation includes:
- Action (what to do)
- Asset (which ticker)
- Reason (why)
- Supporting metrics
- Supporting models
- Expected impact
- Confidence level
- Timestamp
"""
import numpy as np
import pandas as pd
from datetime import datetime
from services.portfolio_score import get_asset_category, identify_portfolio_risks
from services.stress_tester import get_stress_summary


def generate_recommendations(
    tickers: list[str],
    weights: list[float],
    portfolio_value: float,
    risk_summary: pd.DataFrame,
    portfolio_returns: pd.DataFrame,
    regime: dict,
    stress: dict,
    portfolio_score: dict,
    attribution: dict,
    risk_budget: dict,
    forecast_details: dict,
    marketmind_details: dict,
    benchmark_comparison: dict = None,
) -> list[dict]:
    """
    Generate evidence-backed portfolio recommendations.

    Recommendations are derived from the actual portfolio data, not fabricated.
    Each recommendation cites specific metrics and models that support it.
    """
    now = datetime.now().isoformat()
    recommendations = []
    weights_arr = np.array(weights, dtype=float)
    weights_arr = weights_arr / weights_arr.sum()

    # --- 1. Risk concentration / overweight position ---
    max_weight_idx = int(np.argmax(weights_arr))
    max_weight = float(weights_arr[max_weight_idx])
    max_ticker = tickers[max_weight_idx]
    max_ticker_upper = max_ticker.upper().strip()

    if max_weight > 0.20:
        rb = next((r for r in risk_budget.get("risk_contributions", [])
                    if r["ticker"] == max_ticker_upper), None)
        pct_risk = rb.get("percentage_contribution_to_risk", 0) if rb else 0
        recommendations.append({
            "id": f"reduce-{max_ticker_upper}",
            "action": "reduce_position",
            "asset": max_ticker_upper,
            "reason": f"{max_ticker_upper} represents {max_weight*100:.0f}% of portfolio value "
                      f"and {pct_risk:.0f}% of portfolio risk",
            "supporting_metrics": {
                "weight": round(max_weight, 4),
                "risk_contribution_pct": pct_risk,
                "volatility": rb.get("volatility", 0) if rb else 0,
            },
            "supporting_models": ["Risk Budgeting", "Portfolio Scoring"],
            "expected_impact": f"Reducing {max_ticker_upper} to {min(max_weight, 0.15)*100:.0f}% weight "
                               f"would reduce portfolio volatility and concentration risk",
            "confidence": "high" if pct_risk > 25 else "medium",
            "timestamp": now,
        })

    # --- 2. Sector concentration ---
    sector_weights = {}
    for t, w in zip(tickers, weights_arr):
        cat = get_asset_category(t)
        sector_weights[cat] = sector_weights.get(cat, 0) + w

    dominant_sector = max(sector_weights, key=sector_weights.get)
    dominant_pct = sector_weights[dominant_sector]
    if dominant_pct > 0.40:
        sector_tkr = [t for t, w in zip(tickers, weights_arr)
                       if get_asset_category(t) == dominant_sector]
        recommendations.append({
            "id": f"diversify-sector-{dominant_sector}",
            "action": "add_diversification",
            "asset": dominant_sector,
            "reason": f"Overconcentration in {dominant_sector} sector "
                      f"({dominant_pct*100:.0f}% of portfolio)",
            "supporting_metrics": {
                "sector_weight": round(dominant_pct, 4),
                "sector_tickers": sector_tkr,
            },
            "supporting_models": ["Portfolio Scoring — Sector Risk", "Attribution Engine"],
            "expected_impact": f"Adding non-{dominant_sector} positions or reducing {dominant_sector} "
                               f"holdings would improve diversification",
            "confidence": "high" if dominant_pct > 0.50 else "medium",
            "timestamp": now,
        })

    # --- 3. MarketMind model signal ---
    for ticker, mm in marketmind_details.items():
        if isinstance(mm, dict) and mm.get("recommendation") in ("SELL", "BUY"):
            confidence = mm.get("confidence", 0)
            if confidence > 0.55:
                recommendations.append({
                    "id": f"marketmind-{ticker}",
                    "action": "hold" if mm["recommendation"] == "BUY" else "review",
                    "asset": ticker.upper(),
                    "reason": f"MarketMind meta-model signals {mm['recommendation']} "
                              f"(confidence {confidence:.1%}, score {mm['score']:.2f})",
                    "supporting_metrics": {
                        "confidence": confidence,
                        "score": mm.get("score", 0),
                        "class_probabilities": mm.get("class_probabilities", {}),
                    },
                    "supporting_models": ["MarketMind Meta-Model (XGBoost + Technical + Sentiment)"],
                    "expected_impact": "Model considers technical indicators, sentiment, and regime context",
                    "confidence": "high" if confidence > 0.70 else "medium",
                    "timestamp": now,
                })

    # --- 4. Stress test vulnerability ---
    worst_scenario = stress.get("worst_scenario", "Unknown")
    worst_loss_pct = stress.get("worst_loss_pct", 0)
    if worst_loss_pct > 25:
        recommendations.append({
            "id": "stress-test-risk",
            "action": "add_protection",
            "asset": "Portfolio-wide",
            "reason": f"Under stress scenario '{worst_scenario}', portfolio could lose "
                      f"{worst_loss_pct:.1f}%",
            "supporting_metrics": {
                "worst_scenario": worst_scenario,
                "worst_loss_pct": worst_loss_pct,
                "worst_loss": stress.get("worst_loss", 0),
            },
            "supporting_models": ["Stress Tester"],
            "expected_impact": "Adding downside protection (e.g., bonds, cash, or defensive assets) "
                               "could reduce the impact of extreme market events",
            "confidence": "high",
            "timestamp": now,
        })

    # --- 5. Risk-adjusted return ---
    if isinstance(risk_summary, pd.DataFrame) and "Volatility (Annual)" in risk_summary:
        avg_vol = float(risk_summary["Volatility (Annual)"].mean())
        avg_return = float(portfolio_returns.mean().mean() * 252) if not portfolio_returns.empty else 0
        sharpe_proxy = avg_return / avg_vol if avg_vol > 0 else 0

        if avg_vol > 0.35 and sharpe_proxy < 0.4:
            recommendations.append({
                "id": "high-volatility",
                "action": "de-risk",
                "asset": "Portfolio-wide",
                "reason": f"Portfolio volatility ({avg_vol*100:.1f}%) is elevated with "
                          f"suboptimal risk-adjusted return (Sharpe proxy: {sharpe_proxy:.2f})",
                "supporting_metrics": {
                    "volatility": round(avg_vol, 4),
                    "expected_return": round(avg_return, 4),
                    "sharpe_ratio": round(sharpe_proxy, 4),
                },
                "supporting_models": ["Risk Metrics", "Portfolio Scoring"],
                "expected_impact": "Adding lower-volatility assets (bonds, REITs) could improve "
                                   "the Sharpe ratio without significantly impacting expected return",
                "confidence": "high",
                "timestamp": now,
            })

    # --- 6. Benchmark underperformance ---
    if benchmark_comparison and isinstance(benchmark_comparison, dict):
        comp = benchmark_comparison.get("comparison", {})
        alpha = comp.get("alpha", 0)
        ir = comp.get("information_ratio", 0)
        if alpha < 0 and abs(ir) > 0.1:
            recommendations.append({
                "id": "benchmark-underperformance",
                "action": "rebalance_toward_benchmark",
                "asset": benchmark_comparison.get("benchmark_ticker", "Benchmark"),
                "reason": f"Portfolio has negative alpha ({alpha*100:.1f}%) against "
                          f"{benchmark_comparison.get('benchmark_display', 'benchmark')}",
                "supporting_metrics": {
                    "alpha": alpha,
                    "information_ratio": ir,
                    "tracking_error": comp.get("tracking_error", 0),
                },
                "supporting_models": ["Benchmark Engine"],
                "expected_impact": "Rebalancing toward benchmark allocation could improve alpha",
                "confidence": "medium",
                "timestamp": now,
            })

    # --- 7. RL optimization suggestion ---
    rl_ready = portfolio_score.get("rl_ready", False) if isinstance(portfolio_score, dict) else False
    if rl_ready:
        recommendations.append({
            "id": "rl-optimization",
            "action": "consider_rl_allocation",
            "asset": "Portfolio-wide",
            "reason": "PPO RL agent has identified a potentially improved allocation",
            "supporting_metrics": {},
            "supporting_models": ["Portfolio PPO (experimental)"],
            "expected_impact": "Review the RL-suggested allocations for enhanced risk-adjusted returns",
            "confidence": "experimental",
            "timestamp": now,
        })

    # --- 8. Portfolio score gaps ---
    score_components = portfolio_score.get("components", {}) if isinstance(portfolio_score, dict) else {}
    for comp_key, comp_val in score_components.items():
        if isinstance(comp_val, dict) and comp_val.get("score", 100) < comp_val.get("max", 100) * 0.5:
            recommendations.append({
                "id": f"score-gap-{comp_key}",
                "action": "improve_score_component",
                "asset": comp_val.get("label", comp_key),
                "reason": f"This component scores {comp_val['score']}/{comp_val['max']} points "
                          f"(below 50% of maximum)",
                "supporting_metrics": {
                    "current_score": comp_val["score"],
                    "max_score": comp_val["max"],
                    "detail": comp_val.get("detail", ""),
                },
                "supporting_models": ["Portfolio Score Engine"],
                "expected_impact": comp_val.get("detail", ""),
                "confidence": "medium",
                "timestamp": now,
            })

    # --- 9. Regime-aware adjustment ---
    regime_label = regime.get("current_regime", "Unknown") if isinstance(regime, dict) else "Unknown"
    regime_conf = regime.get("confidence", 0) if isinstance(regime, dict) else 0
    if "Bear" in str(regime_label) and regime_conf > 0.5:
        recommendations.append({
            "id": "regime-bearish",
            "action": "increase_cash_allocation",
            "asset": "Portfolio-wide",
            "reason": f"HMM detects {regime_label} regime (confidence {regime_conf:.1%})",
            "supporting_metrics": {
                "regime": regime_label,
                "confidence": regime_conf,
            },
            "supporting_models": ["HMM Regime Detector"],
            "expected_impact": "Increasing cash allocation during bearish regimes preserves capital",
            "confidence": "medium" if regime_conf > 0.6 else "low",
            "timestamp": now,
        })

    return recommendations
