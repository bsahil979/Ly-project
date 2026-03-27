import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM

def detect_market_regime_hmm(returns: pd.Series, n_regimes=3):
    """
    Uses HMM to detect Hidden Market Regimes (e.g., Bull, Bear, Volatile).
    """
    data = returns.values.reshape(-1, 1)
    
    # Standardize
    model = GaussianHMM(n_components=n_regimes, covariance_type="diag", n_iter=1000)
    model.fit(data)
    
    hidden_states = model.predict(data)
    
    # Label states based on mean return
    state_means = []
    for i in range(n_regimes):
        state_means.append(data[hidden_states == i].mean())
    
    # Sort states: 0=Bear, 1=Neutral, 2=Bull (roughly)
    sorted_states = np.argsort(state_means)
    
    curr_state = hidden_states[-1]
    regime_label = "Neutral"
    if curr_state == sorted_states[0]: regime_label = "Bearish/High Volatility"
    elif curr_state == sorted_states[-1]: regime_label = "Bullish/Low Volatility"
    
    return {
        "current_regime": regime_label,
        "state_id": int(curr_state),
        "confidence": float(np.max(model.predict_proba(data)[-1]))
    }