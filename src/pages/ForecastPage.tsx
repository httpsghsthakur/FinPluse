import React, { useEffect, useState } from "react";
import { TrendingUp, Calendar, Info } from "lucide-react";
import { ResponsiveContainer, ComposedChart, Area, Line, XAxis, YAxis, Tooltip } from "recharts";
import { ChartCard } from "../components/ui/ChartCard";
import { ChartSkeleton } from "../components/ui/Skeletons";
import { ForecastPoint, ForecastEvent } from "../types";
import { api } from "../lib/api";
import { formatCurrency, formatDate, CURRENCY_SYMBOLS } from "../lib/utils/formatters";
import { useUserStore } from "../lib/store/useUserStore";

export const ForecastPage: React.FC = () => {
  const { profile } = useUserStore();
  const [range, setRange] = useState<30 | 60 | 90>(90);
  const [points, setPoints] = useState<ForecastPoint[]>([]);
  const [events, setEvents] = useState<ForecastEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadForecast = async () => {
    setIsLoading(true);
    try {
      const res = await api.getForecast(range);
      setPoints(res.points);
      setEvents(res.events);
    } catch (e) { console.error(e); }
    finally { setIsLoading(false); }
  };

  useEffect(() => { loadForecast(); }, [range]);

  const currentLiquidBalance = points.find((p) => p.isActual)?.actualBalance || 43270;
  const minForecastPoint = points.reduce((min, p) => (p.forecastedBalance < min.forecastedBalance ? p : min), points[0] || { forecastedBalance: 0, date: "" });
  const endForecastPoint = points[points.length - 1] || { forecastedBalance: 0 };
  const netDelta = (endForecastPoint.forecastedBalance || 0) - currentLiquidBalance;

  return (
    <div className="space-y-6">
      {/* ═══ Header ═══ */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-fadeInUp">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white font-display">Cash Flow Forecast</h1>
          <p className="text-xs text-slate-400 mt-0.5">90-day predictive balance model with automated recurring bill detection</p>
        </div>
        <div className="flex items-center gap-1.5 p-1 glass-card-static rounded-xl self-start">
          {[30, 60, 90].map((r) => (
            <button key={r} onClick={() => setRange(r as any)}
              className={`px-3 py-1 text-xs font-mono font-medium rounded-lg transition-all cursor-pointer ${
                range === r ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-bold" : "text-slate-400 hover:text-slate-200"
              }`}>{r} Days</button>
          ))}
        </div>
      </div>

      {/* ═══ Metric Cards ═══ */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { label: "Current Total Liquidity", value: formatCurrency(currentLiquidBalance), sub: "Checking + High-Yield Savings", color: "text-white" },
          { label: `Projected ${range}-Day Balance`, value: formatCurrency(endForecastPoint.forecastedBalance), sub: `${netDelta > 0 ? "+" : ""}${formatCurrency(netDelta)} net reserve growth`, color: "text-emerald-400" },
          { label: "Lowest Projected Trough", value: formatCurrency(minForecastPoint.forecastedBalance), sub: `Occurs on ${minForecastPoint.date ? formatDate(minForecastPoint.date, "MMM d, yyyy") : "N/A"} (Safe Buffer)`, color: "text-white" },
        ].map((card, i) => (
          <div key={i} className="glass-card rounded-2xl p-5 space-y-1 animate-fadeInUp" style={{ animationDelay: `${i * 0.08}s` }}>
            <span className="text-xs font-mono uppercase text-slate-400 font-semibold tracking-wider">{card.label}</span>
            <div className={`text-2xl lg:text-3xl font-bold font-mono ${card.color}`}>{card.value}</div>
            <p className="text-xs text-slate-400">{card.sub}</p>
          </div>
        ))}
      </div>

      {/* ═══ Forecast Chart ═══ */}
      {isLoading ? <ChartSkeleton height="h-[360px]" /> : (
        <ChartCard title="Predictive Cash Runway & Confidence Cone"
          subtitle="Solid line: Actual balance | Dashed: ML regression | Shaded: ±1.8σ Uncertainty band"
          footerNote="Regression incorporates salary cadences, verified subscriptions, rent leases, and historical burn rate."
          actions={
            <div className="flex items-center gap-4 text-xs font-mono">
              <span className="flex items-center gap-1.5 text-emerald-400"><span className="w-2.5 h-0.5 bg-emerald-400" /> Actual</span>
              <span className="flex items-center gap-1.5 text-indigo-400"><span className="w-2.5 h-0.5 border-t-2 border-dashed border-indigo-400" /> Forecast</span>
              <span className="flex items-center gap-1.5 text-slate-400"><span className="w-2.5 h-2 bg-indigo-500/20 rounded" /> Confidence Band</span>
            </div>
          }>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={points} margin={{ top: 10, right: 10, left: -5, bottom: 0 }}>
                <defs>
                  <linearGradient id="confidenceGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366F1" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#6366F1" stopOpacity={0.03} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="date" stroke="#64748B" fontSize={11} tickLine={false} tickFormatter={(d) => formatDate(d, "MMM d")} />
                <YAxis stroke="#64748B" fontSize={11} tickLine={false} tickFormatter={(v) => `${CURRENCY_SYMBOLS[profile.currency] || "₹"}${Math.round(v / 1000)}k`} />
                <Tooltip contentStyle={{ backgroundColor: "#0a0a0a", borderColor: "rgba(255,255,255,0.08)", borderRadius: 12 }}
                  formatter={(val: any, name: any) => [`${CURRENCY_SYMBOLS[profile.currency] || "₹"}${Number(val).toLocaleString()}`, name === "actualBalance" ? "Actual Balance" : name === "forecastedBalance" ? "Projected Balance" : name === "upperBound" ? "Upper Band" : "Lower Band"]}
                  labelFormatter={(l) => formatDate(l, "MMMM d, yyyy")} />
                <Area type="monotone" dataKey="upperBound" stroke="transparent" fill="url(#confidenceGrad)" />
                <Area type="monotone" dataKey="lowerBound" stroke="transparent" fill="#030303" />
                <Line type="monotone" dataKey="actualBalance" stroke="#10B981" strokeWidth={3} dot={false} />
                <Line type="monotone" dataKey="forecastedBalance" stroke="#6366F1" strokeWidth={2.5} strokeDasharray="4 4" dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>
      )}

      {/* ═══ Events & Methodology ═══ */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-card rounded-2xl p-6 space-y-4 animate-fadeInUp">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white flex items-center gap-2"><span className="w-1 h-4 bg-emerald-500 rounded-full opacity-60" />Key Forecast Events</h3>
              <p className="text-xs text-slate-400 ml-3">Identified cash inflections in the next {range} days</p>
            </div>
            <span className="text-xs font-mono text-emerald-400 font-bold">{events.length} Events</span>
          </div>
          <div className="space-y-2.5 max-h-[340px] overflow-y-auto pr-1">
            {events.map((ev, i) => {
              const isIncome = ev.amount > 0;
              return (
                <div key={ev.id} className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.04] hover:border-white/[0.08] flex items-center justify-between gap-3 text-xs transition-all animate-fadeInUp" style={{ animationDelay: `${i * 0.04}s` }}>
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg font-bold ${isIncome ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"}`}>
                      <Calendar className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="font-semibold text-slate-100">{ev.title}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{formatDate(ev.date, "EEEE, MMM d, yyyy")}</div>
                    </div>
                  </div>
                  <div className={`font-mono font-bold ${isIncome ? "text-emerald-400" : "text-slate-200"}`}>
                    {isIncome ? `+${formatCurrency(ev.amount)}` : formatCurrency(ev.amount)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="lg:col-span-1 glass-card rounded-2xl p-6 space-y-4 animate-fadeInUp stagger-2">
          <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm">
            <Info className="w-4 h-4" /><span>Forecasting Methodology</span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">Finpluse's predictive engine evaluates 180 days of historical cash-flow data. It factors in:</p>
          <ul className="text-xs text-slate-400 space-y-2 leading-relaxed">
            {[
              { color: "bg-emerald-400", text: "Bi-weekly tech engineering payroll direct deposits on the 1st and 15th." },
              { color: "bg-indigo-400", text: `Fixed apartment rent lease of ${formatCurrency(25000, profile.currency)} debited on the 1st of every month.` },
              { color: "bg-amber-400", text: "High-Yield Savings compound interest yield at 4.75% APY." },
            ].map((item, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className={`w-1.5 h-1.5 rounded-full ${item.color} mt-1.5 shrink-0`} />
                <span>{item.text}</span>
              </li>
            ))}
          </ul>
          <div className="p-3 rounded-xl bg-white/[0.02] border border-white/[0.04] text-[11px] text-slate-400">
            Confidence bounds widen organically over time to reflect discretionary dining and retail variance.
          </div>
        </div>
      </div>
    </div>
  );
};
