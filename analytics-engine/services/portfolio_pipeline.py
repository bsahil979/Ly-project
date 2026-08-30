"""
Unified Portfolio Pipeline — canonical analysis pipeline that chains all
existing ML engines into one coherent output.

Pipeline:
  User Portfolio
  -> Market Data (data_fetcher)
  -> Data Validation
  -> Feature Engineering
  -> Portfolio Analytics (risk_metrics)
  -> ML Models (regime_detector, forecaster, sentiment_analyzer, meta_model)
  -> Risk Engine (risk_metrics + risk_budget)
  -> Stress Engine (stress_tester)
  -> Benchmark Engine (benchmark)
  -> Attribution Engine (attribution)
  -> Optimization (portfolio_rl_service)
  -> Recommendation Engine (recommendation_engine)
  -> Explainability (decision_engine + ai_advisor)
  -> LLM Advisor (ai_advisor)

Each stage consumes outputs from the previous stage.  No calculation is
duplicated across stages.
"""
import os
import numpy as np
import pandas as pd
from datetime import datetime

from services.data_fetcher import get_portfolio_data
from services.risk_metrics import get_risk_summary
from services.regime_detector import detect_market_regime_hmm
from services.stress_tester import get_stress_summary
from services.forecaster import get_lstm_forecast
from services.sentiment_analyzer import get_sentiment_analysis
from services.portfolio_score import (
    compute_portfolio_score,
    compute_asset_allocation,
    get_currency_symbol,
)
from services.benchmark import compute_benchmark_comparison
from services.attribution import compute_attribution
from services.risk_budget import compute_risk_budget, compute_correlation_matrix
from services.recommendation_engine import generate_recommendations
from trading_engine.meta_model import MarketMindMetaModel
from trading_engine.portfolio_rl_service import recommend_allocations, portfolio_rl_is_ready


def _price_series(prices: pd.DataFrame, ticker: str) -> pd.Series:
    """Extract a single ticker's closing-price series from a price DataFrame."""
    sym = ticker.upper().strip()
    if isinstance(prices, pd.Series):
        return prices.dropna()
    cols = {str(c).upper(): c for c in prices.columns}
    if sym in cols:
        return prices[cols[sym]].dropna()
    if len(prices.columns) == 1:
        return prices.iloc[:, 0].dropna()
    raise ValueError(f"No price column for {sym}")


