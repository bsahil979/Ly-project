import argparse
import os
from trading_engine.data_manager import get_processed_data
from trading_engine.models_layer import TradingModels
from trading_engine.rl_agent import train_and_save_ppo


def main():
    parser = argparse.ArgumentParser(description='Pretrain and persist models for a ticker')
    parser.add_argument('--ticker', type=str, default='AAPL')
    parser.add_argument('--period', type=str, default='60d')
    parser.add_argument('--interval', type=str, default='5m')
    parser.add_argument('--lstm_epochs', type=int, default=10)
    parser.add_argument('--rf_estimators', type=int, default=100)
    parser.add_argument('--ppo_timesteps', type=int, default=1000)
    parser.add_argument('--save_dir', type=str, default='../models')
    args = parser.parse_args()

    ticker = args.ticker
    save_dir = args.save_dir

    print(f"Fetching data for {ticker}...")
    df = get_processed_data(ticker=ticker, period=args.period, interval=args.interval)
    if df is None or df.empty:
        print("Failed to fetch or preprocess data. Exiting.")
        return

    print("Training models... this may take a while")
    tm = TradingModels(df)
    lstm_loss = tm.train_lstm(epochs=args.lstm_epochs)
    print(f"LSTM training finished. Last loss: {lstm_loss}")

    # Train RF
    rf = tm.train_rf()
    print("RandomForest trained.")

    # Train HMM
    hmm = tm.train_hmm()
    print("HMM trained.")

    # Persist models
    tgt = tm.save_models(base_dir=save_dir, ticker=ticker)
    print(f"Models saved to {tgt}")

    # Train RL and save
    print("Training PPO (may be slow). Saving policy...")
    ppo_model = train_and_save_ppo(df, save_dir=save_dir, ticker=ticker, timesteps=args.ppo_timesteps)
    print(f"PPO trained and saved for {ticker}.")

if __name__ == '__main__':
    main()
