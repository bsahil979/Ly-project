import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, PieChart, Pie, Cell 
} from 'recharts';
import { 
  TrendingUp, TrendingDown, AlertCircle, Zap, Cpu, Activity, Info, RefreshCcw, DollarSign, BarChart, History, Brain, Target, Compass
} from 'lucide-react';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444'];

const TradingView = ({ tickers = [] }) => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [isThinking, setIsThinking] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState(tickers[0] || '');

  const fetchTradingDecision = async (targetTicker) => {
    const sym = targetTicker || selectedAsset;
    if (!sym) return;
    setLoading(true);
    setIsThinking(false);
    setError(null);
    try {
      const response = await axios.get(`http://localhost:8000/trading/decision?ticker=${sym}`);
      if (response.data.status === 'thinking') {
        setIsThinking(true);
        setData(null);
      } else {
        setData(response.data);
      }
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || err.message || 'Brain Sync Error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (tickers.length > 0 && !tickers.includes(selectedAsset)) {
      setSelectedAsset(tickers[0]);
    }
  }, [tickers]);

  useEffect(() => {
    if (!selectedAsset) return;
    fetchTradingDecision(selectedAsset);
  }, [selectedAsset]);

  const getActionStyles = (action) => {
    if (action === 'BUY') return 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20';
    if (action === 'SELL') return 'text-rose-400 bg-rose-400/10 border-rose-400/20';
    return 'text-amber-400 bg-amber-400/10 border-amber-400/20';
  };

  if (tickers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[450px] bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-12 text-center shadow-2xl animate-in fade-in duration-500">
        <div className="w-20 h-20 rounded-3xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-6">
          <Brain className="w-10 h-10 text-indigo-400" />
        </div>
        <h3 className="text-2xl font-black tracking-tight mb-2">No Assets Selected for AI Brain</h3>
        <p className="text-sm text-gray-400 max-w-md mx-auto leading-relaxed font-medium">
          Add ticker symbols using the top navigation header or Asset Studio gallery to activate live multi-tier cognitive reinforcement learning layers.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-700 pb-12">
      {/* Brain Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-600/20">
            <Brain className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-black tracking-tighter uppercase">Adaptive AI Trading Brain</h1>
            <p className="text-gray-400 font-medium">{selectedAsset} · Multi-Tier Cognitive Intelligence Layer</p>
          </div>
        </div>
        <button 
          onClick={() => fetchTradingDecision(selectedAsset)}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 rounded-2xl font-bold transition-all disabled:opacity-50 shadow-xl shadow-indigo-600/20 active:scale-95"
        >
          {loading ? <RefreshCcw className="w-5 h-5 animate-spin" /> : <Zap className="w-5 h-5" />}
          {loading ? 'Thinking...' : 'Analyze Market'}
        </button>
      </div>

      {/* Asset Selector */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        {tickers.map(ticker => (
          <button
            key={ticker}
            onClick={() => setSelectedAsset(ticker)}
            className={`px-4 py-2 rounded-xl font-bold text-sm transition-all whitespace-nowrap border ${selectedAsset === ticker ? 'bg-indigo-600 text-white border-indigo-500 shadow-lg shadow-indigo-600/20' : 'bg-gray-900/40 text-gray-400 border-gray-800 hover:bg-gray-800/60'}`}
          >
            {ticker}
          </button>
        ))}
      </div>

      {loading && !data ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div key={i} className="h-48 bg-gray-900/40 border border-gray-800 animate-pulse rounded-3xl" />
          ))}
        </div>
      ) : data ? (
        <>
          {/* Main Decision & Thinking Layer */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* 1. DECISION (The Final Output) */}
            <div className="p-8 rounded-[2rem] bg-indigo-600/10 border border-indigo-600/20 backdrop-blur-3xl relative overflow-hidden group">
               <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
                  <Brain className="w-64 h-64 -mr-20 -mt-20" />
               </div>
               
               <div className="flex items-center gap-3 mb-6">
                 <Target className="w-5 h-5 text-indigo-400" />
                 <span className="text-xs font-bold uppercase tracking-widest text-indigo-400">Final Decision</span>
               </div>
               
               <div className="space-y-4 relative z-10">
                 <div className={`text-7xl font-black tracking-tighter ${data.decision.action === 'BUY' ? 'text-emerald-400' : (data.decision.action === 'SELL' ? 'text-rose-400' : 'text-amber-400')}`}>
                   {data.decision.action}
                 </div>
                 <div>
                    <div className="text-sm text-gray-400 font-medium tracking-wide">Final Decision</div>
                    <div className="text-lg font-bold flex items-center gap-2">
                      Confidence: {(data.decision.confidence * 100).toFixed(0)}%
                      {data.is_dry_run && <span className="text-[10px] px-2 py-0.5 bg-gray-800 text-gray-400 rounded-lg">DRY RUN</span>}
                    </div>
                  </div>
                 <p className="text-gray-400 text-sm leading-relaxed">
                   The RL Agent policy integrated all multi-model signals and temporal context to select this action.
                 </p>
               </div>
            </div>

            {/* 2. THINKING (Ensemble Signals) */}
            <div className="lg:col-span-2 p-8 rounded-[2rem] bg-gray-900/40 border border-gray-800/50 space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Cpu className="w-5 h-5 text-indigo-400" />
                  <span className="text-xs font-bold uppercase tracking-widest text-gray-400">Intelligence Layers</span>
                </div>
                <div className={`px-4 py-1 rounded-full text-xs font-bold border ${data.decision.is_weekend ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'}`}>
                  {data.decision.is_weekend ? 'WEEKEND MODE · LOW LIQUIDITY' : 'WEEKDAY MODE · NORMAL TRADING'}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {data.decision.reasoning.map((reason, i) => (
                  <div key={i} className="p-4 rounded-2xl bg-gray-800/30 border border-gray-800/50 hover:border-indigo-500/30 transition-all">
                    <p className="text-xs text-gray-300 leading-relaxed font-medium">
                      {reason}
                    </p>
                  </div>
                ))}
              </div>

              <div className="h-[180px] mt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.chart_data}>
                    <XAxis dataKey="Date" hide />
                    <Tooltip contentStyle={{backgroundColor: '#000', border: 'none', borderRadius: '10px'}} />
                    <Area type="monotone" dataKey="Close" stroke="#6366f1" fill="#6366f1" fillOpacity={0.1} strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* PERCEPTION, MEMORY, LEARNING Section */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* 3. PERCEPTION (Real-time Indicators) */}
            <div className="p-8 rounded-[2rem] bg-gray-900/40 border border-gray-800/50">
              <div className="flex items-center gap-3 mb-6">
                <Activity className="w-5 h-5 text-emerald-400" />
                <span className="text-xs font-bold uppercase tracking-widest text-gray-400">Perception Layer</span>
              </div>
              <div className="space-y-6">
                <div className="flex justify-between items-end">
                  <span className="text-gray-400 text-sm">Momentum (RSI)</span>
                  <span className="text-xl font-bold">{data.chart_data[data.chart_data.length-1].rsi.toFixed(1)}</span>
                </div>
                <div className="flex justify-between items-end">
                  <span className="text-gray-400 text-sm">Trend (MACD)</span>
                  <span className={`text-xl font-bold ${data.chart_data[data.chart_data.length-1].macd_diff > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {data.chart_data[data.chart_data.length-1].macd_diff.toFixed(2)}
                  </span>
                </div>
                <div className="flex justify-between items-end">
                  <span className="text-gray-400 text-sm">Advisory Scope</span>
                  <span className="text-xl font-bold uppercase tracking-tighter">{selectedAsset} · LIVE TRACKING</span>
                </div>
                
                <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl mt-4">
                  <div className="text-[10px] font-bold text-indigo-400 uppercase mb-2">Optimal Policy Alignment</div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-400">Action Execution Weight</span>
                    <span className="text-sm font-bold text-emerald-400">{(data.decision.confidence * 2).toFixed(2)}x Target Base</span>
                  </div>
                </div>
              </div>
            </div>

            {/* 4. MEMORY (Historical Archive) */}
            <div className="p-8 rounded-[2rem] bg-gray-900/40 border border-gray-800/50">
              <div className="flex items-center gap-3 mb-6">
                <History className="w-5 h-5 text-amber-400" />
                <span className="text-xs font-bold uppercase tracking-widest text-gray-400">Memory Archive</span>
              </div>
              <div className="space-y-4 h-[120px] overflow-y-auto custom-scrollbar">
                {/* Visualizing small memory blocks */}
                <div className="grid grid-cols-5 gap-2">
                  {Array.from({length: 15}).map((_, i) => (
                    <div key={i} className={`h-8 rounded-lg border ${i % 3 === 0 ? 'bg-emerald-500/10 border-emerald-500/20' : (i % 3 === 1 ? 'bg-rose-500/10 border-rose-500/20' : 'bg-gray-800 border-gray-700')}`} />
                  ))}
                </div>
                <p className="text-xs text-center text-gray-500 italic mt-2">
                  Stored {data.decision.performance.total_trades} trade scenarios in long-term memory.
                </p>
              </div>
            </div>

            {/* 5. LEARNING (Self-Evaluation) */}
            <div className="p-8 rounded-[2rem] bg-gray-900/40 border border-gray-800/50">
              <div className="flex items-center gap-3 mb-6">
                <Compass className="w-5 h-5 text-rose-400" />
                <span className="text-xs font-bold uppercase tracking-widest text-gray-400">Self-Awareness</span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                 <div className="p-4 rounded-2xl bg-gray-800/30 text-center">
                    <div className="text-2xl font-black">{data.decision.performance.win_rate * 100}%</div>
                    <div className="text-[10px] text-gray-500 font-bold uppercase mt-1">Mental Accuracy</div>
                 </div>
                 <div className="p-4 rounded-2xl bg-gray-800/30 text-center">
                    <div className="text-2xl font-black">+{data.decision.performance.avg_profit * 100}%</div>
                    <div className="text-[10px] text-gray-500 font-bold uppercase mt-1">Growth Index</div>
                 </div>
              </div>
              <p className="text-[10px] text-center text-gray-400 mt-4 leading-relaxed font-medium">
                The brain continuously refines its RL policy based on current "Mental Accuracy" feedback loop.
              </p>
            </div>
          </div>
        </>
      ) : isThinking ? (
        <div className="bg-slate-900/50 border border-indigo-500/30 rounded-[3rem] p-20 flex flex-col items-center justify-center text-center backdrop-blur-xl">
          <div className="relative mb-8">
            <div className="absolute inset-0 bg-indigo-500/20 rounded-full blur-3xl animate-pulse"></div>
            <Brain className="w-24 h-24 text-indigo-400 animate-bounce relative z-10" />
          </div>
          <h2 className="text-4xl font-black text-white mb-4 tracking-tighter uppercase">Neural Link Syncing...</h2>
          <p className="text-slate-400 max-w-md mx-auto text-lg font-medium leading-relaxed">
            The Brain is loading its 5-minute memory and training its neural pathways for instant scalping.
            <br/><br/>
            This happens once on startup. <span className="text-indigo-400 font-bold italic">Stay tuned...</span>
          </p>
          <button 
            onClick={fetchTradingDecision}
            disabled={loading}
            className="mt-10 px-10 py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl font-bold transition-all flex items-center gap-3 shadow-xl shadow-indigo-600/20"
          >
            <RefreshCcw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Analyzing Neural Pathways...' : 'Check Sync Status'}
          </button>
        </div>
      ) : (
        <div className="p-20 text-center bg-gray-900/40 border border-gray-800/50 rounded-[3rem] backdrop-blur-xl">
           <AlertCircle className="w-16 h-16 text-rose-500 mx-auto mb-6 opacity-20" />
          <h2 className="text-2xl font-bold mb-2">Neural Link Failed</h2>
          <p className="text-gray-500 max-w-sm mx-auto">{error || 'Unknown biological error in the trading brain.'}</p>
          <button onClick={fetchTradingDecision} className="mt-8 px-8 py-3 bg-gray-800 hover:bg-gray-700 rounded-2xl font-bold transition-all">
            Reconnect Brain
          </button>
        </div>
      )}
    </div>
  );
};

export default TradingView;
