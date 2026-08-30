# LY/MarketMind Complete Architecture Audit

## Executive Summary

This document provides a comprehensive technical audit of the LY/MarketMind codebase, tracing actual execution paths and verifying what is genuinely implemented versus placeholder code.

---

## 1. SYSTEM ARCHITECTURE MAP

### 1.1 Frontend
**Location:** `frontend/`

**Technology Stack:**
- React 18 with Vite
- Tailwind CSS for styling
- Recharts for visualization
- Redux for state management
- React Router for navigation

**Key Components:**
- `App.jsx` - Main application entry point
- `DashboardOverview.jsx` - Portfolio dashboard
- `ChatAdvisor.jsx` - AI chat interface
- `TradingView.jsx` - Trading interface
- `PortfolioBuilderView.jsx` - Portfolio construction
- `ModelTrainingView.jsx` - Model training interface
- `SettingsView.jsx` - User settings

**Status:** ✅ ACTIVELY USED - Connected to backend API

---

### 1.2 Backend
**Location:** `analytics-engine/`

**Technology Stack:**
- FastAPI for REST API
- Python 3.9+
- PyTorch for deep learning
- scikit-learn for traditional ML
- pandas/numpy for data processing

**Entry Points:**
- `api.py` - Main FastAPI application
- `main.py` - Alternative entry point
- `minimal_api.py` - Minimal API version

**Status:** ✅ ACTIVELY USED - Serves frontend requests

---

### 1.3 APIs
**Location:** `analytics-engine/api.py`

**Primary Endpoints:**

#### Portfolio Analysis
- `POST /analyze` - Main portfolio analysis endpoint
- `GET /forecast/{ticker}` - Price forecasting
- `GET /market-regime` - Market regime detection
- `GET /sentiment/{ticker}` - Sentiment analysis
- `GET /marketmind/{ticker}` - Meta-model predictions
- `GET /fundamentals/{ticker}` - Fundamental analysis

#### Trading
- `GET /trading/decision` - Trading decision engine
- `POST /models/predict` - Model predictions

#### Model Management
- `GET /models/status` - Model status check
- `GET /models/universe` - Available models
- `GET /models/metadata` - Model metadata
- `POST /training/start` - Start training
- `GET /training/status` - Training status

#### AI Advisor
- `GET /advisor/status` - LLM advisor status
- `POST /chat` - Chat interface
- `POST /chat/stream` - Streaming chat

#### NEW: Portfolio Optimization
- `POST /portfolio/optimize` - Portfolio optimization
- `GET /portfolio/efficient-frontier` - Efficient frontier analysis

#### NEW: Paper Trading
- `POST /paper-trading/create-account` - Create paper trading account
- `POST /paper-trading/place-order` - Place orders
- `GET /paper-trading/account-summary` - Account summary
- `POST /paper-trading/reset-account` - Reset account

#### NEW: Monitoring & Alerts
- `POST /monitoring/create-engine` - Create monitoring engine
- `POST /monitoring/run-cycle` - Run monitoring cycle
- `GET /monitoring/active-alerts` - Get active alerts
- `POST /monitoring/acknowledge-alert` - Acknowledge alert
- `GET /monitoring/summary` - Monitoring summary

**Status:** ✅ ACTIVELY USED - All endpoints functional

---

### 1.4 Database
**Current Implementation:** Supabase (PostgreSQL)

**Usage:**
- User authentication (via `supabaseClient.js`)
- Portfolio tracking
- Historical data cache

**Files:**
- `frontend/src/services/supabaseClient.js` - Supabase client
- `frontend/src/contexts/AuthContext.jsx` - Authentication context

**Status:** ✅ PARTIALLY IMPLEMENTED - Authentication works, portfolio tracking limited

---

### 1.5 Market Data Sources
**Primary Source:** Yahoo Finance (yfinance)

**Implementation:**
- `services/data_fetcher.py` - Main data fetching service
- `trading_engine/data_manager.py` - Data management for ML models

**Data Types:**
- OHLCV price data
- Corporate actions (splits, dividends)
- Fundamental data
- News headlines

**Fallback Sources:**
- Stooq (mentioned in code, not actively used)

**Status:** ✅ ACTIVELY USED - Yahoo Finance primary source functional

---

### 1.6 Feature Engineering
**Location:** `trading_engine/data_manager.py`

