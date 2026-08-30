"""
Universal (cross-ticker) models — trained once on pooled data from the full universe.
Used as fallback when per-ticker artifacts are missing (hybrid inference).
"""
import os
import json
import datetime
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from hmmlearn.hmm import GaussianHMM
import torch
import torch.nn as nn

from .models_layer import LSTMModel

RF_FEATURES = ['rsi', 'macd', 'macd_signal', 'adx', 'returns', 'volatility']
UNIVERSAL_DIR = '_universal'
LOOKBACK = 60
MAX_LSTM_SAMPLES = 20000
LSTM_BATCH_SIZE = 128


def _rf_labels(df):
    future_return = df['Close'].shift(-5) / df['Close'] - 1
    y = np.where(future_return > 0.005, 1, np.where(future_return < -0.005, -1, 0))
    valid = ~np.isnan(future_return)
    return df.loc[valid, RF_FEATURES], y[valid], valid


class UniversalModels:
    """Shared RF, HMM, and return-based LSTM for any ticker at inference time."""

    def __init__(self):
        self.scaler_rf = StandardScaler()
        self.scaler_returns = MinMaxScaler()
        self.rf_model = None
        self.hmm_model = None
        self.lstm_model = None

    @staticmethod
    def model_path(base_dir):
        return os.path.join(base_dir, UNIVERSAL_DIR)

    def train_from_frames(self, frames, n_estimators=300, lstm_epochs=25, hmm_regimes=3):
        """frames: list of processed DataFrames (one per ticker)."""
        if not frames:
            raise ValueError("No data frames provided for universal training")

        rf_X_parts, rf_y_parts = [], []
        all_returns = []

        for df in frames:
            if df is None or df.empty:
                continue
            X, y, _ = _rf_labels(df)
            if len(X) > 0:
                rf_X_parts.append(X)
                rf_y_parts.append(y)
            all_returns.append(df['returns'].dropna().values)

        if not rf_X_parts:
            raise ValueError("No valid rows for universal RF training")

        X_all = pd.concat(rf_X_parts, axis=0)
        y_all = np.concatenate(rf_y_parts)
        X_scaled = self.scaler_rf.fit_transform(X_all)
        self.rf_model = RandomForestClassifier(n_estimators=n_estimators, random_state=42, n_jobs=-1)
        self.rf_model.fit(X_scaled, y_all)

        returns_concat = np.concatenate(all_returns).reshape(-1, 1)
        self.hmm_model = GaussianHMM(n_components=hmm_regimes, covariance_type='diag', n_iter=100)
        self.hmm_model.fit(returns_concat)

        # LSTM on per-ticker return windows (pooled, capped to avoid OOM)
        ret_series = np.concatenate(all_returns).astype(np.float32).reshape(-1, 1)
        scaled_all = self.scaler_returns.fit_transform(ret_series).flatten()

        X_parts, y_parts = [], []
        offset = 0
        for arr in all_returns:
            n = len(arr)
            if n <= LOOKBACK:
                offset += n
                continue
            seg = scaled_all[offset:offset + n]
            offset += n
            for i in range(LOOKBACK, n):
                X_parts.append(seg[i - LOOKBACK:i])
                y_parts.append(seg[i])

        if not X_parts:
            raise ValueError("No valid LSTM sequences for universal training")

        X_seq = np.array(X_parts, dtype=np.float32)
        y_seq = np.array(y_parts, dtype=np.float32)
        if len(X_seq) > MAX_LSTM_SAMPLES:
            idx = np.random.default_rng(42).choice(len(X_seq), MAX_LSTM_SAMPLES, replace=False)
            X_seq = X_seq[idx]
            y_seq = y_seq[idx]

        self.lstm_model = LSTMModel(input_size=1)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.lstm_model.parameters(), lr=0.001)
        self.lstm_model.train()
        train_loss = None
        n = len(X_seq)
        for _ in range(lstm_epochs):
            perm = np.random.permutation(n)
            epoch_loss = 0.0
            batches = 0
            for start in range(0, n, LSTM_BATCH_SIZE):
                bi = perm[start:start + LSTM_BATCH_SIZE]
                xb = torch.tensor(X_seq[bi], dtype=torch.float32).unsqueeze(-1)
                yb = torch.tensor(y_seq[bi], dtype=torch.float32).unsqueeze(-1)
                optimizer.zero_grad()
                out = self.lstm_model(xb)
                loss = criterion(out, yb)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
                batches += 1
            train_loss = epoch_loss / max(batches, 1)

        return {
            'rf_samples': int(len(X_all)),
            'tickers': len(frames),
            'lstm_train_loss': train_loss,
            'hmm_regimes': hmm_regimes,
        }

    def save(self, base_dir):
        tgt = self.model_path(base_dir)
        os.makedirs(tgt, exist_ok=True)
        if self.rf_model is not None:
            joblib.dump(self.rf_model, os.path.join(tgt, 'rf.pkl'))
        if self.hmm_model is not None:
            joblib.dump(self.hmm_model, os.path.join(tgt, 'hmm.pkl'))
        if self.lstm_model is not None:
            torch.save(self.lstm_model.state_dict(), os.path.join(tgt, 'lstm.pt'))
        joblib.dump(self.scaler_rf, os.path.join(tgt, 'scaler_rf.pkl'))
        joblib.dump(self.scaler_returns, os.path.join(tgt, 'scaler_returns.pkl'))
        meta = {
            'trained_at': datetime.datetime.utcnow().isoformat(),
            'type': 'universal_hybrid',
            'model_versions': {'rf': '1.0', 'hmm': '1.0', 'lstm': '1.0'},
        }
        with open(os.path.join(tgt, 'metadata.json'), 'w') as f:
            json.dump(meta, f, indent=2)
        return tgt

    def load(self, base_dir):
        tgt = self.model_path(base_dir)
        loaded = {'lstm': False, 'rf': False, 'hmm': False, 'scalers': False}
        if not os.path.isdir(tgt):
            return loaded

        rf_path = os.path.join(tgt, 'rf.pkl')
        if os.path.exists(rf_path):
            self.rf_model = joblib.load(rf_path)
            loaded['rf'] = True

        hmm_path = os.path.join(tgt, 'hmm.pkl')
        if os.path.exists(hmm_path):
            self.hmm_model = joblib.load(hmm_path)
            loaded['hmm'] = True

        lstm_path = os.path.join(tgt, 'lstm.pt')
        if os.path.exists(lstm_path):
            self.lstm_model = LSTMModel(input_size=1)
            self.lstm_model.load_state_dict(torch.load(lstm_path, map_location='cpu'))
            self.lstm_model.eval()
            loaded['lstm'] = True

        sr = os.path.join(tgt, 'scaler_rf.pkl')
        sret = os.path.join(tgt, 'scaler_returns.pkl')
        if os.path.exists(sr) and os.path.exists(sret):
            self.scaler_rf = joblib.load(sr)
            self.scaler_returns = joblib.load(sret)
            loaded['scalers'] = True

        return loaded

    def is_ready(self):
        return (
            self.rf_model is not None
            and self.hmm_model is not None
            and self.lstm_model is not None
        )

    def predict_rf(self, df):
        X_last = df[RF_FEATURES].tail(1)
        X_scaled = self.scaler_rf.transform(X_last)
        signal = self.rf_model.predict(X_scaled)[0]
        prob = float(np.max(self.rf_model.predict_proba(X_scaled)[0]))
        return int(signal), prob

    def detect_regime(self, df):
        returns = df['returns'].values.reshape(-1, 1)
        hidden_states = self.hmm_model.predict(returns)
        state_means = []
        for i in range(self.hmm_model.n_components):
            mask = hidden_states == i
            state_means.append(returns[mask].mean() if mask.any() else 0.0)
        sorted_states = np.argsort(state_means)
        curr = hidden_states[-1]
        if curr == sorted_states[0]:
            return 'Bearish'
        if curr == sorted_states[-1]:
            return 'Bullish'
        return 'Sideways'

    def predict_lstm_prices(self, df, horizon=5):
        """Forecast prices using return-space LSTM, anchored to last close."""
        rets = df['returns'].dropna().values.astype(np.float32).reshape(-1, 1)
        if len(rets) < LOOKBACK:
            last = float(df['Close'].iloc[-1])
            return np.full(horizon, last)

        scaled = self.scaler_returns.transform(rets)
        window = torch.tensor(scaled[-LOOKBACK:], dtype=torch.float32).unsqueeze(0).unsqueeze(-1)
        self.lstm_model.eval()
        preds_scaled = []
        with torch.no_grad():
            for _ in range(horizon):
                pred = self.lstm_model(window).item()
                preds_scaled.append(pred)
                new_entry = torch.tensor([[[pred]]], dtype=torch.float32)
                window = torch.cat([window[:, 1:, :], new_entry], dim=1)

        preds_scaled = np.array(preds_scaled).reshape(-1, 1)
        preds_ret = self.scaler_returns.inverse_transform(preds_scaled).flatten()

        prices = []
        price = float(df['Close'].iloc[-1])
        for r in preds_ret:
            price = price * (1.0 + float(r))
            prices.append(price)
        return np.array(prices)


