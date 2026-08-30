"""
Inference for portfolio-level PPO: weight allocations over universe + cash.
"""
import json
import os
import datetime
import numpy as np
import pandas as pd
from stable_baselines3 import PPO

from services.data_fetcher import get_portfolio_data
from services.regime_detector import detect_market_regime_hmm
from trading_engine.portfolio_rl_env import (
    PortfolioRLEnv,
    build_market_tensors,
    portfolio_rl_model_dir,
    _softmax,
)


def portfolio_rl_is_ready(base_dir: str) -> bool:
    tgt = portfolio_rl_model_dir(base_dir)
    policy = os.path.join(tgt, 'ppo_policy.zip')
    uni = os.path.join(tgt, 'universe.json')
    return os.path.isfile(policy) and os.path.isfile(uni)


def _load_meta(base_dir: str) -> dict:
    with open(os.path.join(portfolio_rl_model_dir(base_dir), 'universe.json'), 'r', encoding='utf-8') as f:
        return json.load(f)


def _load_policy(base_dir: str, env: PortfolioRLEnv):
    path = os.path.join(portfolio_rl_model_dir(base_dir), 'ppo_policy.zip')
    return PPO.load(path, env=env)


def recommend_allocations(
    user_tickers: list[str],
    user_weights: list[float] | None = None,
    base_dir: str | None = None,
    lookback_days: int = 400,
) -> dict:
    """
    Run portfolio PPO on latest data for the trained universe.
    Returns allocations for user_tickers + Cash, renormalized from universe policy.
    """
    base_dir = base_dir or os.path.join(os.path.dirname(__file__), '..', 'models')
    if not portfolio_rl_is_ready(base_dir):
        return {
            'ready': False,
            'error': 'Portfolio RL policy not trained. Run portfolio RL training from Model Training.',
        }

    meta = _load_meta(base_dir)
    universe = meta['tickers']
    end = datetime.date.today()
    start = end - datetime.timedelta(days=lookback_days)
    data = get_portfolio_data(universe, start.isoformat(), end.isoformat())
    prices = data['prices'].ffill().bfill()
    returns = prices.pct_change(fill_method=None).dropna(how='any')
    prices = prices.loc[returns.index]

    # align columns to training order
    missing = [t for t in universe if t not in returns.columns]
    if missing:
        for t in missing:
            returns[t] = 0.0
            prices[t] = prices.iloc[-1, 0] if len(prices.columns) else 100.0
    returns = returns[universe]
    prices = prices[universe]

    tensors = build_market_tensors(prices, returns)

    init = np.zeros(len(universe) + 1, dtype=np.float64)
    init[-1] = 1.0
    if user_weights and user_tickers:
        uw = {t.upper(): w for t, w in zip(user_tickers, user_weights)}
        for i, sym in enumerate(universe):
            if sym.upper() in uw:
                init[i] = uw[sym.upper()]
        s = init.sum()
        if s > 0:
            init /= s

    env = PortfolioRLEnv(tensors, initial_weights=init)
    model = _load_policy(base_dir, env)

    t = env.n_steps - 2
    obs = env._observation(t)
    action, _ = model.predict(obs, deterministic=True)
    weights = _softmax(action)

    full_alloc = {sym: float(weights[i]) for i, sym in enumerate(universe)}
    full_alloc['Cash'] = float(weights[-1])

    user_set = {t.upper() for t in user_tickers}
    subset = {}
    for sym in universe:
        if sym.upper() in user_set:
            subset[sym] = full_alloc[sym]

    sub_sum = sum(subset.values())
    cash_rl = full_alloc['Cash']
    if sub_sum > 0:
        scale = (1.0 - cash_rl) / sub_sum if sub_sum > 0 else 0
        for k in subset:
            subset[k] = round(subset[k] * scale, 4)
    else:
        scale = 0

    user_cash = round(cash_rl + max(0, 1.0 - sum(subset.values()) - cash_rl), 4)
    if user_tickers:
        subset['Cash'] = user_cash

    port_ret = returns.mean(axis=1)
    regime = detect_market_regime_hmm(port_ret)

    top_holdings = sorted(
        [(k, v) for k, v in full_alloc.items() if k != 'Cash'],
        key=lambda x: -x[1],
    )[:10]

    return {
        'ready': True,
        'source': 'portfolio_ppo',
        'universe_size': len(universe),
        'regime': regime,
        'recommended_weights': subset,
        'full_universe_weights': full_alloc,
        'top_universe_holdings': [{'symbol': k, 'weight': round(v, 4)} for k, v in top_holdings],
        'cash_weight': round(full_alloc['Cash'], 4),
        'reasoning': [
            'PPO portfolio policy trained on full universe with Sharpe/drawdown/volatility-aware rewards.',
            f'Current market regime (HMM): {regime.get("current_regime", "Unknown")}.',
            f'Top universe tilts: {", ".join(f"{k} {v*100:.1f}%" for k, v in top_holdings[:5])}.',
            f'Recommended cash (universe): {full_alloc["Cash"]*100:.1f}%.',
        ],
        'rebalance_hint': _rebalance_hint(user_tickers, user_weights, subset),
    }


def _rebalance_hint(user_tickers, user_weights, recommended):
    if not user_tickers or not user_weights or 'Cash' not in recommended:
        return []
    hints = []
    for t, w in zip(user_tickers, user_weights):
        tgt = recommended.get(t, recommended.get(t.upper(), 0))
        diff = tgt - w
        if abs(diff) < 0.02:
            continue
        direction = 'increase' if diff > 0 else 'reduce'
        hints.append(f'{direction} {t} by ~{abs(diff)*100:.1f}%')
    return hints[:8]
