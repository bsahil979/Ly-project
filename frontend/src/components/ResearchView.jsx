import React from 'react';
import { Link } from 'react-router-dom';
import { 
  BarChart3, CheckCircle2, ArrowRight, Sparkles
} from 'lucide-react';

const ResearchView = ({ tickers = [] }) => {

  // Top row: feature summary cards matching actual project tech stack
  const topCards = [
    {
      title: 'VADER Sentiment Engine',
      path: '/dashboard/sentiment',
      color: 'indigo',
      description: 'Multi-source news sentiment aggregation powered by Yahoo Finance & GNews feeds. VADER NLP scoring quantifies bullish/bearish emotional intensity across each tracked instrument.',
      features: [
        'Yahoo Finance + GNews dual-source aggregation',
        'VADER NLP compound sentiment scoring',
        'Bullish vs Bearish polarity distribution',
      ],
    },
    {
      title: 'LSTM + HMM Forecaster',
      path: '/dashboard/forecast',
      color: 'emerald',
      description: 'Deep learning LSTM neural networks generate multi-day price trajectory forecasts. Hidden Markov Models detect current market regime probabilities across your portfolio.',
      features: [
        'PyTorch LSTM 2-layer price forecasting',
        'Gaussian HMM regime detection (Bull/Bear/Neutral)',
        'Monte Carlo VaR & CVaR risk quantification',
      ],
    },
    {
      title: 'RL Decision Brain',
      path: '/dashboard/trading',
      color: 'purple',
      description: 'PPO Reinforcement Learning agent trained via Stable-Baselines3 integrates RSI, MACD, ADX, volatility, and all ensemble model signals to output optimal BUY/SELL/HOLD policy actions.',
      features: [
        'PPO policy gradient agent (Stable-Baselines3)',
        'Multi-signal ensemble: LSTM + RF + HMM inputs',
        'Confidence-weighted action with memory archive',
      ],
    },
  ];

  // Bottom row: detailed named tool cards
  const bottomCards = [
    {
      emoji: '📰',
      title: 'News Sentiment Tracker',
      path: '/dashboard/sentiment',
      description: 'Real-time emotional pulse detection from financial news. Each headline is scored by VADER\'s compound algorithm and aggregated into per-ticker sentiment gauges with source attribution.',
      features: [
        'Per-article compound sentiment scores',
        'Source-attributed headline breakdowns',
        'Trending topic & keyword extraction',
      ],
    },
    {
      emoji: '📈',
      title: 'Quantitative Risk Analyzer',
      path: '/dashboard/forecast',
      description: 'Portfolio-level risk decomposition engine. Calculates annualized volatility, Value at Risk (VaR 95%), Conditional VaR, max drawdown, and outputs AI rebalancing strategy recommendations.',
      features: [
        'Annualized volatility & max drawdown per asset',
        'Monte Carlo VaR (95%) & CVaR stress testing',
        'AI-generated rebalancing strategy options',
      ],
    },
    {
      emoji: '🧠',
      title: 'Adaptive RL Policy Viewer',
      path: '/dashboard/trading',
      description: 'Inspect the Reinforcement Learning agent\'s live decision pipeline. View the multi-tier cognitive layers: Perception (RSI/MACD), Thinking (ensemble signals), Memory (trade archive), and Self-Awareness (win rate).',
      features: [
        'Live perception layer: RSI, MACD, ADX indicators',
        'Decision confidence with reasoning traces',
        'Historical memory archive & mental accuracy',
      ],
    },
  ];

  const getColorClasses = (color) => {
    const map = {
      indigo: {
        border: 'border-indigo-500/20 hover:border-indigo-500/40',
        accent: 'text-indigo-400',
        gradient: 'from-indigo-600/20 to-transparent',
        glow: 'shadow-indigo-500/5',
      },
      emerald: {
        border: 'border-emerald-500/20 hover:border-emerald-500/40',
        accent: 'text-emerald-400',
        gradient: 'from-emerald-600/20 to-transparent',
        glow: 'shadow-emerald-500/5',
      },
      purple: {
        border: 'border-purple-500/20 hover:border-purple-500/40',
        accent: 'text-purple-400',
        gradient: 'from-purple-600/20 to-transparent',
        glow: 'shadow-purple-500/5',
      },
    };
    return map[color] || map.indigo;
  };

  if (tickers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[450px] bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-12 text-center shadow-2xl animate-in fade-in duration-500">
        <div className="w-20 h-20 rounded-3xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-6">
          <BarChart3 className="w-10 h-10 text-indigo-400" />
        </div>
        <h3 className="text-2xl font-black tracking-tight mb-2">No Assets to Research</h3>
        <p className="text-sm text-gray-400 max-w-md mx-auto mb-6 leading-relaxed font-medium">
          Add ticker symbols to your watchlist first. Each research tool below will analyze your active portfolio instruments.
        </p>
        <Link 
          to="/dashboard/manage"
          className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-indigo-600/20 flex items-center gap-2 active:scale-95"
        >
          <span>Open Watchlist Manager</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-12">

      {/* Hero Description */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-widest bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            Research Hub
          </span>
          <span className="text-xs text-gray-500 font-bold">•</span>
          <span className="text-xs text-emerald-400 font-bold flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" /> {tickers.length} Active Instruments
          </span>
        </div>
        <p className="text-sm text-gray-400 max-w-2xl leading-relaxed">
          Multi-model analysis suite integrating LSTM forecasting, HMM regime detection, VADER sentiment NLP, Random Forest classification, and PPO Reinforcement Learning agents.
        </p>
      </div>

      {/* Top Row: Tech Stack Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {topCards.map((card, idx) => {
          const c = getColorClasses(card.color);
          return (
            <Link
              key={idx}
              to={card.path}
              className={`group block bg-[#11131a]/80 backdrop-blur-xl border ${c.border} rounded-2xl p-6 shadow-xl ${c.glow} transition-all duration-300 hover:scale-[1.02] hover:shadow-2xl relative overflow-hidden`}
            >
              <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${c.gradient} rounded-t-2xl`} />
              
              <p className="text-xs text-gray-400 leading-relaxed mb-5 min-h-[72px]">
                {card.description}
              </p>

              <div className="space-y-2.5">
                {card.features.map((feature, fIdx) => (
                  <div key={fIdx} className="flex items-start gap-2.5">
                    <CheckCircle2 className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${c.accent}`} />
                    <span className="text-xs text-gray-300 font-medium leading-relaxed">{feature}</span>
                  </div>
                ))}
              </div>
            </Link>
          );
        })}
      </div>

      {/* Divider */}
      <div className="flex items-center gap-4">
        <div className="flex-1 border-t border-gray-800/40" />
        <span className="w-2 h-2 rounded-full bg-indigo-500/40" />
        <div className="flex-1 border-t border-gray-800/40" />
      </div>

      {/* Bottom Row: Named Tool Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {bottomCards.map((card, idx) => (
          <Link
            key={idx}
            to={card.path}
            className="group block bg-[#11131a]/60 backdrop-blur-xl border border-gray-800/50 hover:border-gray-700/60 rounded-2xl p-6 shadow-lg transition-all duration-300 hover:scale-[1.02] hover:shadow-xl"
          >
            <div className="flex items-center gap-3 mb-4">
              <span className="text-xl">{card.emoji}</span>
              <h3 className="text-sm font-bold text-white tracking-tight group-hover:text-indigo-300 transition-colors">
                {card.title}
              </h3>
            </div>

            <p className="text-xs text-gray-400 leading-relaxed mb-5 min-h-[60px]">
              {card.description}
            </p>

            <div className="space-y-2.5">
              {card.features.map((feature, fIdx) => (
                <div key={fIdx} className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 shrink-0 text-emerald-500" />
                  <span className="text-xs text-gray-300 font-medium leading-relaxed">{feature}</span>
                </div>
              ))}
            </div>

            <div className="mt-5 pt-4 border-t border-gray-800/40 flex items-center justify-between">
              <span className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">Launch Tool</span>
              <ArrowRight className="w-4 h-4 text-gray-600 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" />
            </div>
          </Link>
        ))}
      </div>

      {/* AI Chat Advisor CTA Banner */}
      <Link 
        to="/dashboard/chat"
        className="block bg-gradient-to-r from-indigo-600/10 via-[#11131a] to-purple-600/10 border border-indigo-500/20 hover:border-indigo-500/40 rounded-2xl p-8 transition-all hover:shadow-xl hover:shadow-indigo-500/5 group"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-5">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center shadow-xl shadow-indigo-600/20 shrink-0 group-hover:scale-105 transition-transform">
              <Sparkles className="w-7 h-7 text-white" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white mb-1 group-hover:text-indigo-300 transition-colors">
                AI Portfolio Advisor — Conversational Intelligence
              </h3>
              <p className="text-xs text-gray-400 max-w-xl leading-relaxed">
                Ask anything about your portfolio in natural language. Get instant AI-powered insights combining outputs from the LSTM forecaster, HMM regime detector, VADER sentiment scores, and RL policy recommendations.
              </p>
            </div>
          </div>
          <ArrowRight className="w-5 h-5 text-gray-600 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all shrink-0" />
        </div>
      </Link>
    </div>
  );
};

export default ResearchView;
