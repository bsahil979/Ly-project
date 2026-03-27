import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, TrendingDown, Minus, Loader2, AlertTriangle,
  Newspaper, BarChart3, ExternalLink, ArrowRight, Zap
} from 'lucide-react';
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';
import { PortfolioService } from '../services/api';

const COLORS = { positive: '#10b981', negative: '#f43f5e', neutral: '#6b7280' };

const SentimentView = () => {
  const [sentimentData, setSentimentData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [ticker, setTicker] = useState('AAPL');
  const [inputTicker, setInputTicker] = useState('AAPL');

  const fetchSentiment = async (sym) => {
    try {
      setLoading(true);
      setError(null);
      const res = await PortfolioService.getSentiment(sym);
      setSentimentData(res);
    } catch (err) {
      console.error('Sentiment fetch failed:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSentiment(ticker);
  }, [ticker]);

  const handleAnalyze = () => {
    setTicker(inputTicker.toUpperCase());
  };

  const getSentimentIcon = (sentiment) => {
    if (sentiment === 'Positive') return <TrendingUp className="w-4 h-4 text-emerald-400" />;
    if (sentiment === 'Negative') return <TrendingDown className="w-4 h-4 text-rose-400" />;
    return <Minus className="w-4 h-4 text-gray-400" />;
  };

  const getScoreColor = (score) => {
    if (score >= 0.05) return 'text-emerald-400';
    if (score <= -0.05) return 'text-rose-400';
    return 'text-gray-400';
  };

  const getOverallColor = (sentiment) => {
    if (sentiment?.includes('Bullish')) return 'from-emerald-600 to-teal-700';
    if (sentiment?.includes('Bearish')) return 'from-rose-600 to-pink-700';
    return 'from-gray-600 to-slate-700';
  };

  return (
    <div className="grid grid-cols-12 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      {/* Header */}
      <div className="col-span-12 flex items-center justify-between bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 p-6 rounded-3xl">
        <div className="flex gap-8">
          <div className="flex flex-col">
            <span className="text-xs text-gray-500 uppercase font-bold tracking-widest mb-1">Engine</span>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
              <span className="text-sm font-bold text-gray-200">VADER Sentiment (NLP)</span>
            </div>
          </div>
          <div className="flex flex-col border-l border-gray-800 pl-8">
            <span className="text-xs text-gray-500 uppercase font-bold tracking-widest mb-1">Data Sources</span>
            <span className="text-sm font-bold text-gray-200">Yahoo Finance + Google News</span>
          </div>
          <div className="flex flex-col border-l border-gray-800 pl-8">
            <span className="text-xs text-gray-500 uppercase font-bold tracking-widest mb-1">Ticker</span>
            <span className="text-sm font-bold text-indigo-400">{ticker}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <input
            type="text"
            value={inputTicker}
            onChange={(e) => setInputTicker(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
            className="bg-[#1a1c26] border border-gray-700 rounded-lg px-3 py-2 text-xs w-24 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500/50"
            placeholder="TICKER"
          />
          <button 
            onClick={handleAnalyze}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-2"
          >
            <Zap className="w-3 h-3" /> Analyze
          </button>
        </div>
      </div>

      {loading ? (
        <div className="col-span-12 flex flex-col items-center justify-center h-96 gap-4">
          <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
          <p className="text-gray-400 text-sm">Analyzing sentiment for {ticker}...</p>
        </div>
      ) : error ? (
        <div className="col-span-12 flex flex-col items-center justify-center h-96 gap-4">
          <AlertTriangle className="w-10 h-10 text-yellow-500" />
          <p className="text-gray-400 text-sm">Sentiment error: {error}</p>
        </div>
      ) : sentimentData && (
        <>
          {/* Overall Sentiment Card */}
          <div className="col-span-4">
            <div className={`bg-gradient-to-br ${getOverallColor(sentimentData.overall_sentiment)} rounded-3xl p-8 shadow-xl relative overflow-hidden group h-full`}>
              <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-10 -mt-10 blur-3xl group-hover:scale-110 transition-transform duration-700"></div>
              <p className="text-white/70 text-sm font-medium mb-1">Overall Sentiment</p>
              <h2 className="text-3xl font-bold text-white tracking-tight mb-2">{sentimentData.overall_sentiment}</h2>
              <div className="mt-2 flex items-center gap-2 text-white/90 bg-white/10 w-fit px-3 py-1.5 rounded-full text-xs font-bold backdrop-blur-md uppercase tracking-wide">
                <BarChart3 className="w-3 h-3" />
                Score: {sentimentData.overall_score} | {(sentimentData.confidence * 100).toFixed(0)}% confidence
              </div>
              <p className="mt-4 text-white/60 text-xs">{sentimentData.articles_analyzed} articles from {sentimentData.sources_used?.join(' + ') || 'multiple sources'}</p>
            </div>
          </div>

          {/* Sentiment Breakdown Pie */}
          <div className="col-span-4 bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-6 shadow-xl">
            <h3 className="text-lg font-semibold mb-4">Sentiment Distribution</h3>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Positive', value: sentimentData.sentiment_breakdown.positive },
                      { name: 'Negative', value: sentimentData.sentiment_breakdown.negative },
                      { name: 'Neutral', value: sentimentData.sentiment_breakdown.neutral },
                    ]}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    <Cell fill={COLORS.positive} />
                    <Cell fill={COLORS.negative} />
                    <Cell fill={COLORS.neutral} />
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#11131a', border: '1px solid #374151', borderRadius: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-6 mt-2">
              {[
                { label: 'Bullish', count: sentimentData.sentiment_breakdown.positive, color: 'bg-emerald-500' },
                { label: 'Bearish', count: sentimentData.sentiment_breakdown.negative, color: 'bg-rose-500' },
                { label: 'Neutral', count: sentimentData.sentiment_breakdown.neutral, color: 'bg-gray-500' },
              ].map(item => (
                <div key={item.label} className="flex items-center gap-2 text-xs">
                  <div className={`w-2.5 h-2.5 rounded-full ${item.color}`} />
                  <span className="text-gray-400">{item.label}: <span className="text-white font-bold">{item.count}</span></span>
                </div>
              ))}
            </div>
          </div>

          {/* Score Distribution Bar Chart */}
          <div className="col-span-4 bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-6 shadow-xl">
            <h3 className="text-lg font-semibold mb-4">Article Scores</h3>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sentimentData.articles.map((a, i) => ({ name: `${i + 1}`, score: a.score }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                  <XAxis dataKey="name" stroke="#6b7280" fontSize={10} tickLine={false} axisLine={false} />
                  <YAxis stroke="#6b7280" fontSize={10} tickLine={false} axisLine={false} domain={[-1, 1]} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#11131a', border: '1px solid #374151', borderRadius: '12px' }}
                    formatter={(value) => [value.toFixed(3), 'Compound Score']}
                  />
                  <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                    {sentimentData.articles.map((a, i) => (
                      <Cell key={i} fill={a.score >= 0.05 ? COLORS.positive : a.score <= -0.05 ? COLORS.negative : COLORS.neutral} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* News Feed */}
          <div className="col-span-12 bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-6 shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Newspaper className="w-5 h-5 text-indigo-400" />
                News Sentiment Feed
              </h3>
              <span className="text-xs text-gray-500">{sentimentData.articles_analyzed} articles</span>
            </div>
            <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
              {sentimentData.articles.map((article, idx) => (
                <div 
                  key={idx} 
                  className="flex items-start gap-4 p-4 bg-gray-800/20 rounded-2xl border border-gray-800/30 hover:border-gray-700/50 transition-all group"
                >
                  <div className="mt-1 flex-shrink-0">
                    {getSentimentIcon(article.sentiment)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-200 font-medium leading-snug line-clamp-2 group-hover:text-white transition-colors">
                      {article.title}
                    </p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                      <span>{article.publisher}</span>
                      <span>•</span>
                      <span>{article.published}</span>
                      {article.source && (
                        <>
                          <span>•</span>
                          <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${
                            article.source === 'Google News' ? 'bg-blue-500/10 text-blue-400' : 'bg-violet-500/10 text-violet-400'
                          }`}>{article.source}</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2 flex-shrink-0">
                    <span className={`text-xs font-bold px-2 py-1 rounded-lg ${
                      article.sentiment === 'Positive' ? 'text-emerald-400 bg-emerald-500/10 ring-1 ring-emerald-500/20' :
                      article.sentiment === 'Negative' ? 'text-rose-400 bg-rose-500/10 ring-1 ring-rose-500/20' :
                      'text-gray-400 bg-gray-500/10 ring-1 ring-gray-500/20'
                    }`}>
                      {article.sentiment}
                    </span>
                    <span className={`text-xs font-mono ${getScoreColor(article.score)}`}>
                      {article.score > 0 ? '+' : ''}{article.score}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default SentimentView;
