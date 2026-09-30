import React from 'react';
import { Search, Activity, BookOpen, Clock, FileText } from 'lucide-react';

export const ResearchPage: React.FC = () => {
  return (
    <div className="p-6 md:p-10 space-y-8 animate-fadeIn max-w-7xl mx-auto pb-24">
      
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Stock Research</h1>
          <p className="text-slate-400">Deep-dive technicals, fundamentals, and AI insights.</p>
        </div>
        
        <div className="relative w-full md:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input 
            type="text" 
            placeholder="Search NSE stocks..." 
            className="w-full bg-[#0a0a0a] border border-slate-800 rounded-lg py-2 pl-9 pr-4 text-sm text-white focus:outline-none focus:border-emerald-500/50 transition-colors"
          />
        </div>
      </div>

      <div className="flex flex-col items-center justify-center py-20 text-center border border-slate-800/50 rounded-2xl bg-[#0a0a0a]">
        <div className="w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-6 border border-blue-500/20">
          <BookOpen className="w-8 h-8 text-blue-400" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Search an Instrument</h2>
        <p className="text-slate-400 max-w-sm mb-6">
          Enter a stock symbol above to load comprehensive technical charts, fundamental metrics, and the AI Copilot research view.
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          <span className="px-3 py-1 bg-white/[0.04] border border-white/[0.05] rounded-full text-xs text-slate-300 hover:bg-white/10 cursor-pointer transition-colors">
            RELIANCE
          </span>
          <span className="px-3 py-1 bg-white/[0.04] border border-white/[0.05] rounded-full text-xs text-slate-300 hover:bg-white/10 cursor-pointer transition-colors">
            HDFCBANK
          </span>
          <span className="px-3 py-1 bg-white/[0.04] border border-white/[0.05] rounded-full text-xs text-slate-300 hover:bg-white/10 cursor-pointer transition-colors">
            TCS
          </span>
        </div>
      </div>
      
    </div>
  );
};
