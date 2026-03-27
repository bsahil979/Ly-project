import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
import datetime

def get_lstm_forecast(prices: pd.Series, horizon=30):
    """
    Fallback Forecaster using RandomForest (as TensorFlow is heavy).
    Matches the LSTM interface for seamless switching.
    """
    if len(prices) < 100:
        return [{"date": (datetime.datetime.now() + datetime.timedelta(days=i)).strftime('%Y-%m-%d'), "predicted_price": float(prices.iloc[-1])} for i in range(1, horizon+1)]

    lookback = 20
    
    # Prepare data for RF
    df = pd.DataFrame(prices)
    df.columns = ['Close']
    for i in range(1, lookback + 1):
        df[f'lag_{i}'] = df['Close'].shift(i)
    
    df = df.dropna()
    
    X = df.drop('Close', axis=1).values
    y = df['Close'].values
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # Predict future
    last_window = df.iloc[-1]['Close':].values
    
    predictions = []
    curr_features = last_window[:-1] # Exclude old target, use lags
    # Re-align: [Close, lag_1, ..., lag_19]
    curr_window = df.iloc[-1][['Close'] + [f'lag_{i}' for i in range(1, lookback)]].values
    
    for _ in range(horizon):
        pred = model.predict(curr_window.reshape(1, -1))[0]
        predictions.append(pred)
        # Shift window: new_pred becomes Close, old Close becomes lag_1, etc.
        curr_window = np.insert(curr_window[:-1], 0, pred)

    dates = [(datetime.datetime.now() + datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, horizon+1)]
    
    return [
        {"date": d, "predicted_price": float(p)} 
        for d, p in zip(dates, predictions)
    ]
