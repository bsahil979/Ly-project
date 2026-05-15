import pandas as pd
import numpy as np

class TradingSimulator:
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.holdings = 0
        self.trades = []
        self.equity_curve = [initial_capital]

    def execute_trade(self, action, price, date, confidence=1.0):
        """
        Simulates a trade execution.
        Action: 'BUY', 'SELL', 'HOLD'
        """
        if action == "BUY" and self.capital > 0:
            units = (self.capital * 0.98) / price # 2% reserved for fees/slippage
            self.holdings += units
            self.capital = 0
            self.trades.append({"date": date, "type": "BUY", "price": price, "confidence": confidence})
            
        elif action == "SELL" and self.holdings > 0:
            self.capital += self.holdings * price * 0.98 # 2% fees/slippage
            self.holdings = 0
            self.trades.append({"date": date, "type": "SELL", "price": price, "confidence": confidence})
            
        current_value = self.capital + (self.holdings * price)
        self.equity_curve.append(current_value)
        return current_value

    def get_stats(self):
        """
        Calculates performance metrics.
        """
        if not self.equity_curve:
            return {}
            
        final_value = self.equity_curve[-1]
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        # Win rate (if we have closed trades)
        wins = 0
        losses = 0
        # This is a very simple win rate calculation based on trade sequence
        # In a real app, we'd pair BUY/SELL trades.
        
        return {
            "initial_capital": self.initial_capital,
            "final_value": round(final_value, 2),
            "total_return_pct": round(total_return * 100, 2),
            "trade_count": len(self.trades),
            "equity_curve": self.equity_curve
        }
