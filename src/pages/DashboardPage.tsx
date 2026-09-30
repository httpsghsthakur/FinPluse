import React, { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart2,
  Globe,
  ChevronRight,
  Sparkles,
  AlertTriangle,
  Search,
  Eye,
  PieChart
} from "lucide-react";
import { KpiSkeleton } from "../components/ui/Skeletons";
import { marketApi, MarketOverview } from "../lib/api/markets";
import { formatCurrency } from "../lib/utils/formatters";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from "recharts";

// Mock data for charts
const generateMockChart = () => Array.from({ length: 20 }, (_, i) => ({
  time: i,
  value: 22000 + Math.random() * 1000 + (i * 20)
}));

export const DashboardPage: React.FC = () => {
  const [marketData, setMarketData] = useState<MarketOverview[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchMarkets = async () => {
      try {
        const response = await marketApi.getOverview();
        setMarketData(response.data);
      } catch (e) {
        console.error("Error loading market data", e);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchMarkets();
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiSkeleton />
          <KpiSkeleton />
          <KpiSkeleton />
          <KpiSkeleton />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* ═══ Header Section ═══ */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Market Intelligence</h1>
          <p className="text-sm text-slate-400 mt-1">Live market overview, AI outlook, and portfolio analytics.</p>
        </div>
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input 
            type="text" 
            placeholder="Search instruments (e.g. RELIANCE)..." 
            className="pl-9 pr-4 py-2 bg-slate-900/50 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 w-full md:w-80 transition-all"
          />
        </div>
      </div>

      {/* ═══ Live Market Snapshot (KPIs) ═══ */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {marketData.map((market, idx) => {
          const isPositive = (market.change_percent || 0) >= 0;
          return (
            <div key={market.symbol} className="glass-card rounded-2xl p-5 relative overflow-hidden group hover:border-slate-700 transition-colors animate-fadeInUp" style={{ animationDelay: `${idx * 0.1}s` }}>
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-2">
                  <div className={`p-1.5 rounded bg-slate-800/50 ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {market.symbol.includes("VIX") ? <Activity className="w-4 h-4" /> : <Globe className="w-4 h-4" />}
                  </div>
                  <h3 className="text-sm font-semibold text-slate-300">{market.symbol}</h3>
                </div>
              </div>
              <div className="space-y-1">
                <div className="text-2xl font-bold text-white tracking-tight">
                  {market.ltp?.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </div>
                <div className={`flex items-center gap-1.5 text-sm font-medium ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {isPositive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                  <span>{isPositive ? '+' : ''}{market.change?.toFixed(2)}</span>
                  <span>({isPositive ? '+' : ''}{market.change_percent?.toFixed(2)}%)</span>
                </div>
              </div>
              
              {/* Mini Sparkline */}
              <div className="absolute bottom-0 left-0 right-0 h-12 opacity-20 group-hover:opacity-40 transition-opacity pointer-events-none">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={generateMockChart()}>
                    <defs>
                      <linearGradient id={`grad-${idx}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={isPositive ? '#10B981' : '#F43F5E'} stopOpacity={0.8} />
                        <stop offset="95%" stopColor={isPositive ? '#10B981' : '#F43F5E'} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <Area type="monotone" dataKey="value" stroke={isPositive ? '#10B981' : '#F43F5E'} fill={`url(#grad-${idx})`} strokeWidth={1.5} isAnimationActive={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ═══ AI Market Outlook ═══ */}
        <div className="lg:col-span-2 glass-card rounded-2xl p-6 space-y-5 relative overflow-hidden animate-fadeInUp delay-200">
          <div className="absolute top-0 right-0 p-32 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />
          
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-emerald-400" />
              AI Market Outlook
            </h2>
            <div className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold uppercase tracking-wider">
              Bullish Regime
            </div>
          </div>
          
          <div className="prose prose-invert prose-sm max-w-none text-slate-300">
            <p>
              The broader market structure indicates a <strong className="text-emerald-400">strong bullish bias</strong> heading into the afternoon session. Institutional accumulation is visible in the IT and Banking sectors, while Auto remains neutral.
            </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2">
            <div className="p-3 bg-slate-900/50 rounded-xl border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">Directional Prob</div>
              <div className="text-lg font-bold text-emerald-400">68% UP</div>
            </div>
            <div className="p-3 bg-slate-900/50 rounded-xl border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">Volatility Exp</div>
              <div className="text-lg font-bold text-amber-400">ELEVATED</div>
            </div>
            <div className="p-3 bg-slate-900/50 rounded-xl border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">Breadth</div>
              <div className="text-lg font-bold text-emerald-400">2.4 : 1</div>
            </div>
            <div className="p-3 bg-slate-900/50 rounded-xl border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider mb-1">Risk Level</div>
              <div className="text-lg font-bold text-indigo-400">MODERATE</div>
            </div>
          </div>
        </div>

        {/* ═══ Watchlist / Top Movers ═══ */}
        <div className="glass-card rounded-2xl p-6 space-y-4 animate-fadeInUp delay-300">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <Eye className="w-4 h-4 text-indigo-400" />
              Watchlist Action
            </h2>
            <button className="text-xs text-indigo-400 hover:text-indigo-300 font-medium">View All</button>
          </div>
          
          <div className="space-y-3">
            {[
              { sym: 'HDFCBANK', ltp: '1,432.50', chg: '+1.2%', trend: 'up' },
              { sym: 'RELIANCE', ltp: '2,945.10', chg: '+0.8%', trend: 'up' },
              { sym: 'INFY', ltp: '1,420.75', chg: '-0.4%', trend: 'down' },
              { sym: 'TCS', ltp: '3,890.00', chg: '+0.1%', trend: 'up' },
              { sym: 'ZOMATO', ltp: '184.20', chg: '+4.5%', trend: 'up', alert: true },
            ].map(stock => (
              <div key={stock.sym} className="flex justify-between items-center group cursor-pointer hover:bg-slate-800/30 p-2 -mx-2 rounded-lg transition-colors">
                <div>
                  <div className="text-sm font-bold text-slate-200 flex items-center gap-2">
                    {stock.sym}
                    {stock.alert && <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" title="Volume Spike Alert" />}
                  </div>
                  <div className="text-[10px] text-slate-500 uppercase tracking-wider">EQ • NSE</div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-mono text-slate-200">{stock.ltp}</div>
                  <div className={`text-[11px] font-bold ${stock.trend === 'up' ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {stock.chg}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ═══ Portfolio & Personal Finance (Secondary Module) ═══ */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fadeInUp delay-400">
        <div className="glass-card rounded-2xl p-6 border border-slate-800/50 hover:border-slate-700/50 transition-colors cursor-pointer group">
          <div className="flex justify-between items-start">
            <div>
              <div className="p-2 bg-indigo-500/10 rounded-lg inline-block mb-3 group-hover:bg-indigo-500/20 transition-colors">
                <PieChart className="w-5 h-5 text-indigo-400" />
              </div>
              <h3 className="text-lg font-bold text-slate-100">Portfolio Analytics</h3>
              <p className="text-sm text-slate-400 mt-1">Track your investments, sector exposure, and AI portfolio risk analysis.</p>
            </div>
            <ChevronRight className="w-5 h-5 text-slate-500 group-hover:text-indigo-400 transition-colors" />
          </div>
        </div>
        
        <NavLink to="/app/transactions" className="glass-card rounded-2xl p-6 border border-slate-800/50 hover:border-slate-700/50 transition-colors cursor-pointer group">
          <div className="flex justify-between items-start">
            <div>
              <div className="p-2 bg-emerald-500/10 rounded-lg inline-block mb-3 group-hover:bg-emerald-500/20 transition-colors">
                <Activity className="w-5 h-5 text-emerald-400" />
              </div>
              <h3 className="text-lg font-bold text-slate-100">Personal Finance</h3>
              <p className="text-sm text-slate-400 mt-1">Manage bank statements, track expenses, and view cash-flow forecasts.</p>
            </div>
            <ChevronRight className="w-5 h-5 text-slate-500 group-hover:text-emerald-400 transition-colors" />
          </div>
        </NavLink>
      </div>

    </div>
  );
};
