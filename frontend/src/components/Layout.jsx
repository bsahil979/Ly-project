import React, { useState } from 'react';
import { Search, Plus } from 'lucide-react';
import { useLocation } from 'react-router-dom';

const Layout = ({ children, tickers, setTickers }) => {
  const [searchValue, setSearchValue] = React.useState('');
  const [isAdding, setIsAdding] = React.useState(false);
  const [newTicker, setNewTicker] = React.useState('');
  const location = useLocation();

  const getActiveTab = () => {
    const path = location.pathname;
    if (path === '/dashboard') return 'Overview';
    if (path.includes('forecast')) return 'Forecasting';
    if (path.includes('sentiment')) return 'Sentiment';
    if (path.includes('chat')) return 'Chat Advisor';
    return 'Dashboard';
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
          <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400 uppercase tracking-tight">
            {activeTab}
          </h1>
          <p className="text-gray-400 mt-1">Real-time intelligence for your investments</p>
        </div>
        
        <div className="flex gap-4 items-center">
          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-indigo-400 transition-colors" />
            <input 
              type="text" 
              placeholder="Search / Add Tickers..." 
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAddAsset()}
              className="bg-[#11131a] border border-gray-800/50 rounded-xl py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600/50 focus:border-indigo-600/50 transition-all w-64 shadow-xl"
            />
          </div>

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
                  className="bg-[#1a1c26] border border-indigo-500/50 rounded-xl py-2.5 px-3 text-xs w-24 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
                <button 
                  onClick={() => handleAddAsset()}
                  className="p-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl transition-all shadow-lg"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button 
                onClick={() => setIsAdding(true)}
                className="bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl px-4 py-3 text-sm font-semibold flex items-center gap-2 transition-all shadow-lg shadow-indigo-600/20 active:scale-95"
              >
                <Plus className="w-4 h-4" />
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
