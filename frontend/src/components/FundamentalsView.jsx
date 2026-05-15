import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Building2, Loader2, TrendingUp, ShieldCheck, Activity, DollarSign, Link2, AlertTriangle, ChevronDown } from 'lucide-react';
import { PortfolioService } from '../services/api';

const formatNumber = (value, decimals = 2) => {
  if (value === null || value === undefined || Number.isNaN(value)) return 'N/A';
  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

const formatPercent = (value) => {
  if (value === null || value === undefined || Number.isNaN(value)) return 'N/A';
  return `${(Number(value) * 100).toFixed(2)}%`;
};

const MetricCard = ({ label, value, hint, accent = 'indigo' }) => {
  const accentMap = {
    indigo: 'border-indigo-500/20 text-indigo-300 bg-indigo-500/5',
    emerald: 'border-emerald-500/20 text-emerald-300 bg-emerald-500/5',
    amber: 'border-amber-500/20 text-amber-300 bg-amber-500/5',
  };

  return (
    <div className={`rounded-2xl border p-4 ${accentMap[accent] || accentMap.indigo} bg-[#11131a]/80 backdrop-blur-xl`}>
      <p className="text-[10px] uppercase tracking-wider text-gray-500 font-bold">{label}</p>
      <p className="mt-2 text-lg font-black text-white">{value}</p>
      {hint && <p className="mt-1 text-[11px] text-gray-400 leading-relaxed">{hint}</p>}
    </div>
  );
};

const FundamentalsView = ({ tickers = [] }) => {
  const defaultTicker = tickers[0] || 'AAPL';
  const [ticker, setTicker] = useState(defaultTicker);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const normalizedTickers = useMemo(() => tickers.length > 0 ? tickers : [defaultTicker], [tickers, defaultTicker]);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        const res = await PortfolioService.getFundamentals(ticker);
        setData(res);
      } catch (err) {
        setError(err?.response?.data?.detail || err.message || 'Failed to load fundamentals.');
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [ticker]);

  const company = data?.company || {};
  const valuation = data?.valuation || {};
  const profitability = data?.profitability || {};
  const growth = data?.growth || {};
  const balanceSheet = data?.balance_sheet || {};
  const income = data?.income_statement || {};
  const cashFlow = data?.cash_flow || {};

  return (
    <div className="space-y-8 pb-12 animate-in fade-in duration-500">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full border border-emerald-500/20 bg-emerald-500/10 text-emerald-300 text-[10px] font-black uppercase tracking-widest">
            <ShieldCheck className="w-3 h-3" /> Fundamentals
          </div>
          <h1 className="mt-3 text-3xl font-black tracking-tight text-white">Stock Fundamentals</h1>
          <p className="mt-2 text-sm text-gray-400 max-w-2xl leading-relaxed">
            Review valuation, profitability, growth, and balance-sheet strength for a specific stock.
          </p>
        </div>

        <div className="flex flex-col gap-2 min-w-[220px]">
          <label className="text-[10px] uppercase tracking-wider text-gray-500 font-bold">Choose ticker</label>
          <div className="relative">
            <select
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              className="w-full appearance-none bg-[#11131a] border border-gray-800/60 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
            >
              {normalizedTickers.map((symbol) => (
                <option key={symbol} value={symbol}>{symbol}</option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-gray-500 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-72 gap-3 rounded-3xl border border-gray-800/50 bg-[#11131a]/80">
          <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
          <span className="text-sm text-gray-400">Loading company fundamentals...</span>
        </div>
      ) : error ? (
        <div className="rounded-3xl border border-amber-500/20 bg-amber-500/5 p-6 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-400 mt-0.5" />
          <div>
            <p className="text-sm font-bold text-white">Fundamentals data unavailable</p>
            <p className="text-xs text-gray-400 mt-1">{error}</p>
          </div>
        </div>
      ) : (
        <>
          <section className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            <div className="lg:col-span-2 rounded-3xl border border-gray-800/50 bg-[#11131a]/80 backdrop-blur-xl p-6 shadow-xl">
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-5">
                <div>
                  <div className="flex items-center gap-2 text-indigo-300 text-xs font-black uppercase tracking-widest">
                    <Building2 className="w-4 h-4" /> Company Profile
                  </div>
                  <h2 className="mt-3 text-2xl font-black text-white">{company.name || ticker}</h2>
                  <p className="mt-2 text-sm text-gray-400 leading-relaxed max-w-2xl">{company.website_summary || 'Company summary unavailable.'}</p>
                </div>
                <div className="grid grid-cols-2 gap-3 min-w-[260px]">
                  <MetricCard label="Market Price" value={company.market_price ? `$${formatNumber(company.market_price, 2)}` : 'N/A'} hint={`Currency: ${company.currency || 'USD'}`} accent="emerald" />
                  <MetricCard label="Market Cap" value={company.market_cap ? `$${formatNumber(company.market_cap, 0)}` : 'N/A'} hint={company.country || 'Global market'} />
                </div>
              </div>
            </div>

            <div className="rounded-3xl border border-gray-800/50 bg-[#11131a]/80 backdrop-blur-xl p-6 shadow-xl">
              <div className="flex items-center gap-2 text-emerald-300 text-xs font-black uppercase tracking-widest">
                <TrendingUp className="w-4 h-4" /> Quick Take
              </div>
              <p className="mt-4 text-sm text-gray-300 leading-relaxed">
                {company.market_cap
                  ? `${company.name || ticker} is currently trading at ${company.market_price ? `$${formatNumber(company.market_price, 2)}` : 'an unavailable price'} with a ${valuation.trailing_pe ? `trailing P/E of ${formatNumber(valuation.trailing_pe, 2)}` : 'limited valuation data'}.`
                  : 'Fundamental snapshot unavailable for this symbol.'}
              </p>
            </div>
          </section>

          <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            <MetricCard label="Trailing P/E" value={formatNumber(valuation.trailing_pe, 2)} hint="Price to trailing earnings" />
            <MetricCard label="Forward P/E" value={formatNumber(valuation.forward_pe, 2)} hint="Expected earnings multiple" />
            <MetricCard label="Price / Book" value={formatNumber(valuation.price_to_book, 2)} hint="Book value comparison" />
            <MetricCard label="PEG Ratio" value={formatNumber(valuation.peg_ratio, 2)} hint="Growth-adjusted valuation" />
          </section>

          <section className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            <div className="rounded-3xl border border-gray-800/50 bg-[#11131a]/80 backdrop-blur-xl p-6">
              <div className="flex items-center gap-2 text-indigo-300 text-xs font-black uppercase tracking-widest">
                <Activity className="w-4 h-4" /> Profitability
              </div>
              <div className="mt-5 space-y-3">
                <MetricCard label="Gross Margin" value={formatPercent(profitability.gross_margin)} />
                <MetricCard label="Operating Margin" value={formatPercent(profitability.operating_margin)} />
                <MetricCard label="Net Margin" value={formatPercent(profitability.profit_margin)} />
              </div>
            </div>

            <div className="rounded-3xl border border-gray-800/50 bg-[#11131a]/80 backdrop-blur-xl p-6">
              <div className="flex items-center gap-2 text-indigo-300 text-xs font-black uppercase tracking-widest">
                <DollarSign className="w-4 h-4" /> Growth
              </div>
              <div className="mt-5 space-y-3">
                <MetricCard label="Revenue Growth" value={formatPercent(growth.revenue_growth)} />
                <MetricCard label="Earnings Growth" value={formatPercent(growth.earnings_growth)} />
                <MetricCard label="Quarterly EPS Growth" value={formatPercent(growth.earnings_quarterly_growth)} />
              </div>
            </div>

            <div className="rounded-3xl border border-gray-800/50 bg-[#11131a]/80 backdrop-blur-xl p-6">
              <div className="flex items-center gap-2 text-indigo-300 text-xs font-black uppercase tracking-widest">
                <Link2 className="w-4 h-4" /> Balance Sheet
              </div>
              <div className="mt-5 space-y-3">
                <MetricCard label="Total Cash" value={balanceSheet.total_cash ? `$${formatNumber(balanceSheet.total_cash, 0)}` : 'N/A'} />
                <MetricCard label="Total Debt" value={balanceSheet.total_debt ? `$${formatNumber(balanceSheet.total_debt, 0)}` : 'N/A'} />
                <MetricCard label="Debt / Assets" value={balanceSheet.total_debt && balanceSheet.total_assets ? formatNumber(balanceSheet.total_debt / balanceSheet.total_assets, 2) : 'N/A'} />
              </div>
            </div>
          </section>

          <section className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div className="rounded-3xl border border-gray-800/50 bg-[#11131a]/80 backdrop-blur-xl p-6">
              <h3 className="text-sm font-black text-white uppercase tracking-widest">Income Statement</h3>
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
                <MetricCard label="Revenue" value={income.total_revenue ? `$${formatNumber(income.total_revenue, 0)}` : 'N/A'} />
                <MetricCard label="Gross Profit" value={income.gross_profit ? `$${formatNumber(income.gross_profit, 0)}` : 'N/A'} />
                <MetricCard label="Operating Income" value={income.operating_income ? `$${formatNumber(income.operating_income, 0)}` : 'N/A'} />
                <MetricCard label="Net Income" value={income.net_income ? `$${formatNumber(income.net_income, 0)}` : 'N/A'} />
              </div>
            </div>

            <div className="rounded-3xl border border-gray-800/50 bg-[#11131a]/80 backdrop-blur-xl p-6">
              <h3 className="text-sm font-black text-white uppercase tracking-widest">Cash Flow</h3>
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
                <MetricCard label="Operating Cash Flow" value={cashFlow.operating_cash_flow ? `$${formatNumber(cashFlow.operating_cash_flow, 0)}` : 'N/A'} />
                <MetricCard label="Free Cash Flow" value={cashFlow.free_cash_flow ? `$${formatNumber(cashFlow.free_cash_flow, 0)}` : 'N/A'} />
                <MetricCard label="Capital Expenditure" value={cashFlow.capital_expenditure ? `$${formatNumber(cashFlow.capital_expenditure, 0)}` : 'N/A'} />
              </div>
            </div>
          </section>

          <div className="flex flex-wrap gap-3">
            <Link to="/dashboard/research" className="px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-lg shadow-indigo-600/20">
              Open Research Hub
            </Link>
            <Link to="/dashboard/forecast" className="px-5 py-3 rounded-xl bg-gray-800/70 hover:bg-gray-800 text-gray-200 text-xs font-bold transition-all border border-gray-700/60">
              Open Forecast View
            </Link>
          </div>
        </>
      )}
    </div>
  );
};

export default FundamentalsView;