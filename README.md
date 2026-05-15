# 🚀 Smart Portfolio Advisor & Recommendation System

[![React](https://img.shields.io/badge/Frontend-React-61DAFB?style=for-the-badge&logo=react)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Supabase](https://img.shields.io/badge/Database-Supabase-3ECF8E?style=for-the-badge&logo=supabase)](https://supabase.com/)
[![TensorFlow](https://img.shields.io/badge/AI-TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow)](https://www.tensorflow.org/)

A professional-grade quantitative analytics and financial advisory platform. This system leverages advanced machine learning models (LSTM, Random Forest, HMM, PPO) to provide institutional-level insights for retail investors.

---

## 🏗️ System Architecture

| Component | Technology Stack | Core Responsibility |
| :--- | :--- | :--- |
| **Frontend** | React 18, Tailwind CSS, Recharts | Dynamic Dashboard, Real-time Visualizations, AI Advisor Chat |
| **Analytics Engine** | Python 3.9+, FastAPI, PyTorch | Market Regime Detection, LSTM Forecasting, Signal Classification |
| **Persistence Layer**| Supabase (PostgreSQL) | Secure User Auth, Portfolio Tracking, Historical Data Cache |

---

## ✨ Key Features

- **📊 Advanced Market Analytics**: Real-time momentum tracking and volatility analysis.
- **🤖 AI Strategy Advisor**: A specialized LLM-powered chat interface contextualized with your portfolio data.
- **📈 ML-Powered Forecasting**: LSTM-based price predictions for major tech stocks and indices.
- **🌐 Regime Detection**: Hidden Markov Models (HMM) to identify market phases (Bull, Bear, Volatile).
- **💼 Portfolio Builder**: Quantitative asset allocation tools with risk-reward profiling.
- **⚡ Trading Execution Simulator**: Test strategies in a sandbox environment before going live.

---

## 📂 Repository Structure

```text
smart-portfolio-advisor/
├── frontend/             # React SPA (Vite, Tailwind, Shadcn/UI inspired)
├── analytics-engine/     # Python Microservice (ML Models, Decision Engine)
│   ├── models/           # Pre-trained ML artifacts (LSTM, HMM, RF)
│   ├── services/         # Core logic (Data Fetchers, Forecasting)
│   └── trading_engine/   # RL Agent and Simulation logic
└── scripts/              # Utility scripts for training and verification
```

---

## 🚀 Getting Started

### Prerequisites
- Node.js (v16+)
- Python 3.9+
- Git

### 1. Analytics Engine Setup
```bash
cd analytics-engine
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --port 8000 --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```

### 🏎️ Quick Run (Windows)
For convenience, use the included batch scripts to launch both services:
```bash
run_all.bat
```

---

## 🛠️ Roadmap
- [ ] Integration with live broker APIs (Interactive Brokers, Alpaca)
- [ ] Multi-asset support (Crypto, Commodities, Forex)
- [ ] Advanced Backtesting suite with slippage and commission models
- [ ] Real-time push notifications for signal alerts

---
*Disclaimer: This tool is for educational and research purposes only. Always perform your own due diligence before trading.*
