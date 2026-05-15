import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  TrendingUp, Shield, Lock, Mail, User, ArrowRight, Loader2, Zap, CheckCircle2, Sparkles
} from 'lucide-react';
import { AuthService } from '../services/supabaseClient';

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      if (isLogin) {
        await AuthService.login(email, password, false);
        setSuccess('Successfully logged in! Accessing neural models...');
        setTimeout(() => navigate('/dashboard'), 1000);
      } else {
        if (!fullName) throw new Error('Please enter your full name.');
        await AuthService.register(email, password, fullName, false);
        setSuccess('Account created successfully! Provisioning portfolio space...');
        setTimeout(() => navigate('/dashboard'), 1000);
      }
    } catch (err) {
      setError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      AuthService.createDemoAccount();
      setSuccess('Demo account created! Testing the platform...');
      setTimeout(() => navigate('/dashboard'), 1000);
    } catch (err) {
      setError(err.message || 'Failed to create demo account.');
    } finally {
      setLoading(false);
    }
  };

  // Switch mode helper
  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError(null);
    setSuccess(null);
  };

  return (
    <div className="min-h-screen bg-[#0a0b10] flex items-center justify-center p-6 relative overflow-hidden text-white selection:bg-indigo-500/30">
      {/* Dynamic Background Blurs */}
      <div className="absolute top-1/4 -left-20 w-96 h-96 bg-indigo-600/20 rounded-full blur-[128px] pointer-events-none -z-10 animate-pulse" />
      <div className="absolute bottom-1/4 -right-20 w-96 h-96 bg-emerald-600/10 rounded-full blur-[128px] pointer-events-none -z-10" />

      <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 bg-[#11131a]/80 backdrop-blur-2xl border border-gray-800/60 rounded-3xl overflow-hidden shadow-2xl">
        
        {/* Left Side: Premium Intelligence Intro Panel */}
        <div className="hidden md:flex flex-col justify-between p-12 bg-gradient-to-br from-[#161923] to-[#0e1017] border-r border-gray-800/60 relative">
          <div>
            <div className="flex items-center gap-2 mb-12">
              <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-600/20">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold tracking-tighter uppercase">SmartAdvisor</span>
            </div>

            <span className="inline-flex items-center gap-1.5 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1 rounded-full text-indigo-400 text-xs font-bold uppercase tracking-widest mb-6">
              <Zap className="w-3 h-3" />
              Supabase Core Secured
            </span>

            <h2 className="text-4xl font-black tracking-tighter leading-tight mb-6">
              Connect to the <br />
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-300 to-white">
                Cognitive Matrix.
              </span>
            </h2>

            <p className="text-sm text-gray-400 leading-relaxed mb-8">
              Gain localized edge performance mapping across multi-model asset analytics. Authorized accounts unlock native dry-run portfolios, unthrottled HMM regimes, and sentiment aggregation layers.
            </p>

            <div className="space-y-4">
              {[
                "End-to-End Encrypted User Authentication",
                "Isolated In-Memory Multi-Asset Cache Stores",
                "Synchronous Live Ledger Portfolios"
              ].map((item, idx) => (
                <div key={idx} className="flex items-center gap-3 text-xs text-gray-300 font-medium">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-8 border-t border-gray-800/50 flex items-center gap-3">
            <Shield className="w-5 h-5 text-indigo-400" />
            <span className="text-xs text-gray-500 font-bold tracking-wider uppercase">
              Production TLS / RLS Compliance Enabled
            </span>
          </div>
        </div>

        {/* Right Side: Sleek Glassmorphism Interactive Inputs */}
        <div className="p-8 md:p-12 flex flex-col justify-center">
          <div className="max-w-sm w-full mx-auto">
            <h3 className="text-2xl font-black tracking-tight mb-2">
              {isLogin ? 'Welcome Back' : 'Create Account'}
            </h3>
            <p className="text-xs text-gray-400 mb-8 font-medium">
              {isLogin 
                ? 'Enter your investor credentials to resume tracking.' 
                : 'Instantly provision your multi-tier user sandbox.'}
            </p>

            {error && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl mb-6 font-medium animate-in fade-in duration-300">
                {error}
              </div>
            )}

            {success && (
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs rounded-xl mb-6 font-medium animate-in fade-in duration-300 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                {success}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {!isLogin && (
                <div>
                  <label className="block text-xs text-gray-500 font-bold uppercase tracking-wider mb-1.5">
                    Full Name
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                      <User className="w-4 h-4" />
                    </div>
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="e.g. Sahil Belchada"
                      className="w-full bg-[#161822] border border-gray-800 rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 transition-colors"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs text-gray-500 font-bold uppercase tracking-wider mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                    <Mail className="w-4 h-4" />
                  </div>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="investor@smartadvisor.ai"
                    className="w-full bg-[#161822] border border-gray-800 rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="block text-xs text-gray-500 font-bold uppercase tracking-wider">
                    Password
                  </label>
                  {isLogin && (
                    <a href="#" className="text-xs text-indigo-400 hover:underline">
                      Forgot?
                    </a>
                  )}
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full bg-[#161822] border border-gray-800 rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || success}
                className="w-full mt-6 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-600/50 text-white rounded-xl text-sm font-bold transition-all shadow-lg shadow-indigo-600/20 flex items-center justify-center gap-2 active:scale-[0.98]"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Authenticating...</span>
                  </>
                ) : (
                  <>
                    <span>{isLogin ? 'Sign In' : 'Create Account'}</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            <div className="mt-8 space-y-4">
              <div className="text-center pt-6 border-t border-gray-800/50">
                <span className="text-xs text-gray-500 font-medium">
                  {isLogin ? "Don't have an account?" : "Already have an account?"}{' '}
                </span>
                <button
                  onClick={toggleMode}
                  className="text-xs text-indigo-400 hover:underline font-bold"
                >
                  {isLogin ? 'Sign Up' : 'Sign In'}
                </button>
              </div>

              {isLogin && (
                <div className="pt-4 border-t border-gray-800/50">
                  <button
                    type="button"
                    onClick={handleDemoLogin}
                    disabled={loading}
                    className="w-full py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 disabled:from-purple-600/50 disabled:to-pink-600/50 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-purple-600/20 flex items-center justify-center gap-2 active:scale-[0.98]"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Try Demo (Temporary Account)</span>
                  </button>
                  <p className="text-[10px] text-gray-500 text-center mt-2">
                    Create a temporary test account - it will be deleted on logout
                  </p>
                </div>
              )}
            </div>

            {/* Quick Demo Assist Banner */}
            {isLogin && (
              <div className="mt-6 p-2.5 bg-gray-900/40 border border-gray-800 rounded-xl text-center">
                <span className="text-[10px] text-gray-500 block font-bold uppercase tracking-wider mb-0.5">
                  Quick Login
                </span>
                <span className="text-xs text-gray-400 block">
                  Any email + password works. Real accounts created via Sign Up persist across sessions.
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
