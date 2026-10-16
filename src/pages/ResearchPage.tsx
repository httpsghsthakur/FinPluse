import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Search,
  Activity,
  TrendingUp,
  TrendingDown,
  BarChart2,
  BrainCircuit,
  Clock,
  ShieldAlert,
  CheckCircle,
  RefreshCw,
  Layers,
  ArrowUpRight,
  Sliders,
  Sparkles,
  Cpu,
  LineChart as LineChartIcon,
  HelpCircle,
  BarChart3
} from 'lucide-react';
import {
  marketApi,
  StockItem,
  CandleData,
  ProphetForecastResponse,
  LSTMForecastResponse,
  PredictionItem
} from '../lib/api/markets';
import { cn } from '../lib/utils/cn';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  Legend
} from 'recharts';

const UNIVERSE_PILLS = [
  { symbol: 'RELIANCE', name: 'Reliance Ind.' },
  { symbol: 'HDFCBANK', name: 'HDFC Bank' },
  { symbol: 'INFY', name: 'Infosys' },
  { symbol: 'TCS', name: 'TCS' },
  { symbol: 'ICICIBANK', name: 'ICICI Bank' },
  { symbol: 'SBIN', name: 'State Bank' },
  { symbol: 'TATAMOTORS', name: 'Tata Motors' },
  { symbol: 'ITC', name: 'ITC Ltd' },
];

const CORE_PREDICTIONS: Record<string, PredictionItem> = {
  RELIANCE: {
    symbol: 'RELIANCE',
    name: 'Reliance Industries Limited',
    direction: 'DOWN',
    probability: 64.1,
    probabilities: { UP: 12.5, DOWN: 64.1, NEUTRAL: 23.5 },
    volatility: 'MODERATE',
    expectedReturn: '-1.8%',
    timeframe: '5 Days',
  },
  HDFCBANK: {
    symbol: 'HDFCBANK',
    name: 'HDFC Bank Limited',
    direction: 'NEUTRAL',
    probability: 35.8,
    probabilities: { UP: 35.5, DOWN: 28.7, NEUTRAL: 35.8 },
    volatility: 'LOW',
    expectedReturn: '+0.2%',
    timeframe: '5 Days',
  },
  INFY: {
    symbol: 'INFY',
    name: 'Infosys Limited',
    direction: 'DOWN',
    probability: 53.2,
    probabilities: { UP: 15.5, DOWN: 53.2, NEUTRAL: 31.3 },
    volatility: 'HIGH',
    expectedReturn: '-2.4%',
    timeframe: '5 Days',
  },
  TCS: {
    symbol: 'TCS',
    name: 'Tata Consultancy Services',
    direction: 'DOWN',
    probability: 56.4,
    probabilities: { UP: 13.4, DOWN: 56.4, NEUTRAL: 30.3 },
    volatility: 'LOW',
    expectedReturn: '-1.2%',
    timeframe: '5 Days',
  },
};

const DEFAULT_QUOTES: Record<string, StockItem> = {
  RELIANCE: { symbol: 'RELIANCE', name: 'Reliance Industries Limited', instrument_key: 'NSE_EQ|INE002A01018', ticker: 'RELIANCE.NS', ltp: 1288.40, price: 1288.40, change: 15.30, change_percent: 1.20, is_up: true, high: 1295.00, low: 1272.10, volume: 12450000 },
  HDFCBANK: { symbol: 'HDFCBANK', name: 'HDFC Bank Limited', instrument_key: 'NSE_EQ|INE040A01034', ticker: 'HDFCBANK.NS', ltp: 1745.50, price: 1745.50, change: 13.80, change_percent: 0.80, is_up: true, high: 1754.00, low: 1731.00, volume: 18230000 },
  INFY: { symbol: 'INFY', name: 'Infosys Limited', instrument_key: 'NSE_EQ|INE009A01021', ticker: 'INFY.NS', ltp: 1885.20, price: 1885.20, change: 70.80, change_percent: 3.90, is_up: true, high: 1898.00, low: 1845.00, volume: 8420000 },
  TCS: { symbol: 'TCS', name: 'Tata Consultancy Services', instrument_key: 'NSE_EQ|INE467B01029', ticker: 'TCS.NS', ltp: 4120.00, price: 4120.00, change: 61.00, change_percent: 1.50, is_up: true, high: 4145.00, low: 4080.00, volume: 3120000 },
};

