import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, ArrowRight, BarChart3, Target, Loader2, AlertTriangle
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer
} from 'recharts';
import { PortfolioService } from '../services/api';

const ForecastingView = () => {
  const [forecastData, setForecastData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [ticker, setTicker] = useState('AAPL');
  const [inputTicker, setInputTicker] = useState('AAPL');
  const [currency, setCurrency] = useState('USD');

  const getCurrencySymbol = (code) => {
    const map = { 'USD': '$', 'INR': '₹', 'GBp': 'p', 'EUR': '€', 'JPY': '¥' };
    return map[code] || '$';
  };

  const currencySymbol = getCurrencySymbol(currency);

  const fetchForecast = async (sym) => {
    try {
      setLoading(true);
      setError(null);
      const res = await PortfolioService.getForecast(sym, 30);
      setCurrency(res.currency || 'USD');
      const formatted = res.forecast.map((item, idx) => ({
        name: idx === 0 ? 'Day 1' : `Day ${idx + 1}`,
        price: parseFloat(item.predicted_price.toFixed(2)),
      }));
      setForecastData(formatted);
    } catch (err) {
      console.error('Forecast failed:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForecast(ticker);
  }, [ticker]);

  const handleRetrain = () => {
    setTicker(inputTicker.toUpperCase());
  };

  const startPrice = forecastData[0]?.price || 0;
  const endPrice = forecastData[forecastData.length - 1]?.price || 0;
  const pctChange = startPrice > 0 ? (((endPrice - startPrice) / startPrice) * 100).toFixed(1) : 0;
  const isBullish = endPrice > startPrice;

  return (
    <div className="grid grid-cols-12 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
      
      {/* Model Settings Header */}
      <div className="col-span-12 flex items-center justify-between bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 p-6 rounded-3xl mb-2">
         <div className="flex gap-8">
            <div className="flex flex-col">
               <span className="text-xs text-gray-500 uppercase font-bold tracking-widest mb-1">Active Model</span>
               <div className="flex items-center gap-2">
                 <div className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse" />
                 <span className="text-sm font-bold text-gray-200">RandomForest Forecaster</span>
               </div>
            </div>
            <div className="flex flex-col border-l border-gray-800 pl-8">
               <span className="text-xs text-gray-500 uppercase font-bold tracking-widest mb-1">Ticker</span>
               <span className="text-sm font-bold text-indigo-400">{ticker}</span>
            </div>
            <div className="flex flex-col border-l border-gray-800 pl-8">
               <span className="text-xs text-gray-500 uppercase font-bold tracking-widest mb-1">Horizon</span>
               <span className="text-sm font-bold text-gray-200">30 Days Out</span>
            </div>
         </div>
         <div className="flex items-center gap-3">
           <input
             type="text"
             value={inputTicker}
             onChange={(e) => setInputTicker(e.target.value)}
             className="bg-[#1a1c26] border border-gray-700 rounded-lg px-3 py-2 text-xs w-24 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500/50"
             placeholder="TICKER"
           />
           <button 
             onClick={handleRetrain}
             className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all"
           >
             Forecast
           </button>
         </div>
      </div>

      {/* Main Forecast Chart */}
      <div className="col-span-9 bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-6 shadow-xl">
        <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
          <Target className="w-5 h-5 text-indigo-400" />
          {ticker} — 30-Day Price Trajectory
          <span className="ml-auto text-xs text-gray-500 font-bold uppercase">Live Prediction</span>
        </h3>
        
        {loading ? (
          <div className="flex flex-col items-center justify-center h-96 gap-4">
            <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
            <p className="text-gray-400 text-sm">Running ML forecast for {ticker}...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-96 gap-4">
            <AlertTriangle className="w-8 h-8 text-yellow-500" />
            <p className="text-gray-400 text-sm">Forecast error: {error}</p>
          </div>
        ) : (
          <div className="h-96 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={forecastData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis dataKey="name" stroke="#6b7280" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#6b7280" fontSize={12} tickLine={false} axisLine={false} domain={['auto', 'auto']} tickFormatter={(v) => `${currencySymbol}${v}`} />
                <Tooltip 
                   contentStyle={{ backgroundColor: '#11131a', border: '1px solid #374151', borderRadius: '12px' }}
                   formatter={(value) => [`${currencySymbol}${value}`, 'Predicted Price']}
                />
                <Line 
                  type="monotone" 
                  dataKey="price" 
                  stroke="#6366f1" 
                  strokeWidth={4} 
                  dot={{ r: 3, fill: '#6366f1', strokeWidth: 2, stroke: '#0a0b10' }} 
                  activeDot={{ r: 8, strokeWidth: 0 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Forecast Insights */}
      <div className="col-span-3 flex flex-col gap-6">
        <div className="bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-6">
           <div className="flex items-center gap-3 mb-4">
             <div className={`p-2 rounded-lg ${isBullish ? 'bg-emerald-500/10' : 'bg-rose-500/10'}`}>
               <TrendingUp className={`w-5 h-5 ${isBullish ? 'text-emerald-400' : 'text-rose-400'}`} />
             </div>
             <h4 className="font-bold text-gray-200">{isBullish ? 'Bullish Bias' : 'Bearish Bias'}</h4>
           </div>
           <p className="text-sm text-gray-400 leading-relaxed">
             ML model predicts {ticker} will {isBullish ? 'rise' : 'drop'} by <span className={`font-bold ${isBullish ? 'text-emerald-400' : 'text-rose-400'}`}>{Math.abs(pctChange)}%</span> over the next 30 days, from {currencySymbol}{startPrice.toFixed(2)} to {currencySymbol}{endPrice.toFixed(2)}.
           </p>
           <div className={`mt-4 flex items-center gap-1 text-xs font-bold ${isBullish ? 'text-emerald-400' : 'text-rose-400'}`}>
             {pctChange}% Predicted Change <ArrowRight className="w-3 h-3" />
           </div>
        </div>

        <div className="bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-6 flex-1">
           <h4 className="text-lg font-bold mb-4 flex items-center gap-2">
             <BarChart3 className="w-5 h-5 text-indigo-400" />
             Price Summary
           </h4>
           <div className="space-y-6">
              {[
                { label: 'Start Price', value: `${currencySymbol}${startPrice.toFixed(2)}`, color: 'bg-indigo-500' },
                { label: 'End Price', value: `${currencySymbol}${endPrice.toFixed(2)}`, color: isBullish ? 'bg-emerald-500' : 'bg-rose-500' },
                { label: '30-Day Change', value: `${pctChange}%`, color: isBullish ? 'bg-emerald-500' : 'bg-rose-500' }
              ].map(stat => (
                <div key={stat.label}>
                   <div className="flex justify-between text-xs font-bold uppercase tracking-wider text-gray-500 mb-2">
                     <span>{stat.label}</span>
                     <span className="text-gray-300">{stat.value}</span>
                   </div>
                   <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                     <div className={`h-full ${stat.color} w-2/3`} />
                   </div>
                </div>
              ))}
           </div>
        </div>
      </div>
    </div>
  );
};

export default ForecastingView;
