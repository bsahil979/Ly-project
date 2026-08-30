from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import datetime
import pandas as pd
import yfinance as yf
from services.data_fetcher import get_portfolio_data
from services.risk_metrics import get_risk_summary
from services.regime_detector import detect_market_regime_hmm
from services.stress_tester import get_stress_summary
from services.forecaster import get_lstm_forecast
from services.portfolio_score import compute_portfolio_score, compute_asset_allocation
from agents.decision_engine import generate_decision_options
from agents.ai_advisor import AIAdvisor
from services.sentiment_analyzer import get_sentiment_analysis
from trading_engine.models_layer import TradingModels
from config.ticker_universe import assets_flat, load_universe
from trading_engine.universal_models import apply_hybrid_to_trading_models, universal_is_ready
from trading_engine.portfolio_rl_service import recommend_allocations, portfolio_rl_is_ready
from trading_engine.meta_model import MarketMindMetaModel
from services.portfolio_optimizer import PortfolioOptimizer
from services.paper_trading import PaperTradingEngine, create_paper_trading_account
from services.monitoring_alerts import MonitoringEngine, MonitoringConfig

import glob
import json
import os
import logging


def _model_dir_ready(model_dir: str) -> dict:
    has_lstm = os.path.exists(os.path.join(model_dir, 'lstm.pt')) or os.path.exists(os.path.join(model_dir, 'lstm_state.pt'))
    has_rf = os.path.exists(os.path.join(model_dir, 'rf.pkl')) or os.path.exists(os.path.join(model_dir, 'rf_model.joblib'))
    has_hmm = os.path.exists(os.path.join(model_dir, 'hmm.pkl')) or os.path.exists(os.path.join(model_dir, 'hmm_model.joblib'))
    has_ppo = os.path.exists(os.path.join(model_dir, 'ppo_policy.zip'))
    has_scalers = os.path.exists(os.path.join(model_dir, 'scaler_lstm.pkl')) and os.path.exists(os.path.join(model_dir, 'scaler_rf.pkl'))
    ready = bool(has_lstm and has_rf and has_hmm and has_scalers and has_ppo)
    return {
        "lstm": has_lstm,
        "rf": has_rf,
        "hmm": has_hmm,
        "ppo": has_ppo,
        "scalers": has_scalers,
        "ready": ready,
    }

def get_currency_symbol(currency_map: dict) -> str:
    """Helper to determine dominant currency symbol. Favors INR if present."""
    if "INR" in currency_map.values():
        return "₹"
    counts = pd.Series(currency_map.values()).value_counts()
    dominant = counts.index[0] if not counts.empty else "USD"
    symbols = { "USD": "$", "INR": "₹", "EUR": "€", "GBP": "£" }
    return symbols.get(dominant, "$")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PortfolioRequest(BaseModel):
    tickers: list[str]
    weights: list[float]
    portfolio_value: float = 100000
    start: str = "2020-01-01"
    end: str = "2024-01-01"

analyze_cache = {}


# ─────────────────────────────────────────────────────────────────────────
#  AI Advisor (LLM + RAG overlay)
# ─────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str
    tickers: list[str] = []
    weights: list[float] = []
    portfolio_value: float = 100000
    start: str = "2020-01-01"
    end: str | None = None
    horizon: int = 30
    top_k: int = 5
    stream: bool = False


_ai_advisor: Optional[AIAdvisor] = None


def get_ai_advisor() -> AIAdvisor:
    global _ai_advisor
    if _ai_advisor is None:
        _ai_advisor = AIAdvisor()
    return _ai_advisor


def _marketmind_summary_for_ticker(ticker: str) -> dict | None:
    ticker = ticker.upper().strip()
    model = MarketMindMetaModel(model_dir=os.path.join(os.path.dirname(__file__), 'models', 'meta_model'))
    try:
        if not model.is_ready():
            return None
        if model.model is None:
            model.load()
        if model.model is None:
            return None
        prediction = model.predict_for_ticker(ticker)
        return {
            "ticker": ticker,
            "recommendation": prediction["recommendation"],
            "confidence": prediction["confidence"],
            "score": prediction["score"],
            "class_probabilities": prediction["class_probabilities"],
        }
    except Exception:
        return None


@app.post("/analyze")
def analyze_portfolio(req: PortfolioRequest):
    cache_key = str(sorted(zip(req.tickers, [round(w, 4) for w in req.weights]))) + f"_{req.portfolio_value}_{req.start}_{req.end}"
    if cache_key in analyze_cache:
        return analyze_cache[cache_key]
        
    # Input validation
    if len(req.tickers) != len(req.weights):
        raise HTTPException(status_code=400, detail="Number of tickers and weights must match.")
    if abs(sum(req.weights) - 1.0) > 0.01:
        raise HTTPException(status_code=400, detail=f"Weights must sum to 1.0 (current sum: {sum(req.weights)})")
    try:
        data = get_portfolio_data(req.tickers, req.start, req.end)
        prices = data["prices"]
        returns = data["returns"]
        risk = get_risk_summary(prices, returns)
        regime = detect_market_regime_hmm(returns.mean(axis=1)) # Use mean returns for HMM
        stress = get_stress_summary(req.tickers, req.weights, req.portfolio_value)
        currency_symbol = get_currency_symbol(data["currencies"])
        options = generate_decision_options(
            tickers=req.tickers,
            weights=req.weights,
            risk_summary=risk["summary"],
            regime_summary=regime,
            stress_results=stress,
            portfolio_value=req.portfolio_value,
            currency_symbol=currency_symbol
        )
        models_base = os.path.join(os.path.dirname(__file__), 'models')
        rl_alloc = recommend_allocations(
            user_tickers=req.tickers,
            user_weights=req.weights,
            base_dir=models_base,
        )
        if rl_alloc.get('ready') and rl_alloc.get('recommended_weights'):
            rw = rl_alloc['recommended_weights']
            options.insert(0, {
                'option': 'RL Optimized',
                'emoji': '[PPO]',
                'description': 'PPO portfolio policy — weight targets from full-universe training (Sharpe/drawdown-aware reward).',
                'allocations': {k: f'{round(v * 100)}%' for k, v in rw.items()},
                'expected_return': 'Regime-adaptive (historical simulation)',
                'downside_risk': f'{currency_symbol}{stress.get("worst_loss", 0):,.0f} ({stress.get("worst_loss_pct", 0):.1f}% stress)',
                'reasoning': rl_alloc.get('reasoning', []) + rl_alloc.get('rebalance_hint', []),
                'best_for': 'Investors seeking systematic allocation and dynamic cash management',
            })
        marketmind = {}
        for ticker in req.tickers:
            summary = _marketmind_summary_for_ticker(ticker)
            if summary is not None:
                marketmind[ticker] = summary

        # Portfolio Score (PortfolioPilot-style composite score)
        scores = compute_asset_allocation(req.tickers, req.weights)
        portfolio_score = compute_portfolio_score(
            tickers=req.tickers,
            weights=req.weights,
            risk_summary=risk["summary"],
            returns=returns,
            portfolio_value=req.portfolio_value,
        )

        res = {
            "risk_summary": risk["summary"].round(4).to_dict(),
            "regime_summary": regime,
            "stress_test": stress["stress_table"].to_dict(),
            "decision_options": options,
            "currency_map": data["currencies"],
            "portfolio_rl": rl_alloc,
            "portfolio_rl_ready": portfolio_rl_is_ready(models_base),
            "marketmind": marketmind,
            "marketmind_ready": bool(marketmind),
            "portfolio_score": portfolio_score,
            "asset_allocation": scores,
        }
        analyze_cache[cache_key] = res
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

