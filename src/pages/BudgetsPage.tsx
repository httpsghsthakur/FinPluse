import React, { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { PieChart, Plus, AlertTriangle, ChevronRight, Edit2, Bot, ArrowRight, TrendingUp } from "lucide-react";
import { BudgetCategory, BudgetSummary } from "../types";
import { CategoryIcon } from "../components/ui/CategoryIcon";
import { ProgressBar } from "../components/ui/ProgressBar";
import { KpiSkeleton, TableSkeleton } from "../components/ui/Skeletons";
import { AmountText } from "../components/ui/AmountText";
import { api } from "../lib/api";
import { useUIStore } from "../lib/store/useUIStore";
import { formatCurrency } from "../lib/utils/formatters";
import { useUserStore } from "../lib/store/useUserStore";

export const BudgetsPage: React.FC = () => {
  const { showToast } = useUIStore();
  const { profile } = useUserStore();
  const [summary, setSummary] = useState<BudgetSummary | null>(null);
  const [budgets, setBudgets] = useState<BudgetCategory[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [sum, bList] = await Promise.all([api.getBudgetSummary(), api.getBudgets()]);
      setSummary(sum);
      setBudgets(bList);
    } catch (e) { console.error(e); }
    finally { setIsLoading(false); }
  };

  useEffect(() => { loadData(); }, []);

  if (isLoading || !summary) {
    return <div className="space-y-6"><div className="grid grid-cols-1 sm:grid-cols-3 gap-4"><KpiSkeleton /><KpiSkeleton /><KpiSkeleton /></div><TableSkeleton rows={6} /></div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-fadeInUp">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white font-display">Budgets & Allocations</h1>
          <p className="text-xs text-slate-400 mt-0.5">Category-level envelope allocation with real-time pacing analysis</p>
        </div>
        <NavLink to="/app/settings" className="flex items-center gap-1.5 px-3 py-2 glass-card text-slate-200 text-xs font-semibold rounded-xl hover:border-white/[0.12] transition-all">
          <Edit2 className="w-3.5 h-3.5 text-emerald-400" /><span>Edit Budgets</span>
        </NavLink>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { label: "Total Monthly Budget", value: formatCurrency(summary.totalBudget, profile.currency), sub: `${budgets.length} categories allocated` },
          { label: "Total Spent This Cycle", value: formatCurrency(summary.totalSpent, profile.currency), sub: `${summary.pctUsed.toFixed(0)}% of monthly budget utilized`, color: summary.pctUsed > 90 ? "text-rose-400" : summary.pctUsed > 70 ? "text-amber-400" : "text-emerald-400" },
          { label: "Budget Remaining", value: formatCurrency(summary.totalRemaining, profile.currency), sub: summary.daysLeftInMonth ? `${summary.daysLeftInMonth} days remaining in billing cycle` : "Current period" },
        ].map((card, i) => (
          <div key={i} className="glass-card rounded-2xl p-5 space-y-1 animate-fadeInUp" style={{ animationDelay: `${i * 0.08}s` }}>
            <span className="text-xs font-mono uppercase text-slate-400 font-semibold tracking-wider">{card.label}</span>
            <div className={`text-2xl lg:text-3xl font-bold font-mono ${card.color || "text-white"}`}>{card.value}</div>
            <p className="text-xs text-slate-400">{card.sub}</p>
          </div>
        ))}
      </div>

      {/* Overall Progress */}
      <div className="glass-card rounded-2xl p-5 space-y-3 animate-fadeInUp stagger-3">
        <div className="flex items-center justify-between text-xs">
          <span className="font-bold text-white">Overall Budget Usage</span>
          <span className="font-mono text-slate-400">{formatCurrency(summary.totalSpent)} / {formatCurrency(summary.totalBudget)}</span>
        </div>
        <ProgressBar value={summary.totalSpent} max={summary.totalBudget} size="lg" showPercent />
      </div>

      {/* Budget Categories */}
      <div className="space-y-3 animate-fadeInUp stagger-4">
        {budgets.map((b, i) => {
          const pct = (b.spent / b.budget) * 100;
          const isOver = pct >= 100;
          const isWarn = pct >= 80;
          return (
            <div key={b.categoryId} className="glass-card rounded-2xl p-5 space-y-3 animate-fadeInUp" style={{ animationDelay: `${i * 0.04}s` }}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <CategoryIcon name={b.icon} color={b.color} size="md" />
                  <div>
                    <h3 className="text-sm font-bold text-white">{b.categoryName}</h3>
                    <p className="text-[11px] text-slate-400 font-mono">{formatCurrency(b.spent, profile.currency)} of {formatCurrency(b.budget, profile.currency)}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-lg font-bold font-mono ${isOver ? "text-rose-400" : isWarn ? "text-amber-400" : "text-emerald-400"}`}>
                    {pct.toFixed(0)}%
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">{formatCurrency(b.remaining, profile.currency)} left</span>
                </div>
              </div>
              <ProgressBar value={b.spent} max={b.budget} size="md" color={b.color} />
              {b.aiPacingAlert && (
                <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs flex items-start gap-2 text-amber-300 animate-fadeIn">
                  <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  <span>{b.aiPacingAlert}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* AI Copilot CTA */}
      <div className="glass-card-accent rounded-2xl p-5 space-y-2 animate-fadeInUp">
        <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm"><Bot className="w-4 h-4" /><span>Budget Optimization</span></div>
        <p className="text-xs text-slate-300">Ask Copilot to identify the categories where you can safely reduce spending this month.</p>
        <NavLink to="/app/copilot" className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 font-semibold transition-colors group">
          <span>Ask AI for Budget Analysis</span><ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
        </NavLink>
      </div>
    </div>
  );
};
