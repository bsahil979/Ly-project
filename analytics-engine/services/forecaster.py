import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import datetime
import torch
import torch.nn as nn

class LSTMModel(nn.Module):
    def __init__(self, input_size=1, hidden_size=50, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])  # Take last timestep
        return out

def get_lstm_forecast(prices: pd.Series, horizon=30):
    """
    LSTM Neural Network Forecaster (PyTorch) for time-series price prediction.
    Uses a sequence-to-one architecture with 60-day lookback windows.
    """
    if len(prices) < 100:
        return [
            {"date": (datetime.datetime.now() + datetime.timedelta(days=i)).strftime('%Y-%m-%d'),
             "predicted_price": float(prices.iloc[-1])}
            for i in range(1, horizon + 1)
        ]

    # --- 1. Data Preparation ---
    data = prices.values.reshape(-1, 1).astype(np.float32)
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)

    lookback = 60

    X_train, y_train = [], []
    for i in range(lookback, len(scaled_data)):
        X_train.append(scaled_data[i - lookback:i, 0])
        y_train.append(scaled_data[i, 0])

    X_train = torch.tensor(np.array(X_train), dtype=torch.float32).unsqueeze(-1)  # [N, 60, 1]
    y_train = torch.tensor(np.array(y_train), dtype=torch.float32).unsqueeze(-1)  # [N, 1]

    # --- 2. Build & Train LSTM ---
    model = LSTMModel()
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    model.train()
    for epoch in range(20):
        optimizer.zero_grad()
        output = model(X_train)
        loss = criterion(output, y_train)
        loss.backward()
        optimizer.step()

    # --- 3. Predict Future ---
    model.eval()
    last_window = torch.tensor(scaled_data[-lookback:], dtype=torch.float32).unsqueeze(0)  # [1, 60, 1]
    predictions = []

    with torch.no_grad():
        for _ in range(horizon):
            pred = model(last_window).item()
            predictions.append(pred)
            new_entry = torch.tensor([[[pred]]], dtype=torch.float32)
            last_window = torch.cat([last_window[:, 1:, :], new_entry], dim=1)

    # Inverse transform
    predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()

    dates = [
        (datetime.datetime.now() + datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        for i in range(1, horizon + 1)
    ]

    return [
        {"date": d, "predicted_price": float(p)}
        for d, p in zip(dates, predictions)
    ]
