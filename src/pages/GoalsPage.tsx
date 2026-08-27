import React, { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { Target, Plus, Calendar, ChevronRight, Bot, ArrowRight, Sparkles, TrendingUp, Zap } from "lucide-react";
import { Goal, GoalBoost } from "../types";
import { ProgressBar } from "../components/ui/ProgressBar";
import { TableSkeleton } from "../components/ui/Skeletons";
import { EmptyState } from "../components/ui/EmptyState";
import { api } from "../lib/api";
import { useUIStore } from "../lib/store/useUIStore";
import { useUserStore } from "../lib/store/useUserStore";
import { formatCurrency, formatDate } from "../lib/utils/formatters";

export const GoalsPage: React.FC = () => {
  const { openCreateGoalModal, showToast } = useUIStore();
  const { profile } = useUserStore();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [boosts, setBoosts] = useState<GoalBoost[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadGoals = async () => {
    setIsLoading(true);
    try {
      const [gList, bList] = await Promise.all([api.getGoals(), api.getGoalBoosts()]);
      setGoals(gList);
      setBoosts(bList);
    } catch (e) { console.error(e); }
    finally { setIsLoading(false); }
  };

  useEffect(() => { loadGoals(); }, []);

  const handleApplyBoost = async (boost: GoalBoost) => {
    try {
      await api.applyGoalBoost(boost.id);
      showToast({ type: "success", title: "Boost Applied!", description: `${formatCurrency(boost.amount, profile.currency)} allocated from ${boost.source}.` });
      loadGoals();
    } catch (e) { showToast({ type: "error", title: "Boost Failed" }); }
  };

  const totalTarget = goals.reduce((s, g) => s + g.targetAmount, 0);
  const totalSaved = goals.reduce((s, g) => s + g.currentAmount, 0);
  const overallPct = totalTarget > 0 ? (totalSaved / totalTarget) * 100 : 0;

  if (isLoading) return <div className="space-y-6"><TableSkeleton rows={4} /></div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-fadeInUp">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white font-display">Financial Goals</h1>
          <p className="text-xs text-slate-400 mt-0.5">Track savings targets with AI-powered allocation recommendations</p>
        </div>
        <button onClick={openCreateGoalModal} className="flex items-center gap-1.5 px-3.5 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-xl transition-all cursor-pointer btn-glow">
          <Plus className="w-4 h-4 stroke-[2.5]" /><span>Create Goal</span>
        </button>
      </div>

      {/* Overall Progress Banner */}
      {goals.length > 0 && (
        <div className="glass-card rounded-2xl p-6 space-y-4 animate-fadeInUp stagger-1">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-mono uppercase text-slate-400 font-semibold tracking-wider">Combined Goal Progress</span>
              <div className="text-3xl font-bold font-mono text-white mt-1">{overallPct.toFixed(1)}%</div>
            </div>
            <div className="text-right">
              <div className="text-sm font-mono text-emerald-400">{formatCurrency(totalSaved, profile.currency)}</div>
              <div className="text-xs text-slate-400">of {formatCurrency(totalTarget, profile.currency)}</div>
            </div>
          </div>
          <ProgressBar value={totalSaved} max={totalTarget} size="lg" color="#10B981" />
        </div>
      )}

      {goals.length === 0 ? (
        <EmptyState title="No Goals Set" description="Create your first savings goal and let Finpluse AI track your progress." actionLabel="Create Goal" onAction={openCreateGoalModal} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {goals.map((goal, i) => {
            const pct = (goal.currentAmount / goal.targetAmount) * 100;
            const goalBoosts = boosts.filter((b) => b.goalId === goal.id && !b.isApplied);
            return (
              <div key={goal.id} className="glass-card rounded-2xl p-5 space-y-4 group animate-fadeInUp" style={{ animationDelay: `${i * 0.08}s` }}>
                {/* Hover gradient overlay */}
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-emerald-500/0 to-cyan-500/0 group-hover:from-emerald-500/[0.03] group-hover:to-cyan-500/[0.02] transition-all duration-500 pointer-events-none" />
                
                <div className="relative z-10 space-y-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0">
                        <Target className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-white">{goal.name}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          {goal.priority && (
                            <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${
                              goal.priority === "high" ? "bg-rose-500/10 text-rose-300 border-rose-500/25" :
                              goal.priority === "medium" ? "bg-amber-500/10 text-amber-300 border-amber-500/25" :
                              "bg-slate-500/10 text-slate-300 border-slate-500/25"
                            }`}>{goal.priority} Priority</span>
                          )}
                          <span className="text-[10px] text-slate-400 font-mono flex items-center gap-1">
                            <Calendar className="w-3 h-3" />{formatDate(goal.targetDate, "MMM yyyy")}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold font-mono text-white">{pct.toFixed(0)}%</div>
                    </div>
                  </div>

                  <ProgressBar value={goal.currentAmount} max={goal.targetAmount} size="md" color="#10B981" />
                  
                  <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                    <span>{formatCurrency(goal.currentAmount, profile.currency)} saved</span>
                    <span>{formatCurrency(goal.targetAmount - goal.currentAmount, profile.currency)} remaining</span>
                  </div>

                  {/* AI Boost Suggestions */}
                  {goalBoosts.length > 0 && (
                    <div className="space-y-2">
                      <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 font-bold flex items-center gap-1">
                        <Zap className="w-3 h-3" /> AI Boost Suggestions
                      </span>
                      {goalBoosts.slice(0, 2).map((boost) => (
                        <div key={boost.id} className="p-3 rounded-xl bg-emerald-500/[0.04] border border-emerald-500/15 flex items-center justify-between gap-2 text-xs">
                          <div>
                            <span className="text-slate-200 font-medium">{boost.description}</span>
                            <span className="text-emerald-400 font-mono font-bold ml-2">+{formatCurrency(boost.amount, profile.currency)}</span>
                          </div>
                          <button onClick={() => handleApplyBoost(boost)} className="px-2.5 py-1 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-[11px] rounded-lg transition-all cursor-pointer btn-glow shrink-0">
                            Apply
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* AI Copilot CTA */}
      <div className="glass-card-accent rounded-2xl p-5 space-y-2 animate-fadeInUp">
        <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm"><Bot className="w-4 h-4" /><span>Goal Intelligence</span></div>
        <p className="text-xs text-slate-300">Ask Copilot to analyze your spending and identify optimal allocation strategies for your goals.</p>
        <NavLink to="/app/copilot" className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 font-semibold transition-colors group">
          <span>Optimize My Goals</span><ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
        </NavLink>
      </div>
    </div>
  );
};
