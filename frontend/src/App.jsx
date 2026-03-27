import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import DashboardLayout from './pages/DashboardLayout';
import DashboardOverview from './components/DashboardOverview';
import ForecastingView from './components/ForecastingView';
import SentimentView from './components/SentimentView';
import ChatAdvisor from './components/ChatAdvisor';

function App() {
  const [portfolio, setPortfolio] = useState(['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'RELIANCE.NS', 'SPY']);

  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route 
          path="/dashboard" 
          element={<DashboardLayout tickers={portfolio} setTickers={setPortfolio} />}
        >
          <Route index element={<DashboardOverview tickers={portfolio} />} />
          <Route path="forecast" element={<ForecastingView tickers={portfolio} />} />
          <Route path="sentiment" element={<SentimentView tickers={portfolio} />} />
          <Route path="chat" element={<ChatAdvisor tickers={portfolio} />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
