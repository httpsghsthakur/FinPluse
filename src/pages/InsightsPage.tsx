import React, { useEffect, useState } from "react";
import { Lightbulb, Sparkles, AlertTriangle, TrendingUp, Award, Zap, CheckCircle2, X, ThumbsUp, ArrowRight, Info, Calendar } from "lucide-react";
import { NavLink } from "react-router-dom";
import { Insight, WeeklyDigest } from "../types";
import { CitationChip } from "../components/ui/CitationChip";
import { EmptyState } from "../components/ui/EmptyState";
import { TableSkeleton } from "../components/ui/Skeletons";
import { api } from "../lib/api";
import { useUIStore } from "../lib/store/useUIStore";
import { formatCurrency, formatDate } from "../lib/utils/formatters";

type FilterType = "all" | "alert" | "trend" | "win" | "tip";

export const InsightsPage: React.FC = () => {
  const { showToast } = useUIStore();
  const [digest, setDigest] = useState<WeeklyDigest | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [activeFilter, setActiveFilter] = useState<FilterType>("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [likedIds, setLikedIds] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [dig, insList] = await Promise.all([api.getWeeklyDigest(), api.getInsights()]);
      setDigest(dig);
      setInsights(insList);
    } catch (e) { console.error(e); }
    finally { setIsLoading(false); }
  };

  useEffect(() => { loadData(); }, []);

  const handleDismiss = async (id: string) => {
    try {
      await api.dismissInsight(id);
      setInsights((prev) => prev.map((i) => (i.id === id ? { ...i, isDismissed: true } : i)));
      showToast({ type: "info", title: "Insight Dismissed", description: "Finpluse AI will tune similar notifications." });
    } catch (e) { console.error(e); }
  };

  const handleToggleLike = (id: string) => {
    if (likedIds.includes(id)) {
      setLikedIds(likedIds.filter((x) => x !== id));
    } else {
      setLikedIds([...likedIds, id]);
      showToast({ type: "success", title: "Feedback Saved", description: "We will emphasize this type of insight in your feed." });
    }
  };

  const filteredInsights = insights.filter((i) => !i.isDismissed).filter((i) => activeFilter === "all" ? true : i.category === activeFilter);

  return (
    <div className="space-y-6">
      <div className="animate-fadeInUp">
        <h1 className="text-2xl font-bold tracking-tight text-white font-display">AI Financial Signals & Digest</h1>
        <p className="text-xs text-slate-400 mt-0.5">Proactive telemetry detection across spending velocity, subscriptions, runway, and milestone pacing</p>
      </div>

      {/* Weekly AI Digest Hero */}
      {digest && (
        <div className="glass-card rounded-2xl p-6 space-y-4 animate-fadeInUp stagger-1">
          {/* Top gradient line */}
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-emerald-500/30 to-transparent" />
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  Weekly Intelligence Briefing
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-lg bg-indigo-500/15 text-indigo-300 border border-indigo-500/25">{digest.weekLabel}</span>
                </h2>
                <p className="text-xs text-slate-400">Generated from {(digest.bullets || []).length} detected events</p>
              </div>
            </div>
            <div className="text-right hidden sm:block">
              <span className="text-xs text-slate-400 font-mono">Net Cash Flow</span>
              <div className={`text-lg font-bold font-mono ${digest.netSavings >= 0 ? "text-emerald-400" : "text-rose-400"}`}>
                {digest.netSavings >= 0 ? `+${formatCurrency(digest.netSavings)}` : formatCurrency(digest.netSavings)}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {(digest.bullets || []).map((pt, i) => (
              <div key={i} className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.04] text-xs text-slate-300 leading-relaxed flex items-start gap-2.5 animate-fadeInUp" style={{ animationDelay: `${i * 0.06}s` }}>
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <span>{pt}</span>
              </div>
            ))}
          </div>

          <div className="p-4 rounded-xl glass-card-accent text-xs flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <Zap className="w-4 h-4 text-emerald-400 shrink-0 fill-emerald-400" />
              <span className="text-slate-200"><strong className="text-emerald-400 font-bold">Copilot Recommended: </strong>{digest.actionableTip}</span>
            </div>
            <NavLink to="/app/copilot" className="text-xs text-emerald-400 hover:text-emerald-300 font-bold flex items-center gap-1 shrink-0 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/25 transition-all">
              <span>Ask AI</span><ArrowRight className="w-3 h-3" />
            </NavLink>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 animate-fadeInUp stagger-2">
        {[
          { id: "all", label: "All Signals", icon: Lightbulb },
          { id: "alert", label: "Alerts", icon: AlertTriangle },
          { id: "trend", label: "Trends", icon: TrendingUp },
          { id: "win", label: "Wins", icon: Award },
          { id: "tip", label: "Tips", icon: Zap },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeFilter === tab.id;
          return (
            <button key={tab.id} onClick={() => setActiveFilter(tab.id as FilterType)}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                isActive ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-bold" : "bg-white/[0.03] border border-white/[0.06] text-slate-400 hover:text-slate-200"
              }`}>
              <Icon className="w-3.5 h-3.5" /><span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Insights List */}
      {isLoading ? <TableSkeleton rows={5} /> : filteredInsights.length === 0 ? (
        <EmptyState title="No Active Insights" description="All telemetry signals in this category have been acknowledged or resolved." />
      ) : (
        <div className="space-y-3.5">
          {filteredInsights.map((ins, idx) => {
            const isExpanded = expandedId === ins.id;
            const isLiked = likedIds.includes(ins.id);
            const severityStyles: Record<string, string> = {
              alert: "border-rose-500/20 bg-rose-950/10",
              warning: "border-amber-500/20 bg-amber-950/10",
              success: "border-emerald-500/20 bg-emerald-950/10",
              info: "border-indigo-500/20 bg-indigo-950/10",
            };

            return (
              <div key={ins.id} className="glass-card rounded-2xl p-5 space-y-3 animate-fadeInUp hover:translate-y-[-2px]" style={{ animationDelay: `${idx * 0.05}s` }}>
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded-md border ${severityStyles[ins.severity] || severityStyles.info}`}>{ins.category}</span>
                      <span className="text-[11px] text-slate-400 font-mono">{formatDate(ins.date, "MMM d")}</span>
                    </div>
                    <h3 className="text-sm font-bold text-white">{ins.title}</h3>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button onClick={() => handleToggleLike(ins.id)}
                      className={`p-1.5 rounded-lg border transition-all cursor-pointer ${isLiked ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30" : "bg-white/[0.03] text-slate-400 border-white/[0.06] hover:text-slate-200"}`}>
                      <ThumbsUp className="w-3.5 h-3.5" />
                    </button>
                    <button onClick={() => handleDismiss(ins.id)} className="p-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] text-slate-400 hover:text-rose-400 hover:border-rose-500/25 transition-all cursor-pointer">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed">{ins.description}</p>

                <div className="pt-2 border-t border-white/[0.04] flex items-center justify-between text-xs">
                  <button onClick={() => setExpandedId(isExpanded ? null : ins.id)} className="text-[11px] text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1 cursor-pointer transition-colors">
                    <Info className="w-3.5 h-3.5" /><span>{isExpanded ? "Hide reasoning" : "Why am I seeing this?"}</span>
                  </button>
                  {ins.actionPath && (
                    <NavLink to={ins.actionPath} className="text-[11px] text-slate-200 hover:text-white font-semibold flex items-center gap-1.5 bg-white/[0.03] px-3 py-1.5 rounded-lg border border-white/[0.06] hover:border-white/[0.12] transition-all">
                      <span>{ins.actionLabel || "View Analysis"}</span><ArrowRight className="w-3 h-3" />
                    </NavLink>
                  )}
                </div>

                {isExpanded && (
                  <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] text-xs text-slate-300 space-y-2.5 animate-fadeIn">
                    <div className="leading-relaxed">{ins.whyExplanation}</div>
                    <CitationChip groundedData={ins.groundedData} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
