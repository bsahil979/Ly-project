"""
==========================================================================
  OFFLINE TRAINING PIPELINE  -  Smart Portfolio Advisor
==========================================================================

This script trains ALL ML models on HISTORICAL data and saves them to disk.
It must be run ONCE before the app is deployed to production.

Models trained:
  1. LSTM  - Price forecasting (time-series)
  2. RF    - Buy/Sell signal classifier (tabular)
  3. HMM   - Market regime detector (unsupervised)
  4. PPO   - Reinforcement Learning trading agent

Usage:
  cd analytics-engine
  python -m training.train_all --tickers AAPL MSFT GOOGL --period 5y --lstm_epochs 50

Run 'python -m training.train_all --help' for all options.
==========================================================================
"""

import argparse
import os
import sys
import logging
import json
import time
import datetime
import math
import numpy as np

# Ensure the analytics-engine root is on the path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from trading_engine.data_manager import get_processed_data
from trading_engine.models_layer import TradingModels
from trading_engine.rl_agent import train_and_save_ppo

logger = logging.getLogger('training')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(message)s',
    datefmt='%H:%M:%S'
)

# ──────────────────────────────────────────────────────────────
#   DEFAULT TICKERS  -  The stocks we pre-train models for
# ──────────────────────────────────────────────────────────────
DEFAULT_TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'META', 'AMZN', 'SPY']

# ──────────────────────────────────────────────────────────────
#   TRAIN ONE TICKER
# ──────────────────────────────────────────────────────────────

