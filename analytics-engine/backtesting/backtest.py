import numpy as np
import pandas as pd

def sharpe_ratio(returns, risk_free=0.0):
    mean = returns.mean() - risk_free
    std = returns.std()
    if std == 0:
        return 0.0
    return (np.sqrt(252) * mean) / std

def max_drawdown(equity_curve):
    roll_max = np.maximum.accumulate(equity_curve)
    drawdowns = (equity_curve - roll_max) / roll_max
    return float(drawdowns.min())

def win_rate(returns):
    wins = (returns > 0).sum()
    total = len(returns)
    return float(wins / total) if total > 0 else 0.0

def backtest_from_signals(prices: pd.Series, signals: pd.Series):
    """Simple backtest: signals are -1,0,1 for sell,hold,buy. Returns metrics and equity curve."""
    cash = 100000.0
    position = 0.0
    equity = []
    prev_price = None
    for price, sig in zip(prices, signals):
        if sig == 1 and cash > 0:
            position = cash / price
            cash = 0.0
        elif sig == -1 and position > 0:
            cash = position * price
            position = 0.0
        net = cash + position * price
        equity.append(net)
        prev_price = price

    eq = pd.Series(equity, index=prices.index)
    returns = eq.pct_change().fillna(0)
    metrics = {
        'sharpe': sharpe_ratio(returns),
        'max_drawdown': max_drawdown(eq.values),
        'win_rate': win_rate(returns),
        'total_return': float(eq.iloc[-1] / eq.iloc[0] - 1)
    }
    return metrics, eq