def apply_hybrid_to_trading_models(tm, ticker, models_dir):
    """
    Load per-ticker models into tm; fill gaps from universal pool.
    Returns dict with analysis_mode, components, universal instance, per_ticker_loaded.
    """
    loaded = tm.load_models(base_dir=models_dir, ticker=ticker)
    uni = UniversalModels()
    uni.load(models_dir)

    components = {}
    if loaded.get('lstm'):
        components['lstm'] = 'per_ticker'
    elif uni.lstm_model is not None:
        components['lstm'] = 'universal'

    if loaded.get('rf') and loaded.get('scalers'):
        components['rf'] = 'per_ticker'
    elif uni.rf_model is not None:
        components['rf'] = 'universal'
        tm.rf_model = uni.rf_model
        tm.scaler_rf = uni.scaler_rf

    if loaded.get('hmm'):
        components['hmm'] = 'per_ticker'
    elif uni.hmm_model is not None:
        components['hmm'] = 'universal'
        tm.hmm_model = uni.hmm_model

    if components.get('lstm') == 'universal':
        tm.lstm_model = uni.lstm_model

    modes = set(components.values())
    if modes == {'per_ticker'}:
        analysis_mode = 'per_ticker'
    elif modes == {'universal'}:
        analysis_mode = 'universal'
    elif components:
        analysis_mode = 'hybrid'
    else:
        analysis_mode = 'none'

    return {
        'analysis_mode': analysis_mode,
        'components': components,
        'universal': uni,
        'per_ticker_loaded': loaded,
    }


def universal_is_ready(base_dir):
    """
    Whether universal hybrid artifacts exist. Uses filesystem checks only — does not
    load joblib/torch into RAM (loading on every /models/universe call stalled the UI).
    """
    tgt = UniversalModels.model_path(base_dir)
    if not os.path.isdir(tgt):
        return False, {'lstm': False, 'rf': False, 'hmm': False, 'scalers': False}
    loaded = {
        'lstm': os.path.isfile(os.path.join(tgt, 'lstm.pt')),
        'rf': os.path.isfile(os.path.join(tgt, 'rf.pkl')),
        'hmm': os.path.isfile(os.path.join(tgt, 'hmm.pkl')),
        'scalers': (
            os.path.isfile(os.path.join(tgt, 'scaler_rf.pkl'))
            and os.path.isfile(os.path.join(tgt, 'scaler_returns.pkl'))
        ),
    }
    ready = bool(loaded['lstm'] and loaded['rf'] and loaded['hmm'] and loaded['scalers'])
    return ready, loaded
