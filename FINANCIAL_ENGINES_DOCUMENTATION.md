# Financial Engines Documentation

## Overview

This document describes the financial engines that have been added to the LY codebase to create a comprehensive quantitative investment platform. All engines are grounded in real financial models and data, preventing fabricated conclusions.

## Table of Contents

1. [Portfolio Optimization Engine](#portfolio-optimization-engine)
2. [Paper Trading Engine](#paper-trading-engine)
3. [Monitoring and Alerts Engine](#monitoring-and-alerts-engine)
4. [Explainability Engine](#explainability-engine)
5. [Integration with Existing Systems](#integration-with-existing-systems)
6. [API Endpoints](#api-endpoints)

---

## Portfolio Optimization Engine

### Location
`analytics-engine/services/portfolio_optimizer.py`

### Purpose
Implements modern portfolio theory (MPT) and advanced optimization algorithms to suggest optimal asset allocations based on quantitative analysis.

### Features

#### 1. Mean-Variance Optimization (Markowitz)
- Maximizes Sharpe ratio for given risk level
- Supports custom weight bounds and constraints
- Returns optimal weights with performance metrics

#### 2. Risk Parity Optimization
- Equal risk contribution from each asset
- Balances portfolio based on volatility contributions
- Ideal for risk-balanced portfolios

#### 3. Efficient Frontier Analysis
- Calculates optimal portfolios across risk-return spectrum
- Visualizes trade-offs between risk and return
- Supports target return optimization

#### 4. Constraint Support
- Position limits (min/max weights)
- Sector concentration constraints
- Target return constraints
- Custom risk tolerance levels

### Key Classes

```python
class PortfolioOptimizer:
    def __init__(self, returns: pd.DataFrame, risk_free_rate: float = 0.02)
    def optimize_max_sharpe(self, weight_bounds: Tuple[float, float] = (0, 1)) -> Dict
    def optimize_min_volatility(self, weight_bounds: Tuple[float, float] = (0, 1)) -> Dict
    def optimize_risk_parity(self) -> Dict
    def optimize_target_return(self, target_return: float) -> Dict
    def efficient_frontier(self, n_points: int = 50) -> Dict
    def compare_with_current(self, current_weights: Dict, optimization_method: str) -> Dict
```

### Usage Example

```python
from services.portfolio_optimizer import PortfolioOptimizer
import yfinance as yf

# Fetch historical data
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']
data = yf.download(tickers, start='2020-01-01', end='2024-01-01')['Adj Close']
returns = data.pct_change().dropna()

# Initialize optimizer
optimizer = PortfolioOptimizer(returns, risk_free_rate=0.02)

# Optimize for maximum Sharpe ratio
result = optimizer.optimize_max_sharpe()
print(f"Optimal weights: {result['weights']}")
print(f"Expected return: {result['performance']['return']*100:.2f}%")
print(f"Expected volatility: {result['performance']['volatility']*100:.2f}%")
print(f"Sharpe ratio: {result['performance']['sharpe_ratio']:.4f}")
```

### Performance Metrics
- **Annual Return**: Expected yearly portfolio return
- **Volatility**: Annualized standard deviation of returns
- **Sharpe Ratio**: Risk-adjusted return (return - risk_free_rate) / volatility
- **Efficient Frontier**: Set of optimal portfolios for different risk levels

---

## Paper Trading Engine

### Location
`analytics-engine/services/paper_trading.py`

### Purpose
Simulates real trading without financial risk, allowing strategy testing and validation before live deployment.

### Features

#### 1. Virtual Portfolio Management
- Multiple account support with unique IDs
- Real-time position tracking
- Cash and holdings management
- Account state persistence

#### 2. Order Execution Simulation
- Market, limit, and stop order types
- Realistic commission and slippage modeling
- Order validation and error handling
- Trade execution with timestamps

#### 3. Performance Analytics
- Real-time P&L calculation
- Win rate tracking
- Trade history and audit trail
- Equity curve generation

#### 4. Multi-Strategy Support
- Strategy tagging for trades
- Reason tracking for decisions
- Performance comparison across strategies
- Trade journal export

### Key Classes

```python
class PaperTradingEngine:
    def __init__(self, account_id: str, initial_capital: float, commission_rate: float, slippage_rate: float)
    def place_order(self, ticker: str, side: str, quantity: float, order_type: str, price: Optional[float], strategy: Optional[str], reason: Optional[str]) -> Dict
    def update_positions(self, price_data: Dict[str, float]) -> Dict
    def get_account_summary(self) -> Dict
    def reset_account(self, new_initial_capital: Optional[float]) -> None
    def export_trades(self, format: str = 'csv') -> str
```

### Usage Example

```python
from services.paper_trading import create_paper_trading_account

# Create paper trading account
engine = create_paper_trading_account("demo_account", initial_capital=100000)

# Place orders
engine.place_order(
    ticker="AAPL",
    side="buy",
    quantity=10,
    strategy="momentum",
    reason="Positive momentum signal from ML model"
)

engine.place_order(
    ticker="MSFT",
    side="buy",
    quantity=5,
    strategy="trend_following",
    reason="Uptrend continuation pattern"
)

# Get account summary
summary = engine.get_account_summary()
print(f"Current capital: ${summary['account_summary']['current_capital']:,.2f}")
print(f"Total return: {summary['account_summary']['total_return_pct']:.2f}%")
print(f"Total trades: {summary['performance']['total_trades']}")
```

### Account Features
- **Initial Capital**: Starting portfolio value
- **Current Capital**: Real-time portfolio value including positions
- **Cash**: Available cash for new positions
- **Positions**: Current holdings with unrealized P&L
- **Trade History**: Complete audit trail of all trades

---

## Monitoring and Alerts Engine

### Location
`analytics-engine/services/monitoring_alerts.py`

### Purpose
Real-time portfolio monitoring with intelligent alerting based on risk thresholds and performance metrics.

### Features

#### 1. Performance Monitoring
- Daily return tracking
- Drawdown monitoring
- Volatility analysis
- Performance vs. thresholds

#### 2. Risk Monitoring
- Value at Risk (VaR) tracking
- Concentration risk alerts
- Sector exposure monitoring
- Correlation analysis

#### 3. Position Monitoring
- Position size limits
- Portfolio composition alerts
- Rebalancing recommendations
- Exposure tracking

#### 4. Custom Alert Rules
- User-defined threshold configuration
- Multiple severity levels (info, warning, critical)
- Cooldown periods to prevent alert fatigue
- Alert acknowledgment and resolution tracking

#### 5. Notification System
- Multiple notification channels
- Real-time alert delivery
- Alert history and management
- Integration with external systems

### Key Classes

```python
class MonitoringEngine:
    def __init__(self, config: MonitoringConfig)
    def create_alert_rule(self, name: str, alert_type: str, condition: str, threshold: float, severity: str, cooldown_minutes: int) -> Dict
    def check_performance_alerts(self, portfolio_data: Dict, current_returns: pd.Series) -> List[Alert]
    def check_risk_alerts(self, portfolio_data: Dict, risk_metrics: Dict) -> List[Alert]
    def check_position_alerts(self, portfolio_data: Dict) -> List[Alert]
    def run_monitoring_cycle(self, portfolio_data: Dict, current_returns: pd.Series, risk_metrics: Dict) -> Dict
    def acknowledge_alert(self, alert_id: str) -> bool
    def get_active_alerts(self) -> List[Dict]
```

### Default Thresholds

```python
performance_thresholds = {
    'max_drawdown': 0.15,        # 15% maximum drawdown
    'min_daily_return': -0.05,   # -5% daily return
    'volatility_limit': 0.30     # 30% annual volatility
}

risk_thresholds = {
    'var_95_limit': 0.05,         # 5% daily VaR
    'concentration_limit': 0.30,  # 30% single position
    'sector_concentration': 0.50  # 50% single sector
}

position_thresholds = {
    'min_position_size': 0.01,    # 1% minimum position
    'max_position_size': 0.40     # 40% maximum position
}
```

### Usage Example

```python
from services.monitoring_alerts import create_monitoring_engine, MonitoringConfig

# Create monitoring engine
config = MonitoringConfig(portfolio_id="my_portfolio")
engine = create_monitoring_engine("my_portfolio")

# Add custom alert rule
engine.create_alert_rule(
    name="High Drawdown Alert",
    alert_type="performance",
    condition="drawdown > 0.10",
    threshold=0.10,
    severity="critical",
    cooldown_minutes=60
)

# Run monitoring cycle
portfolio_data = {
    'positions': [
        {'ticker': 'AAPL', 'weight': 0.35},
        {'ticker': 'MSFT', 'weight': 0.30}
    ],
    'drawdown': -0.12
}

current_returns = pd.Series([-0.02, -0.03, -0.01, 0.01, -0.04])
risk_metrics = {'var_95': -0.06}

results = engine.run_monitoring_cycle(portfolio_data, current_returns, risk_metrics)
print(f"Alerts triggered: {results['alerts_triggered']}")
```

### Alert Types
- **Performance**: Drawdowns, returns, volatility thresholds
- **Risk**: VaR limits, concentration risks, correlation spikes
- **Position**: Size limits, exposure changes, rebalancing needs
- **Market**: Regime changes, market stress events
- **System**: Data quality, model availability, API health

---

## Explainability Engine

### Location
`analytics-engine/services/explainability_engine.py`

### Purpose
Ensures all financial recommendations are explainable and grounded in actual model outputs, preventing the LLM from inventing financial conclusions.

### Features

#### 1. Feature Importance Analysis
- Identifies key factors driving decisions
- Quantifies contribution of each factor
- Shows positive/negative impact direction
- Ranks factors by importance

#### 2. Decision Path Explanation
- Step-by-step reasoning chain
- Model contribution breakdown
- Data source attribution
- Confidence calibration

#### 3. Natural Language Generation
- Human-readable explanations
- Structured reasoning format
- Factor-by-factor breakdown
- Audit trail generation

#### 4. Portfolio Recommendation Explanation
- Allocation change reasoning
- Risk-based justifications
- Performance expectations
- Diversification benefits

### Key Classes

```python
class ExplainabilityEngine:
    def __init__(self, audit_dir: str = "./explainability_audit")
    def explain_trading_decision(self, decision_data: Dict, model_outputs: Dict, features: Dict[str, float]) -> DecisionExplanation
    def explain_portfolio_recommendation(self, portfolio_data: Dict, optimization_result: Dict, risk_metrics: Dict) -> Dict
    def generate_natural_language_explanation(self, explanation: DecisionExplanation) -> str
    def get_explanation_summary(self, limit: int = 10) -> Dict
```

### Usage Example

```python
from services.explainability_engine import create_explainability_engine

# Create explainability engine
engine = create_explainability_engine()

# Explain a trading decision
decision_data = {
    'action': 'BUY',
    'confidence': 0.75,
    'regime': 'Bullish',
    'decision_source': 'rf_regime_fallback',
    'rf_signal': 1
}

model_outputs = {
    'forecast': [150, 152, 155, 158, 160],
    'rf_signal': 1
}

features = {
    'rsi': 45,
    'macd_diff': 0.5,
    'volatility': 0.25,
    'adx': 28
}

explanation = engine.explain_trading_decision(decision_data, model_outputs, features)
nl_explanation = engine.generate_natural_language_explanation(explanation)
print(nl_explanation)
```

### Explanation Components

#### Feature Importance
- **LSTM Price Forecast**: Trend and momentum predictions
- **Random Forest Signal**: Technical indicator classification
- **Market Regime (HMM)**: Bullish/bearish/sideways classification
- **RSI Indicator**: Overbought/oversold conditions
- **MACD Momentum**: Trend strength and direction

#### Model Contributions
- **PPO RL Agent**: Reinforcement learning policy
- **Random Forest**: Technical signal classification
- **HMM Regime**: Market state detection
- **LSTM Forecast**: Price trend prediction
- **MarketMind Meta-Model**: Ensemble decision system

#### Data Sources
- Historical price data (OHLCV)
- Market returns data
- News sentiment analysis
- Technical indicator calculations
- Risk metrics computations

---

## Integration with Existing Systems

### LLM Connection Prevention

The explainability engine ensures the LLM cannot invent financial conclusions by:

1. **Structured Data Grounding**: All LLM inputs are grounded in actual model outputs
2. **Explainability Layer**: Decisions are explained before LLM processing
3. **Audit Trail**: All recommendations have traceable decision paths
4. **Model Attribution**: Each recommendation is tied to specific models
5. **Feature Importance**: Clear identification of driving factors

### Existing ML Model Integration

The new engines integrate seamlessly with existing models:

- **LSTM Forecasting**: Used in optimization and explainability
- **Random Forest**: Integrated into decision explanations
- **HMM Regime**: Part of monitoring and explainability
- **PPO RL**: Used in portfolio optimization
- **MarketMind Meta-Model**: Incorporated into explainability

### Data Flow Architecture

```
Market Data → Existing ML Models → Financial Engines → Explainability → LLM → User
                    ↓
              [LSTM, RF, HMM, PPO]
                    ↓
        [Optimization, Paper Trading, Monitoring]
                    ↓
              [Explainability Engine]
                    ↓
          [Grounded, Explainable Output]
                    ↓
                 [LLM Context]
                    ↓
            [Natural Language Response]
```

---

## API Endpoints

### Portfolio Optimization

#### POST `/portfolio/optimize`
Optimize portfolio using modern portfolio theory.

**Request:**
```json
{
  "tickers": ["AAPL", "MSFT", "GOOGL"],
  "weights": [0.4, 0.3, 0.3],
  "start_date": "2020-01-01",
  "end_date": "2024-01-01",
  "optimization_method": "max_sharpe",
  "risk_free_rate": 0.02
}
```

**Response:**
```json
{
  "weights": {"AAPL": 0.35, "MSFT": 0.40, "GOOGL": 0.25},
  "performance": {
    "return": 0.15,
    "volatility": 0.20,
    "sharpe_ratio": 0.65
  },
  "method": "max_sharpe",
  "explanation": "..."
}
```

#### GET `/portfolio/efficient-frontier`
Calculate efficient frontier for a set of tickers.

**Query Parameters:**
- `tickers`: Comma-separated ticker symbols
- `start_date`: Start date for historical data
- `end_date`: End date for historical data
- `n_points`: Number of points on frontier

### Paper Trading

#### POST `/paper-trading/create-account`
Create a new paper trading account.

**Request:**
```json
{
  "account_id": "demo_account",
  "initial_capital": 100000.0
}
```

#### POST `/paper-trading/place-order`
Place an order in a paper trading account.

**Request:**
```json
{
  "account_id": "demo_account",
  "ticker": "AAPL",
  "side": "buy",
  "quantity": 10,
  "order_type": "market",
  "strategy": "momentum",
  "reason": "Positive momentum signal"
}
```

#### GET `/paper-trading/account-summary`
Get summary of a paper trading account.

**Query Parameters:**
- `account_id`: Account identifier

### Monitoring and Alerts

#### POST `/monitoring/create-engine`
Create a monitoring engine for a portfolio.

**Request:**
```json
{
  "portfolio_id": "my_portfolio",
  "performance_thresholds": {
    "max_drawdown": 0.15,
    "min_daily_return": -0.05
  },
  "risk_thresholds": {
    "var_95_limit": 0.05,
    "concentration_limit": 0.30
  }
}
```

#### POST `/monitoring/run-cycle`
Run a monitoring cycle and check for alerts.

**Request:**
```json
{
  "portfolio_id": "my_portfolio",
  "portfolio_data": {
    "positions": [{"ticker": "AAPL", "weight": 0.35}],
    "drawdown": -0.12
  },
  "current_returns": [-0.02, -0.03, -0.01, 0.01, -0.04],
  "risk_metrics": {"var_95": -0.06}
}
```

#### GET `/monitoring/active-alerts`
Get all active (unacknowledged) alerts.

**Query Parameters:**
- `portfolio_id`: Portfolio identifier

#### POST `/monitoring/acknowledge-alert`
Acknowledge an alert.

**Query Parameters:**
- `portfolio_id`: Portfolio identifier
- `alert_id`: Alert identifier

---

## Best Practices

### 1. Always Use Explainability
- Generate explanations for all recommendations
- Include feature importance and model contributions
- Maintain audit trails for compliance

### 2. Ground LLM Context
- Never pass raw prompts to LLM without structured context
- Use explainability engine outputs as LLM input
- Validate LLM outputs against quantitative models

### 3. Monitor Continuously
- Set appropriate thresholds for your risk tolerance
- Use cooldown periods to prevent alert fatigue
- Regularly review and adjust alert rules

### 4. Test Before Live Trading
- Use paper trading to validate strategies
- Compare paper trading results with expectations
- Monitor slippage and commission impacts

### 5. Optimize Responsibly
- Understand the assumptions behind optimization methods
- Consider constraints and real-world limitations
- Regularly rebalance based on monitoring alerts

---

## Troubleshooting

### Common Issues

#### Import Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python path includes the analytics-engine directory

#### Data Availability
- Verify yfinance data access for required tickers
- Check date ranges are valid and have sufficient data
- Ensure internet connectivity for live data

#### Model Loading
- Confirm model files exist in `models/` directory
- Check model compatibility with current code version
- Verify model training was successful

#### API Integration
- Test endpoints individually before integration
- Check CORS settings for frontend integration
- Monitor API logs for error patterns

---

## Future Enhancements

### Planned Features
1. **Advanced Optimization**
   - Factor-based optimization (Fama-French, momentum, value)
   - Black-Litterman model integration
   - Transaction cost modeling

2. **Enhanced Paper Trading**
   - Options and derivatives support
   - Multi-asset class simulation
   - Advanced order types

3. **Monitoring Improvements**
   - Real-time market data integration
   - Predictive alerting
   - Machine learning anomaly detection

4. **Explainability Enhancements**
   - SHAP value integration
   - Counterfactual explanations
   - Interactive visualization

---

## Conclusion

The financial engines described in this document provide a comprehensive, quantitative foundation for investment decision-making. By grounding all recommendations in real models and data, ensuring explainability, and providing robust testing and monitoring capabilities, the system delivers reliable, transparent financial intelligence.

All engines are designed to prevent the LLM from inventing conclusions by requiring structured, model-verified inputs and maintaining clear audit trails for every recommendation.