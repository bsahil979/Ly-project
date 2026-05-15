# Analytics Engine

This package is the Python ML engine for the smart portfolio advisor. It uses a strict separation between offline training and online inference.

## Architecture

- `training/` trains models from historical market data.
- `models/` stores persisted artifacts per ticker.
- `backtesting/` evaluates signals and strategy performance.
- `trading_engine/` contains model, RL, and inference orchestration.
- `api.py` exposes FastAPI inference endpoints.

## Models

- LSTM (`PyTorch`) for next-price forecasting
- Random Forest (`scikit-learn`) for BUY / HOLD / SELL classification
- Gaussian HMM (`hmmlearn`) for regime detection
- PPO (`stable-baselines3`) for trading actions

## Offline training workflow

Use the unified offline trainer:

```powershell
cd "analytics-engine"
python training/train_all.py --tickers AAPL MSFT --period 5y --interval 1d --lstm_epochs 50 --ppo_timesteps 50000 --save_dir ../models
```

This trains all models offline and writes artifacts to:

- `models/{ticker}/lstm.pt`
- `models/{ticker}/rf.pkl`
- `models/{ticker}/hmm.pkl`
- `models/{ticker}/ppo_policy.zip`
- `models/{ticker}/metadata.json`

## Inference workflow

The API runs in load-only mode:

- `train_on_missing=False`
- missing artifacts raise `ModelNotFoundError`
- no training should occur at API startup

Useful endpoints:

- `GET /models/status`
- `POST /models/predict`
- `GET /models/metadata`

## Backtesting

Use `backtesting/backtest.py` to compute:

- Sharpe ratio
- max drawdown
- win rate
- total return
- equity curve

## Quick checks

```powershell
cd "analytics-engine"
python scripts/verify_api.py
```
