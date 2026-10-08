import React, { useEffect, useState } from 'react';
import { Briefcase, TrendingUp, TrendingDown, PieChart, ArrowUpRight, Plus, RefreshCw, X } from 'lucide-react';
import { cn } from '../lib/utils/cn';
import { marketApi, StockItem } from '../lib/api/markets';

interface Holding {
  symbol: string;
  name: string;
  qty: number;
  avg: number;
  sector: string;
}

const DEFAULT_HOLDINGS: Holding[] = [
  { symbol: 'RELIANCE', name: 'Reliance Industries', qty: 50, avg: 1150.00, sector: 'Energy' },
  { symbol: 'HDFCBANK', name: 'HDFC Bank', qty: 120, avg: 680.00, sector: 'Financials' },
  { symbol: 'INFY', name: 'Infosys', qty: 75, avg: 980.00, sector: 'Technology' },
  { symbol: 'TCS', name: 'Tata Consultancy Services', qty: 30, avg: 2050.00, sector: 'Technology' },
];

export const PortfolioPage: React.FC = () => {
  const [holdings, setHoldings] = useState<Holding[]>(() => {
    try {
      const saved = localStorage.getItem('finpluse_portfolio_holdings');
      return saved ? JSON.parse(saved) : DEFAULT_HOLDINGS;
    } catch {
      return DEFAULT_HOLDINGS;
    }
  });

  const [stockQuotes, setStockQuotes] = useState<Record<string, StockItem>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);

  // New holding form state
  const [newSymbol, setNewSymbol] = useState('RELIANCE');
  const [newQty, setNewQty] = useState('10');
  const [newAvg, setNewAvg] = useState('1150');

  const fetchLiveQuotes = async (spin = false) => {
    if (spin) setIsRefreshing(true);
    try {
      const res = await marketApi.getTopStocks();
      const map: Record<string, StockItem> = {};
      res.data.forEach((stk) => {
        map[stk.symbol.toUpperCase()] = stk;
      });
      setStockQuotes(map);
    } catch (e) {
      console.error("Failed to load real quotes for portfolio:", e);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchLiveQuotes();
  }, []);

  const handleAddHolding = (e: React.FormEvent) => {
    e.preventDefault();
    const qty = parseFloat(newQty);
    const avg = parseFloat(newAvg);
    if (!qty || !avg || qty <= 0 || avg <= 0) return;

    const names: Record<string, string> = {
      RELIANCE: 'Reliance Industries',
      HDFCBANK: 'HDFC Bank',
      INFY: 'Infosys',
      TCS: 'Tata Consultancy Services',
    };
    const sectors: Record<string, string> = {
      RELIANCE: 'Energy',
      HDFCBANK: 'Financials',
      INFY: 'Technology',
      TCS: 'Technology',
    };

    const existingIdx = holdings.findIndex(h => h.symbol === newSymbol);
    let updated: Holding[];
    if (existingIdx >= 0) {
      const existing = holdings[existingIdx];
      const totalQty = existing.qty + qty;
      const weightedAvg = (existing.qty * existing.avg + qty * avg) / totalQty;
      updated = [...holdings];
      updated[existingIdx] = { ...existing, qty: totalQty, avg: Math.round(weightedAvg * 100) / 100 };
    } else {
      updated = [...holdings, {
        symbol: newSymbol,
        name: names[newSymbol] || newSymbol,
        qty,
        avg,
        sector: sectors[newSymbol] || 'Large Cap',
      }];
    }

    setHoldings(updated);
    localStorage.setItem('finpluse_portfolio_holdings', JSON.stringify(updated));
    setShowAddModal(false);
  };

  const handleRemoveHolding = (symbol: string) => {
    const updated = holdings.filter(h => h.symbol !== symbol);
    setHoldings(updated);
    localStorage.setItem('finpluse_portfolio_holdings', JSON.stringify(updated));
  };

  // Calculations with real live quotes
  let totalInvested = 0;
  let currentValue = 0;
  let todayPnl = 0;

  const enrichedHoldings = holdings.map((h) => {
    const quote = stockQuotes[h.symbol.toUpperCase()];
    const ltp = quote ? quote.price : h.avg;
    const dayChange = quote ? quote.change : 0;
    const dayChangePct = quote ? quote.change_percent : 0;

    const invested = h.qty * h.avg;
    const current = h.qty * ltp;
    const pnl = current - invested;
    const pnlPct = invested > 0 ? (pnl / invested) * 100 : 0;
    const posTodayPnl = h.qty * dayChange;

    totalInvested += invested;
    currentValue += current;
    todayPnl += posTodayPnl;

    return {
      ...h,
      ltp,
      dayChange,
      dayChangePct,
      invested,
      current,
      pnl,
      pnlPct,
      todayPnl: posTodayPnl,
      isUp: pnl >= 0,
      isDayUp: dayChange >= 0,
    };
  });

  const totalPnl = currentValue - totalInvested;
  const totalPnlPct = totalInvested > 0 ? (totalPnl / totalInvested) * 100 : 0;
  const todayPnlPct = totalInvested > 0 ? (todayPnl / totalInvested) * 100 : 0;

  return (
    <div className="p-6 md:p-10 space-y-8 animate-fadeIn max-w-7xl mx-auto pb-24">
      
      {/* ═══ Header Section ═══ */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-3xl font-bold text-white">My Portfolio</h1>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              LIVE NSE QUOTES
            </span>
          </div>
          <p className="text-slate-400 text-sm">Real-time valuation, realized & unrealized P&L calculated against live market prices.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchLiveQuotes(true)}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3 py-2 bg-white/[0.05] border border-white/10 text-slate-300 font-medium text-xs rounded-lg hover:bg-white/10 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={cn("w-3.5 h-3.5", isRefreshing && "animate-spin")} />
            Sync LTP
          </button>
          <button 
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-black font-bold text-sm rounded-lg hover:bg-emerald-400 transition-colors shadow-lg shadow-emerald-500/10"
          >
            <Plus className="w-4 h-4" />
            Add Position
          </button>
        </div>
      </div>

      {/* ═══ Metric Summary Cards (Live Calculated) ═══ */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-slate-800/50">
          <div className="text-xs uppercase font-medium tracking-wider text-slate-400 mb-1">Total Invested</div>
          <div className="text-2xl font-bold text-white">
            ₹{totalInvested.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-slate-500 mt-2">Capital committed</div>
        </div>

        <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-slate-800/50">
          <div className="text-xs uppercase font-medium tracking-wider text-slate-400 mb-1">Current Value</div>
          <div className="text-2xl font-bold text-emerald-400">
            ₹{currentValue.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="text-[11px] text-slate-500 mt-2">At current market LTP</div>
        </div>

        <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-slate-800/50">
          <div className="text-xs uppercase font-medium tracking-wider text-slate-400 mb-1">Total P&L</div>
          <div className={cn("text-2xl font-bold flex items-center gap-2", totalPnl >= 0 ? "text-emerald-400" : "text-rose-400")}>
            {totalPnl >= 0 ? '+' : '-'}₹{Math.abs(totalPnl).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            <span className={cn(
              "text-xs px-2 py-0.5 rounded-full font-semibold",
              totalPnl >= 0 ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"
            )}>
              {totalPnl >= 0 ? '+' : ''}{totalPnlPct.toFixed(2)}%
            </span>
          </div>
          <div className="text-[11px] text-slate-500 mt-2">Cumulative return</div>
        </div>

        <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-slate-800/50">
          <div className="text-xs uppercase font-medium tracking-wider text-slate-400 mb-1">Today's P&L</div>
          <div className={cn("text-2xl font-bold flex items-center gap-2", todayPnl >= 0 ? "text-emerald-400" : "text-rose-400")}>
            {todayPnl >= 0 ? '+' : '-'}₹{Math.abs(todayPnl).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            <span className={cn(
              "text-xs px-2 py-0.5 rounded-full font-semibold",
              todayPnl >= 0 ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"
            )}>
              {todayPnl >= 0 ? '+' : ''}{todayPnlPct.toFixed(2)}%
            </span>
          </div>
          <div className="text-[11px] text-slate-500 mt-2">Intraday day movement</div>
        </div>
      </div>

      {/* ═══ Current Holdings Table ═══ */}
      <div className="bg-[#0a0a0a] border border-slate-800/50 rounded-2xl overflow-hidden shadow-xl">
        <div className="p-6 border-b border-slate-800/50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-bold text-white">Current Holdings</h2>
          </div>
          <span className="text-xs text-slate-400">
            {enrichedHoldings.length} Positions Active
          </span>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800/50 text-xs uppercase tracking-wider text-slate-500 bg-white/[0.02]">
                <th className="p-4 font-medium">Instrument</th>
                <th className="p-4 font-medium text-right">Qty</th>
                <th className="p-4 font-medium text-right">Avg Price</th>
                <th className="p-4 font-medium text-right">Live LTP</th>
                <th className="p-4 font-medium text-right">Day Chg</th>
                <th className="p-4 font-medium text-right">Current Value</th>
                <th className="p-4 font-medium text-right">Total P&L</th>
                <th className="p-4 font-medium text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {enrichedHoldings.map((pos) => (
                <tr key={pos.symbol} className="hover:bg-white/[0.02] transition-colors">
                  <td className="p-4">
                    <div className="font-bold text-white text-sm">{pos.symbol}</div>
                    <div className="text-xs text-slate-400 flex items-center gap-1.5">
                      <span>{pos.name}</span>
                      <span className="text-[10px] px-1 py-0.2 rounded bg-white/[0.05] text-slate-400">{pos.sector}</span>
                    </div>
                  </td>
                  <td className="p-4 text-right font-medium text-white">{pos.qty}</td>
                  <td className="p-4 text-right text-slate-300 font-mono">₹{pos.avg.toFixed(2)}</td>
                  <td className="p-4 text-right font-mono font-bold text-white">
                    ₹{pos.ltp.toFixed(2)}
                  </td>
                  <td className="p-4 text-right font-mono text-xs">
                    <span className={cn("font-medium", pos.isDayUp ? "text-emerald-400" : "text-rose-400")}>
                      {pos.dayChange >= 0 ? '+' : ''}{pos.dayChange.toFixed(2)} ({pos.dayChangePct >= 0 ? '+' : ''}{pos.dayChangePct.toFixed(2)}%)
                    </span>
                  </td>
                  <td className="p-4 text-right font-medium font-mono text-white">
                    ₹{pos.current.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td className="p-4 text-right font-mono">
                    <div className={cn("font-bold text-sm", pos.isUp ? "text-emerald-400" : "text-rose-400")}>
                      {pos.pnl >= 0 ? '+' : '-'}₹{Math.abs(pos.pnl).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    <div className={cn("text-xs font-semibold", pos.isUp ? "text-emerald-400" : "text-rose-400")}>
                      {pos.pnl >= 0 ? '+' : ''}{pos.pnlPct.toFixed(2)}%
                    </div>
                  </td>
                  <td className="p-4 text-center">
                    <button
                      onClick={() => handleRemoveHolding(pos.symbol)}
                      className="text-xs text-slate-500 hover:text-rose-400 transition-colors p-1"
                      title="Remove holding"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ═══ Add Holding Modal ═══ */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-[#121212] border border-slate-800 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-bold text-white">Add / Update Position</h3>
              <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleAddHolding} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Select Instrument</label>
                <select
                  value={newSymbol}
                  onChange={(e) => {
                    setNewSymbol(e.target.value);
                    const q = stockQuotes[e.target.value];
                    if (q) setNewAvg(q.price.toString());
                  }}
                  className="w-full bg-[#1e1e1e] border border-slate-700 rounded-lg p-2.5 text-white text-sm focus:outline-none focus:border-emerald-500"
                >
                  <option value="RELIANCE">RELIANCE (Reliance Industries)</option>
                  <option value="HDFCBANK">HDFCBANK (HDFC Bank)</option>
                  <option value="INFY">INFY (Infosys)</option>
                  <option value="TCS">TCS (Tata Consultancy Services)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Quantity</label>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={newQty}
                  onChange={(e) => setNewQty(e.target.value)}
                  className="w-full bg-[#1e1e1e] border border-slate-700 rounded-lg p-2.5 text-white text-sm focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Buy Average Price (₹)</label>
                <input
                  type="number"
                  min="0.1"
                  step="0.05"
                  value={newAvg}
                  onChange={(e) => setNewAvg(e.target.value)}
                  className="w-full bg-[#1e1e1e] border border-slate-700 rounded-lg p-2.5 text-white text-sm focus:outline-none focus:border-emerald-500"
                  required
                />
              </div>

              <div className="pt-2 flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 px-4 py-2 bg-white/[0.05] border border-white/10 text-slate-300 font-medium text-sm rounded-lg hover:bg-white/10"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-emerald-500 text-black font-bold text-sm rounded-lg hover:bg-emerald-400"
                >
                  Save Position
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