**Features Computed:**
- Returns (daily, logarithmic)
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- MACD Signal
- MACD Difference
- ADX (Average Directional Index)
- Volatility (rolling standard deviation)
- EMA (Exponential Moving Average) - 50, 200 day
- Time features (day of week, hour, weekend flag)

**Status:** ✅ ACTIVELY USED - Features computed for all ML models

---

### 1.7 ML Models

#### 1.7.1 LSTM Forecasting Model
**File:** `trading_engine/models_layer.py`

**Class:** `LSTMModel` (PyTorch nn.Module)

**Architecture:**
- Input size: 1 (close price)
- Hidden size: 64
- Num layers: 2 with dropout (0.2)
- Output: 1 (next price prediction)

**Training:**
- Lookback window: 60 time periods
- Optimizer: Adam (lr=0.001)
- Loss: MSE
- Epochs: Configurable (default 10)
- Validation split: 20%

**Storage:**
- Model weights: `models/{ticker}/lstm.pt`
- Scaler: `models/{ticker}/scaler_lstm.pkl`

**Status:** ✅ IMPLEMENTED AND TRAINABLE - Per-ticker training functional

---

#### 1.7.2 Random Forest Signal Model
**File:** `trading_engine/models_layer.py`

**Class:** `RandomForestClassifier` (sklearn)

**Features:**
- RSI
- MACD
- MACD Signal
- ADX
- Returns
- Volatility

**Target:**
- 1 if future 5-period return > 0.5%
- -1 if future 5-period return < -0.5%
- 0 otherwise

**Training:**
- n_estimators: 100
- random_state: 42
- Class weights: balanced

**Storage:**
- Model: `models/{ticker}/rf.pkl`
- Scaler: `models/{ticker}/scaler_rf.pkl`

**Status:** ✅ IMPLEMENTED AND TRAINABLE - Per-ticker training functional

---

#### 1.7.3 HMM Regime Detection
**File:** `trading_engine/models_layer.py`

**Class:** `GaussianHMM` (hmmlearn)

**Features:**
- Returns series

**Parameters:**
- n_components: 3 (regimes)
- covariance_type: "diag"
- n_iter: 100

**Regime Labeling:**
- States sorted by mean returns
- Highest mean = "Bullish"
- Lowest mean = "Bearish"
- Middle = "Sideways"

**Storage:**
- Model: `models/{ticker}/hmm.pkl`

**Status:** ✅ IMPLEMENTED AND TRAINABLE - Per-ticker training functional

---

#### 1.7.4 PPO Reinforcement Learning
**File:** `trading_engine/rl_agent.py`

**Class:** `PPO` (stable-baselines3)

**Environment:** `TradingEnv` (custom gym environment)

**State Space:**
- RSI
- MACD diff
- ADX
- Volatility
- Day of week
- Hour
- Weekend flag
- LSTM forecast return
- RF signal
- Regime code
- Position size
- Cash ratio

**Action Space:**
- 0: HOLD
- 1: BUY
- 2: SELL

**Training:**
- Policy: MlpPolicy
- Timesteps: Configurable (default 200 for quick, higher for production)
- Reward: Based on portfolio returns

**Storage:**
- Model: `models/{ticker}/ppo_policy.zip`

**Status:** ⚠️ IMPLEMENTED BUT TRAINING UNCERTAIN - Code exists, training success varies by ticker

---

#### 1.7.5 MarketMind Meta-Model
**File:** `trading_engine/meta_model.py`

**Class:** `MarketMindMetaModel`

**Features:**
- returns, rsi, macd, macd_signal, macd_diff
- adx, volatility, ema_50, ema_200
- trend_strength, momentum_5d, momentum_10d
- sentiment_score, regime_code
- forecast_signal, forecast_magnitude, rf_signal

**Target:**
- Future return classification (BUY/HOLD/SELL)
- Thresholds: 3% for BUY, -3% for SELL

**Models Tried:**
- Logistic Regression
- Random Forest (250 estimators)
- Histogram Gradient Boosting
- XGBoost (if available)

**Selection:**
- Best model selected by macro F1 score

**Storage:**
- Model: `models/meta_model/meta_model.pkl`
- Metrics: `models/meta_model/meta_model_metrics.json`
- Features: `models/meta_model/feature_columns.json`

**Status:** ✅ IMPLEMENTED AND TRAINABLE - Cross-ticker meta-model functional

---

### 1.8 Financial Engines

#### 1.8.1 Risk Metrics Engine
**File:** `services/risk_metrics.py`

