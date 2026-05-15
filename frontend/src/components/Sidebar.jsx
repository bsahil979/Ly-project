import React, { useState, useEffect, useCallback } from 'react';
import { 
  LayoutDashboard, 
  Compass,
  Search,
  Star,
  Radio,
  Wallet,
  Briefcase,
  Settings,
  TrendingUp,
  MessageSquare,
  Activity,
  Cpu,
  Layers,
  LogOut,
  ChevronLeft,
  ChevronRight,
  User
} from 'lucide-react';

import { Link, NavLink, useNavigate } from 'react-router-dom';
import { AuthService, supabase } from '../services/supabaseClient';

const Sidebar = ({ tickers }) => {
  const [user, setUser] = useState(null);
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();

  const checkUser = useCallback(async () => {
    // First try to get user from localStorage directly
    try {
      const mockUserStr = localStorage.getItem('smart_portfolio_mock_user');
      if (mockUserStr) {
        const mockUser = JSON.parse(mockUserStr);
        setUser(mockUser);
        return;
      }
    } catch (e) {
      console.error('Error reading localStorage:', e);
    }

    // Then try AuthService
    const res = await AuthService.getCurrentUser();
    const currentUser = res?.data?.user || null;
    setUser(currentUser);
  }, []);

  useEffect(() => {
    // Initial check
    checkUser();

    // Reactive listener for login/logout events (Supabase)
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) {
        setUser(session.user);
      } else {
        // Check localStorage if supabase session is null
        try {
          const mockUserStr = localStorage.getItem('smart_portfolio_mock_user');
          if (mockUserStr) {
            setUser(JSON.parse(mockUserStr));
          } else {
            setUser(null);
          }
        } catch {
          setUser(null);
        }
      }
    });

    // Reactive listener for mock fallback events
    const handleAuthChange = () => {
      checkUser();
    };
    window.addEventListener('auth-change', handleAuthChange);
    
    // Storage change listener
    const handleStorageChange = (e) => {
      if (e.key === 'smart_portfolio_mock_user') {
        checkUser();
      }
    };
    window.addEventListener('storage', handleStorageChange);

    // Poll to catch updates
    const pollInterval = setInterval(checkUser, 200);

    return () => {
      clearInterval(pollInterval);
      subscription.unsubscribe();
      window.removeEventListener('auth-change', handleAuthChange);
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [checkUser]);

  const handleSignOut = async () => {
    await AuthService.logout();
    setUser(null);
    navigate('/');
  };

  const sections = [
    {
      items: [
        { id: 'Home', icon: LayoutDashboard, path: '/dashboard' },
        { id: 'Discover', icon: Compass, path: '/dashboard/forecast' },
        { id: 'Research', icon: Search, path: '/dashboard/research' },
      ]
    },
    {
      label: 'Tools',
      items: [
        { id: 'Watchlist', icon: Star, path: '/dashboard/manage' },
        { id: 'Fundamentals', icon: Activity, path: '/dashboard/fundamentals' },
        { id: 'RL Trading Brain', icon: Cpu, path: '/dashboard/trading' },
        { id: 'AI Chat Bot', icon: MessageSquare, path: '/dashboard/chat' },
      ]
    },
    {
      label: 'Portfolio',
      items: [
        { id: 'Portfolio Toolbox', icon: Briefcase, path: '/dashboard/manage', end: false },
      ]
    },
    {
      label: 'Account',
      items: [
        { id: 'Settings', icon: Settings, path: '/dashboard/settings' },
      ]
    },
  ];

  return (
    <aside className={`fixed left-0 top-0 h-full ${collapsed ? 'w-[72px]' : 'w-64'} bg-[#0e1017] border-r border-gray-800/40 flex flex-col z-50 transition-all duration-300`}>
      
      {/* Logo Header */}
      <div className={`flex items-center ${collapsed ? 'justify-center' : 'justify-between'} px-5 pt-6 pb-4`}>
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 bg-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-600/20 group-hover:scale-105 transition-transform shrink-0">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <span className="text-lg font-bold tracking-tight text-white">
              <span className="text-indigo-400">S</span>mart<span className="text-indigo-400">A</span>dvisor
            </span>
          )}
        </Link>
        {!collapsed && (
          <button 
            onClick={() => setCollapsed(true)}
            className="w-7 h-7 rounded-lg bg-gray-800/40 border border-gray-800 flex items-center justify-center text-gray-500 hover:text-white hover:bg-gray-800 transition-all"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
          </button>
        )}
        {collapsed && (
          <button 
            onClick={() => setCollapsed(false)}
            className="absolute -right-3 top-7 w-6 h-6 rounded-full bg-[#0e1017] border border-gray-800 flex items-center justify-center text-gray-500 hover:text-white transition-all z-60 shadow-lg"
          >
            <ChevronRight className="w-3 h-3" />
          </button>
        )}
      </div>

      {/* Scrollable Navigation Body */}
      <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-1 custom-scrollbar">
        {sections.map((section, sIdx) => (
          <div key={sIdx} className={sIdx > 0 ? 'pt-4' : ''}>
            {/* Section Label */}
            {section.label && !collapsed && (
              <p className="px-3 mb-2 text-[10px] font-bold uppercase tracking-[0.15em] text-gray-600">
                {section.label}
              </p>
            )}
            {section.label && collapsed && (
              <div className="mx-auto w-8 border-t border-gray-800/60 mb-3" />
            )}

            {/* Section Items */}
            {section.items.map((item) => (
              <NavLink
                key={item.id + item.path}
                to={item.path}
                end={item.path === '/dashboard'}
                title={collapsed ? item.id : undefined}
                className={({ isActive }) => `
                  flex items-center gap-3 rounded-xl transition-all duration-200 mb-0.5
                  ${collapsed ? 'justify-center px-0 py-3 mx-1' : 'px-3 py-2.5'}
                  ${isActive
                    ? 'bg-indigo-600/10 text-white border-l-2 border-indigo-500'
                    : 'text-gray-400 hover:bg-gray-800/40 hover:text-gray-200 border-l-2 border-transparent'
                  }
                `}
              >
                <item.icon className={`shrink-0 ${collapsed ? 'w-5 h-5' : 'w-[18px] h-[18px]'}`} />
                {!collapsed && (
                  <span className="text-[13px] font-medium">{item.id}</span>
                )}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* Bottom Auth Section */}
      <div className={`mt-auto border-t border-gray-800/40 ${collapsed ? 'px-2 py-4' : 'px-4 py-5'} space-y-2`}>
        {user ? (
          <>
            {/* User identity mini-badge */}
            {!collapsed && (
              <div className="flex items-center gap-2.5 px-2 py-2 mb-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center text-white text-xs font-black shadow-md shrink-0">
                  {user.email?.[0]?.toUpperCase() || 'U'}
                </div>
                <div className="flex-1 min-w-0">
                  <span className="text-xs font-bold text-gray-200 block truncate">
                    {user.user_metadata?.full_name || user.email?.split('@')[0]}
                  </span>
                  <span className="text-[10px] text-gray-500 block truncate">{user.email}</span>
                </div>
              </div>
            )}
            {collapsed && (
              <div className="flex justify-center mb-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center text-white text-xs font-black">
                  {user.email?.[0]?.toUpperCase() || 'U'}
                </div>
              </div>
            )}
            <button
              onClick={handleSignOut}
              title={collapsed ? 'Sign Out' : undefined}
              className={`w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-bold transition-all bg-gray-800/40 hover:bg-gray-800 text-gray-400 hover:text-rose-400 border border-gray-800/60 ${collapsed ? 'px-0' : 'px-4'}`}
            >
              <LogOut className="w-4 h-4 shrink-0" />
              {!collapsed && <span>Sign Out</span>}
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => navigate('/auth')}
              className={`w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-bold transition-all bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/20 ${collapsed ? 'px-0' : 'px-4'}`}
            >
              <User className="w-4 h-4 shrink-0" />
              {!collapsed && <span>Sign Up</span>}
            </button>
            <button
              onClick={() => navigate('/auth')}
              className={`w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-bold transition-all bg-gray-800/50 hover:bg-gray-800 text-gray-300 border border-gray-800/60 ${collapsed ? 'px-0' : 'px-4'}`}
            >
              <LogOut className="w-4 h-4 shrink-0" />
              {!collapsed && <span>Log In</span>}
            </button>
          </>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
