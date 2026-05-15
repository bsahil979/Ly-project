import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from hmmlearn.hmm import GaussianHMM
import torch
import torch.nn as nn
import datetime
import os

# --- LSTM Model Definition ---
class LSTMModel(nn.Module):
    def __init__(self, input_size=1, hidden_size=64, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return out

class TradingModels:
    def __init__(self, data):
        self.df = data
        self.scaler_lstm = MinMaxScaler()
        self.scaler_rf = StandardScaler()
        self.rf_model = None
        self.hmm_model = None
        self.lstm_model = None

    # --- LSTM: Price Forecast ---
    def train_lstm(self, epochs=10, val_split=0.2, lookback=60):
        """Train LSTM with optional validation split. Returns metrics dict.

        Metrics: {"train_loss": float, "val_rmse": float, "val_mae": float}
        """
        prices = self.df['Close'].values.reshape(-1, 1).astype(np.float32)
        scaled_data = self.scaler_lstm.fit_transform(prices)

        X, y = [], []
        for i in range(lookback, len(scaled_data)):
            X.append(scaled_data[i-lookback:i, 0])
            y.append(scaled_data[i, 0])

        X = np.array(X)
        y = np.array(y)

        # Train/validation split
        split = int(len(X) * (1 - val_split))
        X_train, X_val = X[:split], X[split:]
        y_train, y_val = y[:split], y[split:]

        X_train_t = torch.tensor(X_train, dtype=torch.float32).unsqueeze(-1)
        y_train_t = torch.tensor(y_train, dtype=torch.float32).unsqueeze(-1)

        self.lstm_model = LSTMModel(input_size=1)
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.lstm_model.parameters(), lr=0.001)

        self.lstm_model.train()
        train_loss = None
        for _ in range(epochs):
            optimizer.zero_grad()
            output = self.lstm_model(X_train_t)
            loss = criterion(output, torch.tensor(y_train, dtype=torch.float32).unsqueeze(-1))
            loss.backward()
            optimizer.step()
            train_loss = loss.item()

        # Validation: iterative one-step forecasting on validation set
        self.lstm_model.eval()
        preds = []
        if len(X_val) > 0:
            window = torch.tensor(X_val[0], dtype=torch.float32).unsqueeze(0).unsqueeze(-1)
            with torch.no_grad():
                for i in range(len(X_val)):
                    out = self.lstm_model(window).item()
                    preds.append(out)
                    new_entry = torch.tensor([[[out]]], dtype=torch.float32)
                    window = torch.cat([window[:, 1:, :], new_entry], dim=1)

            # inverse transform
            preds_inv = self.scaler_lstm.inverse_transform(np.array(preds).reshape(-1, 1)).flatten()
            y_val_inv = self.scaler_lstm.inverse_transform(y_val.reshape(-1, 1)).flatten()

            from sklearn.metrics import mean_squared_error, mean_absolute_error
            import math
            val_rmse = math.sqrt(mean_squared_error(y_val_inv, preds_inv))
            val_mae = mean_absolute_error(y_val_inv, preds_inv)
        else:
            val_rmse = None
            val_mae = None

        return {"train_loss": train_loss, "val_rmse": val_rmse, "val_mae": val_mae}

    def predict_lstm(self, horizon=24):
        self.lstm_model.eval()
        prices = self.df['Close'].values.reshape(-1, 1).astype(np.float32)
        scaled_data = self.scaler_lstm.transform(prices)
        
        lookback = 60
        last_window = torch.tensor(scaled_data[-lookback:], dtype=torch.float32).unsqueeze(0)
        
        preds = []
        with torch.no_grad():
            for _ in range(horizon):
                pred = self.lstm_model(last_window).item()
                preds.append(pred)
                new_entry = torch.tensor([[[pred]]], dtype=torch.float32)
                last_window = torch.cat([last_window[:, 1:, :], new_entry], dim=1)
        
        return self.scaler_lstm.inverse_transform(np.array(preds).reshape(-1, 1)).flatten()

    # --- Persistence ---
    def save_models(self, base_dir="../models", ticker="generic"):
        """
        Save trained models to disk under: {base_dir}/{ticker}/{model_files}
        LSTM: torch state_dict
        RF: joblib
        HMM: joblib
        """
        import json
        os.makedirs(base_dir, exist_ok=True)
        tgt = os.path.join(base_dir, f"{ticker}")
        os.makedirs(tgt, exist_ok=True)

        meta = {
            "ticker": ticker,
            "trained_at": datetime.datetime.utcnow().isoformat(),
            "dataset_range": None,
            "metrics": {},
            "model_versions": {},
        }

        # LSTM
        if self.lstm_model is not None:
            lstm_path = os.path.join(tgt, "lstm.pt")
            torch.save(self.lstm_model.state_dict(), lstm_path)
            meta["model_versions"]["lstm"] = "1.0"

        # RF
        if self.rf_model is not None:
            rf_path = os.path.join(tgt, "rf.pkl")
            joblib.dump(self.rf_model, rf_path)
            meta["model_versions"]["rf"] = "1.0"

        # HMM
        if self.hmm_model is not None:
            hmm_path = os.path.join(tgt, "hmm.pkl")
            joblib.dump(self.hmm_model, hmm_path)
            meta["model_versions"]["hmm"] = "1.0"

        # Scalers (required for correct inference after load)
        joblib.dump(self.scaler_lstm, os.path.join(tgt, "scaler_lstm.pkl"))
        joblib.dump(self.scaler_rf, os.path.join(tgt, "scaler_rf.pkl"))
        meta["model_versions"]["scalers"] = "1.0"

        # Save metadata
        # optionally fill dataset_range if df has index
        try:
            if hasattr(self.df.index, 'min'):
                start = str(self.df.index.min())
                end = str(self.df.index.max())
                meta["dataset_range"] = f"{start} -> {end}"
        except Exception:
            pass

        with open(os.path.join(tgt, "metadata.json"), "w") as f:
            json.dump(meta, f, indent=2)

        return tgt

    def load_models(self, base_dir="../models", ticker="generic"):
        """
        Attempt to load models from disk. Returns list of loaded components.
        """
        tgt = os.path.join(base_dir, f"{ticker}")
        loaded = {"lstm": False, "rf": False, "hmm": False, "scalers": False}
        if not os.path.exists(tgt):
            return loaded

        # LSTM
        lstm_path = os.path.join(tgt, "lstm.pt")
        legacy_lstm_path = os.path.join(tgt, "lstm_state.pt")
        if not os.path.exists(lstm_path) and os.path.exists(legacy_lstm_path):
            lstm_path = legacy_lstm_path
        if os.path.exists(lstm_path):
            if self.lstm_model is None:
                self.lstm_model = LSTMModel(input_size=1)
            state = torch.load(lstm_path, map_location=torch.device('cpu'))
            self.lstm_model.load_state_dict(state)
            loaded["lstm"] = True

        # RF
        rf_path = os.path.join(tgt, "rf.pkl")
        legacy_rf_path = os.path.join(tgt, "rf_model.joblib")
        if not os.path.exists(rf_path) and os.path.exists(legacy_rf_path):
            rf_path = legacy_rf_path
        if os.path.exists(rf_path):
            self.rf_model = joblib.load(rf_path)
            loaded["rf"] = True

        # HMM
        hmm_path = os.path.join(tgt, "hmm.pkl")
        legacy_hmm_path = os.path.join(tgt, "hmm_model.joblib")
        if not os.path.exists(hmm_path) and os.path.exists(legacy_hmm_path):
            hmm_path = legacy_hmm_path
        if os.path.exists(hmm_path):
            self.hmm_model = joblib.load(hmm_path)
            loaded["hmm"] = True

        scaler_lstm_path = os.path.join(tgt, "scaler_lstm.pkl")
        scaler_rf_path = os.path.join(tgt, "scaler_rf.pkl")
        if os.path.exists(scaler_lstm_path) and os.path.exists(scaler_rf_path):
            self.scaler_lstm = joblib.load(scaler_lstm_path)
            self.scaler_rf = joblib.load(scaler_rf_path)
            loaded["scalers"] = True

        return loaded

    # --- Random Forest: Signal Classifier ---
    def train_rf(self, n_estimators=100):
        # Features: RSI, MACD, ADX, Returns, Volatility
        features = ['rsi', 'macd', 'macd_signal', 'adx', 'returns', 'volatility']
        X = self.df[features]
        
        # Target: 1 if next 5 bars return > 0.5%, -1 if < -0.5%, else 0
        future_return = self.df['Close'].shift(-5) / self.df['Close'] - 1
        y = np.where(future_return > 0.005, 1, np.where(future_return < -0.005, -1, 0))
        
        # Drop last entries with NaN targets
        valid_idx = ~np.isnan(future_return)
        X, y = X[valid_idx], y[valid_idx]
        
        X_scaled = self.scaler_rf.fit_transform(X)
        self.rf_model = RandomForestClassifier(n_estimators=n_estimators, random_state=42)
        self.rf_model.fit(X_scaled, y)
        return self.rf_model

    def predict_rf(self):
        features = ['rsi', 'macd', 'macd_signal', 'adx', 'returns', 'volatility']
        X_last = self.df[features].tail(1)
        X_scaled = self.scaler_rf.transform(X_last)
        signal = self.rf_model.predict(X_scaled)[0]
        prob = np.max(self.rf_model.predict_proba(X_scaled)[0])
        return signal, prob

    # --- HMM: Market Regime ---
    def train_hmm(self, n_regimes=3):
        returns = self.df['returns'].values.reshape(-1, 1)
        self.hmm_model = GaussianHMM(n_components=n_regimes, covariance_type="diag", n_iter=100)
        self.hmm_model.fit(returns)
        return self.hmm_model

    def detect_regime(self):
        returns = self.df['returns'].values.reshape(-1, 1)
        hidden_states = self.hmm_model.predict(returns)
        
        # Label regimes by mean returns
        state_means = [returns[hidden_states == i].mean() for i in range(self.hmm_model.n_components)]
        sorted_states = np.argsort(state_means)
        
        curr_state = hidden_states[-1]
        if curr_state == sorted_states[0]: return "Bearish"
        if curr_state == sorted_states[-1]: return "Bullish"
        return "Sideways"

if __name__ == "__main__":
    from data_manager import get_processed_data
    data = get_processed_data()
    tm = TradingModels(data)
    print("Training models...")
    tm.train_lstm(epochs=2)
    tm.train_rf()
    tm.train_hmm()
    
    print("Regime:", tm.detect_regime())
    sig, prob = tm.predict_rf()
    print(f"RF Signal: {sig} (Conf: {prob:.2f})")
    print("LSTM Forecast (next 5h):", tm.predict_lstm(5))
