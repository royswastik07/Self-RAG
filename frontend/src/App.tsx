import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Database, MessageSquare, Settings, Activity } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import DatasetsPage from './pages/DatasetsPage';
import ChatPage from './pages/ChatPage';
import { getStats } from './services/api';

function Sidebar() {
  const location = useLocation();
  const navItems = [
    { path: '/', name: 'Dashboard', icon: <Activity className="w-5 h-5" /> },
    { path: '/datasets', name: 'Datasets', icon: <Database className="w-5 h-5" /> },
    { path: '/chat', name: 'Chat', icon: <MessageSquare className="w-5 h-5" /> },
    { path: '/settings', name: 'Settings', icon: <Settings className="w-5 h-5" /> },
  ];

  return (
    <div className="w-64 h-screen bg-slate-900 text-slate-300 flex flex-col">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">Self-RAG</span>
        </h1>
      </div>
      <nav className="flex-1 px-4 space-y-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                isActive 
                  ? 'bg-slate-800 text-emerald-400 font-medium' 
                  : 'hover:bg-slate-800/50 hover:text-white'
              }`}
            >
              {item.icon}
              {item.name}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-slate-800 text-xs text-slate-500 text-center">
        Enterprise RAG V1.0
      </div>
    </div>
  );
}

function DashboardPlaceholder() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats
  });

  return (
    <div className="p-8">
      <h2 className="text-3xl font-bold text-slate-800 mb-6">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { label: 'Total Datasets', value: stats?.totalDatasets ?? 0 },
          { label: 'Total Documents', value: stats?.totalDocuments ?? 0 },
          { label: 'Avg Confidence', value: stats?.avgConfidence ?? '0%' }
        ].map((stat, i) => (
          <div key={i} className="glass-panel p-6 flex flex-col gap-2">
            <span className="text-slate-500 font-medium">{stat.label}</span>
            <span className="text-4xl font-bold text-slate-800">
              {isLoading ? '...' : stat.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Router>
      <div className="flex h-screen w-full bg-slate-50 overflow-hidden font-sans">
        <Sidebar />
        <main className="flex-1 overflow-y-auto custom-scrollbar relative">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-50/50 via-transparent to-cyan-50/50 pointer-events-none" />
          <div className="relative z-10 h-full">
            <Routes>
              <Route path="/" element={<DashboardPlaceholder />} />
              <Route path="/datasets" element={<DatasetsPage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/settings" element={<div className="p-8">Settings (WIP)</div>} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}
