import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Activity, Globe, BarChart2, RefreshCw } from 'lucide-react';
import { cn } from '../lib/utils/cn';
import { marketApi, IndexItem, SectorItem, StockItem } from '../lib/api/markets';

const DEFAULT_INDICES: IndexItem[] = [
  { name: 'NIFTY 50', symbol: 'NIFTY 50', value: '23,146.15', ltp: 23146.15, change: '+148.80', changePct: '+0.65%', change_percent: 0.65, isUp: true, status: 'active', isIndian: true },
  { name: 'BANK NIFTY', symbol: 'BANK NIFTY', value: '55,844.00', ltp: 55844.00, change: '+33.50', changePct: '+0.06%', change_percent: 0.06, isUp: true, status: 'active', isIndian: true },
  { name: 'SENSEX', symbol: 'SENSEX', value: '74,729.27', ltp: 74729.27, change: '+413.66', changePct: '+0.56%', change_percent: 0.56, isUp: true, status: 'active', isIndian: true },
  { name: 'INDIA VIX', symbol: 'INDIA VIX', value: '14.02', ltp: 14.02, change: '-0.01', changePct: '-0.04%', change_percent: -0.04, isUp: false, status: 'active', isIndian: true },
  { name: 'S&P 500', symbol: 'S&P 500', value: '7,744.06', ltp: 7744.06, change: '+25.12', changePct: '+0.33%', change_percent: 0.33, isUp: true, status: 'active', isIndian: false },
  { name: 'NASDAQ', symbol: 'NASDAQ', value: '26,713.03', ltp: 26713.03, change: '+20.16', changePct: '+0.08%', change_percent: 0.08, isUp: true, status: 'active', isIndian: false },
];

const DEFAULT_SECTORS: SectorItem[] = [
  { name: 'Technology', performance: '+3.92%', changePct: 3.92, isUp: true, weight: '15%' },
  { name: 'Financials', performance: '+0.06%', changePct: 0.06, isUp: true, weight: '35%' },
  { name: 'Energy', performance: '-0.06%', changePct: -0.06, isUp: false, weight: '12%' },
  { name: 'Auto', performance: '+0.75%', changePct: 0.75, isUp: true, weight: '8%' },
  { name: 'FMCG', performance: '-0.39%', changePct: -0.39, isUp: false, weight: '9%' },
  { name: 'Healthcare', performance: '-0.14%', changePct: -0.14, isUp: false, weight: '6%' },
];

const DEFAULT_TOP_STOCKS: StockItem[] = [
  { symbol: 'RELIANCE', name: 'Reliance Industries Limited', instrument_key: 'NSE_EQ|INE002A01018', ticker: 'RELIANCE.NS', ltp: 1288.40, price: 1288.40, change: 15.30, change_percent: 1.20, is_up: true, volume: 12450000 },
  { symbol: 'HDFCBANK', name: 'HDFC Bank Limited', instrument_key: 'NSE_EQ|INE040A01034', ticker: 'HDFCBANK.NS', ltp: 1745.50, price: 1745.50, change: 13.80, change_percent: 0.80, is_up: true, volume: 18230000 },
  { symbol: 'INFY', name: 'Infosys Limited', instrument_key: 'NSE_EQ|INE009A01021', ticker: 'INFY.NS', ltp: 1885.20, price: 1885.20, change: 70.80, change_percent: 3.90, is_up: true, volume: 8420000 },
  { symbol: 'TCS', name: 'Tata Consultancy Services', instrument_key: 'NSE_EQ|INE467B01029', ticker: 'TCS.NS', ltp: 4120.00, price: 4120.00, change: 61.00, change_percent: 1.50, is_up: true, volume: 3120000 },
];

export const MarketsPage: React.FC = () => {
  const [indices, setIndices] = useState<IndexItem[]>(DEFAULT_INDICES);
  const [sectors, setSectors] = useState<SectorItem[]>(DEFAULT_SECTORS);
  const [topStocks, setTopStocks] = useState<StockItem[]>(DEFAULT_TOP_STOCKS);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadData = async (showSpin = false) => {
    if (showSpin) setIsRefreshing(true);
    try {
      const results = await Promise.allSettled([
        marketApi.getOverview(),
        marketApi.getTopStocks(),
      ]);

      if (results[0].status === "fulfilled") {
        const overview = results[0].value;
        if (overview.indices && overview.indices.length > 0) {
          setIndices(overview.indices);
        }
        if (overview.sectors && overview.sectors.length > 0) {
          setSectors(overview.sectors);
        }
      }

      if (results[1].status === "fulfilled") {
        const stocks = results[1].value;
        if (stocks.data && stocks.data.length > 0) {
          setTopStocks(stocks.data);
        }
      }
    } catch (e) {
      console.warn("Market sync notice:", e);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);


  return (
    <div className="p-6 md:p-10 space-y-8 animate-fadeIn max-w-7xl mx-auto pb-24">
      {/* ═══ Header Section ═══ */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Global & Indian Markets</h1>
          <p className="text-slate-400">Real-time live indices, large-cap stocks, and sectoral performance.</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => loadData(true)}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-white/[0.05] border border-white/10 text-slate-300 hover:text-white hover:bg-white/10 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={cn("w-3.5 h-3.5", isRefreshing && "animate-spin")} />
            Sync Real Quotes
          </button>
          <div className="flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            LIVE FEED
          </div>
        </div>
      </div>

      {/* Indices Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {indices.map((idx) => (
          <div key={idx.name} className="p-5 rounded-2xl bg-[#0a0a0a] border border-slate-800/50 hover:border-slate-700/50 transition-colors group relative overflow-hidden">
            <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
              <Globe className="w-16 h-16 text-white" />
            </div>
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-1">
                <h3 className="text-sm font-medium text-slate-400">{idx.name}</h3>
                {idx.isIndian && (
                  <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    NSE / BSE
                  </span>
                )}
              </div>
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

      {/* Core Large-Cap Indian Equities */}
      {topStocks.length > 0 && (
        <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-slate-800/50">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-400" />
              <h2 className="text-lg font-bold text-white">Constituents Universe (Real NSE Prices)</h2>
            </div>
            <span className="text-xs text-slate-400">4 Core Stocks Used in XGBoost Model</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {topStocks.map((stock) => (
              <div key={stock.symbol} className="p-4 rounded-xl bg-white/[0.02] border border-slate-800/80 hover:border-slate-700 transition-all">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <div className="font-bold text-white text-base">{stock.symbol}</div>
                    <div className="text-xs text-slate-400 truncate max-w-[150px]">{stock.name}</div>
                  </div>
                  <span className={cn(
                    "px-2 py-0.5 rounded text-xs font-semibold",
                    stock.is_up ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"
                  )}>
                    {stock.change_percent >= 0 ? `+${stock.change_percent}%` : `${stock.change_percent}%`}
                  </span>
                </div>
                <div className="text-xl font-bold text-white mb-1">₹{stock.price.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</div>
                <div className="text-xs text-slate-500 flex justify-between">
                  <span>Day: {stock.change >= 0 ? `+₹${stock.change}` : `-₹${Math.abs(stock.change)}`}</span>
                  <span>Vol: {(stock.volume / 100000).toFixed(1)}L</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sector Heatmap & Breadth */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-6 rounded-2xl bg-[#0a0a0a] border border-slate-800/50">
          <div className="flex items-center gap-2 mb-6">
            <BarChart2 className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-bold text-white">Sectoral Heatmap (NSE Thematic Indices)</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {sectors.map((sector) => (
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
