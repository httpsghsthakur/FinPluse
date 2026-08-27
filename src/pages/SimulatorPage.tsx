import React, { useState, useEffect, useMemo } from "react";
import { SlidersHorizontal, Zap, RotateCcw, TrendingUp, DollarSign, Percent, Calendar } from "lucide-react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, ReferenceLine } from "recharts";
import { ChartCard } from "../components/ui/ChartCard";
import { api } from "../lib/api";
import { formatCurrency, CURRENCY_SYMBOLS } from "../lib/utils/formatters";
import { useUserStore } from "../lib/store/useUserStore";

interface SimParams {
  monthlyIncome: number;
  monthlyExpenses: number;
  monthlySavingsGoal: number;
  investReturnRate: number;
  emergencyFundTarget: number;
  horizonMonths: number;
}

const PRESETS: { label: string; params: Partial<SimParams> }[] = [
  { label: "Conservative", params: { investReturnRate: 6, monthlySavingsGoal: 10000, monthlyExpenses: 45000 } },
  { label: "Moderate Growth", params: { investReturnRate: 10, monthlySavingsGoal: 15000, monthlyExpenses: 40000 } },
  { label: "Aggressive", params: { investReturnRate: 14, monthlySavingsGoal: 25000, monthlyExpenses: 35000 } },
];

