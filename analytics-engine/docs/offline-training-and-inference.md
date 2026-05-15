# Offline Training and Inference

## Required behavior

This system follows a two-stage architecture:

1. Offline training
2. Online inference

The API must not retrain models at runtime.

## Offline training

Run the trainer on historical data before deployment.

Recommended input size for this project:

- 5 years of daily OHLCV data for stable model runs
- up to 10 years if you want broader regime coverage
- intraday data only when you explicitly need higher-frequency research

Example:

```powershell
cd "analytics-engine"
python training/train_all.py --tickers AAPL MSFT --period 5y --interval 1d --lstm_epochs 50 --ppo_timesteps 50000 --save_dir ../models
```

This should produce one artifact folder per ticker under `models/`.

## Inference mode

The FastAPI server runs with:

- `train_on_missing=False`
- persisted artifact loading only
- no fallback training on startup

If a required artifact is missing, the server should raise `ModelNotFoundError` or return a clear 500 response with the missing resource details.

## Verification goals

When verifying the API, confirm:

- startup is quick
- no training logs appear
- `GET /models/status` shows loaded artifacts
- `POST /models/predict` returns a prediction without retraining
- missing artifacts fail clearly instead of retraining silently

## Production guidance

For deployment:

- schedule retraining separately from inference
- write new artifacts offline
- promote artifacts atomically
- keep inference read-only
- log model metadata and training dates