def run_portfolio_pipeline(
    tickers: list[str],
    weights: list[float],
    portfolio_value: float = 100000,
    start: str = "2020-01-01",
    end: str | None = None,
    horizon: int = 30,
    benchmark: str = "SPY",
    risk_free_rate: float = 0.02,
) -> dict:
    """
    Execute the full portfolio analysis pipeline.

    Returns a structured dict with every stage's output.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    end = end or today

    # ── 1. Market Data ────────────────────────────────────────────────
    data = get_portfolio_data(tickers, start, end)
    prices = data["prices"]
    returns = data["returns"]
    currency_map = data["currencies"]
    currency_symbol = get_currency_symbol(currency_map)

    # ── 2. Risk Engine ────────────────────────────────────────────────
    risk = get_risk_summary(prices, returns)
    risk_summary = risk["summary"].round(4).to_dict()
    drawdown_series = risk["drawdown_series"]

    # ── 3. Market Regime (HMM) ────────────────────────────────────────
    # SPY + portfolio-level regime
    spy_col = {str(c).upper(): c for c in prices.columns}.get("SPY")
    if spy_col:
        spy_prices = prices[spy_col].dropna()
        spy_returns = spy_prices.pct_change().dropna()
        market_regime = detect_market_regime_hmm(spy_returns)
    else:
        market_regime = detect_market_regime_hmm(returns.mean(axis=1))

    portfolio_regime = detect_market_regime_hmm(returns.mean(axis=1))

    # ── 4. Stress Testing ─────────────────────────────────────────────
    stress = get_stress_summary(tickers, weights, portfolio_value)

    # ── 5. Benchmark Comparison ───────────────────────────────────────
    benchmark_result = compute_benchmark_comparison(
        prices, weights, portfolio_value,
        benchmark_ticker=benchmark, risk_free_rate=risk_free_rate
    )

    # ── 6. Attribution ────────────────────────────────────────────────
    attribution = compute_attribution(
        tickers, weights, prices, portfolio_value, currency_symbol
    )

    # ── 7. Risk Budgeting ─────────────────────────────────────────────
    risk_budget = compute_risk_budget(
        tickers, weights, returns, portfolio_value, confidence_level=0.95
    )
    risk_budget["currency"] = currency_symbol

    correlation = compute_correlation_matrix(tickers, returns)

    # ── 8. ML Models: Forecast + Sentiment + MarketMind ───────────────
    ticker_details = {}
    for ticker in tickers:
        sym = ticker.upper().strip()
        detail = {}
        try:
            ticker_prices = _price_series(prices, sym)
            if len(ticker_prices) >= 30:
                forecast = get_lstm_forecast(ticker_prices, horizon, train_epochs=8)
                detail["forecast"] = {
                    "spot_price": float(ticker_prices.iloc[-1]),
                    "predictions": forecast[:5] + ([{"...": "truncated"}] if len(forecast) > 5 else []),
                    "horizon": horizon,
                    "all_predictions": forecast,
                }
            else:
                detail["forecast"] = {"error": f"Insufficient history for {sym}"}
        except Exception as exc:
            detail["forecast_error"] = str(exc)

        try:
            detail["sentiment"] = get_sentiment_analysis(sym)
        except Exception as exc:
            detail["sentiment_error"] = str(exc)

        try:
            model = MarketMindMetaModel(
                model_dir=os.path.join(os.path.dirname(__file__), "..", "models", "meta_model")
            )
            if model.is_ready():
                if model.model is None:
                    model.load()
                if model.model is not None:
                    detail["marketmind"] = model.predict_for_ticker(sym)
                else:
                    detail["marketmind"] = {"status": "not_trained"}
            else:
                detail["marketmind"] = {"status": "not_trained"}
        except Exception as exc:
            detail["marketmind_error"] = str(exc)

        ticker_details[ticker] = detail

    # ── 9. Portfolio Optimizer (PPO RL) ───────────────────────────────
    models_base = os.path.join(os.path.dirname(__file__), "..", "models")
    rl_alloc = recommend_allocations(
        user_tickers=tickers,
        user_weights=weights,
        base_dir=models_base,
    )

    # ── 10. Portfolio Score ───────────────────────────────────────────
    asset_allocation = compute_asset_allocation(tickers, weights)
    portfolio_score = compute_portfolio_score(
        tickers=tickers,
        weights=weights,
        risk_summary=risk["summary"],
        returns=returns,
        portfolio_value=portfolio_value,
    )

    # ── 11. Recommendations ───────────────────────────────────────────
    recommendations = generate_recommendations(
        tickers=tickers,
        weights=weights,
        portfolio_value=portfolio_value,
        risk_summary=risk["summary"],
        portfolio_returns=returns,
        regime=market_regime,
        stress=stress,
        portfolio_score=portfolio_score,
        attribution=attribution,
        risk_budget=risk_budget,
        forecast_details=ticker_details,
        marketmind_details={t: ticker_details.get(t, {}).get("marketmind", {}) for t in tickers},
        benchmark_comparison=benchmark_result,
    )

    # ── Assemble ──────────────────────────────────────────────────────
    return {
        "pipeline_id": datetime.now().isoformat(),
        "tickers": tickers,
        "weights": weights,
        "portfolio_value": portfolio_value,
        "currency": currency_symbol,
        "period": {"start": start, "end": end},
        "risk_engine": risk_summary,
        "market_regime": market_regime,
        "portfolio_regime": portfolio_regime,
        "stress_test": {
            "stress_table": _clean_df(stress["stress_table"]),
            "worst_scenario": stress["worst_scenario"],
            "worst_loss": stress["worst_loss"],
            "worst_loss_pct": stress["worst_loss_pct"],
        },
        "benchmark": benchmark_result,
        "attribution": attribution,
        "risk_budget": risk_budget,
        "correlation": correlation,
        "ml_models": {
            "ticker_details": ticker_details,
            "rl_allocation": rl_alloc,
            "rl_ready": portfolio_rl_is_ready(models_base),
        },
        "portfolio_score": portfolio_score,
        "asset_allocation": asset_allocation,
        "recommendations": recommendations,
    }


def _clean_df(df: pd.DataFrame) -> dict:
    """Convert a DataFrame to a JSON-serializable dict."""
    try:
        return df.to_dict()
    except Exception:
        return {"raw": str(df)}