def train_ticker(
    ticker,
    period='5y',
    interval='1d',
    lstm_epochs=50,
    rf_estimators=200,
    ppo_timesteps=50_000,
    save_dir=None,
    ppo_n_envs=1,
    ppo_checkpoint_interval=0,
    ppo_resume=False,
):
    """
    Complete training pipeline for a single ticker:
      1. Fetch historical data with technical indicators
      2. Train LSTM on price series
      3. Train Random Forest on indicator features
      4. Train HMM on return series
      5. Train PPO RL agent on simulated trading env
      6. Save all artifacts + comprehensive metadata
    """
    if save_dir is None:
        save_dir = os.path.join(os.path.dirname(__file__), '..', 'models')

    start_time = time.time()
    logger.info("=" * 60)
    logger.info(f"  TRAINING: {ticker}  |  period={period}  interval={interval}")
    logger.info("=" * 60)

    # ── Step 1: Fetch & feature-engineer historical data ──────
    logger.info("[1/5] Fetching historical data...")
    df = get_processed_data(ticker=ticker, period=period, interval=interval)
    if df is None or df.empty:
        logger.error(f"No data returned for {ticker}. Skipping.")
        return False

    n_rows = len(df)
    date_range = f"{df.index.min()} -> {df.index.max()}"
    logger.info(f"      Dataset: {n_rows} rows  |  {date_range}")

    tm = TradingModels(df)

    # ── Step 2: Train LSTM ────────────────────────────────────
    logger.info(f"[2/5] Training LSTM ({lstm_epochs} epochs)...")
    lstm_metrics = tm.train_lstm(epochs=lstm_epochs, val_split=0.2)
    logger.info(f"      LSTM train_loss={lstm_metrics['train_loss']:.6f}  "
                f"val_rmse={lstm_metrics.get('val_rmse', 'N/A')}  "
                f"val_mae={lstm_metrics.get('val_mae', 'N/A')}")

    # ── Step 3: Train Random Forest ───────────────────────────
    logger.info(f"[3/5] Training Random Forest ({rf_estimators} trees)...")
    tm.rf_model = tm.train_rf(n_estimators=rf_estimators)

    # Evaluate RF with train/test split
    rf_metrics = _evaluate_rf(tm, df)
    logger.info(f"      RF accuracy={rf_metrics['accuracy']:.4f}  "
                f"precision={rf_metrics['precision']:.4f}  "
                f"recall={rf_metrics['recall']:.4f}  "
                f"f1={rf_metrics['f1']:.4f}")

    # ── Step 4: Train HMM ─────────────────────────────────────
    logger.info("[4/5] Training HMM (3 regimes)...")
    tm.hmm_model = tm.train_hmm(n_regimes=3)
    current_regime = tm.detect_regime()
    hmm_metrics = {
        'n_components': tm.hmm_model.n_components,
        'current_regime': current_regime,
        'converged': bool(tm.hmm_model.monitor_.converged),
        'n_iter': int(tm.hmm_model.monitor_.iter),
    }
    logger.info(f"      HMM converged={hmm_metrics['converged']}  "
                f"regime={current_regime}  "
                f"iterations={hmm_metrics['n_iter']}")

    # ── Save LSTM + RF + HMM ──────────────────────────────────
    logger.info("      Saving LSTM + RF + HMM artifacts...")
    tgt = tm.save_models(base_dir=save_dir, ticker=ticker)

    # ── Step 5: Train PPO RL Agent ────────────────────────────
    logger.info(f"[5/5] Training PPO RL Agent ({ppo_timesteps} timesteps)...")
    train_and_save_ppo(
        df,
        save_dir=save_dir,
        ticker=ticker,
        timesteps=ppo_timesteps,
        n_envs=ppo_n_envs,
        checkpoint_interval=ppo_checkpoint_interval,
        resume=ppo_resume,
    )
    logger.info("      PPO training complete and saved.")

    # ── Write comprehensive metadata ──────────────────────────
    elapsed = time.time() - start_time
    metadata = {
        "ticker": ticker,
        "trained_at": datetime.datetime.utcnow().isoformat(),
        "training_duration_seconds": round(elapsed, 1),
        "dataset": {
            "period": period,
            "interval": interval,
            "rows": n_rows,
            "date_range": date_range,
        },
        "hyperparameters": {
            "lstm_epochs": lstm_epochs,
            "lstm_lookback": 60,
            "lstm_hidden_size": 64,
            "lstm_num_layers": 2,
            "rf_estimators": rf_estimators,
            "hmm_n_regimes": 3,
            "ppo_timesteps": ppo_timesteps,
        },
        "metrics": {
            "lstm": {
                "train_loss": lstm_metrics['train_loss'],
                "val_rmse": lstm_metrics.get('val_rmse'),
                "val_mae": lstm_metrics.get('val_mae'),
            },
            "rf": rf_metrics,
            "hmm": hmm_metrics,
        },
        "model_versions": {
            "lstm": "1.0",
            "rf": "1.0",
            "hmm": "1.0",
            "ppo": "1.0",
        },
    }

    meta_path = os.path.join(tgt, 'metadata.json')
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)

    logger.info(f"  DONE: {ticker} in {elapsed:.1f}s  |  Artifacts -> {tgt}")
    logger.info("")
    return True


def _evaluate_rf(tm, df):
    """Evaluate Random Forest with a proper holdout evaluation."""
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

    features = ['rsi', 'macd', 'macd_signal', 'adx', 'returns', 'volatility']
    X = df[features].copy()
    future_return = df['Close'].shift(-5) / df['Close'] - 1
    y = np.where(future_return > 0.005, 1, np.where(future_return < -0.005, -1, 0))

    valid_idx = ~np.isnan(future_return)
    X_valid = X[valid_idx]
    y_valid = y[valid_idx]

    # Use last 20% as test set (time-series split)
    split = int(len(X_valid) * 0.8)
    X_test = X_valid.iloc[split:]
    y_test = y_valid[split:]

    if len(X_test) == 0:
        return {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0}

    X_test_scaled = tm.scaler_rf.transform(X_test)
    preds = tm.rf_model.predict(X_test_scaled)

    return {
        'accuracy': round(float(accuracy_score(y_test, preds)), 4),
        'precision': round(float(precision_score(y_test, preds, average='macro', zero_division=0)), 4),
        'recall': round(float(recall_score(y_test, preds, average='macro', zero_division=0)), 4),
        'f1': round(float(f1_score(y_test, preds, average='macro', zero_division=0)), 4),
    }


