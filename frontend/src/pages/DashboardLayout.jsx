import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Layout from '../components/Layout';

const DashboardLayout = ({ tickers, setTickers }) => {
  return (
    <div className="min-h-screen bg-[#07080d] text-gray-100 font-sans selection:bg-indigo-500/30">
      <Sidebar tickers={tickers} />
      <Layout tickers={tickers} setTickers={setTickers}>
        <div className="animate-in fade-in duration-500">
          <Outlet />
        </div>
      </Layout>
    </div>
  );
};

export default DashboardLayout;
