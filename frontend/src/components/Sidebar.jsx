import React from 'react';
import { 
  PieChart, 
  Activity, 
  Shield, 
  MessageSquare, 
  TrendingUp 
} from 'lucide-react';

import { Link, NavLink } from 'react-router-dom';

const Sidebar = ({ tickers }) => {
  const menuItems = [
    { id: 'Overview', icon: PieChart, path: '/dashboard' },
    { id: 'Forecasting', icon: Activity, path: '/dashboard/forecast' },
    { id: 'Sentiment', icon: Shield, path: '/dashboard/sentiment' },
    { id: 'Chat Advisor', icon: MessageSquare, path: '/dashboard/chat' },
  ];

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-[#11131a] border-r border-gray-800/50 p-6 flex flex-col gap-8 z-50">
      <Link to="/" className="flex items-center gap-3 group hover:opacity-80 transition-all">
        <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-600/20 group-hover:scale-110 transition-transform">
          <TrendingUp className="w-6 h-6 text-white" />
        </div>
        <span className="text-xl font-bold tracking-tight">SmartAdvisor</span>
      </Link>

      <nav className="flex-1 flex flex-col gap-2">
        {menuItems.map((item) => (
          <NavLink
            key={item.id}
            to={item.path}
            end={item.path === '/dashboard'}
            className={({ isActive }) => `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
              isActive 
                ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-600/20 shadow-inner' 
                : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-200'
            }`}
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.id}</span>
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto p-4 bg-gray-800/20 rounded-2xl border border-gray-800/50">
        <p className="text-xs text-gray-500 mb-2 uppercase tracking-widest font-semibold">Current Portfolio</p>
        <div className="flex flex-wrap gap-2">
          {tickers.map(t => (
            <span key={t} className="px-2 py-1 bg-indigo-600/20 text-indigo-400 rounded text-xs font-bold ring-1 ring-indigo-600/30">
              {t}
            </span>
          ))}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
