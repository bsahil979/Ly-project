import React, { useState, useEffect } from 'react';
import {
  TrendingUp, TrendingDown, Loader2, AlertTriangle, Brain,
  Target, Shield, BarChart3, PieChart as PieIcon, Activity,
  Globe, RefreshCw, Zap, ChevronRight,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, Legend,
  PieChart as RechartsPieChart, Pie,
} from 'recharts';
import { PortfolioService } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const COLORS = ['#6366f1', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#ec4899', '#14b8a6'];

const PortfolioDashboard = ({ tickers = ['AAPL', 'MSFT', 'GOOGL'] }) => {
  const { user } = useAuth();
  const userId = user?.id || user?.email || 'guest';
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  const weights = tickers.length > 0 ? Array(tickers.length).fill(1 / tickers.length) : [];

  useEffect(() => {
    const raw = localStorage.getItem(`onboarding_data_${userId}`);
    if (raw) {
      try {
        const onboarding = JSON.parse(raw);
        if (onboarding.tickers && onboarding.tickers.length > 0) {
          // Use onboarding tickers
        }
      } catch (e) { console.error(e); }
    }
  }, [userId]);

  useEffect(() => {
    if (tickers.length === 0) {
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        const res = await PortfolioService.getPortfolioAnalysis({
          tickers,
          weights,
          portfolio_value: 100000,
          start: '2020-01-01',
          benchmark: 'SPY',
        });
        setData(res);
      } catch (err) {
        const msg = String(err?.message || '');
        if (err?.code === 'ECONNABORTED' || msg.toLowerCase().includes('timeout')) {
          setError('Request timed out. Analytics may still be computing; try again in a few seconds.');
        } else if (err?.code === 'ERR_NETWORK' || msg.includes('Network Error')) {
          setError('Cannot reach analytics API at http://localhost:8000.');
        } else {
          setError(msg || 'Unknown analytics error');
        }
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
        <p className="text-gray-400 text-sm">Running portfolio analysis pipeline...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <AlertTriangle className="w-10 h-10 text-yellow-500" />
        <p className="text-gray-400 text-sm">Analytics engine error: {error}</p>
      </div>
    );
  }

  if (!data) return null;

  const riskSummary = data.risk_engine || {};
  const portfolioScore = data.portfolio_score || {};
  const benchmark = data.benchmark || {};
  const attribution = data.attribution || {};
  const riskBudget = data.risk_budget || {};
  const recommendations = data.recommendations || [];
  const regime = data.market_regime || {};
  const stress = data.stress_test || {};
  const tickerDetails = data.ml_models?.ticker_details || {};

  const volData = riskSummary["Volatility (Annual)"] || {};
  const varData = riskSummary["VaR (95%)"] || {};
  const drawdownData = riskSummary["Max Drawdown"] || {};
  const tickersList = Object.keys(volData);

  const scorePct = portfolioScore.pct || 0;
  const scoreGrade = portfolioScore.grade || 'N/A';

  // Benchmark comparison
  const benchComp = benchmark.comparison || {};
  const benchPortfolio = benchmark.portfolio || {};
  const benchIndex = benchmark.benchmark || {};

  // Attribution data
  const secContrib = attribution.security_contribution || [];
  const sectorContrib = attribution.sector_contribution || [];

  // Risk budget
  const riskContrib = riskBudget.risk_contributions || [];
  const portVol = riskBudget.portfolio_volatility || 0;

  // Tabs
  const tabs = [
    { id: 'overview', label: 'Overview', icon: PieIcon },
    { id: 'risk', label: 'Risk & Budget', icon: Shield },
    { id: 'performance', label: 'Performance', icon: TrendingUp },
    { id: 'intelligence', label: 'Intelligence', icon: Brain },
    { id: 'recommendations', label: 'Recommendations', icon: Target },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header Stats */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          label="Portfolio Score"
          value={portfolioScore.score || 0}
          subtitle={`Grade ${scoreGrade} (${scorePct}%)`}
          icon={<Brain className="w-5 h-5 text-indigo-400" />}
          color="indigo"
        />
        <StatCard
          label="Annualized Volatility"
          value={`${(portVol * 100).toFixed(1)}%`}
          subtitle="Portfolio Risk"
          icon={<Activity className="w-5 h-5 text-rose-400" />}
          color="rose"
        />
        <StatCard
          label="Benchmark Alpha"
          value={`${(benchComp.alpha * 100).toFixed(1)}%`}
          subtitle={`vs ${benchmark.benchmark_display || 'SPY'}`}
          icon={<TrendingUp className="w-5 h-5 text-emerald-400" />}
          color="emerald"
        />
        <StatCard
          label="Market Regime"
          value={regime.current_regime || 'Unknown'}
          subtitle={`Confidence ${((regime.confidence || 0) * 100).toFixed(0)}%`}
          icon={<Globe className="w-5 h-5 text-blue-400" />}
          color="blue"
        />
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 bg-[#11131a]/80 border border-gray-800/50 rounded-xl p-1.5">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab.id
                ? 'bg-indigo-600/20 text-white border border-indigo-500/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/30'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && renderOverview()}
      {activeTab === 'risk' && renderRisk()}
      {activeTab === 'performance' && renderPerformance()}
      {activeTab === 'intelligence' && renderIntelligence()}
      {activeTab === 'recommendations' && renderRecommendations()}
    </div>
  );

  // ── Tab Renderers ──────────────────────────────────────

  function renderOverview() {
    const chartData = tickersList.map((ticker) => ({
      name: ticker,
      volatility: parseFloat(((volData[ticker] || 0) * 100).toFixed(2)),
      var95: parseFloat(((varData[ticker] || 0) * 100).toFixed(2)),
      maxDrawdown: parseFloat(((drawdownData[ticker] || 0) * 100).toFixed(2)),
    }));

    const scoreComponents = portfolioScore.components || {};
    const allocation = data.asset_allocation || [];
    const risksIdentified = portfolioScore.risks_identified || [];

    return (
      <div className="grid grid-cols-12 gap-6">
        {/* Risk Metrics Chart */}
        <div className="col-span-8 bg-[#11131a]/80 border border-gray-800/50 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Risk Metrics by Asset</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} barCategoryGap="30%" barGap={4}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis dataKey="name" stroke="#6b7280" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#6b7280" fontSize={12} tickLine={false} axisLine={false} unit="%" />
                <Tooltip contentStyle={{ backgroundColor: '#11131a', border: '1px solid #374151', borderRadius: '12px' }} />
                <Legend />
                <Bar dataKey="volatility" name="Volatility %" fill="#6366f1" radius={[6, 6, 0, 0]} />
                <Bar dataKey="var95" name="VaR (95%) %" fill="#f59e0b" radius={[6, 6, 0, 0]} />
                <Bar dataKey="maxDrawdown" name="Max Drawdown %" fill="#ef4444" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Portfolio Score */}
        <div className="col-span-4 bg-[#11131a]/80 border border-gray-800/50 rounded-2xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Brain className="w-4 h-4 text-white" />
            </div>
            <h3 className="text-lg font-semibold text-white">Portfolio Score</h3>
          </div>
          <div className="text-center mb-4">
            <div className="text-4xl font-black text-white">{portfolioScore.score || 0}</div>
            <div className="text-sm text-gray-500 mt-1">
              of {portfolioScore.max_score || 1000} · Grade: <span className={`font-bold ${scorePct >= 80 ? 'text-emerald-400' : scorePct >= 70 ? 'text-yellow-400' : scorePct >= 50 ? 'text-orange-400' : 'text-rose-400'}`}>{scoreGrade}</span>
            </div>
          </div>
          <div className="space-y-3">
            {Object.entries(scoreComponents).map(([key, comp]) => (
              <div key={key}>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs text-gray-400">{comp.label}</span>
                  <span className="text-xs font-bold text-gray-300">{comp.score}/{comp.max}</span>
                </div>
                <div className="w-full bg-gray-800/50 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${(comp.score / comp.max) * 100}%`,
                      backgroundColor: comp.score >= comp.max * 0.8 ? '#10b981' : comp.score >= comp.max * 0.6 ? '#f59e0b' : '#ef4444',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sector Allocation */}
        <div className="col-span-6 bg-[#11131a]/80 border border-gray-800/50 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Asset Allocation by Sector</h3>
          <div className="space-y-3">
            {allocation.map((asset, i) => (
              <div key={asset.ticker} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                  <span className="text-sm font-medium text-gray-300">{asset.ticker}</span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-gray-500">{asset.category}</span>
                  <span className="text-xs font-bold text-white">{asset.weight.toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Risks Identified */}
        <div className="col-span-6 bg-[#11131a]/80 border border-gray-800/50 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Risks Identified ({risksIdentified.length})</h3>
          <div className="space-y-3 max-h-48 overflow-y-auto custom-scrollbar">
            {risksIdentified.length === 0 ? (
              <p className="text-xs text-gray-500">No significant risks identified.</p>
            ) : (
              risksIdentified.map((risk, i) => (
                <div key={i} className={`p-3 rounded-xl border-l-2 ${
                  risk.severity === 'high' ? 'border-rose-500 bg-rose-500/5' :
                  risk.severity === 'medium' ? 'border-amber-500 bg-amber-500/5' :
                  'border-blue-500 bg-blue-500/5'
                }`}>
                  <div className="flex justify-between">
                    <span className="text-xs font-bold text-gray-200">{risk.label}</span>
                    <span className={`text-[10px] uppercase font-bold ${
                      risk.severity === 'high' ? 'text-rose-400' :
                      risk.severity === 'medium' ? 'text-amber-400' :
                      'text-blue-400'
                    }`}>{risk.severity}</span>
                  </div>
                  <p className="text-[11px] text-gray-500 mt-1">{risk.description}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    );
  }

  function renderRisk() {
    const rb = riskBudget;
    return (
      <div className="grid grid-cols-12 gap-6">
        {/* Risk Contributions */}
        <div className="col-span-6 bg-[#11131a]/80 border border-gray-800/50 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Risk Contribution</h3>
          <p className="text-xs text-gray-500 mb-4">
            Portfolio volatility: <span className="text-white font-bold">{(rb.portfolio_volatility * 100).toFixed(1)}%</span>
            {' '}· Risk concentration: <span className="text-white font-bold">{rb.risk_concentration}</span>
            {' '}· Diversification ratio: <span className="text-white font-bold">{rb.diversification_ratio?.toFixed(2)}</span>
          </p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskContrib} barCategoryGap="30%">
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis dataKey="ticker" stroke="#6b7280" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#6b7280" fontSize={12} tickLine={false} axisLine={false} unit="%" />
                <Tooltip contentStyle={{ backgroundColor: '#11131a', border: '1px solid #374151', borderRadius: '12px' }} />
                <Bar dataKey="percentage_contribution_to_risk" name="Risk %" fill="#6366f1" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 space-y-2">
            {riskContrib.map((r) => (
              <div key={r.ticker} className="flex justify-between items-center text-xs">
                <span className="text-gray-400">{r.ticker}</span>
                <div className="flex gap-4">
                  <span className="text-gray-500">W: {(r.weight * 100).toFixed(0)}%</span>
                  <span className="text-white font-bold">{r.percentage_contribution_to_risk.toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Summary Table */}
        <div className="col-span-6 bg-[#11131a]/80 border border-gray-800/50 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Risk Metrics Summary</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-800/50">
                  <th className="text-left py-2 text-gray-400">Ticker</th>
                  <th className="text-right py-2 text-gray-400">Volatility</th>
                  <th className="text-right py-2 text-gray-400">VaR (95%)</th>
                  <th className="text-right py-2 text-gray-400">Max Drawdown</th>
                </tr>
              </thead>
              <tbody>
                {tickersList.map((ticker) => (
                  <tr key={ticker} className="border-b border-gray-800/30">
                    <td className="py-2 text-gray-300">{ticker}</td>
                    <td className="py-2 text-right text-gray-300">{((volData[ticker] || 0) * 100).toFixed(1)}%</td>
                    <td className="py-2 text-right text-gray-300">{((varData[ticker] || 0) * 100).toFixed(1)}%</td>
                    <td className="py-2 text-right text-gray-300">{((drawdownData[ticker] || 0) * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Correlation Matrix */}
          {data.correlation?.matrix && (
            <div className="mt-6">
              <h4 className="text-sm font-medium text-gray-400 mb-3">Correlation Matrix</h4>
              <CorrelationMatrix data={data.correlation} />
            </div>
          )}
        </div>
      </div>
    );
  }

  function renderPerformance() {
    const comp = benchComp;
    return (
      <div className="grid grid-cols-12 gap-6">
        {/* Benchmark Comparison */}
        <div className="col-span-6 bg-[#11131a]/80 border border-gray-800/50 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">
            Benchmark Comparison — Portfolio vs {benchmark.benchmark_display || 'SPY'}
          </h3>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="bg-gray-800/30 rounded-xl p-3">
              <span className="text-xs text-gray-500">Alpha</span>
              <p className={`text-lg font-bold ${comp.alpha >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{(comp.alpha * 100).toFixed(1)}%</p>
            </div>
            <div className="bg-gray-800/30 rounded-xl p-3">
              <span className="text-xs text-gray-500">Information Ratio</span>
              <p className={`text-lg font-bold ${comp.information_ratio >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{comp.information_ratio?.toFixed(3)}</p>
            </div>
            <div className="bg-gray-800/30 rounded-xl p-3">
              <span className="text-xs text-gray-500">Beta</span>
              <p className="text-lg font-bold text-gray-300">{comp.beta?.toFixed(3)}</p>
            </div>
            <div className="bg-gray-800/30 rounded-xl p-3">
              <span className="text-xs text-gray-500">Tracking Error</span>
              <p className="text-lg font-bold text-gray-300">{(comp.tracking_error * 100).toFixed(1)}%</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-6">
            <div>
              <h4 className="text-xs text-gray-500 uppercase mb-2">Portfolio</h4>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between"><span>Total Return</span><span className="text-white">{(benchPortfolio.total_return * 100).toFixed(1)}%</span></div>
                <div className="flex justify-between"><span>Annualized</span><span className="text-white">{(benchPortfolio.annualized_return * 100).toFixed(1)}%</span></div>
                <div className="flex justify-between"><span>Volatility</span><span className="text-white">{(benchPortfolio.volatility * 100).toFixed(1)}%</span></div>
                <div className="flex justify-between"><span>Sharpe</span><span className="text-white">{benchPortfolio.sharpe_ratio?.toFixed(3)}</span></div>
                <div className="flex justify-between"><span>Max Drawdown</span><span className="text-white">{(benchPortfolio.max_drawdown * 100).toFixed(1)}%</span></div>
              </div>
            </div>
            <div>
              <h4 className="text-xs text-gray-500 uppercase mb-2">{benchmark.benchmark_display || 'Benchmark'}</h4>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between"><span>Total Return</span><span className="text-white">{(benchIndex.total_return * 100).toFixed(1)}%</span></div>
                <div className="flex justify-between"><span>Annualized</span><span className="text-white">{(benchIndex.annualized_return * 100).toFixed(1)}%</span></div>
                <div className="flex justify-between"><span>Volatility</span><span className="text-white">{(benchIndex.volatility * 100).toFixed(1)}%</span></div>
                <div className="flex justify-between"><span>Max Drawdown</span><span className="text-white">{(benchIndex.max_drawdown * 100).toFixed(1)}%</span></div>
              </div>
            </div>
          </div>
        </div>

        {/* Attribution */}
        <div className="col-span-6 bg-[#11131a]/80 border border-gray-800/50 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Return Attribution</h3>
          <p className="text-xs text-gray-500 mb-4">
            Period: {attribution.period?.start || 'N/A'} → {attribution.period?.end || 'N/A'}
            {' '}· Portfolio Return: <span className="text-white font-bold">{(attribution.portfolio_total_return * 100).toFixed(1)}%</span>
          </p>
          <div className="space-y-4">
            <AttributionTable
              title="Security Contribution"
              items={secContrib}
              valueKey="ticker"
              contribKey="contribution"
              weightKey="weight"
              returnKey="return"
            />
            <AttributionTable
              title="Sector Contribution"
              items={sectorContrib}
              valueKey="category"
              contribKey="contribution"
              weightKey="weight"
              returnKey="return"
            />
          </div>
        </div>
      </div>
    );
  }

  function renderIntelligence() {
    return (
      <div className="grid grid-cols-12 gap-6">
        {/* Market Regime */}
        <div className="col-span-4 bg-[#11131a]/80 border border-gray-800/50 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Market Regime (HMM)</h3>
          <div className="text-center">
            <div className="text-3xl font-black text-white mb-2">{regime.current_regime || 'Unknown'}</div>
            <div className="text-sm text-gray-400 mb-4">State #{regime.state_id} · Confidence {(regime.confidence * 100).toFixed(0)}%</div>
            <div className="bg-gray-800/30 rounded-xl p-3">
              <span className="text-xs text-gray-500">Portfolio Regime</span>
              <p className="text-sm text-gray-300 mt-1">{data.portfolio_regime?.current_regime || 'N/A'}</p>
            </div>
          </div>
        </div>

        {/* Stress Test */}
        <div className="col-span-4 bg-[#11131a]/80 border border-gray-800/50 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Stress Test</h3>
          <div className="space-y-3">
            {stress.worst_scenario && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl">
                <span className="text-xs text-gray-500">Worst Case</span>
                <p className="text-sm font-bold text-rose-400 mt-1">{stress.worst_scenario}</p>
                <p className="text-xs text-gray-400">Loss: {stress.worst_loss_pct?.toFixed(1)}%</p>
              </div>
            )}
            {riskBudget.var_95 !== undefined && (
              <div className="p-3 bg-gray-800/30 rounded-xl">
                <span className="text-xs text-gray-500">VaR (95%)</span>
                <p className="text-sm font-bold text-white mt-1">{(riskBudget.var_95 * 100).toFixed(1)}%</p>
              </div>
            )}
          </div>
        </div>

        {/* ML Forecasts & Sentiment */}
        <div className="col-span-4 bg-[#11131a]/80 border border-gray-800/50 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">ML Intelligence</h3>
          <div className="space-y-3 max-h-64 overflow-y-auto custom-scrollbar">
            {tickers.map((ticker) => {
              const detail = tickerDetails[ticker] || tickerDetails[ticker.toUpperCase()] || {};
              const forecast = detail.forecast;
              const mm = detail.marketmind;
              const hasForecast = forecast && forecast.predictions && forecast.predictions.length > 0;
              const hasMm = mm && mm.recommendation;
              if (!hasForecast && !hasMm) return null;
              return (
                <div key={ticker} className="p-2.5 bg-gray-800/30 rounded-lg">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-bold text-gray-200">{ticker.toUpperCase()}</span>
                  </div>
                  {hasForecast && (
                    <p className="text-xs text-gray-400">
                      Forecast: {forecast.predictions.length} pts · Spot ${forecast.spot_price?.toFixed(2)}
                    </p>
                  )}
                  {hasMm && (
                    <div className="flex justify-between text-xs mt-1">
                      <span className="text-gray-400">MarketMind:</span>
                      <span className={`font-bold ${mm.recommendation === 'BUY' ? 'text-emerald-400' : mm.recommendation === 'SELL' ? 'text-rose-400' : 'text-gray-400'}`}>{mm.recommendation} ({mm.confidence?.toFixed(2)})</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  function renderRecommendations() {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold text-white">Evidence-Backed Recommendations</h3>
          <span className="text-xs text-gray-500">{recommendations.length} recommendations generated</span>
        </div>
        <div className="space-y-4">
          {recommendations.map((rec) => (
            <RecommendationCard key={rec.id} rec={rec} />
          ))}
        </div>
        {recommendations.length === 0 && (
          <div className="bg-[#11131a]/80 border border-gray-800/50 rounded-2xl p-8 text-center">
            <Brain className="w-10 h-10 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No recommendations generated. Portfolio appears well-balanced.</p>
          </div>
        )}
      </div>
    );
  }
};

// ── Sub-components ───────────────────────────────────────────

const StatCard = ({ label, value, subtitle, icon }) => (
  <div className="bg-[#11131a]/80 border border-gray-800/50 rounded-2xl p-4">
    <div className="flex items-center gap-2 mb-2">
      {icon}
      <span className="text-xs text-gray-500 font-medium">{label}</span>
    </div>
    <div className="text-2xl font-black text-white">{value}</div>
    <p className="text-[10px] text-gray-500 mt-1">{subtitle}</p>
  </div>
);

const AttributionTable = ({ title, items, valueKey }) => (
  <div>
    <h4 className="text-xs text-gray-500 uppercase mb-2">{title}</h4>
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-gray-800/50">
            <th className="text-left py-1.5 text-gray-500">{valueKey === 'ticker' ? 'Ticker' : 'Sector'}</th>
            <th className="text-right py-1.5 text-gray-500">%</th>
            <th className="text-right py-1.5 text-gray-500">Return</th>
            <th className="text-right py-1.5 text-gray-500">Contrib</th>
            <th className="text-right py-1.5 text-gray-500">% of Total</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, i) => (
            <tr key={item[valueKey] || i} className="border-b border-gray-800/30">
              <td className="py-1.5 text-gray-300">{item[valueKey] || item.ticker || item.category}</td>
              <td className="py-1.5 text-right text-gray-400">{(item.weight * 100).toFixed(1)}%</td>
              <td className="py-1.5 text-right text-gray-400">{(item.return * 100).toFixed(1)}%</td>
              <td className="py-1.5 text-right text-gray-400">{item.contribution.toFixed(4)}</td>
              <td className="py-1.5 text-right font-bold text-white">{item.contribution_pct.toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

const CorrelationMatrix = ({ data }) => {
  const tickers = data.tickers || [];
  const matrix = data.matrix || [];
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr>{tickers.map((t) => <th key={t} className="text-center py-1.5 text-gray-500">{t}</th>)}</tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={tickers[i] || i}>
              <th className="text-left py-1.5 text-gray-400">{tickers[i] || '?'}</th>
              {row.map((val, j) => (
                <td
                  key={j}
                  className="text-center py-1.5 font-medium"
                  style={{
                    color: val > 0.7 ? '#ef4444' : val > 0.3 ? '#f59e0b' : val > -0.3 ? '#9ca3af' : val > -0.7 ? '#3b82f6' : '#10b981',
                  }}
                >{val.toFixed(2)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const RecommendationCard = ({ rec }) => {
  const severityColors = {
    high: 'border-rose-500 bg-rose-500/5',
    medium: 'border-amber-500 bg-amber-500/5',
    low: 'border-blue-500 bg-blue-500/5',
    experimental: 'border-purple-500 bg-purple-500/5',
  };
  const colorClass = severityColors[rec.confidence] || 'border-gray-500 bg-gray-500/5';
  return (
    <div className={`border-l-2 rounded-xl p-4 ${colorClass}`}>
      <div className="flex justify-between items-start mb-2">
        <div>
          <span className="text-xs font-bold uppercase text-gray-500">{rec.action}</span>
          <span className="text-sm font-bold text-white"> {rec.asset}</span>
        </div>
        <span className={`text-[10px] uppercase font-bold px-2 py-1 rounded ${
          rec.confidence === 'high' ? 'text-rose-300 bg-rose-500/10' :
          rec.confidence === 'medium' ? 'text-amber-300 bg-amber-500/10' :
          'text-blue-300 bg-blue-500/10'
        }`}>{rec.confidence}</span>
      </div>
      <p className="text-sm text-gray-300 mb-2">{rec.reason}</p>
      {rec.supporting_metrics && Object.keys(rec.supporting_metrics).length > 0 && (
        <div className="text-xs text-gray-500 mb-2">
          <span className="font-medium text-gray-400">Metrics:</span>
          {Object.entries(rec.supporting_metrics).map(([k, v]) => (
            <span key={k} className="ml-2">{k}: {typeof v === 'number' ? v.toFixed ? v.toFixed(v > 1 ? 2 : 4) : v : v}</span>
          ))}
        </div>
      )}
      <div className="flex items-center gap-2 mt-2">
        <button className="text-xs px-3 py-1.5 bg-gray-800/50 text-gray-300 rounded-lg hover:bg-gray-700/50 transition-colors">
          Review
        </button>
        <button className="text-xs px-3 py-1.5 bg-indigo-600/20 text-indigo-300 rounded-lg hover:bg-indigo-600/30 transition-colors">
          Simulate
        </button>
        <span className="text-[10px] text-gray-600">
          Models: {rec.supporting_models?.join(', ') || 'N/A'}
        </span>
      </div>
    </div>
  );
};

export default PortfolioDashboard;
