from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import datetime
import pandas as pd
import yfinance as yf
from services.data_fetcher import get_portfolio_data
from services.risk_metrics import get_risk_summary
from services.regime_detector import detect_market_regime_hmm
from services.stress_tester import get_stress_summary
from services.forecaster import get_lstm_forecast
from agents.decision_engine import generate_decision_options
from services.sentiment_analyzer import get_sentiment_analysis
from trading_engine.models_layer import TradingModels
import glob
import json

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
        res = {
            "risk_summary": risk["summary"].round(4).to_dict(),
            "regime_summary": regime,
            "stress_test": stress["stress_table"].to_dict(),
            "decision_options": options,
            "currency_map": data["currencies"]
        }
        analyze_cache[cache_key] = res
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

forecast_cache = {}

@app.get("/forecast/{ticker}")
def forecast_ticker(ticker: str, horizon: int = 30):
    cache_key = f"{ticker.upper()}_{horizon}"
    if cache_key in forecast_cache:
        return forecast_cache[cache_key]
        
    try:
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        data = get_portfolio_data([ticker], "2020-01-01", today)
        prices = data["prices"]
        # Handle potential multi-index or DataFrame structure
        if isinstance(prices, pd.DataFrame) and ticker in prices.columns:
            prices = prices[ticker]
        elif isinstance(prices, pd.DataFrame):
            # Fallback for single ticker as series
            prices = prices.iloc[:, 0]
            
        forecast = get_lstm_forecast(prices, horizon)
        currency = data.get("currencies", {}).get(ticker, "USD")
        res = {"ticker": ticker, "forecast": forecast, "currency": currency}
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
import os

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
            "ticker": ticker
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
    loaded = tm.load_models(base_dir=base, ticker=t)

    if model_choice == 'lstm':
        if not loaded.get('lstm'):
            raise HTTPException(status_code=404, detail="LSTM model not found for ticker")
        preds = tm.predict_lstm(horizon=req.horizon)
        return {"ticker": t, "model": "lstm", "horizon": req.horizon, "forecast": preds.tolist()}

    if model_choice == 'rf':
        if not loaded.get('rf'):
            raise HTTPException(status_code=404, detail="RF model not found for ticker")
        sig, prob = tm.predict_rf()
        return {"ticker": t, "model": "rf", "signal": int(sig), "confidence": float(prob)}

    if model_choice == 'hmm':
        if not loaded.get('hmm'):
            raise HTTPException(status_code=404, detail="HMM model not found for ticker")
        regime = tm.detect_regime()
        return {"ticker": t, "model": "hmm", "regime": regime}

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