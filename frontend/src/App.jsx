import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import DashboardLayout from './pages/DashboardLayout';
import PortfolioDashboard from './components/PortfolioDashboard';
import ForecastingView from './components/ForecastingView';
import SentimentView from './components/SentimentView';
import ChatAdvisor from './components/ChatAdvisor';
import TradingView from './components/TradingView';
import AuthPage from './pages/AuthPage';
import PortfolioBuilderView from './components/PortfolioBuilderView';
import SettingsView from './components/SettingsView';
import ResearchView from './components/ResearchView';
import FundamentalsView from './components/FundamentalsView';
import ModelTrainingView from './components/ModelTrainingView';
import { PortfolioStorageService } from './services/supabaseClient';
import { AuthProvider, useAuth } from './contexts/AuthContext';

function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0a0b10] text-gray-400">
        <div className="text-center space-y-4">
          <div className="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p>Validating session…</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth" state={{ from: location.pathname }} replace />;
  }

  return children;
}

function AppContent() {
  const [portfolio, setPortfolio] = useState([]);
  const { user } = useAuth();
  const userId = user?.id || user?.email || 'guest';

  useEffect(() => {
    const loadPortfolio = async () => {
      const savedTickers = await PortfolioStorageService.getUserPortfolio(userId);
      setPortfolio(savedTickers || ['AAPL', 'MSFT', 'GOOGL']);
    };
    loadPortfolio();
  }, [userId]);

  const setTickers = (updater) => {
    setPortfolio((prevState) => {
      const nextState = typeof updater === 'function' ? updater(prevState) : updater;
      PortfolioStorageService.saveUserPortfolio(userId, nextState);
      return nextState;
    });
  };

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/auth" element={<AuthPage />} />
      <Route
        path="/dashboard/*"
        element={
          <RequireAuth>
            <DashboardLayout tickers={portfolio} setTickers={setTickers} />
          </RequireAuth>
        }
      >
        <Route index element={<PortfolioDashboard tickers={portfolio} />} />
        <Route path="manage" element={<PortfolioBuilderView tickers={portfolio} setTickers={setTickers} />} />
        <Route path="settings" element={<SettingsView tickers={portfolio} setTickers={setTickers} />} />
        <Route path="research" element={<ResearchView tickers={portfolio} />} />
        <Route path="fundamentals" element={<FundamentalsView tickers={portfolio} />} />
        <Route path="forecast" element={<ForecastingView tickers={portfolio} />} />
        <Route path="sentiment" element={<SentimentView tickers={portfolio} />} />
        <Route path="chat" element={<ChatAdvisor tickers={portfolio} />} />
        <Route path="trading" element={<TradingView tickers={portfolio} />} />
        <Route path="training" element={<ModelTrainingView tickers={portfolio} />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;