export const SimulatorPage: React.FC = () => {
  const { profile } = useUserStore();
  const [params, setParams] = useState<SimParams>({
    monthlyIncome: 85000,
    monthlyExpenses: 42000,
    monthlySavingsGoal: 15000,
    investReturnRate: 10,
    emergencyFundTarget: 150000,
    horizonMonths: 24,
  });

  const simData = useMemo(() => {
    const data: { month: number; balance: number; invested: number; emergency: number }[] = [];
    let balance = 43270;
    let invested = 0;
    let emergency = 0;
    const monthlyReturn = params.investReturnRate / 100 / 12;

    for (let m = 0; m <= params.horizonMonths; m++) {
      data.push({ month: m, balance, invested, emergency: Math.min(emergency, params.emergencyFundTarget) });
      const surplus = params.monthlyIncome - params.monthlyExpenses;
      if (emergency < params.emergencyFundTarget) {
        const emContrib = Math.min(surplus * 0.3, params.emergencyFundTarget - emergency);
        emergency += emContrib;
        const remainSurplus = surplus - emContrib;
        const investContrib = Math.min(remainSurplus, params.monthlySavingsGoal);
        invested += invested * monthlyReturn + investContrib;
        balance += surplus - emContrib - investContrib;
      } else {
        const investContrib = Math.min(surplus, params.monthlySavingsGoal);
        invested += invested * monthlyReturn + investContrib;
        balance += surplus - investContrib;
      }
    }
    return data;
  }, [params]);

  const finalBalance = simData[simData.length - 1]?.balance || 0;
  const finalInvested = simData[simData.length - 1]?.invested || 0;
  const finalEmergency = simData[simData.length - 1]?.emergency || 0;
  const totalProjectedWealth = finalBalance + finalInvested + finalEmergency;

  const updateParam = (key: keyof SimParams, value: number) => {
    setParams((prev) => ({ ...prev, [key]: value }));
  };

  const applyPreset = (preset: Partial<SimParams>) => {
    setParams((prev) => ({ ...prev, ...preset }));
  };

  const resetDefaults = () => {
    setParams({
      monthlyIncome: 85000, monthlyExpenses: 42000, monthlySavingsGoal: 15000,
      investReturnRate: 10, emergencyFundTarget: 150000, horizonMonths: 24,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-fadeInUp">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white font-display">What-If Simulator</h1>
          <p className="text-xs text-slate-400 mt-0.5">Monte Carlo-style scenario planning with real-time projection recalculation</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono px-2 py-1 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 animate-breathing">
            <Zap className="w-3 h-3 inline mr-1" />LIVE COMPUTE
          </span>
          <button onClick={resetDefaults} className="p-2 glass-card text-slate-400 hover:text-white rounded-xl cursor-pointer transition-all hover:border-white/[0.12]">
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Presets */}
      <div className="flex items-center gap-2 animate-fadeInUp stagger-1">
        <span className="text-[10px] font-mono uppercase text-slate-400 tracking-wider mr-2">Presets:</span>
        {PRESETS.map((p, i) => (
          <button key={i} onClick={() => applyPreset(p.params)}
            className="px-3 py-1.5 rounded-lg glass-card text-xs font-semibold text-slate-300 hover:text-emerald-400 hover:border-emerald-500/30 transition-all cursor-pointer">
            {p.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls Panel */}
        <div className="lg:col-span-1 glass-card rounded-2xl p-6 space-y-6 animate-fadeInUp stagger-2">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-emerald-400" /> Scenario Parameters
          </h3>

          {[
            { key: "monthlyIncome" as const, label: "Monthly Income", icon: DollarSign, min: 20000, max: 500000, step: 5000 },
            { key: "monthlyExpenses" as const, label: "Monthly Expenses", icon: DollarSign, min: 10000, max: 300000, step: 5000 },
            { key: "monthlySavingsGoal" as const, label: "Investment Contribution", icon: TrendingUp, min: 0, max: 100000, step: 1000 },
            { key: "investReturnRate" as const, label: "Expected Annual Return (%)", icon: Percent, min: 0, max: 30, step: 0.5 },
            { key: "emergencyFundTarget" as const, label: "Emergency Fund Target", icon: DollarSign, min: 0, max: 500000, step: 10000 },
            { key: "horizonMonths" as const, label: "Projection Horizon (Months)", icon: Calendar, min: 6, max: 60, step: 6 },
          ].map(({ key, label, icon: Icon, min, max, step }) => (
            <div key={key} className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-400 flex items-center gap-1.5">
                  <Icon className="w-3 h-3" /> {label}
                </span>
                <span className="font-mono font-bold text-white">
                  {key === "investReturnRate" ? `${params[key]}%` : key === "horizonMonths" ? `${params[key]}M` : formatCurrency(params[key], profile.currency)}
                </span>
              </div>
              <input
                type="range" min={min} max={max} step={step} value={params[key]}
                onChange={(e) => updateParam(key, parseFloat(e.target.value))}
                className="w-full cursor-pointer"
              />
            </div>
          ))}
        </div>

        {/* Results + Chart */}
        <div className="lg:col-span-2 space-y-4">
          {/* Result KPIs */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { label: "Total Wealth", value: formatCurrency(totalProjectedWealth, profile.currency), color: "text-white" },
              { label: "Liquid Cash", value: formatCurrency(finalBalance, profile.currency), color: "text-emerald-400" },
              { label: "Invested", value: formatCurrency(finalInvested, profile.currency), color: "text-indigo-400" },
              { label: "Emergency", value: formatCurrency(finalEmergency, profile.currency), color: "text-amber-400" },
            ].map((kpi, i) => (
              <div key={i} className="glass-card rounded-xl p-4 space-y-1 animate-fadeInUp" style={{ animationDelay: `${i * 0.06}s` }}>
                <span className="text-[9px] font-mono uppercase text-slate-400 tracking-wider">{kpi.label}</span>
                <div className={`text-lg font-bold font-mono ${kpi.color}`}>{kpi.value}</div>
              </div>
            ))}
          </div>

          {/* Chart */}
          <ChartCard title="Projected Wealth Growth"
            subtitle={`${params.horizonMonths}-month forward simulation`}
            actions={
              <div className="flex items-center gap-3 text-xs font-mono">
                <span className="flex items-center gap-1.5 text-emerald-400"><span className="w-2 h-2 rounded-full bg-emerald-400" /> Cash</span>
                <span className="flex items-center gap-1.5 text-indigo-400"><span className="w-2 h-2 rounded-full bg-indigo-400" /> Invested</span>
                <span className="flex items-center gap-1.5 text-amber-400"><span className="w-2 h-2 rounded-full bg-amber-400" /> Emergency</span>
              </div>
            }>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={simData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="cashGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="investGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366F1" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#6366F1" stopOpacity={0.0} />
                    </linearGradient>
                    <linearGradient id="emGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="month" stroke="#64748B" fontSize={11} tickLine={false} tickFormatter={(v) => `M${v}`} />
                  <YAxis stroke="#64748B" fontSize={11} tickLine={false} tickFormatter={(v) => `${CURRENCY_SYMBOLS[profile.currency] || "₹"}${Math.round(v / 1000)}k`} />
                  <Tooltip contentStyle={{ backgroundColor: "#0a0a0a", borderColor: "rgba(255,255,255,0.08)", borderRadius: 12 }}
                    formatter={(val: any, name: any) => [`${CURRENCY_SYMBOLS[profile.currency] || "₹"}${Number(val).toLocaleString()}`, name === "balance" ? "Liquid Cash" : name === "invested" ? "Invested Portfolio" : "Emergency Fund"]} />
                  <Area type="monotone" dataKey="balance" stroke="#10B981" strokeWidth={2.5} fill="url(#cashGrad)" />
                  <Area type="monotone" dataKey="invested" stroke="#6366F1" strokeWidth={2} fill="url(#investGrad)" />
                  <Area type="monotone" dataKey="emergency" stroke="#F59E0B" strokeWidth={2} fill="url(#emGrad)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>
        </div>
      </div>
    </div>
  );
};
