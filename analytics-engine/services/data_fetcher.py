import yfinance as yf
import pandas as pd

def fetch_price_data(tickers: list, start: str, end: str) -> pd.DataFrame:
    """
    Fetches historical closing prices for a list of tickers.
    """
    data = yf.download(tickers, start=start, end=end, auto_adjust=True)["Close"]
    data.dropna(inplace=True)
    return data


def compute_daily_returns(price_data: pd.DataFrame) -> pd.DataFrame:
    """
    Computes daily percentage returns from price data.
    """
    returns = price_data.pct_change().dropna()
    return returns


def get_currency_metadata(tickers: list) -> dict:
    """
    Fetches currency for a list of tickers from yfinance.
    """
    currencies = {}
    for ticker in tickers:
        try:
            # Suffix-based fallback to avoid slow .info calls where obvious
            if ticker.endswith('.NS') or ticker.endswith('.BO'):
                currencies[ticker] = "INR"
            else:
                t = yf.Ticker(ticker)
                currencies[ticker] = t.info.get('currency', 'USD')
        except:
            currencies[ticker] = "USD"
    return currencies


def get_portfolio_data(tickers: list, start: str, end: str):
    """
    Master function — fetches prices and computes returns in one call.
    Includes currency metadata.
    """
    prices = fetch_price_data(tickers, start, end)
    returns = compute_daily_returns(prices)
    currencies = get_currency_metadata(tickers)

    return {
        "prices": prices,
        "returns": returns,
        "currencies": currencies
    }