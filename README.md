# Smart Financial Advisor & Recommendation System

A highly structured, microservices-oriented financial advisory platform.

## Architecture

| Layer | Technology | Responsibility |
| :--- | :--- | :--- |
| **Frontend** | React, Tailwind, Recharts | User Interface, Data Visualization, Advisor Chat |
| **Gateway** | Spring Boot, Spring Security | Authentication (JWT), Portfolio Management (PostgreSQL), API Orchestration |
| **Analytics** | FastAPI, TensorFlow, hmmlearn | Statistical Risk Analysis, LSTM Price Forecasting, Regime Detection |

## Directory Structure

```text
smart-portfolio-advisor/
├── frontend/             # React SPA (Vite)
├── backend/              # Spring Boot Java Service [INITIATED]
└── analytics-engine/     # Python FastAPI Microservice
```

## Getting Started

### 1. Analytics Engine (Python)
- Navigate to `analytics-engine/`
- Install dependencies: `pip install -r requirements.txt`
- Run: `uvicorn main:app --reload`

### 2. Backend Gateway (Java)
- Navigate to `backend/`
- Run: `mvn spring-boot:run`

### 3. Frontend (React)
- Navigate to `frontend/`
- Install: `npm install`
- Run: `npm run dev`