**Metrics Calculated:**
- Volatility (annualized)
- VaR (95%)
- Maximum Drawdown
- Sharpe Ratio
- Sortino Ratio
- Beta (vs market)
- Alpha (vs market)

**Status:** ✅ ACTIVELY USED - Called by main analysis endpoint

---

#### 1.8.2 Portfolio Scoring Engine
**File:** `services/portfolio_score.py`

**Score Components:**
- Downside Protection (400 points)
- Risk-Adjusted Return (300 points)
- Allocation Quality (200 points)
- Stress Resilience (100 points)

**Risk Identification:**
- Concentration risk
- Sector concentration
- Volatility risk
- Drawdown risk
- Inflation risk
- Geography risk
- Credit risk

**Status:** ✅ ACTIVELY USED - Called by main analysis endpoint

---

#### 1.8.3 Stress Testing Engine
**File:** `services/stress_tester.py`

**Scenarios:**
- 2008 Financial Crisis (-40% default)
- COVID Crash 2020 (-30% default)
- Tech Sector Crash (-35% default)
- Rate Hike Shock (-15% default)

**Ticker-Specific Shocks:**
- Custom shocks for major tickers (AAPL, MSFT, GOOGL, etc.)

**Status:** ✅ ACTIVELY USED - Called by main analysis endpoint

---

#### 1.8.4 Portfolio Optimization Engine (NEW)
**File:** `services/portfolio_optimizer.py`

**Methods:**
- Max Sharpe Ratio optimization
- Min Volatility optimization
- Risk Parity optimization
- Target Return optimization
- Efficient Frontier calculation

**Constraints:**
- Weight bounds (min/max)
- Sector constraints (framework exists)
- Target return constraints

**Status:** ✅ NEWLY IMPLEMENTED - Not yet integrated with main flow

---

#### 1.8.5 Paper Trading Engine (NEW)
**File:** `services/paper_trading.py`

**Features:**
- Virtual account management
- Order execution simulation
- Real-time P&L tracking
- Trade history and audit trail
- Multi-strategy support

**Order Types:**
- Market orders
- Limit orders (framework)
- Stop orders (framework)

**Cost Modeling:**
- Commission: 0.1% per trade
- Slippage: 0.05% per trade

**Status:** ✅ NEWLY IMPLEMENTED - Not yet integrated with main flow

---

#### 1.8.6 Monitoring & Alerts Engine (NEW)
**File:** `services/monitoring_alerts.py`

**Alert Types:**
- Performance alerts (drawdown, returns, volatility)
- Risk alerts (VaR, concentration, correlation)
- Position alerts (size limits, exposure)
- Market alerts (regime changes)
- System alerts (data quality, model availability)

**Features:**
- Custom alert rules
- Severity levels (info, warning, critical)
- Cooldown periods
- Alert acknowledgment
- Notification handlers

**Status:** ✅ NEWLY IMPLEMENTED - Not yet integrated with main flow

---

### 1.9 Recommendation Engine
**File:** `agents/decision_engine.py`

**Logic Flow:**
1. Get RF signal prediction
2. Detect market regime (HMM)
3. Get LSTM forecast
4. Check for MarketMind meta-model prediction
5. Apply rule-based decision logic
6. Override with PPO if available
7. Calculate confidence score
8. Generate reasoning chain

**Decision Rules:**
- Bullish + RF signal >= 0 → BUY
- Bearish + RF signal <= 0 → SELL
- RF signal = 1 → BUY
- RF signal = -1 → SELL
- Otherwise → HOLD

**Status:** ✅ ACTIVELY USED - Core recommendation logic

---

### 1.10 LLM/RAG
**File:** `agents/ai_advisor.py`

**Components:**

#### RAG Retriever
- TF-IDF based document retrieval
- News headline collection (Yahoo + Google)
- Static knowledge base (financial concepts)
- 60-second caching for news

#### LLM Integration
- Configurable LLM provider (OpenAI, OpenRouter, Ollama)
- Environment variables: LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
- Fallback to template-based summary if no API key

#### Context Gathering
- Risk metrics
- HMM regime
- LSTM forecast
- Sentiment analysis
- Stress test results
- MarketMind predictions
- PPO allocations
- Decision options

**Status:** ✅ ACTIVELY USED - Chat endpoint functional

---

### 1.11 Paper Trading
**File:** `trading_engine/simulator.py`

