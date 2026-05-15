# Verification Checklist

Use this checklist after changing inference behavior.

## Cold start

- API starts without retraining
- no LSTM, RF, HMM, or PPO training logs appear at boot
- startup is fast

## Status endpoint

- `GET /models/status` returns `train_on_missing=false`
- each ticker entry shows loaded artifacts
- metadata is present when available

## Prediction endpoint

- `POST /models/predict` returns a result for an existing ticker
- inference is fast
- no training is triggered

## Missing model case

- remove or rename one artifact temporarily
- restart the API
- confirm a clear error is returned
- confirm no fallback retraining occurs

## RL loading

- PPO policy is loaded from disk
- no PPO learning occurs on API boot

## LSTM loading

- LSTM state is loaded from disk
- forecasting returns normally
