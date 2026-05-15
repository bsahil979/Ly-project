from fastapi.testclient import TestClient
import os
import json
from api import app, models_status
from trading_engine.data_manager import get_processed_data
from trading_engine.decision_engine import DecisionEngine


def print_heading(h):
    print('\n' + '='*10 + ' ' + h + ' ' + '='*10)


def main():
    client = TestClient(app)

    # 1) /models/status
    print_heading('/models/status')
    r = client.get('/models/status')
    print('status code:', r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print('no json')

    # 2) DecisionEngine load-only initialization (expect clear error if missing)
    print_heading('DecisionEngine load-only initialize')
    data = get_processed_data(ticker='AAPL', period='60d', interval='5m')
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    models_dir = os.path.join(base, 'models')
    print('models_dir=', models_dir)
    de = DecisionEngine(data, ticker='AAPL', models_dir=models_dir, train_on_missing=False)
    try:
        de.initialize(rl_timesteps=10)
        print('initialize() completed without raising — models loaded or trained')
    except Exception as e:
        print('initialize() raised:', repr(e))

    # 3) /models/predict (lstm) — ensure no retraining and clear responses
    print_heading('/models/predict')
    payload = {'ticker': 'AAPL', 'model': 'lstm', 'horizon': 5}
    r2 = client.post('/models/predict', json=payload)
    print('status code:', r2.status_code)
    try:
        print(json.dumps(r2.json(), indent=2))
    except Exception:
        print('no json')


if __name__ == '__main__':
    main()
