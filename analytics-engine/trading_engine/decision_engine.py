import numpy as np
import pandas as pd
import json
import os
import datetime
from .models_layer import TradingModels
from .exceptions import ModelNotFoundError
from .rl_agent import TradingEnv
from stable_baselines3 import PPO

class BrainMemory:
    """The 'Memory' layer: stores past decisions and outcomes."""
    def __init__(self, filepath="trading_memory.json"):
        self.filepath = filepath
        self.history = self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    return json.load(f)
            except:
                return []
        return []

    def record(self, entry):
        self.history.append(entry)
        # Keep only last 50 memories to stay sharp
        if len(self.history) > 50:
            self.history = self.history[-50:]
        with open(self.filepath, "w") as f:
            json.dump(self.history, f, indent=4)

    def get_performance(self):
        if not self.history:
            return {"win_rate": 0.5, "total_trades": 0, "avg_profit": 0}
        
        # In a real app, we'd wait for actual outcomes. 
        # Here we simulate 'Learning' by looking at previous entries.
        wins = sum(1 for h in self.history if h.get("outcome") == "win")
        total = len(self.history)
        return {
            "win_rate": round(wins / total if total > 0 else 0.5, 2),
            "total_trades": total,
            "avg_profit": 0.02 # mock
        }

class DecisionEngine:
    def __init__(self, data, ticker="generic", models_dir="../models", train_on_missing: bool = True):
        self.data = data
        self.ticker = ticker
        self.models_dir = models_dir
        self.tm = TradingModels(data)
        self.memory = BrainMemory()
        self.rl_model = None
        self.train_on_missing = train_on_missing
        
    def initialize(self, rl_timesteps=200):
        """Train or load all models. Prefer loading persisted artifacts when available."""
        print("Brain thinking: Attempting to load persisted models...")
        loaded = self.tm.load_models(base_dir=self.models_dir, ticker=self.ticker)

        # Handle missing components according to train_on_missing flag
        missing = []
        for key in ("lstm", "rf", "hmm", "scalers"):
            if not loaded.get(key, False):
                missing.append(key)

        if missing:
            if not self.train_on_missing:
                raise ModelNotFoundError(f"Missing persisted models for {self.ticker}: {missing}. train_on_missing=False so aborting initialization.")
            # fallback: train missing components during development/demo
            if "lstm" in missing:
                print("LSTM not found on disk — training LSTM...")
                self.tm.train_lstm(epochs=1)
            else:
                print("LSTM loaded from disk.")

            if "rf" in missing:
                print("RF not found on disk — training RF...")
                self.tm.train_rf()
            else:
                print("RF loaded from disk.")

            if "hmm" in missing:
                print("HMM not found on disk — training HMM...")
                self.tm.train_hmm()
            else:
                print("HMM loaded from disk.")
        else:
            print("All models loaded from disk.")

        # RL: try to load a saved policy first
        print("Brain learning: Initializing RL Agent (load if available)...")
        env = TradingEnv(self.data)
        ppo_path = os.path.join(self.models_dir, f"{self.ticker}", "ppo_policy.zip")
        if os.path.exists(ppo_path):
            try:
                print(f"Loading PPO policy from {ppo_path}")
                self.rl_model = PPO.load(ppo_path, env=env)
                print("PPO policy loaded from disk.")
            except Exception as e:
                print("Failed to load PPO policy, will train new one:", e)
                self.rl_model = PPO("MlpPolicy", env, verbose=0)
                self.rl_model.learn(total_timesteps=rl_timesteps)
        else:
            # Reduce timesteps for demo speed, usually higher in production
            self.rl_model = PPO("MlpPolicy", env, verbose=0)
            self.rl_model.learn(total_timesteps=rl_timesteps)
        
    def get_decision(self):
        """
        The 'Brain' Thinking & Decision Loop.
        Combines Perception, Thinking (Models), for a final Decision.
        """
        # 1. Perception & Thinking
        rf_sig, rf_prob = self.tm.predict_rf()
        regime = self.tm.detect_regime()
        lstm_forecast = self.tm.predict_lstm(5) 
        
        last_row = self.data.iloc[-1]
        is_weekend = bool(last_row['is_weekend'])
        
        # 2. Decision Layer (RL Agent)
        # FIX: Ensure all inputs are scalar floats to avoid unhashable numpy error
        obs = np.array([
            float(last_row['rsi']),
            float(last_row['macd_diff']),
            float(last_row['adx']),
            float(last_row['volatility']),
            float(last_row['day_of_week']) / 6.0,
            float(last_row['hour']) / 23.0,
            float(last_row['is_weekend']),
            float((lstm_forecast[-1] / last_row['Close']) - 1), 
            float(rf_sig),
            1.0 if regime == "Bullish" else (-1.0 if regime == "Bearish" else 0.0),
            1.0, 1.0 # Mock balance ratios
        ], dtype=np.float32)
        
        # Use predict with deterministic=True for the final brain decision
        rl_action, _ = self.rl_model.predict(obs, deterministic=True)
        
        # 3. Learning Loop (Context Awareness)
        action_map = {0: "HOLD", 1: "BUY", 2: "SELL"}
        final_action = action_map[int(rl_action)]
        
        # Brain Adjustment: Be more cautious on weekends
        confidence_boost = 0
        if is_weekend:
            # Weekend = Low Liquidity Context
            if final_action != "HOLD":
                confidence_boost -= 0.1 # Reduce confidence due to weekend risk
        
        # 4. Memory Recording
        perf = self.memory.get_performance()
        decision_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": final_action,
            "price": float(last_row['Close']),
            "regime": regime,
            "is_weekend": is_weekend,
            "outcome": "pending" # Would be updated later
        }
        self.memory.record(decision_entry)

        # 5. Final Output Assembly
        confidence = float(rf_prob * 0.4)
        if (final_action == "BUY" and rf_sig == 1) or (final_action == "SELL" and rf_sig == -1):
            confidence += 0.4
        if (final_action == "BUY" and regime == "Bullish") or (final_action == "SELL" and regime == "Bearish"):
            confidence += 0.2
        
        # Apply context-based adjustment
        confidence = max(0, min(1.0, confidence + confidence_boost))

        reasoning = [
            f"Perception: It is {'the weekend' if is_weekend else 'a weekday'}. Volume and liquidity are { 'lower' if is_weekend else 'normal' }.",
            f"Thinking: HMM identifies a {regime} regime. LSTM projects { 'upward' if lstm_forecast[-1] > last_row['Close'] else 'downward' } movement.",
            f"Memory: Brain has observed {perf['total_trades']} past situations with a {perf['win_rate']:.0%} success rate.",
            f"Decision: RL policy selected {final_action} after weighing all multi-model signals."
        ]
        
        return {
            "action": final_action,
            "confidence": round(confidence, 2),
            "reasoning": reasoning,
            "regime": regime,
            "is_weekend": is_weekend,
            "forecast": lstm_forecast.tolist(),
            "performance": perf
        }

if __name__ == "__main__":
    from .data_manager import get_processed_data
    print("Brain wake up: Fetching data...")
    data = get_processed_data()
    de = DecisionEngine(data)
    de.initialize()
    print("Brain Decision:", de.get_decision())
