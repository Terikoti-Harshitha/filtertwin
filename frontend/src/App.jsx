import React, { useState } from 'react';
import { PurifierProvider } from './context/PurifierContext';
import Navbar from './components/layout/Navbar';
import Sidebar from './components/layout/Sidebar';
import Dashboard from './pages/Dashboard';
import Simulator from './pages/Simulator';
import Monitoring from './pages/Monitoring';
import Diagnostics from './pages/Diagnostics';
import Evaluation from './pages/Evaluation';
import Maintenance from './pages/Maintenance';
import History from './pages/History';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderActivePage = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard setActiveTab={setActiveTab} />;
      case 'simulator':
        return <Simulator />;
      case 'monitoring':
        return <Monitoring />;
      case 'diagnostics':
        return <Diagnostics setActiveTab={setActiveTab} />;
      case 'evaluation':
        return <Evaluation />;
      case 'maintenance':
        return <Maintenance />;
      case 'history':
        return <History />;
      default:
        return <Dashboard setActiveTab={setActiveTab} />;
    }
  };

  return (
    <PurifierProvider>
      <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100">
        <Navbar />
        <div className="flex flex-1 overflow-hidden">
          <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
          <main className="flex-1 overflow-y-auto p-6 lg:p-8 max-w-7xl mx-auto w-full">
            {renderActivePage()}
          </main>
        </div>
      </div>
    </PurifierProvider>
  );
}
