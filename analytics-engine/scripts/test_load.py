import sys
import pathlib
import os

# Ensure project root is on sys.path so 'trading_engine' package is importable
root = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from trading_engine.data_manager import get_processed_data
from trading_engine.decision_engine import DecisionEngine

print('Fetching data...')
data = get_processed_data(ticker='AAPL', period='60d', interval='5m')
models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
models_dir = os.path.abspath(models_dir)
print('Models dir =', models_dir)
de = DecisionEngine(data, ticker='AAPL', models_dir=models_dir)
print('Initializing engine (should load saved models if present)...')
de.initialize(rl_timesteps=10)
print('Done. Decision sample:')
print(de.get_decision())
