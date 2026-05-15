import React from 'react';
import { 
  BarChart3, Shield, Zap, Globe, Cpu, TrendingUp, 
  ArrowRight, MessageSquare, Target, ChevronRight
} from 'lucide-react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-[#0a0b10] text-white selection:bg-indigo-500/30">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-[#0a0b10]/80 backdrop-blur-xl border-b border-gray-800/50">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-2 group cursor-pointer">
            <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-600/20 group-hover:scale-110 transition-transform">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tighter uppercase">SmartAdvisor</span>
          </div>
          
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-400">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#market" className="hover:text-white transition-colors">Global Markets</a>
            <a href="#tech" className="hover:text-white transition-colors">Technology</a>
          </div>

          <Link 
            to="/auth"
            className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-2.5 rounded-xl text-sm font-bold transition-all shadow-lg shadow-indigo-600/20 active:scale-95"
          >
            Launch Dashboard
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-40 pb-20 px-6 overflow-hidden">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-indigo-600/10 rounded-full blur-[120px] -z-10 opacity-50"></div>
        
        <div className="max-w-7xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 px-4 py-2 rounded-full text-indigo-400 text-xs font-bold uppercase tracking-widest mb-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <Zap className="w-3 h-3" />
            Next-Gen Portfolio Intelligence
          </div>
          
          <h1 className="text-6xl md:text-8xl font-bold tracking-tighter mb-8 bg-clip-text text-transparent bg-gradient-to-b from-white to-gray-400 animate-in fade-in slide-in-from-bottom-8 duration-1000">
            Precision Intelligence for <br/> <span className="text-indigo-500">Global Markets</span>
          </h1>
          
          <p className="max-w-2xl mx-auto text-gray-400 text-lg md:text-xl leading-relaxed mb-12 animate-in fade-in slide-in-from-bottom-12 duration-1000">
            The world's first multi-tier financial advisor combining HMM market regime signals, 
            VADER sentiment intelligence, and ML-driven forecasting in a unified interface.
          </p>

          <div className="flex flex-col md:flex-row items-center justify-center gap-4 animate-in fade-in slide-in-from-bottom-16 duration-1000">
            <Link 
              to="/auth"
              className="px-8 py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-2xl text-lg font-bold transition-all flex items-center gap-2 shadow-2xl shadow-indigo-600/40"
            >
              Get Started Free <ArrowRight className="w-5 h-5" />
            </Link>
            <button className="px-8 py-4 bg-gray-800/10 border border-gray-800 hover:bg-gray-800/30 text-white rounded-2xl text-lg font-bold transition-all">
              Watch Demo
            </button>
          </div>

          {/* Floating Mockup */}
          <div className="mt-24 relative max-w-5xl mx-auto group">
            <div className="absolute inset-0 bg-indigo-600/20 rounded-3xl blur-[100px] opacity-0 group-hover:opacity-100 transition-opacity duration-1000"></div>
            <img 
              src="/landing_page_mockup_1774550413981.png" 
              alt="Dashboard Preview" 
              className="rounded-3xl border border-gray-800/50 shadow-2xl relative z-10 hover:-translate-y-2 transition-transform duration-700"
            />
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-32 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-3xl md:text-5xl font-bold mb-4 tracking-tight">Institutional-Grade Analysis</h2>
            <p className="text-gray-400">Everything you need to navigate volatile market regimes with confidence.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              { 
                icon: <MessageSquare className="w-6 h-6 text-indigo-400" />,
                title: "Sentiment Intelligence",
                desc: "Multi-source news aggregation with real-time VADER NLP scoring from Yahoo & Google News."
              },
              { 
                icon: <Globe className="w-6 h-6 text-emerald-400" />,
                title: "Global Compatibility",
                desc: "Full support for US and Indian markets (NSE/BSE) with localized currency (₹/$) support."
              },
              { 
                icon: <Target className="w-6 h-6 text-rose-400" />,
                title: "ML Forecasting",
                desc: "30-day price trajectories powered by advanced Random Forest & LSTM regressors."
              },
              { 
                icon: <Cpu className="w-6 h-6 text-amber-400" />,
                title: "Regime Detection",
                desc: "Unsupervised Hidden Markov Models (HMM) to identify bullish, bearish, and neutral cycles."
              }
            ].map((f, i) => (
              <div key={i} className="p-8 rounded-3xl bg-gray-900/40 border border-gray-800/50 hover:border-indigo-500/30 transition-all hover:bg-gray-900/60 group">
                <div className="w-12 h-12 rounded-2xl bg-gray-800 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  {f.icon}
                </div>
                <h3 className="text-xl font-bold mb-3">{f.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-20 border-t border-gray-800/50 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-6 h-6 text-indigo-500" />
            <span className="text-lg font-bold tracking-tighter uppercase">SmartAdvisor</span>
          </div>
          <div className="flex gap-12 text-sm text-gray-500 font-medium">
             <a href="#" className="hover:text-white transition-colors">Terms</a>
             <a href="#" className="hover:text-white transition-colors">Privacy</a>
             <a href="#" className="hover:text-white transition-colors">Security</a>
             <a href="#" className="hover:text-white transition-colors">Status</a>
          </div>
          <p className="text-xs text-gray-600">© 2026 SmartAdvisor AI. All data is for educational purposes.</p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
