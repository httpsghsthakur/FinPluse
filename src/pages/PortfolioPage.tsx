import React from 'react';
import { Briefcase, TrendingUp, TrendingDown, PieChart, ArrowUpRight, Plus } from 'lucide-react';
import { cn } from '../lib/utils/cn';

const POSITIONS = [
  { symbol: 'RELIANCE', name: 'Reliance Ind.', qty: 50, avg: 2850.50, ltp: 2945.10, pnl: '+4,730.00', pnlPct: '+3.32%', isUp: true },
  { symbol: 'HDFCBANK', name: 'HDFC Bank', qty: 120, avg: 1450.00, ltp: 1432.50, pnl: '-2,100.00', pnlPct: '-1.21%', isUp: false },
  { symbol: 'INFY', name: 'Infosys', qty: 75, avg: 1390.25, ltp: 1420.75, pnl: '+2,287.50', pnlPct: '+2.19%', isUp: true },
];

export const PortfolioPage: React.FC = () => {
  return (
    <div className="p-6 md:p-10 space-y-8 animate-fadeIn max-w-7xl mx-auto pb-24">
      
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">My Portfolio</h1>
          <p className="text-slate-400">Live holdings, performance, and risk analysis.</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-black font-bold text-sm rounded-lg hover:bg-emerald-400 transition-colors">
          <Plus className="w-4 h-4" />
          Add Transaction
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-slate-800/50">
          <div className="text-sm text-slate-400 mb-1">Total Invested</div>
          <div className="text-2xl font-bold text-white">₹4,20,538.75</div>
        </div>
        <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-slate-800/50">
          <div className="text-sm text-slate-400 mb-1">Current Value</div>
          <div className="text-2xl font-bold text-emerald-400">₹4,25,456.25</div>
        </div>
        <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-slate-800/50">
          <div className="text-sm text-slate-400 mb-1">Total P&L</div>
          <div className="text-2xl font-bold text-emerald-400 flex items-center gap-2">
            +₹4,917.50 <span className="text-sm bg-emerald-500/10 px-2 py-0.5 rounded-full">+1.17%</span>
          </div>
        </div>
        <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-slate-800/50">
          <div className="text-sm text-slate-400 mb-1">Today's P&L</div>
          <div className="text-2xl font-bold text-rose-400 flex items-center gap-2">
            -₹850.20 <span className="text-sm bg-rose-500/10 px-2 py-0.5 rounded-full">-0.20%</span>
          </div>
        </div>
      </div>

      <div className="bg-[#0a0a0a] border border-slate-800/50 rounded-2xl overflow-hidden">
        <div className="p-6 border-b border-slate-800/50 flex items-center gap-2">
          <Briefcase className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-bold text-white">Current Holdings</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800/50 text-xs uppercase tracking-wider text-slate-500 bg-white/[0.02]">
                <th className="p-4 font-medium">Instrument</th>
                <th className="p-4 font-medium text-right">Qty</th>
                <th className="p-4 font-medium text-right">Avg Price</th>
                <th className="p-4 font-medium text-right">LTP</th>
                <th className="p-4 font-medium text-right">Current Value</th>
                <th className="p-4 font-medium text-right">P&L</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {POSITIONS.map((pos, i) => (
                <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                  <td className="p-4">
                    <div className="font-bold text-white">{pos.symbol}</div>
                    <div className="text-xs text-slate-400">{pos.name}</div>
                  </td>
                  <td className="p-4 text-right font-medium text-white">{pos.qty}</td>
                  <td className="p-4 text-right text-slate-300">₹{pos.avg.toFixed(2)}</td>
                  <td className="p-4 text-right text-slate-300">₹{pos.ltp.toFixed(2)}</td>
                  <td className="p-4 text-right font-medium text-white">
                    ₹{(pos.qty * pos.ltp).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="p-4 text-right">
                    <div className={cn("font-bold", pos.isUp ? "text-emerald-400" : "text-rose-400")}>
                      {pos.pnl}
                    </div>
                    <div className={cn("text-xs", pos.isUp ? "text-emerald-400" : "text-rose-400")}>
                      {pos.pnlPct}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
