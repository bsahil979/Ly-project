import json
import os
from typing import Iterable, Optional

import numpy as np
import pandas as pd

from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from services.sentiment_analyzer import get_sentiment_analysis
from trading_engine.data_manager import get_processed_data


DEFAULT_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
META_MODEL_DIR = os.path.join(DEFAULT_MODEL_DIR, 'meta_model')

FEATURE_COLUMNS = [
    'returns',
    'rsi',
    'macd',
    'macd_signal',
    'macd_diff',
    'adx',
    'volatility',
    'ema_50',
    'ema_200',
    'trend_strength',
    'momentum_5d',
    'momentum_10d',
    'sentiment_score',
    'regime_code',
    'forecast_signal',
    'forecast_magnitude',
    'rf_signal',
]


class MarketMindMetaModel:
    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = model_dir or META_MODEL_DIR
        os.makedirs(self.model_dir, exist_ok=True)
        self.model_path = os.path.join(self.model_dir, 'meta_model.pkl')
        self.metrics_path = os.path.join(self.model_dir, 'meta_model_metrics.json')
        self.feature_path = os.path.join(self.model_dir, 'feature_columns.json')
        self.model = None
        self.feature_columns = FEATURE_COLUMNS.copy()
        self.metadata = {}

    @staticmethod
    def _safe_float(value, default=0.0):
        try:
            return float(value)
        except Exception:
            return float(default)

    @staticmethod
    def _regime_code_from_series(series: pd.Series) -> int:
        avg_ret = float(series.mean()) if len(series) else 0.0
        if avg_ret > 0.0015:
            return 1
        if avg_ret < -0.0015:
            return -1
        return 0

    @staticmethod
    def _sentiment_score(ticker: str):
        try:
            result = get_sentiment_analysis(ticker)
            return MarketMindMetaModel._safe_float(result.get('overall_score', 0.0), 0.0)
        except Exception:
            return 0.0

    @staticmethod
    def _build_signal_features(df: pd.DataFrame, ticker: str = None) -> pd.DataFrame:
        out = df.copy()
        out['ema_50'] = out['Close'].ewm(span=50, adjust=False).mean()
        out['ema_200'] = out['Close'].ewm(span=200, adjust=False).mean()
        out['trend_strength'] = (out['Close'] - out['ema_50']) / out['ema_50'].replace(0, np.nan)
        out['momentum_5d'] = out['Close'].pct_change(5)
        out['momentum_10d'] = out['Close'].pct_change(10)
        # forecast_signal: forward momentum proxy (used in training for per-date features)
        # In live prediction, this is overwritten with actual TimesFM forecast signal
        out['forecast_signal'] = out['returns'].fillna(0.0).rolling(10).mean()
        out['forecast_magnitude'] = out['returns'].abs().fillna(0.0).rolling(10).mean()
        out['rf_signal'] = (out['rsi'] - 50) / 50.0
        out['regime_code'] = out['returns'].fillna(0.0).rolling(30).mean().apply(
            lambda x: 1 if x > 0.0015 else (-1 if x < -0.0015 else 0)
        )
        return out

    @classmethod
    def _label_for_future_return(cls, future_return: pd.Series, buy_threshold: float, sell_threshold: float) -> pd.Series:
        return np.where(
            future_return > buy_threshold,
            1,
            np.where(future_return < sell_threshold, -1, 0),
        )

    def build_dataset(
        self,
        tickers: Iterable[str],
        start: str = '2018-01-01',
        end: Optional[str] = None,
        horizon: int = 5,
        buy_threshold: float = 0.03,
        sell_threshold: float = -0.03,
        max_rows: Optional[int] = None,
    ) -> pd.DataFrame:
        rows = []
        for ticker in tickers:
            try:
                df = get_processed_data(ticker=ticker, period='3y', interval='1d')
            except Exception:
                continue
            if df is None or df.empty:
                continue
            df = df.copy()
            df = df.loc[(df.index >= pd.Timestamp(start))]
            if end is not None:
                df = df.loc[(df.index <= pd.Timestamp(end))]
            if df.empty:
                continue
            df = self._build_signal_features(df, ticker=ticker)
            sentiment_score = self._sentiment_score(ticker)
            df['sentiment_score'] = sentiment_score
            df['ticker'] = ticker
            future_return = (df['Close'].shift(-horizon) / df['Close']) - 1
            label = self._label_for_future_return(future_return, buy_threshold, sell_threshold)
            df['target'] = label
            df['future_return'] = future_return
            if 'Date' not in df.columns:
                df = df.copy()
                df.insert(1, 'Date', pd.to_datetime(df.index))

            selected = df[[
                'ticker',
                'Date',
                'Close',
                'returns',
                'rsi',
                'macd',
                'macd_signal',
                'macd_diff',
                'adx',
                'volatility',
                'ema_50',
                'ema_200',
                'trend_strength',
                'momentum_5d',
                'momentum_10d',
                'sentiment_score',
                'regime_code',
                'forecast_signal',
                'forecast_magnitude',
                'rf_signal',
                'target',
                'future_return',
            ]].copy()
            selected = selected.replace([np.inf, -np.inf], np.nan).dropna()
            rows.append(selected)
        if not rows:
            raise ValueError('No valid rows were produced for the selected tickers.')

        dataset = pd.concat(rows, ignore_index=True)
        if max_rows is not None and len(dataset) > max_rows:
            dataset = dataset.sample(n=max_rows, random_state=42)
        dataset = dataset.reset_index(drop=True)
        dataset_path = os.path.join(self.model_dir, 'meta_dataset.csv')
        dataset.to_csv(dataset_path, index=False)
        with open(self.feature_path, 'w', encoding='utf-8') as f:
            json.dump(self.feature_columns, f, indent=2)
        return dataset

    def train(self, dataset: pd.DataFrame, test_size: float = 0.2, random_state: int = 42):
        features = [c for c in self.feature_columns if c in dataset.columns]
        if not features:
            raise ValueError('No valid feature columns found in dataset.')

        X = dataset[features].replace([np.inf, -np.inf], np.nan).fillna(method='ffill').fillna(method='bfill')
        y = dataset['target'].astype(int)

        # Remap labels from {-1, 0, 1} to {0, 1, 2} for XGBoost compatibility
        label_map = {-1: 0, 0: 1, 1: 2}
        y_mapped = y.map(label_map)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False, random_state=random_state,
        )
        _, _, y_mapped_train, y_mapped_test = train_test_split(
            X, y_mapped, test_size=test_size, shuffle=False, random_state=random_state,
        )

        candidate_models = {
            'logistic_regression': LogisticRegression(max_iter=3000, class_weight='balanced'),
            'random_forest': RandomForestClassifier(n_estimators=250, random_state=random_state, class_weight='balanced'),
            'hist_gradient_boost': HistGradientBoostingClassifier(random_state=random_state),
        }

        # Try XGBoost if available
        try:
            from xgboost import XGBClassifier
            candidate_models['xgboost'] = XGBClassifier(
                n_estimators=300, max_depth=6, learning_rate=0.1,
                random_state=random_state, eval_metric='mlogloss', tree_method='hist',
            )
        except ImportError:
            pass

        metrics = {}
        best_name = None
        best_model = None
        best_score = -1.0

        for name, model in candidate_models.items():
            try:
                model.fit(X_train, y_mapped_train)
            except Exception:
                continue
            preds = model.predict(X_test)
            # Remap predictions back from {0, 1, 2} to {-1, 0, 1} for evaluation
            reverse_map = {0: -1, 1: 0, 2: 1}
            preds = np.array([reverse_map.get(int(p), 0) for p in preds])
            accuracy = accuracy_score(y_test, preds)
            macro_f1 = f1_score(y_test, preds, average='macro', zero_division=0)
            precision = precision_score(y_test, preds, average='macro', zero_division=0)
            recall = recall_score(y_test, preds, average='macro', zero_division=0)

            metrics[name] = {
                'accuracy': float(accuracy),
                'f1_macro': float(macro_f1),
                'precision_macro': float(precision),
                'recall_macro': float(recall),
            }

            if macro_f1 > best_score:
                best_score = macro_f1
                best_name = name
                best_model = model

        if best_model is None:
            raise RuntimeError('No model could be trained.')

        self.model = best_model
        self.metadata = {
            'selected_model': best_name,
            'metrics': metrics,
            'features': features,
            'test_size': test_size,
        }

        with open(self.feature_path, 'w', encoding='utf-8') as f:
            json.dump(features, f, indent=2)
        with open(self.metrics_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)

        with open(self.model_path, 'wb') as f:
            import pickle
            pickle.dump(best_model, f)

        return self.metadata

    def is_ready(self) -> bool:
        return os.path.exists(self.model_path)

    def load(self):
        if not self.is_ready():
            return False
        with open(self.model_path, 'rb') as f:
            import pickle
            self.model = pickle.load(f)
        if os.path.exists(self.feature_path):
            with open(self.feature_path, 'r', encoding='utf-8') as f:
                self.feature_columns = json.load(f)
        return True

    def predict_single(self, row: pd.DataFrame):
        if self.model is None:
            raise ValueError('The model is not loaded.')
        if row.empty:
            raise ValueError('No row available for prediction.')
        features = [c for c in self.feature_columns if c in row.columns]
        if not features:
            raise ValueError('Input row is missing the required feature columns.')
        x = row[features].replace([np.inf, -np.inf], np.nan).fillna(method='ffill').fillna(method='bfill')
        probs = self.model.predict_proba(x)[0]
        class_labels = self.model.classes_
        idx = int(np.argmax(probs))
        label = int(class_labels[idx])
        confidence = float(probs[idx])
        # Map {0, 1, 2} back to {-1, 0, 1} and recommendation
        reverse_map = {0: -1, 1: 0, 2: 1}
        mapped_label = reverse_map.get(label, 0)
        return {
            'recommendation': 'BUY' if mapped_label == 1 else ('SELL' if mapped_label == -1 else 'HOLD'),
            'score': int(mapped_label),
            'confidence': round(confidence, 4),
            'class_probabilities': {str(int(c)): float(p) for c, p in zip(class_labels, probs)},
        }

    def predict_for_ticker(self, ticker: str, horizon: int = 5):
        if not self.is_ready() and not self.load():
            raise FileNotFoundError('Meta model not found. Run the training script first.')
        df = get_processed_data(ticker=ticker, period='1y', interval='1d')
        if df is None or df.empty:
            raise ValueError(f'No data available for {ticker}.')
        df = self._build_signal_features(df, ticker=ticker)
        sentiment_score = self._sentiment_score(ticker)
        df['sentiment_score'] = sentiment_score
        row = df.tail(1).copy()

        # Overwrite forecast_signal with actual TimesFM forecast for live prediction
        try:
            from services.forecaster import get_lstm_forecast
            prices = df['Close']
            forecast_result = get_lstm_forecast(prices, horizon=5)
            if forecast_result and len(forecast_result) >= 2:
                first_price = float(forecast_result[0].get('predicted_price', 0))
                last_price = float(forecast_result[-1].get('predicted_price', 0))
                direction = last_price - first_price
                spot = first_price or 1.0
                row['forecast_signal'] = direction / spot
                row['forecast_magnitude'] = abs(direction / spot)
        except Exception:
            pass

        row['regime_code'] = self._regime_code_from_series(df['returns'].tail(30).fillna(0.0))
        row['rf_signal'] = float((row['rsi'].iloc[-1] - 50) / 50.0 if 'rsi' in row.columns else 0.0)
        row['future_return'] = float(((row['Close'].iloc[-1] / row['Close'].shift(horizon).iloc[-1]) - 1) if row['Close'].shift(horizon).iloc[-1] else 0.0)
        row = row[[c for c in self.feature_columns if c in row.columns]].copy()
        return self.predict_single(row)