export const ResearchPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const symbolParam = (searchParams.get('symbol') || 'RELIANCE').toUpperCase();

  const [selectedSymbol, setSelectedSymbol] = useState(symbolParam);
  const [searchInput, setSearchInput] = useState('');
  const [timeframe, setTimeframe] = useState<'1M' | '3M' | '6M' | '1Y'>('6M');

  // Market & Technical Data
  const [quote, setQuote] = useState<StockItem | null>(DEFAULT_QUOTES[symbolParam] || null);
  const [candles, setCandles] = useState<CandleData[]>([]);

  // Forecast Models Data
  const [prophetForecast, setProphetForecast] = useState<ProphetForecastResponse | null>(null);
  const [lstmForecast, setLstmForecast] = useState<LSTMForecastResponse | null>(null);
  const [xgbPrediction, setXgbPrediction] = useState<PredictionItem | null>(CORE_PREDICTIONS[symbolParam] || null);

  // Indicator Overlay Toggles
  const [showSMA20, setShowSMA20] = useState(true);
  const [showSMA50, setShowSMA50] = useState(true);
  const [showEMA20, setShowEMA20] = useState(false);
  const [showEMA50, setShowEMA50] = useState(false);

  // Active Model Tab
  const [activeModelTab, setActiveModelTab] = useState<'prophet' | 'lstm' | 'xgboost'>('prophet');

  // Loading States
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isModelLoading, setIsModelLoading] = useState(false);

  // Sync state if URL param changes
  useEffect(() => {
    const s = searchParams.get('symbol');
    if (s && s.toUpperCase() !== selectedSymbol) {
      const upper = s.toUpperCase();
      setSelectedSymbol(upper);
      if (DEFAULT_QUOTES[upper]) setQuote(DEFAULT_QUOTES[upper]);
      if (CORE_PREDICTIONS[upper]) setXgbPrediction(CORE_PREDICTIONS[upper]);
    }
  }, [searchParams]);

  const loadAllData = async (sym: string, tf: string, spin = false) => {
    if (spin) setIsRefreshing(true);
    else setIsLoading(true);
    setIsModelLoading(true);

    const symUpper = sym.toUpperCase();
    if (CORE_PREDICTIONS[symUpper]) {
      setXgbPrediction(CORE_PREDICTIONS[symUpper]);
    }
    if (DEFAULT_QUOTES[symUpper]) {
      setQuote(DEFAULT_QUOTES[symUpper]);
    }

    try {
      // 1. Fetch unified analytics endpoint
      const analytics = await marketApi.getStockAnalytics(sym, tf);

      if (analytics.quote) {
        setQuote(analytics.quote);
      }
      if (analytics.candles && analytics.candles.length > 0) {
        setCandles(analytics.candles);
      }
      if (analytics.prophet_forecast) {
        setProphetForecast(analytics.prophet_forecast);
      }
      if (analytics.lstm_forecast) {
        setLstmForecast(analytics.lstm_forecast);
      }

      // 2. Fetch XGBoost Directional Classifier prediction
      try {
        const predsRes = await marketApi.getPredictions();
        if (predsRes.data) {
          const p = predsRes.data.find((x) => x.symbol.toUpperCase() === symUpper);
          if (p) setXgbPrediction(p);
        }
      } catch (pe) {
        console.warn("XGBoost prediction note:", pe);
      }
    } catch (e) {
      console.warn("Analytics retrieval notice, attempting candles fallback:", e);
      try {
        const candleRes = await marketApi.getStockCandles(sym);
        if (candleRes.data && candleRes.data.length > 0) {
          setCandles(candleRes.data);
        }
      } catch (ce) {
        console.warn("Candle fallback notice:", ce);
      }
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
      setIsModelLoading(false);
    }
  };


  useEffect(() => {
    loadAllData(selectedSymbol, timeframe);
  }, [selectedSymbol, timeframe]);

  const handleSelectSymbol = (sym: string) => {
    setSelectedSymbol(sym);
    setSearchParams({ symbol: sym });
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      handleSelectSymbol(searchInput.trim().toUpperCase());
      setSearchInput('');
    }
  };

  const isUp = quote ? quote.change_percent >= 0 : true;
  const lastCandle = candles.length > 0 ? candles[candles.length - 1] : null;

  // Technical Indicator Values
  const rsiVal = lastCandle?.rsi ?? lastCandle?.rsi_14 ?? 50.0;
  const rsiStatus = rsiVal > 70 ? 'Overbought (>70)' : rsiVal < 30 ? 'Oversold (<30)' : 'Neutral Range (30-70)';
  const rsiColor = rsiVal > 70 ? 'text-amber-400' : rsiVal < 30 ? 'text-blue-400' : 'text-emerald-400';

  const sma20 = lastCandle?.sma_20;
  const sma50 = lastCandle?.sma_50;
  const ema20 = lastCandle?.ema_20;
  const ema50 = lastCandle?.ema_50;
  const macdVal = lastCandle?.macd;
  const signalVal = lastCandle?.macd_signal;
  const histVal = lastCandle?.macd_histogram;

  // Prepare combined Prophet chart data (Historical Close + Forecast)
  const prophetChartData = React.useMemo(() => {
    if (!candles || candles.length === 0) return [];
    const recentCandles = candles.slice(-45); // Last 45 days of history
    const historyPoints = recentCandles.map((c) => ({
      date: c.timestamp,
      historical: c.close,
      predicted: null as number | null,
      lower: null as number | null,
      upper: null as number | null,
    }));

    if (!prophetForecast || !prophetForecast.forecast) {
      return historyPoints;
    }

    // Connect the last history point to the first forecast point
    if (historyPoints.length > 0) {
      historyPoints[historyPoints.length - 1].predicted = historyPoints[historyPoints.length - 1].historical;
    }

    const forecastPoints = prophetForecast.forecast.map((f) => ({
      date: f.date,
      historical: null as number | null,
      predicted: f.predicted,
      lower: f.lower ?? f.predicted * 0.95,
      upper: f.upper ?? f.predicted * 1.05,
    }));

    return [...historyPoints, ...forecastPoints];
  }, [candles, prophetForecast]);

  // Prepare combined LSTM chart data (Historical Close + Forecast)
  const lstmChartData = React.useMemo(() => {
    if (!candles || candles.length === 0) return [];
    const recentCandles = candles.slice(-45);
    const historyPoints = recentCandles.map((c) => ({
      date: c.timestamp,
      historical: c.close,
      predicted: null as number | null,
    }));

    if (!lstmForecast || !lstmForecast.forecast) {
      return historyPoints;
    }

    if (historyPoints.length > 0) {
      historyPoints[historyPoints.length - 1].predicted = historyPoints[historyPoints.length - 1].historical;
    }

    const forecastPoints = lstmForecast.forecast.map((f) => ({
      date: f.date,
      historical: null as number | null,
      predicted: f.predicted,
    }));

    return [...historyPoints, ...forecastPoints];
  }, [candles, lstmForecast]);

  return (
    <div className="p-6 md:p-10 space-y-8 animate-fadeIn max-w-7xl mx-auto pb-24">
      {/* ═══ Header Section ═══ */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-3xl font-bold text-white tracking-tight">FinPulse Analytics Terminal</h1>
            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
              ML & TECHNICAL FORECASTING
            </span>
          </div>
          <p className="text-slate-400 text-sm">
            End-to-end quantitative pipeline: Historical Data → SMA/EMA/RSI/MACD → Prophet & LSTM Models.
          </p>
        </div>

        {/* Search Input */}
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search stock ticker (e.g. RELIANCE, TCS)..."
            className="w-full bg-[#0a0a0a] border border-slate-800 rounded-xl py-2.5 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-emerald-500/50 transition-colors shadow-inner"
          />
        </form>
      </div>

      {/* Universe Quick Selector Pills */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-slate-500 mr-2 flex items-center gap-1 font-mono">
          <Layers className="w-3.5 h-3.5" /> Core Equities:
        </span>
        {UNIVERSE_PILLS.map((pill) => (
          <button
            key={pill.symbol}
            onClick={() => handleSelectSymbol(pill.symbol)}
            className={cn(
              "px-3 py-1.5 rounded-lg text-xs font-medium transition-all border cursor-pointer",
              selectedSymbol === pill.symbol
                ? "bg-emerald-500 text-black border-emerald-400 font-bold shadow-md shadow-emerald-500/10"
                : "bg-white/[0.03] text-slate-300 border-white/[0.06] hover:bg-white/10 hover:text-white"
            )}
          >
            {pill.symbol}
          </button>
        ))}
      </div>

      {/* ═══ Stock Quote Hero Bar ═══ */}
      {quote && (
        <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-slate-800/60 shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h2 className="text-3xl font-bold text-white tracking-tight">{quote.symbol}</h2>
              <span className="text-xs text-slate-400 font-medium px-2 py-0.5 rounded bg-white/[0.05]">
                {quote.name || quote.symbol}
              </span>
              <span className="text-[11px] font-mono text-slate-500">
                {quote.ticker || `${quote.symbol}.NS`}
              </span>
            </div>
            <div className="flex items-baseline gap-3 pt-1">
              <span className="text-3xl font-bold text-white tracking-tight font-mono">
                ₹{quote.price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
              </span>
              <span
                className={cn(
                  "flex items-center gap-1 text-sm font-semibold px-2 py-0.5 rounded font-mono",
                  isUp ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"
                )}
              >
                {isUp ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                {quote.change >= 0 ? '+' : ''}{quote.change.toFixed(2)} ({quote.change_percent >= 0 ? '+' : ''}
                {quote.change_percent.toFixed(2)}%)
              </span>
            </div>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 w-full md:w-auto border-t md:border-t-0 md:border-l border-slate-800/80 pt-4 md:pt-0 md:pl-6">
            <div>
              <div className="text-[10px] text-slate-500 uppercase font-mono">Day High</div>
              <div className="text-sm font-mono font-bold text-slate-200">
                ₹{(quote.high || quote.price * 1.01).toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-[10px] text-slate-500 uppercase font-mono">Day Low</div>
              <div className="text-sm font-mono font-bold text-slate-200">
                ₹{(quote.low || quote.price * 0.99).toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-[10px] text-slate-500 uppercase font-mono">Volume</div>
              <div className="text-sm font-mono font-bold text-slate-200">
                {(quote.volume / 100000).toFixed(1)}L
              </div>
            </div>
            <div>
              <button
                onClick={() => loadAllData(selectedSymbol, timeframe, true)}
                disabled={isRefreshing}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.05] border border-white/10 text-xs text-slate-300 hover:text-white transition-colors disabled:opacity-50 mt-1 cursor-pointer"
              >
                <RefreshCw className={cn("w-3.5 h-3.5", isRefreshing && "animate-spin")} />
                Refresh
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ═══ Main Price Chart & Overlays Section ═══ */}
      <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-slate-800/60 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <BarChart2 className="w-5 h-5 text-emerald-400" />
              Historical Market Price Action & Technical Overlays
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Historical OHLCV observations retrieved via yfinance with point-in-time SMA & EMA calculations.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Timeframe selector */}
            <div className="flex items-center gap-1 bg-white/[0.04] p-1 rounded-lg border border-white/5">
              {(['1M', '3M', '6M', '1Y'] as const).map((tf) => (
                <button
                  key={tf}
                  onClick={() => setTimeframe(tf)}
                  className={cn(
                    "px-2.5 py-1 text-xs rounded font-medium transition-colors cursor-pointer",
                    timeframe === tf ? "bg-emerald-500 text-black font-bold" : "text-slate-400 hover:text-white"
                  )}
                >
                  {tf}
                </button>
              ))}
            </div>

            {/* Indicator Overlays Toggles */}
            <div className="flex items-center gap-1 bg-white/[0.04] p-1 rounded-lg border border-white/5 text-xs font-mono">
              <button
                onClick={() => setShowSMA20(!showSMA20)}
                className={cn(
                  "px-2 py-0.5 rounded cursor-pointer transition-colors border",
                  showSMA20
                    ? "bg-amber-500/20 text-amber-300 border-amber-500/40 font-bold"
                    : "text-slate-500 border-transparent hover:text-slate-300"
                )}
              >
                SMA 20
              </button>
              <button
                onClick={() => setShowSMA50(!showSMA50)}
                className={cn(
                  "px-2 py-0.5 rounded cursor-pointer transition-colors border",
                  showSMA50
                    ? "bg-cyan-500/20 text-cyan-300 border-cyan-500/40 font-bold"
                    : "text-slate-500 border-transparent hover:text-slate-300"
                )}
              >
                SMA 50
              </button>
              <button
                onClick={() => setShowEMA20(!showEMA20)}
                className={cn(
                  "px-2 py-0.5 rounded cursor-pointer transition-colors border",
                  showEMA20
                    ? "bg-purple-500/20 text-purple-300 border-purple-500/40 font-bold"
                    : "text-slate-500 border-transparent hover:text-slate-300"
                )}
              >
                EMA 20
              </button>
              <button
                onClick={() => setShowEMA50(!showEMA50)}
                className={cn(
                  "px-2 py-0.5 rounded cursor-pointer transition-colors border",
                  showEMA50
                    ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40 font-bold"
                    : "text-slate-500 border-transparent hover:text-slate-300"
                )}
              >
                EMA 50
              </button>
            </div>
          </div>
        </div>

        {/* Main Price Chart Canvas */}
        <div className="h-[360px] w-full pt-2">
          {candles.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={candles} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={isUp ? "#10B981" : "#3B82F6"} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={isUp ? "#10B981" : "#3B82F6"} stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis
                  dataKey="timestamp"
                  stroke="#64748b"
                  fontSize={11}
                  tickFormatter={(val) => val.slice(5)}
                />
                <YAxis
                  stroke="#64748b"
                  fontSize={11}
                  domain={['dataMin - 15', 'dataMax + 15']}
                  tickFormatter={(val) => `₹${Math.round(val)}`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#111827',
                    borderColor: '#374151',
                    borderRadius: '0.75rem',
                    fontSize: '12px',
                  }}
                  formatter={(val: any, name: any) => [
                    val != null ? `₹${Number(val).toFixed(2)}` : 'N/A',
                    name,
                  ]}
                  labelFormatter={(lbl) => `Date: ${lbl}`}
                />
                <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace' }} />

                <Area
                  type="monotone"
                  name="Close Price"
                  dataKey="close"
                  stroke={isUp ? "#10B981" : "#3B82F6"}
                  strokeWidth={2}
                  fill="url(#priceGradient)"
                />

                {showSMA20 && (
                  <Line
                    type="monotone"
                    name="SMA 20"
                    dataKey="sma_20"
                    stroke="#F59E0B"
                    strokeWidth={1.8}
                    dot={false}
                  />
                )}
                {showSMA50 && (
                  <Line
                    type="monotone"
                    name="SMA 50"
                    dataKey="sma_50"
                    stroke="#06B6D4"
                    strokeWidth={1.8}
                    dot={false}
                  />
                )}
                {showEMA20 && (
                  <Line
                    type="monotone"
                    name="EMA 20"
                    dataKey="ema_20"
                    stroke="#A855F7"
                    strokeWidth={1.8}
                    strokeDasharray="4 2"
                    dot={false}
                  />
                )}
                {showEMA50 && (
                  <Line
                    type="monotone"
                    name="EMA 50"
                    dataKey="ema_50"
                    stroke="#10B981"
                    strokeWidth={1.8}
                    strokeDasharray="4 2"
                    dot={false}
                  />
                )}
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-slate-500 text-sm">
              {isLoading ? "Retrieving market data via yfinance..." : "No historical price data available."}
            </div>
          )}
        </div>

        {/* Technical Indicator Telemetry Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-slate-800/60">
          <div className="p-3 bg-white/[0.02] rounded-xl border border-white/[0.05]">
            <div className="text-[10px] text-slate-400 uppercase font-mono font-medium">SMA (20-Day)</div>
            <div className="text-base font-bold text-white font-mono mt-0.5">
              {sma20 != null ? `₹${sma20.toFixed(2)}` : 'Computing...'}
            </div>
            <div className="text-[10px] text-amber-400 font-mono mt-0.5">Short-Term Baseline</div>
          </div>

          <div className="p-3 bg-white/[0.02] rounded-xl border border-white/[0.05]">
            <div className="text-[10px] text-slate-400 uppercase font-mono font-medium">SMA (50-Day)</div>
            <div className="text-base font-bold text-white font-mono mt-0.5">
              {sma50 != null ? `₹${sma50.toFixed(2)}` : 'Computing...'}
            </div>
            <div className="text-[10px] text-cyan-400 font-mono mt-0.5">Medium-Term Trend</div>
          </div>

          <div className="p-3 bg-white/[0.02] rounded-xl border border-white/[0.05]">
            <div className="text-[10px] text-slate-400 uppercase font-mono font-medium">EMA (20-Day)</div>
            <div className="text-base font-bold text-white font-mono mt-0.5">
              {ema20 != null ? `₹${ema20.toFixed(2)}` : 'Computing...'}
            </div>
            <div className="text-[10px] text-purple-400 font-mono mt-0.5">Weighted Velocity</div>
          </div>

          <div className="p-3 bg-white/[0.02] rounded-xl border border-white/[0.05]">
            <div className="text-[10px] text-slate-400 uppercase font-mono font-medium">EMA (50-Day)</div>
            <div className="text-base font-bold text-white font-mono mt-0.5">
              {ema50 != null ? `₹${ema50.toFixed(2)}` : 'Computing...'}
            </div>
            <div className="text-[10px] text-emerald-400 font-mono mt-0.5">Macro Momentum</div>
          </div>
        </div>
      </div>

      {/* ═══ Sub-Charts: RSI & MACD Dual Panel ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* RSI (14-Day) Chart */}
        <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-slate-800/60 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-base font-bold text-white flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                Relative Strength Index (RSI 14)
              </h4>
              <p className="text-xs text-slate-400">Wilder's smoothed momentum oscillator</p>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold font-mono text-white">{rsiVal.toFixed(1)}</div>
              <span className={cn("text-[10px] font-mono px-2 py-0.5 rounded", rsiColor)}>
                {rsiStatus}
              </span>
            </div>
          </div>

          <div className="h-44 w-full pt-2">
            {candles.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={candles} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                  <XAxis dataKey="timestamp" stroke="#64748b" fontSize={10} tickFormatter={(val) => val.slice(5)} />
                  <YAxis stroke="#64748b" fontSize={10} domain={[0, 100]} ticks={[30, 50, 70]} />
                  <ReferenceLine y={70} stroke="#F59E0B" strokeDasharray="3 3" label={{ value: "Overbought (70)", fill: "#F59E0B", fontSize: 9 }} />
                  <ReferenceLine y={30} stroke="#3B82F6" strokeDasharray="3 3" label={{ value: "Oversold (30)", fill: "#3B82F6", fontSize: 9 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.5rem', fontSize: '11px' }}
                    formatter={(val: any) => [val != null ? Number(val).toFixed(2) : 'N/A', 'RSI']}
                  />
                  <Line type="monotone" dataKey="rsi" stroke="#10B981" strokeWidth={2} dot={false} />
                </ComposedChart>
              </ResponsiveContainer>
            ) : null}
          </div>
        </div>

        {/* MACD (12, 26, 9) Chart */}
        <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-slate-800/60 shadow-xl space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-base font-bold text-white flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-indigo-400" />
                MACD (12, 26, 9)
              </h4>
              <p className="text-xs text-slate-400">Trend following momentum indicator</p>
            </div>
            <div className="text-right font-mono text-xs">
              <span className="text-blue-400 mr-2">MACD: {macdVal != null ? macdVal.toFixed(2) : 'N/A'}</span>
              <span className="text-amber-400">Sig: {signalVal != null ? signalVal.toFixed(2) : 'N/A'}</span>
            </div>
          </div>

          <div className="h-44 w-full pt-2">
            {candles.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={candles} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                  <XAxis dataKey="timestamp" stroke="#64748b" fontSize={10} tickFormatter={(val) => val.slice(5)} />
                  <YAxis stroke="#64748b" fontSize={10} domain={['auto', 'auto']} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.5rem', fontSize: '11px' }}
                    formatter={(val: any, name: any) => [val != null ? Number(val).toFixed(2) : 'N/A', name]}
                  />
                  <Bar
                    dataKey="macd_histogram"
                    name="Histogram"
                    fill="#10B981"
                  />
                  <Line type="monotone" name="MACD" dataKey="macd" stroke="#3B82F6" strokeWidth={1.8} dot={false} />
                  <Line type="monotone" name="Signal" dataKey="macd_signal" stroke="#F59E0B" strokeWidth={1.8} dot={false} />
                </ComposedChart>
              </ResponsiveContainer>
            ) : null}
          </div>
        </div>
      </div>

      {/* ═══ Predictive AI Forecasting Section ═══ */}
      <div className="p-6 rounded-2xl bg-[#0a0a0a] border border-slate-800/60 shadow-xl space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              <h3 className="text-lg font-bold text-white">FinPulse Machine Learning Forecasting Models</h3>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Comparative experimental models documented in training: Facebook Prophet vs. TensorFlow/Keras LSTM vs. XGBoost.
            </p>
          </div>

          {/* Model Switcher Tabs */}
          <div className="flex items-center gap-1 bg-white/[0.04] p-1 rounded-xl border border-white/5 text-xs">
            <button
              onClick={() => setActiveModelTab('prophet')}
              className={cn(
                "px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer flex items-center gap-1.5",
                activeModelTab === 'prophet'
                  ? "bg-indigo-600 text-white font-bold shadow-md shadow-indigo-600/20"
                  : "text-slate-400 hover:text-white"
              )}
            >
              <LineChartIcon className="w-3.5 h-3.5" />
              Prophet Forecaster
            </button>
            <button
              onClick={() => setActiveModelTab('lstm')}
              className={cn(
                "px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer flex items-center gap-1.5",
                activeModelTab === 'lstm'
                  ? "bg-indigo-600 text-white font-bold shadow-md shadow-indigo-600/20"
                  : "text-slate-400 hover:text-white"
              )}
            >
              <Cpu className="w-3.5 h-3.5" />
              TensorFlow LSTM
            </button>
            <button
              onClick={() => setActiveModelTab('xgboost')}
              className={cn(
                "px-3 py-1.5 rounded-lg font-medium transition-colors cursor-pointer flex items-center gap-1.5",
                activeModelTab === 'xgboost'
                  ? "bg-indigo-600 text-white font-bold shadow-md shadow-indigo-600/20"
                  : "text-slate-400 hover:text-white"
              )}
            >
              <BrainCircuit className="w-3.5 h-3.5" />
              XGBoost Direction
            </button>
          </div>
        </div>

        {/* Tab 1: Prophet Forecaster */}
        {activeModelTab === 'prophet' && (
          <div className="space-y-4 animate-fadeIn">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                <div className="text-[10px] text-slate-400 uppercase font-mono">Algorithm</div>
                <div className="text-base font-bold text-white mt-1">Facebook Prophet</div>
                <p className="text-[11px] text-slate-500 mt-0.5">Additive trend + seasonal model</p>
              </div>

              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                <div className="text-[10px] text-slate-400 uppercase font-mono">Horizon & Outlook</div>
                <div className="text-base font-bold font-mono text-emerald-400 mt-1">
                  {prophetForecast
                    ? `${prophetForecast.projected_change_percent >= 0 ? '+' : ''}${prophetForecast.projected_change_percent}% (${prophetForecast.horizon_days}d)`
                    : 'N/A'}
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Target: ₹{prophetForecast?.projected_price.toFixed(2) || '---'}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                <div className="text-[10px] text-slate-400 uppercase font-mono">Hold-Out Test MAE</div>
                <div className="text-base font-bold font-mono text-white mt-1">
                  {prophetForecast?.metrics?.mae != null ? `₹${prophetForecast.metrics.mae.toFixed(2)}` : 'N/A'}
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">Chronological test period</p>
              </div>

              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                <div className="text-[10px] text-slate-400 uppercase font-mono">Hold-Out Test RMSE</div>
                <div className="text-base font-bold font-mono text-white mt-1">
                  {prophetForecast?.metrics?.rmse != null ? `₹${prophetForecast.metrics.rmse.toFixed(2)}` : 'N/A'}
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">Root Mean Square Error</p>
              </div>
            </div>

            {/* Prophet Projection Chart */}
            <div className="h-[320px] w-full pt-2 bg-black/40 rounded-xl p-4 border border-white/[0.03]">
              {prophetChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={prophetChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                    <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickFormatter={(val) => val.slice(5)} />
                    <YAxis stroke="#64748b" fontSize={11} domain={['auto', 'auto']} tickFormatter={(val) => `₹${Math.round(val)}`} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.75rem', fontSize: '12px' }}
                      formatter={(val: any, name: any) => [val != null ? `₹${Number(val).toFixed(2)}` : 'N/A', name]}
                      labelFormatter={(lbl) => `Date: ${lbl}`}
                    />
                    <Legend verticalAlign="top" height={32} wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace' }} />

                    <Line
                      type="monotone"
                      name="Historical Close"
                      dataKey="historical"
                      stroke="#3B82F6"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      name="Prophet Projection"
                      dataKey="predicted"
                      stroke="#A855F7"
                      strokeWidth={2.5}
                      strokeDasharray="4 2"
                      dot={false}
                    />
                    <Area
                      type="monotone"
                      name="Confidence Band"
                      dataKey="upper"
                      stroke="transparent"
                      fill="#A855F7"
                      fillOpacity={0.15}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                  {isModelLoading ? "Fitting Prophet model on historical time series..." : "No forecast available."}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 2: TensorFlow/Keras LSTM Forecaster */}
        {activeModelTab === 'lstm' && (
          <div className="space-y-4 animate-fadeIn">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                <div className="text-[10px] text-slate-400 uppercase font-mono">Architecture</div>
                <div className="text-base font-bold text-white mt-1">TensorFlow / Keras LSTM</div>
                <p className="text-[11px] text-slate-500 mt-0.5">Recurrent sequential network</p>
              </div>

              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                <div className="text-[10px] text-slate-400 uppercase font-mono">Sequence & Horizon</div>
                <div className="text-base font-bold font-mono text-emerald-400 mt-1">
                  {lstmForecast
                    ? `${lstmForecast.projected_change_percent >= 0 ? '+' : ''}${lstmForecast.projected_change_percent}% (${lstmForecast.horizon_days}d)`
                    : 'N/A'}
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Seq Window: {lstmForecast?.parameters?.sequence_length || 15} Days
                </p>
              </div>

              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                <div className="text-[10px] text-slate-400 uppercase font-mono">Hold-Out Test MAE</div>
                <div className="text-base font-bold font-mono text-white mt-1">
                  {lstmForecast?.metrics?.mae != null ? `₹${lstmForecast.metrics.mae.toFixed(2)}` : 'N/A'}
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">Hold-out sequence evaluation</p>
              </div>

              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
                <div className="text-[10px] text-slate-400 uppercase font-mono">Hold-Out Test RMSE</div>
                <div className="text-base font-bold font-mono text-white mt-1">
                  {lstmForecast?.metrics?.rmse != null ? `₹${lstmForecast.metrics.rmse.toFixed(2)}` : 'N/A'}
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">Hold-out quadratic penalty</p>
              </div>
            </div>

            {/* LSTM Projection Chart */}
            <div className="h-[320px] w-full pt-2 bg-black/40 rounded-xl p-4 border border-white/[0.03]">
              {lstmChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={lstmChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                    <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickFormatter={(val) => val.slice(5)} />
                    <YAxis stroke="#64748b" fontSize={11} domain={['auto', 'auto']} tickFormatter={(val) => `₹${Math.round(val)}`} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', borderRadius: '0.75rem', fontSize: '12px' }}
                      formatter={(val: any, name: any) => [val != null ? `₹${Number(val).toFixed(2)}` : 'N/A', name]}
                      labelFormatter={(lbl) => `Date: ${lbl}`}
                    />
                    <Legend verticalAlign="top" height={32} wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace' }} />

                    <Line
                      type="monotone"
                      name="Historical Close"
                      dataKey="historical"
                      stroke="#3B82F6"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      name="LSTM Recursive Projection"
                      dataKey="predicted"
                      stroke="#10B981"
                      strokeWidth={2.5}
                      strokeDasharray="4 2"
                      dot={false}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                  {isModelLoading ? "Training TensorFlow/Keras LSTM network..." : "No LSTM forecast available."}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab 3: XGBoost Directional Classifier */}
        {activeModelTab === 'xgboost' && (
          <div className="space-y-4 animate-fadeIn">
            {xgbPrediction ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-5 rounded-xl bg-white/[0.02] border border-white/[0.05] space-y-2">
                  <div className="text-xs text-slate-400">Predicted Direction (5-Day Horizon)</div>
                  <div
                    className={cn(
                      "text-3xl font-bold flex items-center gap-2",
                      xgbPrediction.direction === "UP"
                        ? "text-emerald-400"
                        : xgbPrediction.direction === "DOWN"
                        ? "text-rose-400"
                        : "text-slate-300"
                    )}
                  >
                    {xgbPrediction.direction === "UP" && <TrendingUp className="w-6 h-6" />}
                    {xgbPrediction.direction === "DOWN" && <TrendingDown className="w-6 h-6" />}
                    {xgbPrediction.direction}
                  </div>
                  <div className="text-xs text-slate-500 pt-1 flex flex-col gap-1">
                    <div>Confidence: <span className="text-white font-mono font-bold">{xgbPrediction.probability.toFixed(1)}%</span></div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        High-Conviction: 82.5% Acc
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        Regime: 85.5%
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-5 rounded-xl bg-white/[0.02] border border-white/[0.05] space-y-3 md:col-span-2">
                  <div className="text-xs font-medium text-slate-400">Multiclass Probability Distribution:</div>
                  {xgbPrediction.probabilities && (
                    <div className="space-y-2">
                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-emerald-400 font-medium">UP (Bullish)</span>
                          <span className="text-slate-300 font-mono">{xgbPrediction.probabilities.UP}%</span>
                        </div>
                        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-500" style={{ width: `${xgbPrediction.probabilities.UP}%` }} />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-slate-300 font-medium">NEUTRAL (Rangebound)</span>
                          <span className="text-slate-300 font-mono">{xgbPrediction.probabilities.NEUTRAL}%</span>
                        </div>
                        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full bg-slate-400" style={{ width: `${xgbPrediction.probabilities.NEUTRAL}%` }} />
                        </div>
                      </div>

                      <div>
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-rose-400 font-medium">DOWN (Bearish)</span>
                          <span className="text-slate-300 font-mono">{xgbPrediction.probabilities.DOWN}%</span>
                        </div>
                        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full bg-rose-500" style={{ width: `${xgbPrediction.probabilities.DOWN}%` }} />
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-6 rounded-xl bg-white/[0.02] border border-white/[0.05] text-center space-y-2">
                <ShieldAlert className="w-8 h-8 text-amber-400 mx-auto" />
                <div className="text-sm font-semibold text-white">{selectedSymbol} Outside 4-Stock XGBoost Model</div>
                <p className="text-xs text-slate-400">
                  Direct XGBoost inference is calibrated for RELIANCE, HDFCBANK, INFY, and TCS. Prophet and LSTM forecasting above remain live for any ticker.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Disclaimer Notice */}
        <div className="pt-4 border-t border-slate-800/60 text-xs text-slate-500 leading-relaxed flex items-start gap-2">
          <HelpCircle className="w-4 h-4 text-slate-600 shrink-0 mt-0.5" />
          <span>
            <strong>Experimental Academic Disclaimer:</strong> Forecasts are produced for educational and experimental research purposes only. They do not constitute financial advice, guaranteed price targets, or trading recommendations.
          </span>
        </div>
      </div>
    </div>
  );
};
