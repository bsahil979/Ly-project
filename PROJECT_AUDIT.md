# Project Audit: Smart Portfolio Advisor / MarketMind Upgrade Compatibility

## Executive Summary

This repository does contain a real machine learning pipeline, but it does not yet implement the MarketMind upgrade specification as described in the provided document.

What is actually implemented is a local, per-ticker and hybrid ML trading stack based on:

- LSTM forecasting (PyTorch)
- Random Forest signal classification (scikit-learn)
- HMM market regime detection (hmmlearn)
- PPO reinforcement learning agent (stable-baselines3)
- VADER sentiment analysis from news headlines
- Rule-based portfolio decision logic

What is not implemented yet is the required MarketMind meta-decision model, a proper explainable model training pipeline, chronological evaluation, and a genuine end-to-end backtesting framework that matches the specification.

This audit confirms the project is feasible to upgrade, but only in phases and only with evidence-based implementation.

---

## 1. Models That Exist

The real codebase contains the following models and components.

### 1.1 LSTM Forecasting Model

Implemented in:

- `analytics-engine/trading_engine/models_layer.py`
- `analytics-engine/services/forecaster.py`

Evidence:

- `LSTMModel` is defined as a custom PyTorch `nn.Module`.
- `TradingModels.train_lstm(...)` builds price sequences and trains the model.
- `TradingModels.predict_lstm(...)` outputs a forecast.
- Models are saved to disk as `lstm.pt`.

Status:

- Real, implemented, and trained locally.
- Used in inference and saved models.

### 1.2 Random Forest Signal Model

Implemented in:

- `analytics-engine/trading_engine/models_layer.py`
- `analytics-engine/trading_engine/universal_models.py`

Evidence:

- `RandomForestClassifier` is imported from `sklearn.ensemble`.
- It is trained on technical indicators such as RSI, MACD, ADX, returns, and volatility.
- `train_rf(...)` and `predict_rf(...)` are implemented.
- Saved to `rf.pkl`.

Status:

- Real, implemented, and trained locally.
- Used as the main signal component.

### 1.3 Gaussian Hidden Markov Model (HMM)

Implemented in:

- `analytics-engine/trading_engine/models_layer.py`
- `analytics-engine/services/regime_detector.py`

Evidence:

- `from hmmlearn.hmm import GaussianHMM`
- `train_hmm(...)` fits the model to return series.
- `detect_regime()` labels the current regime by sorting state means.

Status:

- Real, implemented, and trained locally.
- Used for market regime categorization.

### 1.4 PPO Reinforcement Learning Model

Implemented in:

- `analytics-engine/trading_engine/rl_agent.py`
- `analytics-engine/trading_engine/portfolio_rl_service.py`
- `analytics-engine/trading_engine/decision_engine.py`

Evidence:

- `from stable_baselines3 import PPO`
- `train_and_save_ppo(...)` trains a PPO agent.
- `DecisionEngine.initialize()` loads `ppo_policy.zip` if present.
- `portfolio_rl_service.py` also contains a PPO portfolio allocation recommendation flow.

Status:

- Real, implemented, but not consistently guaranteed to be trained for all tickers.
- It is used conditionally and may fall back to rule-based strategies.

### 1.5 Sentiment Analysis

Implemented in:

- `analytics-engine/services/sentiment_analyzer.py`

Evidence:

- Uses `vaderSentiment` and Yahoo/Google news fetching.
- Produces aggregate sentiment scores per ticker.

Status:

- Real, implemented.
- Not a Hugging Face fine-tuned model.
- Not a transformer-based NLP model.

---

## 2. Models Actually Trained

The training workflow is in:

- `analytics-engine/training/train_all.py`

This script trains all of the following for each ticker:

1. LSTM
2. Random Forest
3. HMM
4. PPO

The code explicitly says:

- save LSTM as `lstm.pt`
- save RF as `rf.pkl`
- save HMM as `hmm.pkl`
- save PPO as `ppo_policy.zip`
- save scaler files for inference

Therefore, the project does train local ML models and saves them to `analytics-engine/models/...`.

---

## 3. Models Defined but Not Fully Used

The following appear to exist but are not yet a complete MarketMind-style decision model:

### 3.1 Meta-Decision Model

There is no actual trained model that combines:

- LSTM output
- RF signal output
- HMM regime
- sentiment
- technical features
- future-return labels

into one final `BUY/HOLD/SELL` model.

The current final decision is rule-driven in:

- `analytics-engine/trading_engine/decision_engine.py`

This final decision is not a learned model.

### 3.2 Financial NLP Fine-Tuning Pipeline

There is no fine-tuned transformer model for financial text or stock sentiment classification.

The repo uses VADER sentiment instead of a fine-tuned Hugging Face or finance-specific NLP model.

### 3.3 Global Train/Test Evaluation Pipeline

There is no chronological split and no proper training/evaluation artifact set for the upgrade spec.

The current workflow is mainly local training and inference, not formal model comparison or backtesting on withheld time windows.

---

## 4. Training Scope and Data Usage

### 4.1 Ticker-Level Training

The project trains per ticker, not as a single global meta-model dataset, as seen in:

- `analytics-engine/training/train_all.py`

It calls `train_ticker(...)` and then saves into `models/{ticker}`.

This means the project currently trains one ticker's models separately.

### 4.2 Data Sources

