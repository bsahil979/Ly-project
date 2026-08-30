"""
Multi-asset portfolio RL environment.
Actions: allocation weights over N universe assets + cash (softmax-normalized).
Reward: return - drawdown penalty - volatility penalty + Sharpe bonus - turnover cost.
"""
import json
import os
import numpy as np
import pandas as pd
import gymnasium as gym
from gymnasium import spaces
from hmmlearn.hmm import GaussianHMM

FEATURES_PER_ASSET = 5  # momentum, vol, signal, current_weight, asset_drawdown
GLOBAL_FEATURES = 9     # regime(3), port_vol, port_dd, sharpe, cash_w, turnover, step_frac
PORTFOLIO_RL_DIR = '_portfolio_rl'


def _softmax(x):
    x = np.asarray(x, dtype=np.float64)
    x = x - x.max()
    e = np.exp(x)
    return e / (e.sum() + 1e-12)


def _fit_regime_states(portfolio_returns: np.ndarray, n_regimes: int = 3) -> np.ndarray:
    """HMM regime id per timestep on portfolio return series."""
    r = portfolio_returns.reshape(-1, 1)
    valid = ~np.isnan(r.flatten())
    states = np.zeros(len(r), dtype=np.int32)
    if valid.sum() < 30:
        return states
    try:
        hmm = GaussianHMM(n_components=n_regimes, covariance_type='diag', n_iter=80, random_state=42)
        hmm.fit(r[valid])
        states[valid] = hmm.predict(r[valid])
    except Exception:
        pass
    return states


def build_market_tensors(prices: pd.DataFrame, returns: pd.DataFrame):
    """
    Precompute per-timestep asset features and portfolio-level series for the env.
    prices, returns: aligned DataFrames (index=dates, columns=tickers).
    """
    tickers = list(returns.columns)
    ret = returns.values.astype(np.float64)
    px = prices.values.astype(np.float64)
    n_steps, n_assets = ret.shape

    mom = np.zeros_like(ret)
    vol = np.zeros_like(ret)
    signal = np.zeros_like(ret)
    for i in range(n_assets):
        s = pd.Series(ret[:, i])
        mom[:, i] = s.rolling(21, min_periods=5).mean().fillna(0).values
        vol[:, i] = s.rolling(21, min_periods=5).std().fillna(0.01).values
        signal[:, i] = np.sign(mom[:, i])

    port_ret = np.nanmean(ret, axis=1)
    port_ret = np.nan_to_num(port_ret, nan=0.0)
    regimes = _fit_regime_states(port_ret, n_regimes=3)

    port_vol = pd.Series(port_ret).rolling(21, min_periods=5).std().fillna(0.01).values
    equity = np.cumprod(1.0 + port_ret)
    peak = np.maximum.accumulate(equity)
    port_dd = (equity - peak) / (peak + 1e-12)

    sharpe_roll = np.zeros(n_steps)
    for t in range(n_steps):
        window = port_ret[max(0, t - 59) : t + 1]
        if len(window) > 5:
            std = window.std() + 1e-8
            sharpe_roll[t] = (window.mean() / std) * np.sqrt(252)

    asset_features = np.stack(
        [mom, vol, signal, np.zeros_like(ret), np.zeros_like(ret)], axis=-1
    )  # last two: weights, asset_dd filled in env

    return {
        'tickers': tickers,
        'returns': ret,
        'prices': px,
        'asset_features': asset_features,
        'regimes': regimes,
        'port_vol': port_vol,
        'port_dd': port_dd,
        'sharpe_roll': sharpe_roll,
        'n_steps': n_steps,
        'n_assets': n_assets,
    }


