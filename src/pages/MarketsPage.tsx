import React from 'react';
import { TrendingUp, TrendingDown, Activity, Globe, BarChart2 } from 'lucide-react';
import { cn } from '../../lib/utils/cn';

const INDICES = [
  { name: 'NIFTY 50', value: '22,512.45', change: '+124.30', changePct: '+0.55%', isUp: true },
  { name: 'BANK NIFTY', value: '48,150.10', change: '-45.20', changePct: '-0.09%', isUp: false },
  { name: 'SENSEX', value: '74,225.50', change: '+350.80', changePct: '+0.47%', isUp: true },
  { name: 'NIFTY IT', value: '35,120.90', change: '+410.20', changePct: '+1.18%', isUp: true },
  { name: 'S&P 500', value: '5,214.50', change: '+45.10', changePct: '+0.87%', isUp: true },
  { name: 'NASDAQ', value: '16,340.20', change: '+180.50', changePct: '+1.12%', isUp: true },
];

const SECTORS = [
  { name: 'Technology', performance: '+1.2%', isUp: true, weight: '15%' },
  { name: 'Financials', performance: '-0.4%', isUp: false, weight: '35%' },
  { name: 'Energy', performance: '+0.8%', isUp: true, weight: '12%' },
  { name: 'Auto', performance: '+2.1%', isUp: true, weight: '8%' },
  { name: 'FMCG', performance: '-0.1%', isUp: false, weight: '9%' },
  { name: 'Healthcare', performance: '+0.5%', isUp: true, weight: '6%' },
];

export const MarketsPage: React.FC = () => {
  return (
    <div className="p-6 md:p-10 space-y-8 animate-fadeIn max-w-7xl mx-auto pb-24">
      
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Global Markets</h1>
          <p className="text-slate-400">Real-time indices and sectoral performance.</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          MARKETS OPEN
        </div>
      </div>

      {/* Indices Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {INDICES.map((idx) => (
          <div key={idx.name} className="p-5 rounded-2xl bg-[#0a0a0a] border border-slate-800/50 hover:border-slate-700/50 transition-colors group relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
              <Globe className="w-16 h-16 text-white" />
            </div>
            <div className="relative z-10">
              <h3 className="text-sm font-medium text-slate-400 mb-1">{idx.name}</h3>
              <div className="text-2xl font-bold text-white mb-2">{idx.value}</div>
              <div className={cn(
                "flex items-center gap-1.5 text-sm font-medium",
                idx.isUp ? "text-emerald-400" : "text-rose-400"
              )}>
                {idx.isUp ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                {idx.change} ({idx.changePct})
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Sector Heatmap & Breadth */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-6 rounded-2xl bg-[#0a0a0a] border border-slate-800/50">
          <div className="flex items-center gap-2 mb-6">
            <BarChart2 className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-bold text-white">Sectoral Heatmap</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {SECTORS.map((sector) => (
              <div 
                key={sector.name} 
                className={cn(
                  "p-4 rounded-xl border flex flex-col justify-between h-24",
                  sector.isUp 
                    ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" 
                    : "bg-rose-500/10 border-rose-500/20 text-rose-400"
                )}
              >
                <div className="text-sm font-medium text-white">{sector.name}</div>
                <div className="flex items-end justify-between">
                  <div className="text-lg font-bold">{sector.performance}</div>
                  <div className="text-xs opacity-60 font-mono">Wgt: {sector.weight}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-slate-800/50 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-6">
              <Activity className="w-5 h-5 text-blue-400" />
              <h2 className="text-lg font-bold text-white">Market Breadth</h2>
            </div>
            <div className="space-y-6">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-emerald-400 font-medium">Advances (1,245)</span>
                  <span className="text-rose-400 font-medium">Declines (850)</span>
                </div>
                <div className="h-2 bg-rose-500/20 rounded-full overflow-hidden flex">
                  <div className="h-full bg-emerald-500" style={{ width: '60%' }}></div>
                </div>
              </div>
              
              <div className="pt-4 border-t border-slate-800/50">
                <div className="text-sm text-slate-400 mb-1">52-Week Highs vs Lows</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-emerald-400">142</span>
                  <span className="text-slate-500">/</span>
                  <span className="text-lg font-bold text-rose-400">12</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
};
