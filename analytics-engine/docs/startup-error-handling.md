# Startup Error Handling

## Goal

The API must behave as an inference-only service.

If a model is missing, startup should fail clearly instead of triggering training.

## Current behavior

- `DecisionEngine(..., train_on_missing=False)` is used by the API.
- `DecisionEngine.initialize()` raises `ModelNotFoundError` when required artifacts are missing.
- `background_initialize()` captures the exception and stores the error string.
- `GET /trading/decision` returns the underlying startup error when initialization fails.
- `GET /models/status` includes `server.train_on_missing=false`.

## Expected failure mode

When a ticker does not have trained artifacts:

- do not train models
- do not silently recover
- do not cache a fake ready state
- return a clear error message naming the missing artifact set

## Suggested operator checklist

1. Run offline training first.
2. Confirm the target ticker exists under `models/{ticker}`.
3. Start the API.
4. Call `GET /models/status`.
5. Call `POST /models/predict`.
6. If startup fails, inspect the returned error string and missing files.
