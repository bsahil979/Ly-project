import React, { useState } from 'react';
import Layout from '../components/Layout';
import DashboardOverview from '../components/DashboardOverview';
import ForecastingView from '../components/ForecastingView';
import SentimentView from '../components/SentimentView';
import ChatAdvisor from '../components/ChatAdvisor';

const Dashboard = () => {
  const [currentTab, setCurrentTab] = useState('Overview');
  const [portfolio, setPortfolio] = useState(['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'RELIANCE.NS', 'SPY']);

  const renderContent = () => {
    switch (currentTab) {
      case 'Overview': return <DashboardOverview tickers={portfolio} />;
      case 'Forecasting': return <ForecastingView tickers={portfolio} />;
      case 'Sentiment': return <SentimentView tickers={portfolio} />;
      case 'Chat Advisor': return <ChatAdvisor tickers={portfolio} />;
      default: return <DashboardOverview tickers={portfolio} />;
    }
  };

  return (
    <Layout 
      tickers={portfolio} 
      currentTab={currentTab} 
      setTab={setCurrentTab} 
      onPortfolioUpdate={setPortfolio}
    >
      {renderContent()}
    </Layout>
  );
};

export default Dashboard;