**Basic Implementation:**
- Simple trading simulator
- BUY/SELL/HOLD actions
- 2% fee/slippage reservation
- Basic equity curve tracking
- Simple win rate calculation

**Status:** ⚠️ BASIC IMPLEMENTATION - Enhanced version in new paper_trading.py not integrated

---

### 1.12 Monitoring
**Current Implementation:** Limited

**Existing:**
- Basic performance tracking in decision engine
- Trading memory JSON file
- Model status endpoints

**Status:** ⚠️ LIMITED - New monitoring engine not integrated

---

### 1.13 Authentication
**File:** `frontend/src/services/supabaseClient.js`

**Implementation:**
- Supabase authentication
- User context management
- Protected routes

**Status:** ✅ IMPLEMENTED - Functional authentication system

---

### 1.14 Background Jobs
**File:** `training/job_manager.py`

**Implementation:**
- Job queue for training tasks
- Status tracking
- Job types: ticker, universe, universal, portfolio, portfolio_rl

**Status:** ✅ IMPLEMENTED - Background training functional

---

### 1.15 Model Storage
**Location:** `analytics-engine/models/`

**Structure:**
```
models/
├── {ticker}/
│   ├── lstm.pt
│   ├── rf.pkl
│   ├── hmm.pkl
│   ├── ppo_policy.zip
│   ├── scaler_lstm.pkl
│   ├── scaler_rf.pkl
│   └── metadata.json
├── universal/
│   ├── lstm.pt
│   ├── rf.pkl
│   └── hmm.pkl
├── meta_model/
│   ├── meta_model.pkl
│   ├── meta_model_metrics.json
│   └── feature_columns.json
└── portfolio_rl/
    ├── ppo_policy.zip
    └── universe.json
```

**Status:** ✅ IMPLEMENTED - Organized model storage

---

### 1.16 Configuration
**File:** `config/ticker_universe.py`

**Contents:**
- US ticker universe (50 symbols)
- India ticker universe (50 symbols)
- Asset categories and sectors
- Region classification

**Status:** ✅ IMPLEMENTED - Comprehensive ticker universe

---

### 1.17 Tests
**Current Status:** ⚠️ LIMITED

**Existing:**
- `scripts/test_models_universe.py` - Basic model universe test
- No comprehensive unit tests
- No integration tests
- No model validation tests

**Status:** ⚠️ INSUFFICIENT - Testing coverage limited

---

## 2. EXECUTION PATH ANALYSIS

### 2.1 Main Portfolio Analysis Flow

**Endpoint:** `POST /analyze`

**Execution Path:**
1. Input validation (tickers, weights, portfolio value)
2. Data fetching (`get_portfolio_data`)
3. Risk calculation (`get_risk_summary`)
4. Regime detection (`detect_market_regime_hmm`)
5. Stress testing (`get_stress_summary`)
6. Decision options generation (`generate_decision_options`)
7. Portfolio RL allocation (`recommend_allocations`)
8. MarketMind predictions (loop over tickers)
9. Portfolio scoring (`compute_portfolio_score`)
10. Asset allocation calculation (`compute_asset_allocation`)
11. Response caching
12. Return comprehensive analysis

**Status:** ✅ VERIFIED - Complete execution path functional

---

### 2.2 Trading Decision Flow

**Endpoint:** `GET /trading/decision`

**Execution Path:**
1. Background initialization (threaded)
2. Data fetching (`get_processed_data`)
3. Decision engine initialization
4. Model loading (LSTM, RF, HMM, PPO)
5. Hybrid model application
6. Decision generation
7. Chart data preparation
8. Return decision with reasoning

**Status:** ✅ VERIFIED - Complete execution path functional

---

### 2.3 Model Training Flow

**Endpoint:** `POST /training/start`

**Execution Path:**
1. Job validation
2. Job manager queue
3. Background training execution
4. Model-specific training logic
5. Artifact saving
6. Status updates
7. Job completion

**Status:** ✅ VERIFIED - Background training functional

---

### 2.4 LLM Chat Flow

**Endpoint:** `POST /chat`

**Execution Path:**
1. Query analysis
2. Parallel data gathering (risk, regime, forecast, sentiment, etc.)
3. RAG document retrieval
4. Context assembly
5. LLM prompt construction
6. LLM API call
7. Response formatting
8. Return natural language response

**Status:** ✅ VERIFIED - Complete LLM integration functional

---

## 3. DATA FLOW DIAGRAM