forecast_cache = {}


@app.on_event("startup")
def _clear_forecast_cache_on_startup():
    """Drop stale forecasts from previous API runs (wrong symbol scale / old code)."""
    forecast_cache.clear()
    analyze_cache.clear()


def _price_series_for_ticker(prices: pd.DataFrame | pd.Series, ticker: str) -> pd.Series:
    """Resolve closing prices for one symbol (column names may differ by case)."""
    sym = ticker.upper().strip()
    if isinstance(prices, pd.Series):
        return prices.dropna()
    if not isinstance(prices, pd.DataFrame):
        raise ValueError("Unexpected prices type")
    cols = {str(c).upper(): c for c in prices.columns}
    if sym in cols:
        return prices[cols[sym]].dropna()
    if len(prices.columns) == 1:
        return prices.iloc[:, 0].dropna()
    raise ValueError(f"No price column for {sym}")


@app.post("/forecast/cache/clear")
def clear_forecast_cache():
    forecast_cache.clear()
    return {"status": "ok", "message": "Forecast cache cleared"}


def _forecast_from_saved_lstm(prices: pd.Series, sym: str, horizon: int):
    """Use on-disk per-ticker LSTM when available (fast path)."""
    base = os.path.join(os.path.dirname(__file__), 'models')
    lstm_path = os.path.join(base, sym, 'lstm.pt')
    if not os.path.exists(lstm_path):
        lstm_path = os.path.join(base, sym, 'lstm_state.pt')
    if not os.path.exists(lstm_path):
        return None
    df = pd.DataFrame({'Close': prices.astype(float).values}, index=prices.index)
    tm = TradingModels(df)
    loaded = tm.load_models(base_dir=base, ticker=sym)
    if not (loaded.get('lstm') and loaded.get('scalers')):
        return None
    preds = tm.predict_lstm(horizon=horizon)
    dates = [
        (datetime.datetime.now() + datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        for i in range(1, horizon + 1)
    ]
    return [
        {'date': d, 'predicted_price': float(p)}
        for d, p in zip(dates, preds)
    ]


@app.get("/forecast/{ticker}")
def forecast_ticker(ticker: str, horizon: int = 30, refresh: bool = False):
    sym = ticker.upper().strip()
    cache_key = f"{sym}_{horizon}"
    if refresh and cache_key in forecast_cache:
        forecast_cache.pop(cache_key, None)
    if not refresh and cache_key in forecast_cache:
        cached = forecast_cache[cache_key]
        # Invalidate stale cache (e.g. wrong symbol or mock data from an old run)
        try:
            spot_check = float(cached.get("spot_price") or 0)
            first_pred = float(cached["forecast"][0]["predicted_price"])
            if spot_check > 0 and abs(first_pred - spot_check) / spot_check > 0.10:
                forecast_cache.pop(cache_key, None)
            else:
                return cached
        except (KeyError, IndexError, TypeError, ValueError):
            forecast_cache.pop(cache_key, None)

    try:
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        start = (datetime.datetime.now() - datetime.timedelta(days=365 * 3)).strftime('%Y-%m-%d')
        data = get_portfolio_data([sym], start, today)
        prices = _price_series_for_ticker(data["prices"], sym)
        if len(prices) < 30:
            raise HTTPException(status_code=400, detail=f"Insufficient price history for {sym}")

        spot_price = float(prices.iloc[-1])
        forecast = _forecast_from_saved_lstm(prices, sym, horizon)
        if forecast is None:
            forecast = get_lstm_forecast(prices, horizon, train_epochs=8)

        # Anchor trajectory to live close when the fresh LSTM level drifts (stale/wrong scale)
        if forecast:
            first_pred = float(forecast[0]["predicted_price"])
            if spot_price > 0 and abs(first_pred - spot_price) / spot_price > 0.10:
                scale = spot_price / first_pred
                for row in forecast:
                    row["predicted_price"] = float(row["predicted_price"]) * scale

        currency = data.get("currencies", {}).get(sym, "USD")
        if sym.endswith(".NS") or sym.endswith(".BO"):
            currency = "INR"
        res = {
            "ticker": sym,
            "forecast": forecast,
            "currency": currency,
            "spot_price": spot_price,
        }
        forecast_cache[cache_key] = res
        return res
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Forecasting error: {str(e)}")

regime_cache = None

@app.get("/market-regime")
def market_regime():
    global regime_cache
    if regime_cache is not None:
        return regime_cache
        
    try:
        # Using SPY as a market proxy
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        data = get_portfolio_data(["SPY"], "2020-01-01", today)
        # Returns for single ticker might be Series or DataFrame
        returns = data["returns"]
        if isinstance(returns, pd.DataFrame) and "SPY" in returns.columns:
            returns = returns["SPY"]
        elif isinstance(returns, pd.DataFrame):
            returns = returns.iloc[:, 0]
            
        regime = detect_market_regime_hmm(returns)
        regime_cache = regime
        return regime
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regime detection error: {str(e)}")

sentiment_cache = {}

@app.get("/sentiment/{ticker}")
def sentiment_analysis(ticker: str):
    ticker = ticker.upper()
    if ticker in sentiment_cache:
        return sentiment_cache[ticker]
        
    try:
        result = get_sentiment_analysis(ticker)
        sentiment_cache[ticker] = result
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Sentiment error: {str(e)}")


@app.get("/marketmind/{ticker}")
def marketmind_prediction(ticker: str):
    ticker = ticker.upper().strip()
    model = MarketMindMetaModel(model_dir=os.path.join(os.path.dirname(__file__), 'models', 'meta_model'))
    try:
        if not model.is_ready():
            raise FileNotFoundError('MarketMind meta-model has not been trained yet.')
        if model.model is None:
            model.load()
        if model.model is None:
            raise FileNotFoundError('MarketMind meta-model has not been trained yet.')
        prediction = model.predict_for_ticker(ticker)
        return {
            "ticker": ticker,
            "marketmind_model": prediction,
            "status": "ready",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MarketMind prediction error: {str(e)}")


@app.get("/fundamentals/{ticker}")
def fundamentals_analysis(ticker: str):
    ticker = ticker.upper().strip()
    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}
        income_stmt = stock.income_stmt
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cash_flow

        def latest_value(frame, label):
            if frame is None or frame.empty or label not in frame.index:
                return None
            series = frame.loc[label].dropna()
            if series.empty:
                return None
            return float(series.iloc[0])

        def safe_number(value):
            try:
                if value is None:
                    return None
                if isinstance(value, str) and not value.strip():
                    return None
                return float(value)
            except Exception:
                return None

        return {
            "ticker": ticker,
            "company": {
                "name": info.get("shortName") or info.get("longName") or ticker,
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "country": info.get("country"),
                "market_price": safe_number(info.get("currentPrice") or info.get("regularMarketPrice")),
                "currency": info.get("currency", "USD"),
                "market_cap": safe_number(info.get("marketCap")),
                "website": info.get("website"),
                "website_summary": info.get("longBusinessSummary"),
            },
            "valuation": {
                "trailing_pe": safe_number(info.get("trailingPE")),
                "forward_pe": safe_number(info.get("forwardPE")),
                "price_to_book": safe_number(info.get("priceToBook")),
                "price_to_sales": safe_number(info.get("priceToSalesTrailing12Months")),
                "peg_ratio": safe_number(info.get("pegRatio")),
                "dividend_yield": safe_number(info.get("dividendYield")),
            },
            "profitability": {
                "gross_margin": safe_number(info.get("grossMargins")),
                "operating_margin": safe_number(info.get("operatingMargins")),
                "profit_margin": safe_number(info.get("profitMargins")),
                "return_on_assets": safe_number(info.get("returnOnAssets")),
                "return_on_equity": safe_number(info.get("returnOnEquity")),
            },
            "growth": {
                "revenue_growth": safe_number(info.get("revenueGrowth")),
                "earnings_growth": safe_number(info.get("earningsGrowth")),
                "earnings_quarterly_growth": safe_number(info.get("earningsQuarterlyGrowth")),
            },
            "balance_sheet": {
                "total_cash": latest_value(balance_sheet, "Cash And Cash Equivalents"),
                "total_debt": latest_value(balance_sheet, "Total Debt"),
                "total_assets": latest_value(balance_sheet, "Total Assets"),
                "total_liabilities": latest_value(balance_sheet, "Total Liab"),
                "current_assets": latest_value(balance_sheet, "Current Assets"),
                "current_liabilities": latest_value(balance_sheet, "Current Liabilities"),
            },
            "income_statement": {
                "total_revenue": latest_value(income_stmt, "Total Revenue"),
                "gross_profit": latest_value(income_stmt, "Gross Profit"),
                "operating_income": latest_value(income_stmt, "Operating Income"),
                "net_income": latest_value(income_stmt, "Net Income"),
            },
            "cash_flow": {
                "operating_cash_flow": latest_value(cash_flow, "Operating Cash Flow"),
                "free_cash_flow": latest_value(cash_flow, "Free Cash Flow"),
                "capital_expenditure": latest_value(cash_flow, "Capital Expenditure"),
            },
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Fundamentals error: {str(e)}")

import threading
from trading_engine.data_manager import get_processed_data
from trading_engine.decision_engine import DecisionEngine

engine_cache = {}
engine_status = {}
engine_errors = {}

def background_initialize(ticker: str):
    try:
        data = get_processed_data(ticker=ticker, period="60d", interval="5m")
        models_dir = os.path.join(os.path.dirname(__file__), "models")
        # In production / API mode we prefer load-only; do NOT train missing models at startup
        de = DecisionEngine(data, ticker=ticker, models_dir=models_dir, train_on_missing=False)
        # attempt to load persisted models (will raise if artifacts missing)
        de.initialize(rl_timesteps=200)
        dec = de.get_decision()
        
        last_rows = data.tail(40).copy()
        chart_data = []
        for idx, row in last_rows.iterrows():
            chart_data.append({
                "Date": idx.strftime("%H:%M") if hasattr(idx, "strftime") else str(idx),
                "Close": float(row["Close"]),
                "rsi": float(0 if pd.isna(row.get("rsi")) else row.get("rsi", 50)),
                "macd_diff": float(0 if pd.isna(row.get("macd_diff")) else row.get("macd_diff", 0))
            })
            
        engine_cache[ticker] = {
            "decision": dec,
            "chart_data": chart_data,
            "wallet": {
                "status": "connected",
                "scope": "quantitative_advisory"
            },
            "is_dry_run": True,
            "ticker": ticker,
            "analysis_mode": dec.get("analysis_mode", "per_ticker"),
            "model_sources": dec.get("model_sources", {}),
            "has_rl": dec.get("has_rl", False),
            "uses_live_data": True,
        }
        engine_status[ticker] = "ready"
        engine_errors.pop(ticker, None)
    except Exception as e:
        import traceback
        traceback.print_exc()
        engine_status[ticker] = "error"
        engine_errors[ticker] = str(e)

@app.get("/trading/decision")
def get_trading_decision(ticker: str = "AAPL"):
    ticker = ticker.upper()
    status = engine_status.get(ticker, "uninitialized")
    
    if status == "uninitialized":
        engine_status[ticker] = "thinking"
        t = threading.Thread(target=background_initialize, args=(ticker,))
        t.start()
        return {"status": "thinking", "ticker": ticker}
        
    if status == "thinking":
        return {"status": "thinking", "ticker": ticker}
        
    if status == "error":
        engine_status[ticker] = "uninitialized"
        detail = engine_errors.get(ticker, f"Neural Link Engine failed to converge on {ticker}.")
        raise HTTPException(status_code=500, detail=detail)
        
    return engine_cache[ticker]


@app.get('/models/status')
def models_status():
    """List persisted models and metadata under analytics-engine/models/"""
    base = os.path.join(os.path.dirname(__file__), 'models')
    if not os.path.exists(base):
        return {"models": [], "server": {"train_on_missing": False}}

    models = []
    for d in sorted(os.listdir(base)):
        path = os.path.join(base, d)
        if not os.path.isdir(path):
            continue
        meta_path = os.path.join(path, 'metadata.json')
        meta = {}
        if os.path.exists(meta_path):
            try:
                with open(meta_path, 'r') as f:
                    meta = json.load(f)
            except Exception:
                meta = {}

        has_lstm = os.path.exists(os.path.join(path, 'lstm.pt')) or os.path.exists(os.path.join(path, 'lstm_state.pt'))
        has_rf = os.path.exists(os.path.join(path, 'rf.pkl')) or os.path.exists(os.path.join(path, 'rf_model.joblib'))
        has_hmm = os.path.exists(os.path.join(path, 'hmm.pkl')) or os.path.exists(os.path.join(path, 'hmm_model.joblib'))
        has_ppo = os.path.exists(os.path.join(path, 'ppo_policy.zip')) or os.path.exists(os.path.join(path, 'ppo_policy'))
        models.append({
            "ticker": d,
            "loaded": bool(has_lstm and has_rf and has_hmm),
            "artifacts": {
                "lstm": has_lstm,
                "rf": has_rf,
                "hmm": has_hmm,
                "ppo": has_ppo,
            },
            "metadata": meta,
            "files": sorted([os.path.basename(p) for p in glob.glob(os.path.join(path, '*'))])
        })

    return {"models": models, "server": {"train_on_missing": False}}


@app.get('/models/universe')
def models_universe():
    """Curated 50 US + 50 India tickers with trained flags for UI (ML vs live-only)."""
    base = os.path.join(os.path.dirname(__file__), 'models')
    universe = load_universe()
    assets = assets_flat()
    ready_symbols = []

    for asset in assets:
        sym = asset["symbol"]
        model_dir = os.path.join(base, sym)
        if os.path.isdir(model_dir):
            status = _model_dir_ready(model_dir)
            asset["trained"] = status["ready"]
            asset["artifacts"] = {k: status[k] for k in ("lstm", "rf", "hmm", "ppo", "scalers")}
            if status["ready"]:
                ready_symbols.append(sym)
        else:
            asset["trained"] = False
            asset["artifacts"] = {"lstm": False, "rf": False, "hmm": False, "ppo": False, "scalers": False}

    us_ready = [a for a in assets if a["region"] == "US" and a["trained"]]
    india_ready = [a for a in assets if a["region"] == "India" and a["trained"]]
    uni_ready, _ = universal_is_ready(base)
    port_rl_ready = portfolio_rl_is_ready(base)

    return {
        "total_universe": len(assets),
        "ready_count": len(ready_symbols),
        "ready_symbols": ready_symbols,
        "us": [a for a in assets if a["region"] == "US"],
        "india": [a for a in assets if a["region"] == "India"],
        "all_assets": assets,
        "assets": [a for a in assets if a["trained"]],
        "universal_ready": uni_ready,
        "portfolio_rl_ready": port_rl_ready,
        "summary": {
            "us_total": len(universe["us"]),
            "india_total": len(universe["india"]),
            "us_ready": len(us_ready),
            "india_ready": len(india_ready),
        },
    }


class PredictRequest(BaseModel):
    ticker: str
    model: str = 'lstm'  # one of: lstm, rf, hmm
    horizon: int = 30


@app.post('/models/predict')
def models_predict(req: PredictRequest):
    t = req.ticker.upper()
    model_choice = req.model.lower()
    try:
        data = get_processed_data(ticker=t, period='60d', interval='5m')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data for {t}: {e}")

    tm = TradingModels(data)
    base = os.path.join(os.path.dirname(__file__), 'models')
    hybrid = apply_hybrid_to_trading_models(tm, t, base)
    sources = hybrid['components']
    mode = hybrid['analysis_mode']
    uni = hybrid['universal']

    if model_choice == 'lstm':
        if sources.get('lstm') == 'universal':
            preds = uni.predict_lstm_prices(data, horizon=req.horizon)
        elif sources.get('lstm') == 'per_ticker':
            preds = tm.predict_lstm(horizon=req.horizon)
        else:
            raise HTTPException(status_code=404, detail="No LSTM model (per-ticker or universal)")
        return {
            "ticker": t, "model": "lstm", "horizon": req.horizon,
            "forecast": preds.tolist(), "source": sources.get('lstm', mode),
        }

    if model_choice == 'rf':
        if sources.get('rf') == 'universal':
            sig, prob = uni.predict_rf(data)
        elif sources.get('rf') == 'per_ticker':
            sig, prob = tm.predict_rf()
        else:
            raise HTTPException(status_code=404, detail="No RF model (per-ticker or universal)")
        return {
            "ticker": t, "model": "rf", "signal": int(sig),
            "confidence": float(prob), "source": sources.get('rf', mode),
        }

    if model_choice == 'hmm':
        if sources.get('hmm') == 'universal':
            regime = uni.detect_regime(data)
        elif sources.get('hmm') == 'per_ticker':
            regime = tm.detect_regime()
        else:
            raise HTTPException(status_code=404, detail="No HMM model (per-ticker or universal)")
        return {
            "ticker": t, "model": "hmm", "regime": regime,
            "source": sources.get('hmm', mode),
        }

    raise HTTPException(status_code=400, detail="Unknown model choice; must be one of: lstm, rf, hmm")


@app.get('/models/metadata')
def models_metadata(ticker: str | None = None):
    """Return stored metadata.json for one ticker or all tickers."""
    base = os.path.join(os.path.dirname(__file__), 'models')
    if not os.path.exists(base):
        return {"models": []}

    def load_meta(model_dir):
        meta_path = os.path.join(model_dir, 'metadata.json')
        if not os.path.exists(meta_path):
            return None
        try:
            with open(meta_path, 'r') as f:
                return json.load(f)
        except Exception:
            return None

    if ticker:
        t = ticker.upper()
        model_dir = os.path.join(base, t)
        if not os.path.exists(model_dir):
            raise HTTPException(status_code=404, detail=f"No model directory found for {t}")
        meta = load_meta(model_dir)
        if meta is None:
            raise HTTPException(status_code=404, detail=f"No metadata.json found for {t}")
        return {"ticker": t, "metadata": meta}

    models = []
    for d in sorted(os.listdir(base)):
        model_dir = os.path.join(base, d)
        if not os.path.isdir(model_dir):
            continue
        meta = load_meta(model_dir)
        if meta is not None:
            models.append({"ticker": d, "metadata": meta})

    return {"models": models}


# ── Background model training ─────────────────────────────────────────────

from training import job_manager


class TrainingStartRequest(BaseModel):
    job_type: str  # ticker | universe | universal | portfolio
    ticker: str | None = None
    tickers: list[str] | None = None
    preset: str = 'quick'  # quick | standard


@app.get('/portfolio/rl/allocation')
def portfolio_rl_allocation(tickers: str, weights: str = ''):
    """
    Query: tickers=AAPL,MSFT&weights=0.5,0.5
    Returns PPO recommended weights for the user's watchlist.
    """
    sym_list = [t.strip().upper() for t in tickers.split(',') if t.strip()]
    w_list = []
    if weights.strip():
        try:
            w_list = [float(x) for x in weights.split(',')]
        except ValueError:
            raise HTTPException(status_code=400, detail='Invalid weights')
    if w_list and len(w_list) != len(sym_list):
        raise HTTPException(status_code=400, detail='tickers and weights length must match')
    if not w_list and sym_list:
        w_list = [1.0 / len(sym_list)] * len(sym_list)
    base = os.path.join(os.path.dirname(__file__), 'models')
    return recommend_allocations(sym_list, w_list, base_dir=base)


@app.get('/training/status')
def training_status():
    """Poll background training job progress."""
    return job_manager.get_status()


@app.post('/training/start')
def training_start(req: TrainingStartRequest):
    """
    Start a background training job (one at a time).
    job_type:
      - ticker: retrain one symbol (req.ticker)
      - universe: retrain all 100 + universal hybrid
      - universal: retrain shared hybrid models only
      - portfolio: retrain symbols in req.tickers (watchlist)
      - portfolio_rl: train full-universe allocation PPO (weights + cash)
    """
    job_type = req.job_type.strip().lower()
    if job_type not in ('ticker', 'universe', 'universal', 'portfolio', 'portfolio_rl'):
        raise HTTPException(
            status_code=400,
            detail='job_type must be ticker, universe, universal, portfolio, or portfolio_rl',
        )

    ok, msg = job_manager.start_job(
        job_type=job_type,
        preset=req.preset,
        ticker=req.ticker,
        tickers=req.tickers,
    )
    if not ok:
        raise HTTPException(status_code=409, detail=msg)
    return {'status': 'started', 'message': msg, 'job': job_manager.get_status()}


# ─────────────────────────────────────────────────────────────────────────
#  AI Advisor endpoints
# ─────────────────────────────────────────────────────────────────────────

@app.get('/advisor/status')
def advisor_status():
    """Check whether the LLM + RAG advisor layer is configured."""
    return get_ai_advisor().get_status()


@app.post('/chat')
def chat(req: ChatRequest):
    """
    LLM-powered conversational response augmented with RAG retrieval.

    The endpoint gathers structured outputs from every ML microservice
    (risk metrics, HMM regime, LSTM forecast, VADER sentiment, stress
    tests, MarketMind meta-model, PPO RL allocations, decision options),
    retrieves the most relevant news headlines + financial knowledge-base
    documents via TF-IDF, then calls the configured LLM to produce a
    natural-language explanation.

    Returns immediately with the full response.  For incremental
    token-by-token delivery use ``POST /chat/stream`` instead.
    """
    advisor = get_ai_advisor()

    try:
        return advisor.chat(
            query=req.query,
            tickers=req.tickers,
            weights=req.weights,
            portfolio_value=req.portfolio_value,
            start=req.start,
            end=req.end,
            horizon=req.horizon,
            top_k=req.top_k,
        )
    except Exception as exc:
        logger = logging.getLogger(__name__)
        logger.exception("AI Advisor chat failed")
        raise HTTPException(
            status_code=500,
            detail=f"Advisor error: {str(exc)}",
        )


@app.post('/chat/stream')
def chat_stream(req: ChatRequest):
    """
    Server-Sent Events (SSE) stream of the LLM token stream.

    Each line is ``data: {json}`` with either ``{"content": "..."}``
    chunks or ``{"done": true}`` at the end.
    """
    from fastapi.responses import StreamingResponse

    advisor = get_ai_advisor()

    def event_stream():
        try:
            yield from advisor.stream_chat(
                query=req.query,
                tickers=req.tickers,
                weights=req.weights,
                portfolio_value=req.portfolio_value,
                start=req.start,
                end=req.end,
                horizon=req.horizon,
                top_k=req.top_k,
            )
        except Exception as exc:
            logger = logging.getLogger(__name__)
            logger.exception("AI Advisor stream chat failed")
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
            yield f"data: {json.dumps({'done': True, 'error': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/chat/tools")
def chat_with_tools(req: ChatRequest):
    """
    Agentic chat: LLM receives tools, calls them, and responds with
    structured financial analysis backed by quantitative engines.

    The LLM never calculates metrics itself — it calls tools which return
    structured results from the backend engines.
    """
    advisor = get_ai_advisor()
    try:
        return advisor.chat_with_tools(
            query=req.query,
            tickers=req.tickers,
            weights=req.weights,
            portfolio_value=req.portfolio_value,
        )
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Advisor tool-calling error: {str(exc)}",
        )