Primary source used in the data pipeline is:

- `analytics-engine/trading_engine/data_manager.py`

This uses `yfinance` and a fallback path via Stooq.

The project already incorporates:

- OHLCV price data
- returns
- technical indicators
- time features

This matches the specification's initial baseline for market data collection.

### 4.3 Feature Set

The existing technical feature set is real and implemented:

- RSI
- MACD, MACD Signal, MACD Difference
- ADX
- returns
- volatility
- rolling metrics
- time features

This is enough to support the next step of building a meta-model dataset.

---

## 5. Final Recommendation Logic

The current final recommendation is not learned from data; it is rule-based.

Evidence:

- `DecisionEngine._rule_action(...)` in `analytics-engine/trading_engine/decision_engine.py`
- `generate_decision_options(...)` in `analytics-engine/agents/decision_engine.py`

The decision flow is approximately:

1. Forecast LSTM
2. Predict RF signal
3. Detect HMM regime
4. Apply rule logic to decide BUY/HOLD/SELL
5. Optionally use PPO if available

This is not a MarketMind Meta-Decision Model. It is an ensemble-style decision rule with optional RL override.

---

## 6. PPO Status

The document asks whether PPO is genuinely trained and used.

Answer: yes, somewhat.

- PPO is genuinely implemented and trainable.
- It is saved as `ppo_policy.zip` and loaded by the decision engine.
- However, PPO is not necessarily the final model that controls BUY/HOLD/SELL in all cases.
- In the current logic, the code falls back to RF/HMM rules if PPO is absent or not loaded.

Therefore, PPO exists and is used conditionally, but it is not the single unified MarketMind meta-decision model described in the specification.

---

## 7. Fake, Placeholder, or Hard-Coded Behavior

The repository does contain some risk of placeholder logic, but not obviously fake model outputs in the main code path.

Examples of real logic:

- actual technical indicators
- actual LSTM/RF/HMM training code
- actual saved artifacts
- real sentiment analysis via VADER
- real data fetching from Yahoo Finance

However, there are still implementation gaps relative to the specification:

- no real meta-model training and evaluation
- no chronological model splitting for financial time series
- no explainability pipeline (SHAP or equivalent)
- no genuine backtesting record tied to a trained MarketMind model
- no documented and validated results
- no fine-tuning pipeline for finance NLP

---

## 8. What Is Missing Compared to the Spec

The following are not yet implemented in a verifiable way:

- `PROJECT_AUDIT.md` (now created)
- `MODEL_DOCUMENTATION.md`
- `MODEL_EVALUATION.md`
- `BACKTEST_RESULTS.md`
- `ARCHITECTURE.md`
- Meta-Decision Model training dataset builder
- Chronological train/validation/test split
- Model comparison across candidate algorithms
- Backtesting against buy-and-hold and model strategy
- Explainable AI outputs
- Financial NLP fine-tuning pipeline
- Reproducible model metrics from real experiments

---

## 9. Audit Conclusion

This project is implementable as a MarketMind-style upgrade, but only as a staged engineering effort.

The code is strong enough to support the first phases because it already has:

- real market data loading
- technical indicators
- multiple ML models
- alerting/signal logic
- sentiment analysis
- saved model artifacts

The project is not yet ready for a full claims-based MarketMind deployment because the meta-model and validation infrastructure are missing.

---

## 10. Recommended Implementation Plan

### Phase 0: Complete and Keep this audit

- Keep `PROJECT_AUDIT.md` as the source of truth.
- Do not claim model results without executing actual training and evaluation.

### Phase 1: Validate Existing System

- Confirm which models train successfully for a small ticker list.
- Validate saved artifacts and inference output.
- Create a clean chronological split strategy.

### Phase 2: Build MarketMind Meta-Model Dataset

- Gather market feature rows across multiple tickers.
- Add LSTM forecast feature, RF probabilities, HMM regime, and sentiment score.
- Create future return labels with configurable horizons and thresholds.
- Save the dataset with timestamp and ticker metadata.

### Phase 3: Train Candidate Meta-Models

- Logistic Regression baseline
- Random Forest baseline
- Gradient Boosting/XGBoost if available
- Optional neural network
- Compare metrics on chronological validation/test sets

### Phase 4: Save and Expose Model Outputs

- Add API schema separating:
  - raw model outputs
  - decision layer
  - final recommendation
  - explanation
- Save model metadata and evaluation metrics

### Phase 5: Backtesting and Explainability

- Add historical simulation over time
- Compute Sharpe ratio, drawdown, annual return, volatility
- Add SHAP-based or feature-importance explanation

### Phase 6: Optional Financial NLP

- Add a financial sentiment transformer model only after data collection and evaluation
- Do not claim fine-tuning until actual model training and validation occur

### Phase 7: PPO Portfolio Optimization Audit

- Review whether PPO is genuinely useful for portfolio allocation or whether it is a secondary policy module
- Validate it with real training runs and metrics

---

## 11. Final Position

This repository is a good base for the MarketMind upgrade, but the upgrade is not yet implemented as a genuine end-to-end investment intelligence system.

The correct path is:

1. preserve the working local ML pipeline,
2. add the meta-model data pipeline,
3. perform chronological evaluation,
4. select the best model,
5. then add backtesting and explanation features.

This is feasible and aligned with the project's existing architecture.
