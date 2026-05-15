import React, { useState } from 'react';
import { 
  Search, Plus, Check, X, TrendingUp, Layers, 
  Sparkles, ArrowRight, Zap, Globe, Coins, Building2 
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

// Pre-defined popular curated global lists with visual metadata
const CURATED_ASSETS = [
  // Tech Giants
  { symbol: 'AAPL', name: 'Apple Inc.', category: 'Tech Giants', icon: '🍏', description: 'Consumer electronics and software services.' },
  { symbol: 'MSFT', name: 'Microsoft Corp.', category: 'Tech Giants', icon: '🪟', description: 'Cloud computing, AI, and enterprise software.' },
  { symbol: 'GOOGL', name: 'Alphabet Inc.', category: 'Tech Giants', icon: '🔍', description: 'Search engine, online advertising, and cloud infrastructure.' },
  { symbol: 'NVDA', name: 'NVIDIA Corp.', category: 'Tech Giants', icon: '🎮', description: 'High-performance GPU accelerators for Artificial Intelligence.' },
  { symbol: 'AMZN', name: 'Amazon.com Inc.', category: 'Tech Giants', icon: '📦', description: 'E-commerce logistics powerhouse and AWS hosting.' },
  
  // Cryptocurrencies
  { symbol: 'BTC-USD', name: 'Bitcoin USD', category: 'Crypto', icon: '₿', description: 'Decentralized digital gold asset store of value.' },
  { symbol: 'ETH-USD', name: 'Ethereum USD', category: 'Crypto', icon: 'Ξ', description: 'Smart contract engine backing decentralized finance pipelines.' },
  { symbol: 'SOL-USD', name: 'Solana USD', category: 'Crypto', icon: '☀️', description: 'High-throughput layer-1 blockchain architecture.' },

  // Emerging Markets (India)
  { symbol: 'RELIANCE.NS', name: 'Reliance Industries', category: 'India Equities', icon: '🇮🇳', description: 'Conglomerate spanning energy, petrochemicals, and retail networks.' },
  { symbol: 'TCS.NS', name: 'Tata Consultancy', category: 'India Equities', icon: '💻', description: 'Global IT consulting, software execution, and digital transformation.' },
  { symbol: 'INFY.NS', name: 'Infosys Limited', category: 'India Equities', icon: '🌐', description: 'Next-generation digital services and consulting framework.' },
  { symbol: 'HDFCBANK.NS', name: 'HDFC Bank Ltd', category: 'India Equities', icon: '🏦', description: 'India’s pre-eminent private sector banking corporate.' },
  { symbol: 'TATAMOTORS.NS', name: 'Tata Motors Limited', category: 'India Equities', icon: '🚗', description: 'Automotive manufacturing covering EV transformations.' },

  // ETFs & Indices
  { symbol: 'SPY', name: 'SPDR S&P 500 ETF', category: 'ETFs & Indices', icon: '📈', description: 'Tracks the performance of the top 500 US publicly traded blue chips.' },
  { symbol: 'QQQ', name: 'Invesco QQQ Trust', category: 'ETFs & Indices', icon: '🚀', description: 'Heavily tech-weighted index monitoring non-financial Nasdaq leaders.' },
  { symbol: 'DIA', name: 'Dow Jones ETF', category: 'ETFs & Indices', icon: '🏗️', description: 'Measures industrial leaders scaling traditional value sectors.' }
];

const CATEGORIES = ['All Assets', 'Tech Giants', 'Crypto', 'India Equities', 'ETFs & Indices'];

const PortfolioBuilderView = ({ tickers, setTickers }) => {
  const [activeCategory, setActiveCategory] = useState('All Assets');
  const [searchQuery, setSearchQuery] = useState('');
  const [customTicker, setCustomTicker] = useState('');
  const navigate = useNavigate();

  // Helper toggle
  const toggleAsset = (symbol) => {
    if (tickers.includes(symbol)) {
      setTickers(tickers.filter(t => t !== symbol));
    } else {
      setTickers([...tickers, symbol]);
    }
  };

  // Add custom manual asset
  const handleAddCustom = (e) => {
    e?.preventDefault();
    const cleanSymbol = customTicker.toUpperCase().trim();
    if (!cleanSymbol) return;
    if (tickers.includes(cleanSymbol)) {
      setCustomTicker('');
      return;
    }
    setTickers([...tickers, cleanSymbol]);
    setCustomTicker('');
  };

  // Filter implementation
  const filteredAssets = CURATED_ASSETS.filter(asset => {
    const matchesCategory = activeCategory === 'All Assets' || asset.category === activeCategory;
    const matchesSearch = asset.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          asset.name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="grid grid-cols-12 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      {/* Header Banner */}
      <div className="col-span-12 bg-gradient-to-r from-[#161923] via-[#11131a] to-[#161923] border border-gray-800/60 rounded-3xl p-8 relative overflow-hidden shadow-2xl">
         <div className="absolute top-0 right-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-[100px] pointer-events-none -z-10" />
         <div className="max-w-3xl">
           <span className="inline-flex items-center gap-1.5 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1 rounded-full text-indigo-400 text-xs font-bold uppercase tracking-widest mb-4">
             <Zap className="w-3 h-3" /> Intuitive Provisioning Sector
           </span>
           <h2 className="text-3xl font-black tracking-tight mb-2">Curated Asset Studio</h2>
           <p className="text-sm text-gray-400 leading-relaxed font-medium">
             Instantly insert premium standard assets into your synchronized Supabase account ledger. Browse category silos, filter instruments interactively, or register specific global stock symbols manually.
           </p>
         </div>
      </div>

      {/* Main Studio Catalog Left Section */}
      <div className="col-span-12 lg:col-span-8 flex flex-col gap-6">
         
         {/* Live Search & Category Toolbar */}
         <div className="bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-2xl p-4 flex flex-col md:flex-row gap-4 items-center justify-between shadow-xl">
            {/* Search Input */}
            <div className="relative w-full md:w-72">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search popular assets..."
                className="w-full bg-[#161822] border border-gray-800 rounded-xl pl-9 pr-4 py-2.5 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 transition-colors"
              />
              {searchQuery && (
                <button onClick={() => setSearchQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white">
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Interactive Tab Selectors */}
            <div className="flex flex-wrap gap-1 w-full md:w-auto justify-start">
              {CATEGORIES.map(cat => (
                <button
                  key={cat}
                  onClick={() => setActiveCategory(cat)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                    activeCategory === cat
                      ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20'
                      : 'text-gray-400 hover:bg-gray-800/60 hover:text-gray-200'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
         </div>

         {/* Curated Grid Display */}
         <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredAssets.length > 0 ? (
              filteredAssets.map(asset => {
                const isSelected = tickers.includes(asset.symbol);
                return (
                  <div 
                    key={asset.symbol}
                    onClick={() => toggleAsset(asset.symbol)}
                    className={`p-5 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between group relative overflow-hidden ${
                      isSelected 
                        ? 'bg-indigo-600/10 border-indigo-500/40 shadow-xl shadow-indigo-500/5' 
                        : 'bg-[#11131a]/60 border-gray-800/40 hover:border-gray-700/60 hover:bg-[#11131a]'
                    }`}
                  >
                    <div>
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex items-center gap-3">
                          <span className="text-2xl select-none">{asset.icon}</span>
                          <div>
                            <h4 className="text-sm font-bold text-white tracking-tight group-hover:text-indigo-400 transition-colors">
                              {asset.symbol}
                            </h4>
                            <span className="text-[10px] text-gray-500 font-medium block truncate max-w-[140px]">
                              {asset.name}
                            </span>
                          </div>
                        </div>

                        <button 
                          className={`w-7 h-7 rounded-xl flex items-center justify-center text-xs font-bold transition-all ${
                            isSelected 
                              ? 'bg-emerald-500 text-white shadow-md shadow-emerald-500/20' 
                              : 'bg-gray-800/80 text-gray-400 group-hover:bg-indigo-600 group-hover:text-white'
                          }`}
                        >
                          {isSelected ? <Check className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
                        </button>
                      </div>

                      <p className="text-xs text-gray-400 font-medium leading-relaxed mt-1">
                        {asset.description}
                      </p>
                    </div>

                    <div className="mt-4 pt-3 border-t border-gray-800/40 flex items-center justify-between">
                      <span className="text-[9px] text-gray-500 uppercase font-bold tracking-widest">
                        {asset.category}
                      </span>
                      <span className={`text-[9px] px-2 py-0.5 rounded font-bold uppercase tracking-wider ${
                        isSelected ? 'bg-emerald-500/10 text-emerald-400' : 'bg-gray-800 text-gray-500'
                      }`}>
                        {isSelected ? 'Provisioned' : 'Available'}
                      </span>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="col-span-2 p-12 text-center bg-[#11131a]/40 border border-gray-800/40 rounded-2xl">
                <p className="text-xs text-gray-500">No popular assets match your explicit filter constraints.</p>
              </div>
            )}
         </div>
      </div>

      {/* Right Sub-Panel: Custom Input & Active Ledger Manifest */}
      <div className="col-span-12 lg:col-span-4 flex flex-col gap-6">
         
         {/* Live Custom Ticker Input Box */}
         <div className="bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-6 shadow-xl">
            <h3 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-2 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              Manual Instrument Search
            </h3>
            <p className="text-xs text-gray-500 mb-4 font-medium">
              Want an asset not listed? Type its specific exchange code (e.g. <span className="text-indigo-400 font-mono">TSLA</span> or <span className="text-indigo-400 font-mono">META</span>) below.
            </p>

            <form onSubmit={handleAddCustom} className="flex gap-2">
              <input
                type="text"
                value={customTicker}
                onChange={(e) => setCustomTicker(e.target.value)}
                placeholder="Enter ticker symbol..."
                className="w-full bg-[#161822] border border-gray-800 rounded-xl px-3 py-2.5 text-xs text-white uppercase focus:outline-none focus:border-indigo-500 transition-colors"
              />
              <button
                type="submit"
                className="px-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-indigo-600/20 shrink-0"
              >
                Add
              </button>
            </form>
         </div>

         {/* Active Tickers Manifest Container */}
         <div className="bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-6 shadow-xl flex-1 flex flex-col justify-between">
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-bold uppercase tracking-wider text-gray-200">
                  Active Manifest
                </h3>
                <span className="px-2 py-0.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-full text-[10px] font-bold">
                  {tickers.length} {tickers.length === 1 ? 'Asset' : 'Assets'}
                </span>
              </div>

              {tickers.length > 0 ? (
                <div className="space-y-2 max-h-[260px] overflow-y-auto pr-1 custom-scrollbar">
                  {tickers.map(sym => {
                    const known = CURATED_ASSETS.find(a => a.symbol === sym);
                    return (
                      <div 
                        key={sym} 
                        className="flex items-center justify-between p-2.5 bg-gray-800/30 rounded-xl border border-gray-800/50 group"
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <span className="text-sm shrink-0">{known?.icon || '📊'}</span>
                          <span className="text-xs font-bold text-white tracking-tight block truncate">
                            {sym}
                          </span>
                        </div>
                        <button
                          onClick={() => toggleAsset(sym)}
                          title="Remove Asset"
                          className="p-1 hover:bg-rose-500/10 text-gray-500 hover:text-rose-400 rounded transition-colors"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="p-8 text-center border border-dashed border-gray-800/60 rounded-2xl my-2">
                  <p className="text-xs text-gray-600 font-medium">Your tracking ground is entirely clear.</p>
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-gray-800/60 mt-4">
              <button
                onClick={() => navigate('/dashboard')}
                disabled={tickers.length === 0}
                className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-600/30 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-indigo-600/20 flex items-center justify-center gap-2 active:scale-98"
              >
                <span>Confirm & Execute Matrix</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
         </div>
      </div>
    </div>
  );
};

export default PortfolioBuilderView;
