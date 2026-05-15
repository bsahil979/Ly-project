import React, { useState, useEffect } from 'react';
import { Search, Plus } from 'lucide-react';
import { useLocation } from 'react-router-dom';

const Layout = ({ children, tickers, setTickers }) => {
  const [searchValue, setSearchValue] = React.useState('');
  const [isAdding, setIsAdding] = React.useState(false);
  const [newTicker, setNewTicker] = React.useState('');
  const location = useLocation();

  const getActiveTab = () => {
    const path = location.pathname;
    if (path === '/dashboard') return 'Home';
    if (path.includes('research')) return 'Research';
    if (path.includes('forecast')) return 'Discover';
    if (path.includes('sentiment')) return 'Sentiment Analysis';
    if (path.includes('chat')) return 'AI Chat Bot';
    if (path.includes('trading')) return 'RL Trading Brain';
    if (path.includes('manage')) return 'Watchlist';
    if (path.includes('settings')) return 'Settings';
    return 'Dashboard';
  };

  const getSubtitle = () => {
    const path = location.pathname;
    if (path === '/dashboard') return 'Your portfolio overview & K-Score rankings';
    if (path.includes('research')) return 'Comprehensive multi-model analysis suite';
    if (path.includes('forecast')) return 'LSTM & HMM powered multi-horizon forecasts';
    if (path.includes('sentiment')) return 'Aggregated news & social sentiment analysis';
    if (path.includes('chat')) return 'AI-powered conversational portfolio intelligence';
    if (path.includes('trading')) return 'PPO reinforcement learning BUY / SELL / HOLD decisions';
    if (path.includes('manage')) return 'Curate and manage your tracked instruments';
    if (path.includes('settings')) return 'Account preferences & system configuration';
    return 'Real-time intelligence for your investments';
  };

  const activeTab = getActiveTab();

  const handleAddAsset = (manualTicker) => {
    const ticker = (manualTicker || newTicker || searchValue).toUpperCase().trim();
    if (!ticker) return;
    if (tickers.includes(ticker)) return alert('Asset already in portfolio');
    
    setTickers([...tickers, ticker]);
    setSearchValue('');
    setNewTicker('');
    setIsAdding(false);
  };

  return (
    <div className="ml-64 p-8 min-h-screen">
      <header className="flex justify-between items-center mb-10">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            {activeTab}
          </h1>
          <p className="text-xs text-gray-500 mt-1 font-medium">{getSubtitle()}</p>
        </div>
        
        <div className="flex gap-3 items-center">
          {/* Unified Search Bar */}
          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-indigo-400 transition-colors" />
            <input 
              type="text" 
              placeholder="Search / Add Tickers..." 
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddAsset()}
              className="bg-[#11131a] border border-gray-800/50 rounded-xl py-2.5 pl-10 pr-4 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-600/50 focus:border-indigo-600/50 transition-all w-56 shadow-xl text-white"
            />
          </div>

          {/* Quick Add Asset */}
          <div className="flex items-center gap-2">
            {isAdding ? (
              <div className="flex items-center gap-2 animate-in fade-in slide-in-from-right-2 duration-300">
                <input 
                  autoFocus
                  type="text"
                  placeholder="Ticker..."
                  value={newTicker}
                  onChange={(e) => setNewTicker(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddAsset()}
                  onBlur={() => !newTicker && setIsAdding(false)}
                  className="bg-[#1a1c26] border border-indigo-500/50 rounded-xl py-2 px-3 text-xs w-24 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
                <button 
                  onClick={() => handleAddAsset()}
                  className="p-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl transition-all shadow-lg"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button 
                onClick={() => setIsAdding(true)}
                className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl px-4 py-2.5 text-xs font-bold flex items-center gap-2 transition-all shadow-lg shadow-indigo-600/20 active:scale-95"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Asset
              </button>
            )}
          </div>
        </div>
      </header>
      
      {children}
    </div>
  );
};

export default Layout;