class PortfolioRLEnv(gym.Env):
    """
    Daily rebalance portfolio over a fixed universe.
    action: raw logits (n_assets + 1) -> softmax -> weights including cash.
    """

    metadata = {'render_modes': []}

    def __init__(
        self,
        tensors: dict,
        initial_weights: np.ndarray | None = None,
        rebalance_cost: float = 0.001,
        dd_penalty: float = 2.0,
        vol_penalty: float = 0.5,
        sharpe_bonus: float = 0.02,
        lookback_warmup: int = 60,
    ):
        super().__init__()
        self.tensors = tensors
        self.tickers = tensors['tickers']
        self.returns = tensors['returns']
        self.asset_features = tensors['asset_features'].copy()
        self.regimes = tensors['regimes']
        self.port_vol = tensors['port_vol']
        self.port_dd = tensors['port_dd']
        self.sharpe_roll = tensors['sharpe_roll']
        self.n_steps = tensors['n_steps']
        self.n_assets = tensors['n_assets']
        self.rebalance_cost = rebalance_cost
        self.dd_penalty = dd_penalty
        self.vol_penalty = vol_penalty
        self.sharpe_bonus = sharpe_bonus
        self.warmup = lookback_warmup

        n = self.n_assets + 1
        self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(n,), dtype=np.float32)
        obs_dim = self.n_assets * FEATURES_PER_ASSET + GLOBAL_FEATURES
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
        )

        if initial_weights is None:
            w = np.zeros(self.n_assets + 1, dtype=np.float64)
            w[-1] = 1.0
            self.initial_weights = w
        else:
            self.initial_weights = np.asarray(initial_weights, dtype=np.float64)

        self.current_step = self.warmup
        self.weights = self.initial_weights.copy()
        self.equity = 1.0
        self.peak_equity = 1.0
        self.episode_dd = 0.0
        self.asset_peak = np.ones(self.n_assets)

    def _regime_onehot(self, t):
        r = int(self.regimes[t]) if t < len(self.regimes) else 0
        oh = np.zeros(3, dtype=np.float32)
        oh[min(r, 2)] = 1.0
        return oh

    def _observation(self, t):
        af = self.asset_features[t].copy()
        asset_dd = np.zeros(self.n_assets, dtype=np.float32)
        for i in range(self.n_assets):
            p = self.tensors['prices'][t, i]
            if p > 0:
                self.asset_peak[i] = max(self.asset_peak[i], p)
                asset_dd[i] = (p - self.asset_peak[i]) / (self.asset_peak[i] + 1e-12)
        af[:, 3] = self.weights[: self.n_assets]
        af[:, 4] = asset_dd
        flat = af.flatten().astype(np.float32)

        global_vec = np.concatenate([
            self._regime_onehot(t),
            np.array([
                float(self.port_vol[t]),
                float(self.port_dd[t]),
                float(self.sharpe_roll[t]),
                float(self.weights[-1]),
                0.0,
                float(t) / max(self.n_steps, 1),
            ], dtype=np.float32),
        ])
        return np.concatenate([flat, global_vec]).astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = self.warmup
        self.weights = self.initial_weights.copy()
        self.equity = 1.0
        self.peak_equity = 1.0
        self.episode_dd = 0.0
        self.asset_peak = np.ones(self.n_assets)
        return self._observation(self.current_step), {}

    def step(self, action):
        t = self.current_step
        if t >= self.n_steps - 1:
            return self._observation(t), 0.0, True, False, {}

        new_w = _softmax(action)
        turnover = float(np.abs(new_w - self.weights).sum())
        self.weights = new_w

        asset_rets = self.returns[t + 1]
        asset_rets = np.nan_to_num(asset_rets, nan=0.0)
        port_ret = float(np.dot(self.weights[: self.n_assets], asset_rets))
        # cash earns 0 in simplified model

        self.equity *= 1.0 + port_ret
        self.peak_equity = max(self.peak_equity, self.equity)
        step_dd = (self.equity - self.peak_equity) / (self.peak_equity + 1e-12)
        self.episode_dd = min(self.episode_dd, step_dd)

        reward = port_ret * 100.0
        reward -= self.dd_penalty * max(0.0, -step_dd) * 10.0
        reward -= self.vol_penalty * float(self.port_vol[t])
        reward += self.sharpe_bonus * float(self.sharpe_roll[t])
        reward -= self.rebalance_cost * turnover * 100.0

        self.current_step += 1
        done = self.current_step >= self.n_steps - 1
        return self._observation(self.current_step), float(reward), done, False, {
            'portfolio_return': port_ret,
            'weights': self.weights.copy(),
            'turnover': turnover,
        }


def portfolio_rl_model_dir(base_dir: str) -> str:
    return os.path.join(base_dir, PORTFOLIO_RL_DIR)


def save_universe_meta(base_dir: str, tickers: list, extra: dict | None = None):
    tgt = portfolio_rl_model_dir(base_dir)
    os.makedirs(tgt, exist_ok=True)
    meta = {'tickers': tickers, 'n_assets': len(tickers), **(extra or {})}
    with open(os.path.join(tgt, 'universe.json'), 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)
    return tgt
