import React, { useEffect, useState } from "react";
import { marketApi, StockItem } from "../lib/api/markets";
import { TrendingUp, TrendingDown, Filter, Search } from "lucide-react";

export const ScreenerPage: React.FC = () => {
  const [stocks, setStocks] = useState<StockItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterUp, setFilterUp] = useState<boolean | null>(null);

  useEffect(() => {
    const fetchScreener = async () => {
      try {
        const res = await marketApi.getTopStocks();
        setStocks(res.data || []);
      } catch (e) {
        console.error("Failed to load screener stocks", e);
      } finally {
        setLoading(false);
      }
    };
    fetchScreener();
  }, []);

  const filtered = stocks.filter(s => {
    const matchesSearch = s.symbol.toLowerCase().includes(searchTerm.toLowerCase()) || s.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterUp === null ? true : s.is_up === filterUp;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Stock Screener</h1>
          <p className="text-gray-400 mt-2">Filter and screen real-time top volume equities.</p>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-500" />
          <input
            type="text"
            placeholder="Search symbols..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-gray-950 border border-gray-800 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-gray-500 focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none transition-all"
          />
        </div>
        
        <div className="flex items-center gap-2">
          <button 
            onClick={() => setFilterUp(null)}
            className={`px-4 py-2.5 rounded-lg border text-sm font-medium transition-colors ${filterUp === null ? 'bg-gray-800 border-gray-700 text-white' : 'bg-transparent border-gray-800 text-gray-400 hover:text-white hover:border-gray-700'}`}
          >
            All
          </button>
          <button 
            onClick={() => setFilterUp(true)}
            className={`px-4 py-2.5 rounded-lg border text-sm font-medium transition-colors flex items-center gap-2 ${filterUp === true ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-transparent border-gray-800 text-gray-400 hover:text-white hover:border-gray-700'}`}
          >
            <TrendingUp className="h-4 w-4" /> Gainers
          </button>
          <button 
            onClick={() => setFilterUp(false)}
            className={`px-4 py-2.5 rounded-lg border text-sm font-medium transition-colors flex items-center gap-2 ${filterUp === false ? 'bg-rose-500/10 border-rose-500/30 text-rose-400' : 'bg-transparent border-gray-800 text-gray-400 hover:text-white hover:border-gray-700'}`}
          >
            <TrendingDown className="h-4 w-4" /> Losers
          </button>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64 text-emerald-500">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <Filter className="h-8 w-8 mb-4 opacity-50" />
            <p>No equities match your current filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-gray-400 uppercase bg-gray-900/50 border-b border-gray-800">
                <tr>
                  <th className="px-6 py-4 font-medium">Symbol / Name</th>
                  <th className="px-6 py-4 font-medium text-right">LTP (₹)</th>
                  <th className="px-6 py-4 font-medium text-right">Change</th>
                  <th className="px-6 py-4 font-medium text-right">Volume</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {filtered.map((stock) => (
                  <tr key={stock.symbol} className="hover:bg-gray-800/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex flex-col">
                        <span className="font-semibold text-white">{stock.symbol}</span>
                        <span className="text-xs text-gray-500">{stock.name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <span className="text-white font-medium">{stock.ltp.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className={`flex items-center justify-end gap-1 ${stock.is_up ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {stock.is_up ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                        <span>{stock.is_up ? '+' : ''}{stock.change.toFixed(2)} ({stock.change_percent.toFixed(2)}%)</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right text-gray-400">
                      {stock.volume.toLocaleString('en-IN')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
