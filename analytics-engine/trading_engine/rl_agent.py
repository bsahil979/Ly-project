import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv

class TradingEnv(gym.Env):
    """
    A custom environment for trading BTC.
    State: [RSI, MACD, ADX, Volatility, LSTM_Pred, RF_Signal, HMM_Regime, Balance, Net_Worth]
    Actions: 0 (Hold), 1 (Buy), 2 (Sell)
    """
    def __init__(self, df, initial_balance=10000):
        super(TradingEnv, self).__init__()
        self.df = df
        self.initial_balance = initial_balance
        
        # Action space: 0: Hold, 1: Buy, 2: Sell
        self.action_space = spaces.Discrete(3)
        
        # Observation space: 12 features (added day, hour, weekend)
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(12,), dtype=np.float32
        )
        
        self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.balance = self.initial_balance
        self.net_worth = self.initial_balance
        self.shares_held = 0
        self.cost_basis = 0
        self.current_step = 0
        
        return self._next_observation(), {}

    def _next_observation(self):
        row = self.df.iloc[self.current_step]
        obs = np.array([
            row['rsi'],
            row['macd_diff'],
            row['adx'],
            row['volatility'],
            row['day_of_week'] / 6.0,
            row['hour'] / 23.0,
            row['is_weekend'],
            0, # LSTM placeholder
            0, # RF placeholder
            0, # HMM placeholder
            self.balance / self.initial_balance,
            self.net_worth / self.initial_balance
        ], dtype=np.float32)
        return obs

    def step(self, action):
        current_price = self.df.iloc[self.current_step]['Close']
        
        # Execute trade
        if action == 1: # Buy
            if self.balance > 0:
                self.shares_held += self.balance / current_price
                self.balance = 0
                self.cost_basis = current_price
        elif action == 2: # Sell
            if self.shares_held > 0:
                self.balance += self.shares_held * current_price
                self.shares_held = 0
        
        self.current_step += 1
        self.net_worth = self.balance + (self.shares_held * current_price)
        
        # Reward: change in net worth
        reward = (self.net_worth - self.initial_balance) / self.initial_balance
        
        done = self.current_step >= len(self.df) - 1
        truncated = False
        
        return self._next_observation(), reward, done, truncated, {}

def train_ppo_agent(df):
    env = TradingEnv(df)
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=1000)
    return model


def _make_vec_env(df, n_envs=1):
    if n_envs <= 1:
        return DummyVecEnv([lambda: Monitor(TradingEnv(df))])
    # create separate env factories (they will share the same dataframe but run independently)
    def make_factory(_):
        return lambda: Monitor(TradingEnv(df))
    return SubprocVecEnv([make_factory(i) for i in range(n_envs)])


def _find_latest_checkpoint(checkpoint_dir):
    import glob
    import os
    if not os.path.isdir(checkpoint_dir):
        return None
    # look for zip files or any file in the checkpoint folder
    candidates = glob.glob(os.path.join(checkpoint_dir, '*.zip'))
    if not candidates:
        candidates = glob.glob(os.path.join(checkpoint_dir, '*'))
    if not candidates:
        return None
    # pick newest by modification time
    latest = max(candidates, key=os.path.getmtime)
    return latest


def train_and_save_ppo(df, save_dir="../models", ticker="generic", timesteps=1000, n_envs=1, checkpoint_interval=None, resume=False):
    """Train a PPO agent and save policy to disk under save_dir/{ticker}/ppo_policy

    - `n_envs` enables vectorized environments (use >1 for SubprocVecEnv).
    - `checkpoint_interval` will save intermediate models every N steps to
      `{save_dir}/{ticker}/checkpoints/`.
    """
    import os
    vec_env = _make_vec_env(df, n_envs=n_envs)

    # Attempt to resume from latest checkpoint if requested
    checkpoint_dir = os.path.join(save_dir, str(ticker), 'checkpoints')
    model = None
    if resume:
        latest = _find_latest_checkpoint(checkpoint_dir)
        if latest:
            try:
                model = PPO.load(latest, env=vec_env)
            except Exception:
                model = None

    # create new model if not resumed
    if model is None:
        model = PPO("MlpPolicy", vec_env, verbose=1)

    callbacks = []
    checkpoint_dir = os.path.join(save_dir, str(ticker), 'checkpoints')
    if checkpoint_interval and checkpoint_interval > 0:
        os.makedirs(checkpoint_dir, exist_ok=True)
        cb = CheckpointCallback(save_freq=checkpoint_interval, save_path=checkpoint_dir, name_prefix='ppo_ckpt')
        callbacks.append(cb)

    if callbacks:
        model.learn(total_timesteps=timesteps, callback=callbacks)
    else:
        model.learn(total_timesteps=timesteps)

    # final save
    tgt = os.path.join(save_dir, f"{ticker}")
    os.makedirs(tgt, exist_ok=True)
    model_path = os.path.join(tgt, "ppo_policy")
    try:
        model.save(model_path)
    except Exception:
        # best-effort: still return model
        pass

    # close vectorized env
    try:
        vec_env.close()
    except Exception:
        pass

    return model

if __name__ == "__main__":
    import argparse
    # Mock data for quick testing
    df = pd.DataFrame({
        'Close': np.linspace(100, 150, 100),
        'rsi': np.random.rand(100) * 100,
        'macd_diff': np.random.rand(100),
        'adx': np.random.rand(100) * 50,
        'volatility': np.random.rand(100) * 0.02
    })

    parser = argparse.ArgumentParser()
    parser.add_argument('--timesteps', type=int, default=1000, help='Number of PPO timesteps to train')
    parser.add_argument('--preset', choices=['quick','standard','extended','large'], help='Preset timesteps: quick=10k, standard=50k, extended=100k, large=1M')
    parser.add_argument('--save_dir', default='../models')
    parser.add_argument('--ticker', default='generic')
    parser.add_argument('--n_envs', type=int, default=1, help='Number of parallel environments')
    parser.add_argument('--checkpoint_interval', type=int, default=0, help='Save checkpoints every N steps (0 disabled)')
    parser.add_argument('--resume', action='store_true', help='Resume from latest checkpoint if available')
    args = parser.parse_args()

    preset_map = {
        'quick': 10_000,
        'standard': 50_000,
        'extended': 100_000,
        'large': 1_000_000,
    }

    steps = args.timesteps
    if args.preset:
        steps = preset_map.get(args.preset, args.timesteps)

    model = train_and_save_ppo(df, save_dir=args.save_dir, ticker=args.ticker, timesteps=steps, n_envs=args.n_envs, checkpoint_interval=args.checkpoint_interval, resume=args.resume)
    print(f"RL Model trained for {steps} timesteps.")
