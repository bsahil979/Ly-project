from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import datetime
import pandas as pd
from services.data_fetcher import get_portfolio_data
from services.risk_metrics import get_risk_summary
from services.regime_detector import detect_market_regime_hmm
from services.stress_tester import get_stress_summary
from services.forecaster import get_lstm_forecast
from agents.decision_engine import generate_decision_options
from services.sentiment_analyzer import get_sentiment_analysis

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

@app.post("/analyze")
def analyze_portfolio(req: PortfolioRequest):
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
        return {
            "risk_summary": risk["summary"].round(4).to_dict(),
            "regime_summary": regime,
            "stress_test": stress["stress_table"].to_dict(),
            "decision_options": options,
            "currency_map": data["currencies"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/forecast/{ticker}")
def forecast_ticker(ticker: str, horizon: int = 30):
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
        return {"ticker": ticker, "forecast": forecast, "currency": currency}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Forecasting error: {str(e)}")

@app.get("/market-regime")
def market_regime():
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
        return regime
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regime detection error: {str(e)}")

@app.get("/sentiment/{ticker}")
def sentiment_analysis(ticker: str):
    try:
        result = get_sentiment_analysis(ticker.upper())
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Sentiment error: {str(e)}")