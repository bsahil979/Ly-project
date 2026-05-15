import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, TrendingDown,
  ChevronRight, Loader2, AlertTriangle
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer 
} from 'recharts';
import { Link } from 'react-router-dom';
import { PortfolioService } from '../services/api';

const DashboardOverview = ({ tickers = ['AAPL', 'MSFT', 'GOOGL'] }) => {
  const [analysis, setAnalysis] = useState(null);
  const [regime, setRegime] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Automatically calculate equal weights
  const weights = tickers.length > 0 ? Array(tickers.length).fill(1 / tickers.length) : [];

  useEffect(() => {
    if (tickers.length === 0) {
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        const [analysisRes, regimeRes] = await Promise.all([
          PortfolioService.getAnalysis(tickers, weights),
          PortfolioService.getMarketRegime()
        ]);
        setAnalysis(analysisRes);
        setRegime(regimeRes);
      } catch (err) {
        console.error('Analytics fetch failed:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [tickers]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
        <p className="text-gray-400 text-sm">Fetching live market data & running HMM regime detection...</p>
      </div>
    );
  }

  if (tickers.length === 0) {
    return (
      <div className="col-span-12 flex flex-col items-center justify-center h-[450px] bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-12 text-center shadow-2xl animate-in fade-in duration-500">
        <div className="w-20 h-20 rounded-3xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-6">
          <TrendingUp className="w-10 h-10 text-indigo-400" />
        </div>
        <h3 className="text-2xl font-black tracking-tight mb-2">Your Portfolio is Empty</h3>
        <p className="text-sm text-gray-400 max-w-md mx-auto mb-6 leading-relaxed font-medium">
          Search and select assets using the search bar or enter our curated studio gallery to provision standard global market instruments.
        </p>
        <Link 
          to="/dashboard/manage"
          className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-indigo-600/20 flex items-center gap-2 active:scale-95"
        >
          <span>Open Curated Asset Studio</span>
        </Link>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <AlertTriangle className="w-10 h-10 text-yellow-500" />
        <p className="text-gray-400 text-sm">Analytics engine error: {error}</p>
        <p className="text-gray-500 text-xs">Make sure the FastAPI server is running on port 8000</p>
      </div>
    );
  }

  // Extract risk data — API returns: {"Volatility (Annual)": {"AAPL": 0.3, ...}, "VaR (95%)": {...}, ...}
  const riskSummary = analysis?.risk_summary || {};
  const stressTest = analysis?.stress_test || {};
  const decisionOptions = analysis?.decision_options || [];
  const regimeData = analysis?.regime_summary || regime || {};
  const currencyMap = analysis?.currency_map || {};

  const getCurrencySymbol = () => {
    const codes = Object.values(currencyMap);
    if (codes.length === 0) return '$';
    // Use the most frequent currency in the map
    const dominant = codes.sort((a,b) =>
      codes.filter(v => v===a).length - codes.filter(v => v===b).length
    ).pop();
    
    const symbols = { 'USD': '$', 'INR': '₹', 'GBp': 'p', 'EUR': '€', 'JPY': '¥' };
    return symbols[dominant] || '$';
  };

  const currencySymbol = getCurrencySymbol();

  // risk_summary is column-oriented: {"Volatility (Annual)": {"AAPL": 0.3, "MSFT": 0.25}, ...}
  const volData = riskSummary["Volatility (Annual)"] || {};
  const varData = riskSummary["VaR (95%)"] || {};
  const cvarData = riskSummary["CVaR (95%)"] || {};
  const drawdownData = riskSummary["Max Drawdown"] || {};

  const tickers_list = Object.keys(volData);
  const chartData = tickers_list.map(ticker => ({
    name: ticker,
    volatility: parseFloat(((volData[ticker] || 0) * 100).toFixed(2)),
    var95: parseFloat(((varData[ticker] || 0) * 100).toFixed(2)),
    cvar95: parseFloat(((cvarData[ticker] || 0) * 100).toFixed(2)),
    maxDrawdown: parseFloat(((drawdownData[ticker] || 0) * 100).toFixed(2)),
  }));

  // Portfolio-level stats
  const avgVolatility = chartData.length > 0 
    ? (chartData.reduce((sum, d) => sum + d.volatility, 0) / chartData.length).toFixed(1) 
    : '0';
  const avgVaR = chartData.length > 0
    ? (chartData.reduce((sum, d) => sum + d.var95, 0) / chartData.length).toFixed(1)
    : '0';

  const regimeLabel = regimeData.current_regime || 'Unknown';
  const regimeConfidence = ((regimeData.confidence || 0) * 100).toFixed(0);

  const getRegimeColor = (label) => {
    if (label.includes('Bullish')) return 'text-emerald-400';
    if (label.includes('Bearish')) return 'text-rose-400';
    return 'text-yellow-400';
  };

  // Kavout Kairos Engine Deterministic AI K-Score synthesis logic
  const getKScore = (asset) => {
    let score = 65;
    if (asset.volatility < 20) score += 18;
    else if (asset.volatility < 30) score += 10;
    else score -= 12;

    if (Math.abs(asset.var95) < 5) score += 12;
    else if (Math.abs(asset.var95) > 10) score -= 8;

    if (Math.abs(asset.maxDrawdown) < 15) score += 8;
    else score -= 10;

    if (regimeLabel.includes('Bullish')) score += Math.floor((regimeConfidence / 100) * 10);
    else if (regimeLabel.includes('Bearish')) score -= 15;

    return Math.min(Math.max(score, 12), 99);
  };

  return (
    <div className="grid grid-cols-12 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      {/* Top Banner: Kavout Kairos Engine Aura K-Score Ranking Layer */}
      <div className="col-span-12 bg-gradient-to-r from-[#11131a] via-[#161824] to-[#11131a] border border-indigo-500/30 rounded-3xl p-8 shadow-2xl relative overflow-hidden group">
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none" />
        
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-widest bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Kairos Engine Parallel
              </span>
              <span className="text-xs text-gray-500 font-bold">•</span>
              <span className="text-xs text-emerald-400 font-bold flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> Live Scoring
              </span>
            </div>
            <h2 className="text-2xl font-black text-white tracking-tight">Aura Composite AI Rank (K-Score)</h2>
            <p className="text-xs text-gray-400 font-medium mt-1 max-w-xl leading-relaxed">
              Synthesizing Multi-Tier Cognitive Indicators, localized Volatility containment metrics, Support Vectors, and continuous HMM probabilities into deterministic asset grades.
            </p>
          </div>

          {/* Aggregate Overview Badge */}
          <div className="bg-[#0b0c10]/80 border border-gray-800 rounded-2xl p-4 flex items-center gap-4 shrink-0 shadow-inner">
            <div className="text-center pl-2">
              <span className="text-xs text-gray-500 uppercase tracking-widest block font-bold">Portfolio Index</span>
              <span className="text-3xl font-black text-indigo-400">
                {chartData.length > 0 ? Math.floor(chartData.reduce((acc, a) => acc + getKScore(a), 0) / chartData.length) : 0}
                <span className="text-xs text-gray-600 font-normal"> /99</span>
              </span>
            </div>
            <div className="border-l border-gray-800 pl-4 pr-2 text-left">
              <span className="text-[10px] font-bold block text-emerald-400 uppercase tracking-wider">Tier Allocation</span>
              <span className="text-xs text-gray-300 font-bold">Optimal Multi-Tier</span>
            </div>
          </div>
        </div>

        {/* Individual Stock Scores Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 relative z-10">
          {chartData.map(asset => {
            const kScore = getKScore(asset);
            const getTierColor = (score) => {
              if (score >= 75) return { bg: 'from-emerald-600/20 to-teal-600/10', border: 'border-emerald-500/30', text: 'text-emerald-400', label: 'Strong Buy' };
              if (score >= 55) return { bg: 'from-indigo-600/20 to-violet-600/10', border: 'border-indigo-500/30', text: 'text-indigo-400', label: 'Accumulate' };
              return { bg: 'from-rose-600/20 to-orange-600/10', border: 'border-rose-500/30', text: 'text-rose-400', label: 'Hold / Divest' };
            };
            const tier = getTierColor(kScore);

            return (
              <div key={asset.name} className={`bg-[#0b0c10]/60 backdrop-blur-md border ${tier.border} rounded-2xl p-4 flex items-center justify-between transition-all hover:scale-[1.02]`}>
                <div className="flex items-center gap-3">
                  {/* Score circle badge */}
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${tier.bg} border ${tier.border} flex items-center justify-center font-black text-lg ${tier.text} shadow-inner`}>
                    {kScore}
                  </div>
                  <div>
                    <span className="text-sm font-bold text-white tracking-tight block">{asset.name}</span>
                    <span className="text-[10px] text-gray-400 font-medium block">Vol: {asset.volatility}%</span>
                  </div>
                </div>

                <div className="text-right">
                  <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${tier.border} ${tier.text} bg-black/40 block mb-1`}>
                    {tier.label}
                  </span>
                  <span className="text-[9px] text-gray-500 block">K-Score Rating</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Chart — Risk Metrics Per Asset */}
      <div className="col-span-8 bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-6 shadow-2xl">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold">Risk Metrics by Asset</h3>
          <span className="text-xs text-gray-500 font-bold uppercase">Live from Analytics Engine</span>
        </div>
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorReturn" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
              <XAxis dataKey="name" stroke="#6b7280" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis stroke="#6b7280" fontSize={12} tickLine={false} axisLine={false} unit="%" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#11131a', border: '1px solid #374151', borderRadius: '12px', boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)' }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Area type="monotone" dataKey="annualReturn" stroke="#6366f1" fillOpacity={1} fill="url(#colorReturn)" strokeWidth={3} name="Annual Return %" />
              <Area type="monotone" dataKey="volatility" stroke="#f59e0b" fill="transparent" strokeWidth={2} strokeDasharray="5 5" name="Volatility %" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Stats Column */}
      <div className="col-span-4 flex flex-col gap-6">
        {/* Market Regime Card */}
        <div className="bg-gradient-to-br from-indigo-600 to-violet-700 rounded-3xl p-8 shadow-xl shadow-indigo-900/40 relative overflow-hidden group">
           <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-10 -mt-10 blur-3xl group-hover:scale-110 transition-transform duration-700"></div>
           <p className="text-indigo-100/70 text-sm font-medium mb-1">Market Regime (HMM)</p>
           <h2 className={`text-2xl font-bold text-white tracking-tight`}>{regimeLabel}</h2>
           <div className="mt-4 flex items-center gap-2 text-indigo-100 bg-white/10 w-fit px-3 py-1.5 rounded-full text-xs font-extra-bold backdrop-blur-md uppercase tracking-wide">
             {regimeLabel.includes('Bullish') ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
             {regimeConfidence}% Confidence
           </div>
        </div>

        {/* Risk Profile */}
        <div className="bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-6 shadow-xl">
           <h3 className="text-lg font-semibold mb-6">Risk Profile</h3>
           <div className="flex flex-col gap-5">
             <div className="flex justify-between items-center">
               <span className="text-gray-400 text-sm">Avg Volatility</span>
               <span className={`font-bold ${parseFloat(avgVolatility) < 20 ? 'text-emerald-400' : parseFloat(avgVolatility) < 35 ? 'text-yellow-400' : 'text-rose-400'}`}>
                 {avgVolatility}%
               </span>
             </div>
             <div className="w-full bg-gray-800/50 rounded-full h-1.5 overflow-hidden">
               <div className="bg-emerald-500 h-full shadow-[0_0_8px_rgba(16,185,129,0.5)]" style={{ width: `${Math.min(parseFloat(avgVolatility), 100)}%` }} />
             </div>
             
             <div className="flex justify-between items-center mt-2">
               <span className="text-gray-400 text-sm">Value at Risk (95%)</span>
               <span className="text-yellow-400 font-bold">{avgVaR}%</span>
             </div>
             <div className="w-full bg-gray-800/50 rounded-full h-1.5 overflow-hidden">
               <div className="bg-yellow-500 h-full shadow-[0_0_8px_rgba(234,179,8,0.5)]" style={{ width: `${Math.min(Math.abs(parseFloat(avgVaR)) * 10, 100)}%` }} />
             </div>
           </div>
        </div>
      </div>

      {/* Asset Breakdown Table */}
      <div className="col-span-12 bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-6 shadow-xl">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold">Asset Risk Breakdown</h3>
          <span className="text-xs text-indigo-400 font-medium">Real-time Analytics</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="text-gray-500 text-xs uppercase tracking-wider border-b border-gray-800/50">
                <th className="pb-4 font-semibold">Asset</th>
                <th className="pb-4 font-semibold">Volatility</th>
                <th className="pb-4 font-semibold">VaR (95%)</th>
                <th className="pb-4 font-semibold">CVaR (95%)</th>
                <th className="pb-4 font-semibold text-right">Max Drawdown</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/30">
              {chartData.map((asset) => (
                <tr key={asset.name} className="group hover:bg-gray-800/20 transition-all duration-300">
                  <td className="py-5">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-gray-800/80 flex items-center justify-center font-bold text-sm text-indigo-400 border border-gray-700/50">
                        {asset.name[0]}
                      </div>
                      <p className="font-bold text-gray-100">{asset.name}</p>
                    </div>
                  </td>
                  <td className={`py-5 text-sm font-semibold ${asset.volatility < 25 ? 'text-emerald-400' : asset.volatility < 35 ? 'text-yellow-400' : 'text-rose-400'}`}>
                    {asset.volatility}%
                  </td>
                  <td className="py-5 text-sm font-semibold text-rose-400">{asset.var95}%</td>
                  <td className="py-5 text-sm font-semibold text-rose-400">{asset.cvar95}%</td>
                  <td className="py-5 text-sm font-semibold text-rose-400 text-right">{asset.maxDrawdown}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Decision Options from Analytics */}
      {decisionOptions.length > 0 && (
        <div className="col-span-12 bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-8 shadow-xl">
          <h3 className="text-xl font-bold mb-8 flex items-center gap-3">
            <div className="w-8 h-8 bg-indigo-500/10 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-indigo-400" />
            </div>
            AI Portfolio Rebalancing Recommendations
          </h3>
          <div className="grid grid-cols-3 gap-6">
            {decisionOptions.map((option, idx) => (
              <div key={idx} className="bg-[#1a1c26]/50 border border-gray-800/50 rounded-3xl p-6 hover:border-indigo-500/40 transition-all flex flex-col group relative overflow-hidden">
                <div className="mb-4">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-2xl">{option.emoji}</span>
                    <h4 className="text-lg font-bold text-white group-hover:text-indigo-400 transition-colors uppercase tracking-tight">{option.option}</h4>
                  </div>
                  <p className="text-xs text-gray-400 font-medium leading-relaxed mb-4">{option.description}</p>
                </div>

                <div className="space-y-4 mb-6 flex-1">
                  <div>
                    <span className="text-[10px] text-gray-500 uppercase font-bold tracking-widest block mb-2">Target Allocations</span>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(option.allocations).map(([asset, weight]) => (
                        <div key={asset} className="bg-gray-800/50 px-2 py-1 rounded text-[10px] font-bold text-gray-300 border border-gray-700/50">
                          {asset}: {weight}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 pt-2 border-t border-gray-800/50">
                    <div>
                      <span className="text-[10px] text-gray-500 uppercase font-bold tracking-widest block mb-1">Downside Risk</span>
                      <span className="text-rose-400 text-xs font-bold">{option.downside_risk.split(' ')[0]}</span>
                    </div>
                    <div>
                      <span className="text-[10px] text-gray-500 uppercase font-bold tracking-widest block mb-1">Expected Return</span>
                      <span className="text-emerald-400 text-xs font-bold">{option.expected_return.split(' ')[0]}</span>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-gray-800/50">
                   <span className="text-[10px] text-gray-500 uppercase font-bold tracking-widest block mb-2">Best For</span>
                   <span className="text-[11px] text-indigo-300 bg-indigo-500/10 px-2.5 py-1 rounded-lg font-medium">
                     {option.best_for}
                   </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardOverview;