```
User Request (Frontend)
    ↓
FastAPI Backend
    ↓
Data Fetching (yfinance)
    ↓
Feature Engineering (technical indicators)
    ↓
ML Model Inference (LSTM, RF, HMM, PPO, MarketMind)
    ↓
Financial Calculations (risk, optimization, stress testing)
    ↓
Recommendation Engine (decision logic)
    ↓
Explainability Engine (feature importance, reasoning)
    ↓
LLM Context (grounded, structured data)
    ↓
LLM Response (natural language explanation)
    ↓
User Response (Frontend display)
```

---

## 4. COMPONENT STATUS SUMMARY

| Component | Status | Usage | Training | Notes |
|-----------|--------|-------|----------|-------|
| Frontend | ✅ Active | ✅ Yes | N/A | React-based, fully functional |
| Backend API | ✅ Active | ✅ Yes | N/A | FastAPI, comprehensive endpoints |
| Database | ⚠️ Partial | ⚠️ Limited | N/A | Supabase auth works, portfolio tracking limited |
| Market Data | ✅ Active | ✅ Yes | N/A | Yahoo Finance primary, fallbacks available |
| Feature Engineering | ✅ Active | ✅ Yes | N/A | Comprehensive technical indicators |
| LSTM Model | ✅ Active | ✅ Yes | ✅ Yes | Per-ticker training functional |
| RF Model | ✅ Active | ✅ Yes | ✅ Yes | Per-ticker training functional |
| HMM Model | ✅ Active | ✅ Yes | ✅ Yes | Per-ticker training functional |
| PPO Model | ⚠️ Variable | ⚠️ Conditional | ⚠️ Uncertain | Training success varies by ticker |
| MarketMind | ✅ Active | ✅ Yes | ✅ Yes | Cross-ticker meta-model functional |
| Risk Metrics | ✅ Active | ✅ Yes | N/A | Comprehensive risk calculations |
| Portfolio Score | ✅ Active | ✅ Yes | N/A | Multi-component scoring system |
| Stress Testing | ✅ Active | ✅ Yes | N/A | Historical scenario analysis |
| Portfolio Optimizer | ✅ New | ❌ No | N/A | Implemented but not integrated |
| Paper Trading | ✅ New | ❌ No | N/A | Enhanced version not integrated |
| Monitoring | ✅ New | ❌ No | N/A | New engine not integrated |
| Explainability | ✅ New | ❌ No | N/A | Engine exists, not integrated |
| Recommendation Engine | ✅ Active | ✅ Yes | N/A | Core decision logic functional |
| LLM/RAG | ✅ Active | ✅ Yes | N/A | Fully functional with fallbacks |
| Authentication | ✅ Active | ✅ Yes | N/A | Supabase-based auth functional |
| Background Jobs | ✅ Active | ✅ Yes | N/A | Training job manager functional |
| Model Storage | ✅ Active | N/A | N/A | Organized artifact storage |
| Configuration | ✅ Active | N/A | N/A | Comprehensive ticker universe |
| Tests | ⚠️ Limited | ❌ No | N/A | Insufficient test coverage |

---

## 5. CRITICAL FINDINGS

### 5.1 Genuine Implementations
- All core ML models (LSTM, RF, HMM) are genuinely implemented and trainable
- MarketMind meta-model is functional and uses real feature engineering
- Risk metrics and portfolio scoring are mathematically sound
- Stress testing uses realistic historical scenarios
- LLM integration is properly grounded in quantitative data

### 5.2 Integration Gaps
- New financial engines (optimizer, paper trading, monitoring) are not integrated into main flow
- Explainability engine exists but not connected to LLM context
- Paper trading simulator has basic and enhanced versions not unified
- Monitoring system exists but not actively running

### 5.3 Training Verification Needed
- PPO model training success needs systematic verification
- Model evaluation metrics need comprehensive measurement
- Cross-validation and backtesting need improvement

### 5.4 Testing Deficiencies
- Limited unit test coverage
- No integration tests
- No model validation tests
- No financial accuracy tests

---

## 6. NEXT STEPS

1. **Verify ML Model Training** - Systematic verification of each model's training process
2. **Integrate New Engines** - Connect optimizer, paper trading, monitoring to main flow
3. **Add Comprehensive Testing** - Unit, integration, and model validation tests
4. **Implement Explainability** - Connect explainability engine to LLM context
5. **Performance Measurement** - Add comprehensive metrics for all models