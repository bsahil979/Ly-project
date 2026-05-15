import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import DashboardLayout from './pages/DashboardLayout';
import DashboardOverview from './components/DashboardOverview';
import ForecastingView from './components/ForecastingView';
import SentimentView from './components/SentimentView';
import ChatAdvisor from './components/ChatAdvisor';
import TradingView from './components/TradingView';
import AuthPage from './pages/AuthPage';
import PortfolioBuilderView from './components/PortfolioBuilderView';
import SettingsView from './components/SettingsView';
import ResearchView from './components/ResearchView';
import FundamentalsView from './components/FundamentalsView';
import { AuthService, PortfolioStorageService, supabase } from './services/supabaseClient';

function App() {
  const [portfolio, setPortfolioState] = useState([]);
  const [userId, setUserId] = useState(null);

  useEffect(() => {
    const syncUserSpace = async (userObj) => {
      const uid = userObj?.id || userObj?.email || null;
      setUserId(uid);
      if (uid) {
        const savedTickers = await PortfolioStorageService.getUserPortfolio(uid);
        setPortfolioState(savedTickers || []);
      } else {
        setPortfolioState([]);
      }
    };

    const handleAuthChange = () => {
      AuthService.getCurrentUser().then(res => {
        syncUserSpace(res?.data?.user);
      }).catch(e => console.warn("Init load info:", e));
    };

    // Initial check
    handleAuthChange();

    // Supabase listener
    const { data } = supabase.auth.onAuthStateChange((event, session) => {
      syncUserSpace(session?.user);
    });

    // Mock listener
    window.addEventListener('auth-change', handleAuthChange);

    return () => {
      data?.subscription?.unsubscribe();
      window.removeEventListener('auth-change', handleAuthChange);
    };
  }, []);

  const setPortfolio = (updater) => {
    let nextState;
    if (typeof updater === 'function') {
      nextState = updater(portfolio);
    } else {
      nextState = updater;
    }
    setPortfolioState(nextState);
    if (userId) {
      PortfolioStorageService.saveUserPortfolio(userId, nextState);
    }
  };

  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/auth" element={<AuthPage />} />
        <Route 
          path="/dashboard" 
          element={<DashboardLayout tickers={portfolio} setTickers={setPortfolio} />}
        >
          <Route index element={<DashboardOverview tickers={portfolio} />} />
          <Route path="manage" element={<PortfolioBuilderView tickers={portfolio} setTickers={setPortfolio} />} />
          <Route path="settings" element={<SettingsView tickers={portfolio} setTickers={setPortfolio} />} />
          <Route path="research" element={<ResearchView tickers={portfolio} />} />
          <Route path="fundamentals" element={<FundamentalsView tickers={portfolio} />} />
          <Route path="forecast" element={<ForecastingView tickers={portfolio} />} />
          <Route path="sentiment" element={<SentimentView tickers={portfolio} />} />
          <Route path="chat" element={<ChatAdvisor tickers={portfolio} />} />
          <Route path="trading" element={<TradingView tickers={portfolio} />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