# ─────────────────────────────────────────────────────────────────────────

class PortfolioAnalyzeRequest(BaseModel):
    tickers: list[str]
    weights: list[float]
    portfolio_value: float = 100000
    start: str = "2020-01-01"
    end: str | None = None
    horizon: int = 30
    benchmark: str = "SPY"
    risk_free_rate: float = 0.02


@app.post("/portfolio/analyze")
def portfolio_analyze(req: PortfolioAnalyzeRequest):
    """
    Unified portfolio analysis pipeline — chains all ML engines.

    Returns: risk metrics, market regime, stress test, benchmark comparison,
    attribution, risk budgeting, ML forecasts/sentiment/MarketMind,
    portfolio score, RL allocation, and evidence-backed recommendations.
    """
    if len(req.tickers) != len(req.weights):
        raise HTTPException(status_code=400, detail="tickers and weights length must match")
    if abs(sum(req.weights) - 1.0) > 0.01:
        raise HTTPException(status_code=400, detail=f"Weights must sum to 1.0 (current: {sum(req.weights)})")

    try:
        from services.portfolio_pipeline import run_portfolio_pipeline
        result = run_portfolio_pipeline(
            tickers=req.tickers,
            weights=req.weights,
            portfolio_value=req.portfolio_value,
            start=req.start,
            end=req.end,
            horizon=req.horizon,
            benchmark=req.benchmark,
            risk_free_rate=req.risk_free_rate,
        )
        return _clean_json(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────
#  Phase 2: Benchmark Engine
# ─────────────────────────────────────────────────────────────────────────

class BenchmarkCompareRequest(BaseModel):
    tickers: list[str]
    weights: list[float]
    portfolio_value: float = 100000
    start: str = "2020-01-01"
    end: str | None = None
    benchmark_ticker: str = "SPY"
    risk_free_rate: float = 0.02


@app.get("/benchmarks")
def list_benchmarks():
    """Return all supported benchmark options."""
    from services.benchmark import list_available_benchmarks
    return {"benchmarks": list_available_benchmarks()}


@app.post("/portfolio/benchmark")
def portfolio_benchmark(req: BenchmarkCompareRequest):
    """Compare portfolio performance against a benchmark."""
    if len(req.tickers) != len(req.weights):
        raise HTTPException(status_code=400, detail="tickers and weights length must match")
    try:
        from services.data_fetcher import get_portfolio_data
        from services.benchmark import compute_benchmark_comparison
        from services.portfolio_score import get_currency_symbol
        end = req.end or datetime.datetime.now().strftime('%Y-%m-%d')
        data = get_portfolio_data(req.tickers + [req.benchmark_ticker], req.start, end)
        weights = list(req.weights) + [0.0]  # benchmark is extra column
        result = compute_benchmark_comparison(
            data["prices"], req.weights, req.portfolio_value,
            benchmark_ticker=req.benchmark_ticker, risk_free_rate=req.risk_free_rate
        )
        return _clean_json(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Benchmark error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────
#  Phase 3: Attribution Engine
# ─────────────────────────────────────────────────────────────────────────

class AttributionRequest(BaseModel):
    tickers: list[str]
    weights: list[float]
    portfolio_value: float = 100000
    start: str = "2020-01-01"
    end: str | None = None


@app.post("/portfolio/attribution")
def portfolio_attribution(req: AttributionRequest):
    """Compute portfolio return attribution (security, sector, asset-class)."""
    if len(req.tickers) != len(req.weights):
        raise HTTPException(status_code=400, detail="tickers and weights length must match")
    try:
        from services.data_fetcher import get_portfolio_data
        from services.attribution import compute_attribution
        from services.portfolio_score import get_currency_symbol
        end = req.end or datetime.datetime.now().strftime('%Y-%m-%d')
        data = get_portfolio_data(req.tickers, req.start, end)
        currency = get_currency_symbol(data["currencies"])
        result = compute_attribution(req.tickers, req.weights, data["prices"], req.portfolio_value, currency)
        return _clean_json(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Attribution error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────
#  Phase 4: Risk Budgeting
# ─────────────────────────────────────────────────────────────────────────

class RiskBudgetRequest(BaseModel):
    tickers: list[str]
    weights: list[float]
    portfolio_value: float = 100000
    start: str = "2020-01-01"
    end: str | None = None
    confidence_level: float = 0.95


@app.post("/portfolio/risk-budget")
def portfolio_risk_budget(req: RiskBudgetRequest):
    """Compute risk contribution analysis (MCR, CCR, PCR)."""
    if len(req.tickers) != len(req.weights):
        raise HTTPException(status_code=400, detail="tickers and weights length must match")
    try:
        from services.data_fetcher import get_portfolio_data
        from services.risk_budget import compute_risk_budget, compute_correlation_matrix
        from services.portfolio_score import get_currency_symbol
        end = req.end or datetime.datetime.now().strftime('%Y-%m-%d')
        data = get_portfolio_data(req.tickers, req.start, end)
        currency = get_currency_symbol(data["currencies"])
        risk_budget = compute_risk_budget(req.tickers, req.weights, data["returns"], req.portfolio_value, req.confidence_level)
        risk_budget["currency"] = currency
        correlation = compute_correlation_matrix(req.tickers, data["returns"])
        return _clean_json({"risk_budget": risk_budget, "correlation": correlation})
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Risk budget error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────
#  Phase 5: Goal Engine
# ─────────────────────────────────────────────────────────────────────────

class GoalRequest(BaseModel):
    tickers: list[str]
    weights: list[float]
    current_capital: float
    monthly_contribution: float
    target_amount: float
    time_horizon_years: float
    num_sims: int = 1000
    start: str = "2020-01-01"
    end: str | None = None
    risk_free_rate: float = 0.02


@app.post("/portfolio/goal")
def portfolio_goal_analysis(req: GoalRequest):
    """Run goal-based portfolio analysis with Monte Carlo simulation."""
    if len(req.tickers) != len(req.weights):
        raise HTTPException(status_code=400, detail="tickers and weights length must match")
    try:
        from services.data_fetcher import get_portfolio_data
        from services.goal_analyzer import compute_goal_analysis
        end = req.end or datetime.datetime.now().strftime('%Y-%m-%d')
        data = get_portfolio_data(req.tickers, req.start, end)
        result = compute_goal_analysis(
            tickers=req.tickers,
            weights=req.weights,
            current_capital=req.current_capital,
            monthly_contribution=req.monthly_contribution,
            target_amount=req.target_amount,
            time_horizon_years=req.time_horizon_years,
            returns=data["returns"],
            num_sims=req.num_sims,
            risk_free_rate=req.risk_free_rate,
        )
        return _clean_json(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Goal analysis error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────
#  Phase 6: Recommendations
# ─────────────────────────────────────────────────────────────────────────

class RecommendationsRequest(BaseModel):
    tickers: list[str]
    weights: list[float]
    portfolio_value: float = 100000
    start: str = "2020-01-01"
    end: str | None = None
    benchmark: str = "SPY"


@app.post("/recommendations")
def get_recommendations(req: RecommendationsRequest):
    """Generate evidence-backed portfolio recommendations from the full pipeline."""
    if len(req.tickers) != len(req.weights):
        raise HTTPException(status_code=400, detail="tickers and weights length must match")
    try:
        from services.portfolio_pipeline import run_portfolio_pipeline
        result = run_portfolio_pipeline(
            tickers=req.tickers,
            weights=req.weights,
            portfolio_value=req.portfolio_value,
            start=req.start,
            end=req.end,
            benchmark=req.benchmark,
        )
        return _clean_json({"recommendations": result["recommendations"]})
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Recommendations error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────
#  Phase 7: LLM Tool Integration
# ─────────────────────────────────────────────────────────────────────────

class ToolRequest(BaseModel):
    tickers: list[str] = []
    weights: list[float] = []
    portfolio_value: float = 100000
    start: str = "2020-01-01"
    end: str | None = None
    horizon: int = 30
    benchmark: str = "SPY"
    risk_free_rate: float = 0.02
    ticker: str = ""
    target_amount: float = 0
    current_capital: float = 0
    monthly_contribution: float = 0
    time_horizon_years: float = 0
    num_sims: int = 1000
    scenario: str = ""


_tool_registry = None

def _get_tool_registry():
    global _tool_registry
    if _tool_registry is None:
        from trading_engine.portfolio_rl_service import PPARecommendationTool
        _tool_registry = {
            "get_portfolio": _tool_get_portfolio,
            "analyze_portfolio": _tool_analyze_portfolio,
            "analyze_risk": _tool_analyze_risk,
            "compare_benchmark": _tool_compare_benchmark,
            "analyze_attribution": _tool_analyze_attribution,
            "analyze_risk_budget": _tool_analyze_risk_budget,
            "optimize_portfolio": _tool_optimize_portfolio,
            "run_stress_test": _tool_run_stress_test,
            "analyze_goal": _tool_analyze_goal,
            "forecast_asset": _tool_forecast_asset,
            "get_market_regime": _tool_get_market_regime,
        }
    return _tool_registry


def _tool_get_portfolio(req: ToolRequest) -> dict:
    from services.portfolio_pipeline import run_portfolio_pipeline
    result = run_portfolio_pipeline(
        tickers=req.tickers, weights=req.weights,
        portfolio_value=req.portfolio_value,
        start=req.start, end=req.end, horizon=req.horizon,
        benchmark=req.benchmark, risk_free_rate=req.risk_free_rate,
    )
    return {
        "portfolio_value": result["portfolio_value"],
        "currency": result["currency"],
        "tickers": result["tickers"],
        "weights": result["weights"],
        "portfolio_score": result.get("portfolio_score", {}),
        "asset_allocation": result.get("asset_allocation", []),
    }


def _tool_analyze_portfolio(req: ToolRequest) -> dict:
    from services.portfolio_pipeline import run_portfolio_pipeline
    result = run_portfolio_pipeline(
        tickers=req.tickers, weights=req.weights,
        portfolio_value=req.portfolio_value,
        start=req.start, end=req.end, horizon=req.horizon,
        benchmark=req.benchmark, risk_free_rate=req.risk_free_rate,
    )
    return {
        "returns": _clean_json(result.get("risk_engine", {})),
        "portfolio_score": result.get("portfolio_score", {}),
        "asset_allocation": result.get("asset_allocation", []),
    }


def _tool_analyze_risk(req: ToolRequest) -> dict:
    from services.portfolio_pipeline import run_portfolio_pipeline
    result = run_portfolio_pipeline(
        tickers=req.tickers, weights=req.weights,
        portfolio_value=req.portfolio_value,
        start=req.start, end=req.end, horizon=req.horizon,
        benchmark=req.benchmark, risk_free_rate=req.risk_free_rate,
    )
    return {
        "risk_summary": result.get("risk_engine", {}),
        "risk_budget": result.get("risk_budget", {}),
        "correlation": result.get("correlation", {}),
        "stress_test": result.get("stress_test", {}),
    }


def _tool_compare_benchmark(req: ToolRequest) -> dict:
    from services.portfolio_pipeline import run_portfolio_pipeline
    result = run_portfolio_pipeline(
        tickers=req.tickers, weights=req.weights,
        portfolio_value=req.portfolio_value,
        start=req.start, end=req.end, horizon=req.horizon,
        benchmark=req.benchmark, risk_free_rate=req.risk_free_rate,
    )
    return result.get("benchmark", {})


def _tool_analyze_attribution(req: ToolRequest) -> dict:
    from services.portfolio_pipeline import run_portfolio_pipeline
    result = run_portfolio_pipeline(
        tickers=req.tickers, weights=req.weights,
        portfolio_value=req.portfolio_value,
        start=req.start, end=req.end, horizon=req.horizon,
        benchmark=req.benchmark, risk_free_rate=req.risk_free_rate,
    )
    return result.get("attribution", {})


def _tool_analyze_risk_budget(req: ToolRequest) -> dict:
    from services.portfolio_pipeline import run_portfolio_pipeline
    result = run_portfolio_pipeline(
        tickers=req.tickers, weights=req.weights,
        portfolio_value=req.portfolio_value,
        start=req.start, end=req.end, horizon=req.horizon,
        benchmark=req.benchmark, risk_free_rate=req.risk_free_rate,
    )
    return result.get("risk_budget", {})


def _tool_optimize_portfolio(req: ToolRequest) -> dict:
    from services.portfolio_pipeline import run_portfolio_pipeline
    result = run_portfolio_pipeline(
        tickers=req.tickers, weights=req.weights,
        portfolio_value=req.portfolio_value,
        start=req.start, end=req.end, horizon=req.horizon,
        benchmark=req.benchmark, risk_free_rate=req.risk_free_rate,
    )
    return {
        "rl_allocation": result.get("ml_models", {}).get("rl_allocation", {}),
        "rl_ready": result.get("ml_models", {}).get("rl_ready", False),
        "status": "experimental" if result.get("ml_models", {}).get("rl_ready", False) else "not_ready",
    }


def _tool_run_stress_test(req: ToolRequest) -> dict:
    from services.portfolio_pipeline import run_portfolio_pipeline
    result = run_portfolio_pipeline(
        tickers=req.tickers, weights=req.weights,
        portfolio_value=req.portfolio_value,
        start=req.start, end=req.end, horizon=req.horizon,
        benchmark=req.benchmark, risk_free_rate=req.risk_free_rate,
    )
    return result.get("stress_test", {})


def _tool_analyze_goal(req: ToolRequest) -> dict:
    from services.data_fetcher import get_portfolio_data
    from services.goal_analyzer import compute_goal_analysis
    end = req.end or datetime.datetime.now().strftime('%Y-%m-%d')
    data = get_portfolio_data(req.tickers, req.start, end)
    return compute_goal_analysis(
        tickers=req.tickers, weights=req.weights,
        current_capital=req.current_capital,
        monthly_contribution=req.monthly_contribution,
        target_amount=req.target_amount,
        time_horizon_years=req.time_horizon_years,
        returns=data["returns"], num_sims=req.num_sims,
        risk_free_rate=req.risk_free_rate,
    )


def _tool_forecast_asset(req: ToolRequest) -> dict:
    from services.data_fetcher import get_portfolio_data
    from services.forecaster import get_lstm_forecast
    end = req.end or datetime.datetime.now().strftime('%Y-%m-%d')
    data = get_portfolio_data([req.ticker], "2020-01-01", end)
    prices = data["prices"]
    if isinstance(prices, pd.DataFrame):
        prices = prices.iloc[:, 0] if len(prices.columns) == 1 else prices[req.ticker.upper()]
    forecast = get_lstm_forecast(prices.dropna(), req.horizon, train_epochs=8)
    return {
        "ticker": req.ticker,
        "spot_price": float(prices.iloc[-1]),
        "forecast": forecast,
        "horizon": req.horizon,
    }


def _tool_get_market_regime(req: ToolRequest) -> dict:
    from services.data_fetcher import get_portfolio_data
    from services.regime_detector import detect_market_regime_hmm
    end = req.end or datetime.datetime.now().strftime('%Y-%m-%d')
    data = get_portfolio_data(["SPY"], "2020-01-01", end)
    prices = data["prices"]
    if isinstance(prices, pd.DataFrame):
        prices = prices.iloc[:, 0] if len(prices.columns) == 1 else prices["SPY"]
    returns = prices.pct_change().dropna()
    return detect_market_regime_hmm(returns)


@app.get("/tools")
def list_tools():
    """List all available LLM tools."""
    return {
        "tools": [
            {"name": name, "description": desc}
            for name, desc in [
                ("get_portfolio", "Get portfolio summary: value, score, allocation"),
                ("analyze_portfolio", "Full portfolio analytics: returns, score, allocation"),
                ("analyze_risk", "Risk metrics: VaR, CVaR, volatility, drawdown, risk budget"),
                ("compare_benchmark", "Compare portfolio vs benchmark: alpha, beta, IR, tracking error"),
                ("analyze_attribution", "Return attribution: security, sector, asset-class contribution"),
                ("analyze_risk_budget", "Risk contribution: MCR, CCR, PCR per asset"),
                ("optimize_portfolio", "Get PPO RL optimization suggestions (experimental)"),
                ("run_stress_test", "Run stress tests: 2008 crisis, COVID, rate shocks"),
                ("analyze_goal", "Goal-based analysis: Monte Carlo, success probability"),
                ("forecast_asset", "ML price forecast for a specific ticker"),
                ("get_market_regime", "Current market regime via HMM"),
            ]
        ]
    }


@app.post("/tools/call")
def call_tool(req: ToolRequest, tool: str = ""):
    """Call a specific financial tool with structured parameters."""
    tool = tool or req.ticker
    registry = _get_tool_registry()
    if tool not in registry:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool}. Available: {list(registry.keys())}")
    try:
        result = registry[tool](req)
        return _clean_json({"tool": tool, "result": result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Tool error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────
#  PPO Model Status (Phase 9)
# ─────────────────────────────────────────────────────────────────────────

@app.get("/ppo/status")
def ppo_status():
    """Return PPO model status — always marked EXPERIMENTAL."""
    models_base = os.path.join(os.path.dirname(__file__), "models")
    ready = portfolio_rl_is_ready(models_base)
    return {
        "model": "PPO Portfolio RL Agent",
        "status": "experimental",
        "ready": ready,
        "warning": (
            "PPO is EXPERIMENTAL and must not be used for production recommendations "
            "until: training is verified, reward function validated, backtest exists, "
            "out-of-sample evaluation done, transaction costs included, and performance "
            "compared against baselines. Use the Conservative/Balanced decision options "
            "from the analyze endpoint for production decisions."
        ),
        "requirements_met": {
            "training_verified": False,
            "reward_function_validated": False,
            "backtest_exists": False,
            "out_of_sample_evaluation": False,
            "transaction_costs_included": False,
            "baseline_comparison": False,
        },
    }


# ─────────────────────────────────────────────────────────────────────────
#  Utility: clean JSON serialization
# ─────────────────────────────────────────────────────────────────────────

def _clean_json(obj):
    """Recursively convert pandas/numpy objects to JSON-serializable values."""
    import numpy as np
    import pandas as pd
    if isinstance(obj, dict):
        return {str(k): _clean_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean_json(v) for v in obj]
    if isinstance(obj, (pd.Series, pd.DataFrame)):
        try:
            return _clean_json(obj.to_dict())
        except Exception:
            return str(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        v = float(obj)
        if np.isnan(v) or np.isinf(v):
            return None
        return v
    if isinstance(obj, np.bool_):
        return bool(obj)
    if not isinstance(obj, str):
        try:
            if pd.isna(obj):
                return None
        except (TypeError, ValueError):
            pass
    return obj

class OptimizationRequest(BaseModel):
    tickers: list[str]
    weights: list[float] = []
    start_date: str = "2020-01-01"
    end_date: str = "2024-01-01"
    optimization_method: str = "max_sharpe"  # max_sharpe, min_volatility, risk_parity
    risk_free_rate: float = 0.02


@app.post('/portfolio/optimize')
def optimize_portfolio(req: OptimizationRequest):
    """
    Optimize portfolio using modern portfolio theory.
    
    Methods:
    - max_sharpe: Maximize Sharpe ratio
    - min_volatility: Minimize portfolio volatility
    - risk_parity: Equal risk contribution
    """
    try:
        # Get historical data
        data = get_portfolio_data(req.tickers, req.start_date, req.end_date)
        returns = data["returns"]
        
        # Initialize optimizer
        optimizer = PortfolioOptimizer(returns, req.risk_free_rate)
        
        # Get optimization result
        if req.weights:
            current_weights_dict = dict(zip(req.tickers, req.weights))
            result = optimizer.compare_with_current(current_weights_dict, req.optimization_method)
        else:
            if req.optimization_method == 'max_sharpe':
                result = optimizer.optimize_max_sharpe()
            elif req.optimization_method == 'min_volatility':
                result = optimizer.optimize_min_volatility()
            elif req.optimization_method == 'risk_parity':
                result = optimizer.optimize_risk_parity()
            else:
                result = optimizer.optimize_max_sharpe()
        
        return result
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
            
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Optimization error: {str(e)}")


@app.get('/portfolio/efficient-frontier')
def get_efficient_frontier(tickers: str, start_date: str = "2020-01-01", end_date: str = "2024-01-01", n_points: int = 50):
    """
    Calculate efficient frontier for a set of tickers.
    
    Query: tickers=AAPL,MSFT,GOOGL&start_date=2020-01-01&end_date=2024-01-01&n_points=50
    """
    try:
        ticker_list = [t.strip().upper() for t in tickers.split(',') if t.strip()]
        data = yf.download(ticker_list, start=start_date, end=end_date)['Adj Close']
        returns = data.pct_change().dropna()
        
        optimizer = PortfolioOptimizer(returns)
        frontier = optimizer.efficient_frontier(n_points=n_points)
        
        return {
            'tickers': ticker_list,
            'efficient_frontier': frontier,
            'date_range': {'start': start_date, 'end': end_date}
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Efficient frontier error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────
#  Paper Trading endpoints
# ─────────────────────────────────────────────────────────────────────────

class PaperTradingAccountRequest(BaseModel):
    account_id: str = "default"
    initial_capital: float = 100000.0


class OrderRequest(BaseModel):
    account_id: str = "default"
    ticker: str
    side: str  # buy or sell
    quantity: float
    order_type: str = "market"  # market, limit, stop
    price: Optional[float] = None
    strategy: Optional[str] = None
    reason: Optional[str] = None


@app.post('/paper-trading/create-account')
def create_paper_account(req: PaperTradingAccountRequest):
    """Create a new paper trading account."""
    try:
        engine = create_paper_trading_account(
            account_id=req.account_id,
            initial_capital=req.initial_capital
        )
        return {
            'status': 'created',
            'account_id': req.account_id,
            'initial_capital': req.initial_capital
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Account creation error: {str(e)}")


@app.post('/paper-trading/place-order')
def place_paper_order(req: OrderRequest):
    """Place an order in a paper trading account."""
    try:
        engine = PaperTradingEngine(account_id=req.account_id)
        result = engine.place_order(
            ticker=req.ticker,
            side=req.side,
            quantity=req.quantity,
            order_type=req.order_type,
            price=req.price,
            strategy=req.strategy,
            reason=req.reason
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order placement error: {str(e)}")


@app.get('/paper-trading/account-summary')
def get_paper_account_summary(account_id: str = "default"):
    """Get summary of a paper trading account."""
    try:
        engine = PaperTradingEngine(account_id=account_id)
        summary = engine.get_account_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Account summary error: {str(e)}")


@app.post('/paper-trading/reset-account')
def reset_paper_account(account_id: str = "default", new_capital: Optional[float] = None):
    """Reset a paper trading account."""
    try:
        engine = PaperTradingEngine(account_id=account_id)
        engine.reset_account(new_initial_capital=new_capital)
        return {'status': 'reset', 'account_id': account_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Account reset error: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────
#  Monitoring and Alerts endpoints
# ─────────────────────────────────────────────────────────────────────────

class MonitoringConfigRequest(BaseModel):
    portfolio_id: str
    performance_thresholds: Optional[Dict[str, float]] = None
    risk_thresholds: Optional[Dict[str, float]] = None
    position_thresholds: Optional[Dict[str, float]] = None


class MonitoringCycleRequest(BaseModel):
    portfolio_id: str
    portfolio_data: Dict
    current_returns: List[float]
    risk_metrics: Dict


@app.post('/monitoring/create-engine')
def create_monitoring_endpoint(req: MonitoringConfigRequest):
    """Create a monitoring engine for a portfolio."""
    try:
        config = MonitoringConfig(
            portfolio_id=req.portfolio_id,
            performance_thresholds=req.performance_thresholds,
            risk_thresholds=req.risk_thresholds,
            position_thresholds=req.position_thresholds
        )
        engine = MonitoringEngine(config)
        return {
            'status': 'created',
            'portfolio_id': req.portfolio_id,
            'config': {
                'performance_thresholds': config.performance_thresholds,
                'risk_thresholds': config.risk_thresholds,
                'position_thresholds': config.position_thresholds
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Monitoring engine creation error: {str(e)}")


@app.post('/monitoring/run-cycle')
def run_monitoring_cycle(req: MonitoringCycleRequest):
    """Run a monitoring cycle and check for alerts."""
    try:
        config = MonitoringConfig(portfolio_id=req.portfolio_id)
        engine = MonitoringEngine(config)
        
        # Convert returns to pandas Series
        returns_series = pd.Series(req.current_returns)
        
        results = engine.run_monitoring_cycle(
            portfolio_data=req.portfolio_data,
            current_returns=returns_series,
            risk_metrics=req.risk_metrics
        )
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Monitoring cycle error: {str(e)}")


@app.get('/monitoring/active-alerts')
def get_active_alerts(portfolio_id: str = "default"):
    """Get all active (unacknowledged) alerts for a portfolio."""
    try:
        config = MonitoringConfig(portfolio_id=portfolio_id)
        engine = MonitoringEngine(config)
        alerts = engine.get_active_alerts()
        return {
            'portfolio_id': portfolio_id,
            'active_alerts': alerts,
            'count': len(alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Active alerts error: {str(e)}")


@app.post('/monitoring/acknowledge-alert')
def acknowledge_alert(portfolio_id: str = "default", alert_id: str = ""):
    """Acknowledge an alert."""
    try:
        config = MonitoringConfig(portfolio_id=portfolio_id)
        engine = MonitoringEngine(config)
        success = engine.acknowledge_alert(alert_id)
        return {
            'success': success,
            'alert_id': alert_id,
            'portfolio_id': portfolio_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert acknowledgment error: {str(e)}")


@app.get('/monitoring/summary')
def get_monitoring_summary(portfolio_id: str = "default"):
    """Get monitoring summary for a portfolio."""
    try:
        config = MonitoringConfig(portfolio_id=portfolio_id)
        engine = MonitoringEngine(config)
        summary = engine.get_monitoring_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Monitoring summary error: {str(e)}")


@app.post('/monitoring/create-rule')
def create_alert_rule(
    portfolio_id: str = "default",
    name: str = "",
    alert_type: str = "performance",
    condition: str = "",
    threshold: float = 0.0,
    severity: str = "warning",
    cooldown_minutes: int = 60
):
    """Create a new alert rule."""
    try:
        config = MonitoringConfig(portfolio_id=portfolio_id)
        engine = MonitoringEngine(config)
        rule = engine.create_alert_rule(
            name=name,
            alert_type=alert_type,
            condition=condition,
            threshold=threshold,
            severity=severity,
            cooldown_minutes=cooldown_minutes
        )
        return rule
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert rule creation error: {str(e)}")
