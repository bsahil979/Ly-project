import React, { useState, useEffect } from 'react';
import { 
  User, Shield, Cpu, Sliders, Database, LogOut, AlertTriangle, 
  CheckCircle2, RefreshCw, Layers, Zap, Globe, Coins, Lock 
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { AuthService, PortfolioStorageService } from '../services/supabaseClient';

const SettingsView = ({ tickers, setTickers }) => {
  const [user, setUser] = useState(null);
  const [fullName, setFullName] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [dryRun, setDryRun] = useState(true);
  const [horizon, setHorizon] = useState('30');
  const [isLoading, setIsLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchSession = async () => {
      try {
        const res = await AuthService.getCurrentUser();
        const usr = res?.data?.user || null;
        setUser(usr);
        if (usr?.user_metadata?.full_name) {
          setFullName(usr.user_metadata.full_name);
        } else {
          setFullName(usr?.email?.split('@')[0] || 'Quantitative Investor');
        }
      } catch (err) {
        console.warn("Session check profile fallback:", err);
      }
    };
    fetchSession();

    // Load extra UI variables from local storage if previously modified
    const savedCur = localStorage.getItem('aura_pref_currency') || 'USD';
    const savedDry = localStorage.getItem('aura_pref_dry_run') !== 'false';
    const savedHor = localStorage.getItem('aura_pref_horizon') || '30';
    setCurrency(savedCur);
    setDryRun(savedDry);
    setHorizon(savedHor);
  }, []);

  const triggerStatus = (text, isErr = false) => {
    setStatusMsg({ text, isErr });
    setTimeout(() => setStatusMsg(null), 4000);
  };

  // Profile parameter commit simulated/real save logic
  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      // If user active, we can update local metadata preferences
      localStorage.setItem('aura_pref_name', fullName);
      triggerStatus("Profile attributes updated successfully inside private ledger.");
    } catch (err) {
      triggerStatus("Ledger update blocked.", true);
    } finally {
      setIsLoading(false);
    }
  };

  // Preference engine triggers
  const handleSavePreferences = (e) => {
    e.preventDefault();
    localStorage.setItem('aura_pref_currency', currency);
    localStorage.setItem('aura_pref_dry_run', dryRun ? 'true' : 'false');
    localStorage.setItem('aura_pref_horizon', horizon);
    triggerStatus("Computational system preferences saved and loaded into active memory blocks.");
  };

  // Execute explicit Purge command
  const handlePurgeSpace = async () => {
    if (window.confirm("Are you certain you wish to purge all custom assets from your active monitoring space?")) {
      setTickers([]);
      if (user?.id || user?.email) {
        await PortfolioStorageService.saveUserPortfolio(user.id || user.email, []);
      }
      triggerStatus("Manifest ground cleared completely.");
    }
  };

  // Auth exit handshake
  const handleSignOut = async () => {
    setIsLoading(true);
    await AuthService.logout();
    setUser(null);
    navigate('/');
  };

  return (
    <div className="grid grid-cols-12 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-700 max-w-6xl mx-auto pb-12">
      
      {/* Dynamic Status Alert Container */}
      {statusMsg && (
        <div className={`col-span-12 p-4 rounded-2xl flex items-center gap-3 border backdrop-blur-xl animate-in fade-in slide-in-from-top-2 duration-300 ${
          statusMsg.isErr 
            ? 'bg-rose-500/10 border-rose-500/20 text-rose-300' 
            : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
        }`}>
          {statusMsg.isErr ? <AlertTriangle className="w-5 h-5 shrink-0" /> : <CheckCircle2 className="w-5 h-5 shrink-0" />}
          <span className="text-xs font-bold">{statusMsg.text}</span>
        </div>
      )}

      {/* Primary Column 1: Identity & Authorization Block */}
      <div className="col-span-12 lg:col-span-6 flex flex-col gap-6">
        
        {/* Connected Credentials Card */}
        <div className="bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-8 shadow-xl relative overflow-hidden group">
           <div className="absolute top-0 right-0 w-48 h-48 bg-indigo-500/5 rounded-full -mr-16 -mt-16 blur-3xl group-hover:scale-125 transition-transform duration-700" />
           
           <div className="flex items-center gap-3 mb-6">
             <User className="w-5 h-5 text-indigo-400" />
             <span className="text-xs font-bold uppercase tracking-widest text-gray-400">Identity Silo</span>
           </div>

           <div className="flex items-center gap-4 mb-6">
             <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center font-black text-2xl text-white shadow-xl shadow-indigo-600/20 ring-4 ring-indigo-500/10">
               {fullName ? fullName.charAt(0).toUpperCase() : 'U'}
             </div>
             <div className="flex-1 min-w-0">
               <h3 className="text-lg font-black text-white tracking-tight truncate">
                 {fullName}
               </h3>
               <span className="text-xs text-gray-400 font-medium block truncate mt-0.5">
                 {user?.email || 'Guest Environment Provisioning'}
               </span>
               <span className={`inline-block mt-2 px-2.5 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider ${
                 user ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
               }`}>
                 {user ? 'Verified Multi-Tenant Scope' : 'Temporary Guest Storage'}
               </span>
             </div>
           </div>

           {/* Update Form Profile */}
           <form onSubmit={handleSaveProfile} className="space-y-4 pt-4 border-t border-gray-800/40">
             <div>
               <label className="block text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1.5">
                 Display Name Handle
               </label>
               <input
                 type="text"
                 value={fullName}
                 onChange={(e) => setFullName(e.target.value)}
                 placeholder="Investor full name..."
                 className="w-full bg-[#161822] border border-gray-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 transition-colors"
               />
             </div>

             <div className="flex justify-end">
               <button
                 type="submit"
                 disabled={isLoading}
                 className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-indigo-600/20 active:scale-95"
               >
                 {isLoading ? 'Committing...' : 'Commit Profile Attributes'}
               </button>
             </div>
           </form>
        </div>

        {/* Security & Access Management Ground */}
        <div className="bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-8 shadow-xl">
           <div className="flex items-center gap-3 mb-6">
             <Shield className="w-5 h-5 text-emerald-400" />
             <span className="text-xs font-bold uppercase tracking-widest text-gray-400">Security & Authentication</span>
           </div>

           <div className="space-y-4">
             <div className="p-4 rounded-2xl bg-gray-800/20 border border-gray-800/60 flex items-center justify-between">
               <div className="flex items-center gap-3">
                 <Lock className="w-4 h-4 text-gray-500" />
                 <div>
                   <span className="text-xs font-bold text-white block">Supabase Native JWT Sessions</span>
                   <span className="text-[10px] text-gray-500 block">Isolated dynamic schema multi-tenancy rules applied.</span>
                 </div>
               </div>
               <span className="px-2 py-0.5 bg-indigo-500/10 text-indigo-400 rounded text-[9px] font-bold uppercase">
                 Active
               </span>
             </div>

             {user ? (
               <div className="pt-2 border-t border-gray-800/40 flex items-center justify-between">
                 <div>
                   <span className="text-xs font-bold text-gray-200 block">Sign Out Current Session</span>
                   <span className="text-[10px] text-gray-500 block">Clear secure authentication tokens safely.</span>
                 </div>
                 <button
                   onClick={handleSignOut}
                   disabled={isLoading}
                   className="px-4 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 rounded-xl text-xs font-bold transition-colors flex items-center gap-2"
                 >
                   <LogOut className="w-3.5 h-3.5" />
                   <span>Sign Out</span>
                 </button>
               </div>
             ) : (
               <div className="pt-2 border-t border-gray-800/40 flex items-center justify-between">
                 <div>
                   <span className="text-xs font-bold text-gray-200 block">Require Secure Multi-Tenancy</span>
                   <span className="text-[10px] text-gray-500 block">Provision persistent dynamic tracking ledgers.</span>
                 </div>
                 <button
                   onClick={() => navigate('/auth')}
                   className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all shadow-md"
                 >
                   Authenticate Now
                 </button>
               </div>
             )}
           </div>
        </div>
      </div>

      {/* Primary Column 2: Compute Engine & Synchronization Engine Parameters */}
      <div className="col-span-12 lg:col-span-6 flex flex-col gap-6">
        
        {/* System Computation Controls */}
        <div className="bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-8 shadow-xl">
           <div className="flex items-center gap-3 mb-6">
             <Cpu className="w-5 h-5 text-indigo-400" />
             <span className="text-xs font-bold uppercase tracking-widest text-gray-400">System Execution Engine</span>
           </div>

           <form onSubmit={handleSavePreferences} className="space-y-5">
             {/* Target Base Currency */}
             <div>
               <label className="block text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1.5 flex items-center gap-1.5">
                 <Coins className="w-3 h-3 text-indigo-400" /> Target Preferred Display Currency
               </label>
               <select
                 value={currency}
                 onChange={(e) => setCurrency(e.target.value)}
                 className="w-full bg-[#161822] border border-gray-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 transition-colors"
               >
                 <option value="USD">USD ($) — Standard US Dollar</option>
                 <option value="INR">INR (₹) — Indian Rupee Equivalents</option>
                 <option value="EUR">EUR (€) — Euro Settlement Matrix</option>
                 <option value="GBp">GBp (p) — Sterling Pounds Core</option>
                 <option value="JPY">JPY (¥) — Japanese Yen Telemetry</option>
               </select>
             </div>

             {/* Reinforcement Learning Lookback Horizon */}
             <div>
               <label className="block text-[10px] text-gray-500 uppercase tracking-widest font-bold mb-1.5 flex items-center gap-1.5">
                 <Sliders className="w-3 h-3 text-indigo-400" /> Default Prediction Horizon
               </label>
               <select
                 value={horizon}
                 onChange={(e) => setHorizon(e.target.value)}
                 className="w-full bg-[#161822] border border-gray-800 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 transition-colors"
               >
                 <option value="14">14 Days Out — Responsive Scalping Cache</option>
                 <option value="30">30 Days Out — Optimal Ensemble Base</option>
                 <option value="60">60 Days Out — Extended Trend Multipliers</option>
               </select>
             </div>

             {/* Dry Run Toggle Switch */}
             <div className="pt-2 border-t border-gray-800/40 flex items-center justify-between">
               <div>
                 <span className="text-xs font-bold text-gray-200 block">Dry Run Simulation Mode</span>
                 <span className="text-[10px] text-gray-500 block max-w-xs">Run policy analysis securely inside localized mathematical reinforcement testing loops.</span>
               </div>
               
               <button
                 type="button"
                 onClick={() => setDryRun(!dryRun)}
                 className={`w-11 h-6 rounded-full transition-colors relative p-0.5 focus:outline-none ${
                   dryRun ? 'bg-indigo-600' : 'bg-gray-800'
                 }`}
               >
                 <div className={`w-5 h-5 rounded-full bg-white transition-transform ${
                   dryRun ? 'translate-x-5' : 'translate-x-0'
                 }`} />
               </button>
             </div>

             <div className="pt-4 border-t border-gray-800/40 flex justify-end">
               <button
                 type="submit"
                 className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-indigo-600/20 active:scale-95"
               >
                 Apply Hardware Settings
               </button>
             </div>
           </form>
        </div>

        {/* Dynamic Ledger Purging Sandbox Ground */}
        <div className="bg-[#11131a]/80 backdrop-blur-xl border border-gray-800/50 rounded-3xl p-8 shadow-xl">
           <div className="flex items-center gap-3 mb-6">
             <Database className="w-5 h-5 text-rose-400" />
             <span className="text-xs font-bold uppercase tracking-widest text-gray-400">Sandbox Ledger Storage</span>
           </div>

           <div className="space-y-4">
             <p className="text-xs text-gray-400 leading-relaxed font-medium">
               Purging unlinks your custom index lists instantly, leaving your initial tracking scope completely blank. This provides pristine isolated environments for test routines.
             </p>

             <div className="p-4 rounded-2xl bg-rose-500/5 border border-rose-500/10 flex items-center justify-between">
               <div>
                 <span className="text-xs font-bold text-rose-300 block">Active Ledger Manifest</span>
                 <span className="text-[10px] text-rose-400/80 block">Contains precisely {tickers.length} active symbols.</span>
               </div>
               
               <button
                 onClick={handlePurgeSpace}
                 disabled={tickers.length === 0}
                 className="px-4 py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-40 text-white rounded-xl text-xs font-bold transition-all shadow-lg shadow-rose-600/20 flex items-center gap-2 active:scale-95 shrink-0"
               >
                 <RefreshCw className="w-3.5 h-3.5" />
                 <span>Purge Ledger</span>
               </button>
             </div>
           </div>
        </div>

      </div>
    </div>
  );
};

export default SettingsView;