# ──────────────────────────────────────────────────────────────
#   CLI ENTRY POINT
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Train all ML models on historical market data.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train default tickers (AAPL, MSFT, GOOGL, TSLA, META, AMZN, SPY)
  python -m training.train_all

  # Train specific tickers with custom settings
  python -m training.train_all --tickers AAPL MSFT --period 5y --lstm_epochs 100

  # Quick training (fewer epochs/timesteps for testing)
  python -m training.train_all --tickers AAPL --ppo_preset quick --lstm_epochs 10
        """
    )
    parser.add_argument('--tickers', nargs='+', default=DEFAULT_TICKERS,
                        help=f'Tickers to train (default: {DEFAULT_TICKERS})')
    parser.add_argument('--period', default='5y',
                        help='Historical data period (default: 5y)')
    parser.add_argument('--interval', default='1d',
                        help='Data interval (default: 1d)')
    parser.add_argument('--lstm_epochs', type=int, default=50,
                        help='LSTM training epochs (default: 50)')
    parser.add_argument('--ppo_timesteps', type=int, default=50_000,
                        help='PPO training timesteps (default: 50000)')
    parser.add_argument('--ppo_preset', choices=['quick', 'standard', 'extended', 'large'],
                        help='PPO preset: quick=10k, standard=50k, extended=100k, large=1M')
    parser.add_argument('--ppo_n_envs', type=int, default=1,
                        help='Number of parallel PPO environments')
    parser.add_argument('--ppo_checkpoint_interval', type=int, default=0,
                        help='Save PPO checkpoints every N steps (0=disabled)')
    parser.add_argument('--ppo_resume', action='store_true',
                        help='Resume PPO from latest checkpoint if available')
    parser.add_argument('--save_dir', default=None,
                        help='Directory to save models (default: analytics-engine/models/)')
    args = parser.parse_args()

    # Resolve save_dir
    save_dir = args.save_dir
    if save_dir is None:
        save_dir = os.path.join(os.path.dirname(__file__), '..', 'models')

    # Map preset
    preset_map = {
        'quick': 10_000,
        'standard': 50_000,
        'extended': 100_000,
        'large': 1_000_000,
    }
    ppo_steps = preset_map.get(args.ppo_preset, args.ppo_timesteps) if args.ppo_preset else args.ppo_timesteps

    # Banner
    logger.info("=" * 60)
    logger.info("  SMART PORTFOLIO ADVISOR  -  Model Training Pipeline")
    logger.info("=" * 60)
    logger.info(f"  Tickers    : {args.tickers}")
    logger.info(f"  Period     : {args.period}")
    logger.info(f"  Interval   : {args.interval}")
    logger.info(f"  LSTM epochs: {args.lstm_epochs}")
    logger.info(f"  PPO steps  : {ppo_steps}")
    logger.info(f"  Save dir   : {os.path.abspath(save_dir)}")
    logger.info("=" * 60)
    logger.info("")

    total_start = time.time()
    results = {}

    for t in args.tickers:
        try:
            success = train_ticker(
                t,
                period=args.period,
                interval=args.interval,
                lstm_epochs=args.lstm_epochs,
                ppo_timesteps=ppo_steps,
                save_dir=save_dir,
                ppo_n_envs=args.ppo_n_envs,
                ppo_checkpoint_interval=args.ppo_checkpoint_interval,
                ppo_resume=args.ppo_resume,
            )
            results[t] = "OK" if success else "FAILED (no data)"
        except Exception as e:
            logger.exception(f"Training failed for {t}: {e}")
            results[t] = f"ERROR: {e}"

    total_elapsed = time.time() - total_start

    # Summary
    logger.info("=" * 60)
    logger.info("  TRAINING SUMMARY")
    logger.info("=" * 60)
    for t, status in results.items():
        icon = "[+]" if status == "OK" else "[-]"
        logger.info(f"  {icon} {t:6s} : {status}")
    logger.info(f"  Total time: {total_elapsed:.1f}s")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
