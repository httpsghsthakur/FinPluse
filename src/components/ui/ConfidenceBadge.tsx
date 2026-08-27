import React from "react";
import { ShieldCheck, ShieldAlert, Sparkles } from "lucide-react";
import { cn } from "../../lib/utils/cn";

interface ConfidenceBadgeProps {
  confidence?: "High" | "Medium" | "Low" | "high" | "medium" | "low";
  score?: number;
  band?: "high" | "medium" | "low";
  className?: string;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  confidence,
  score,
  band,
  className,
}) => {
  const norm = (band || confidence || "high").toLowerCase();

  const styles: Record<string, { bg: string; icon: any; text: string }> = {
    high: {
      bg: "bg-emerald-500/10 text-emerald-400 border-emerald-500/25",
      icon: ShieldCheck,
      text: "High Grounding Confidence",
    },
    medium: {
      bg: "bg-amber-500/10 text-amber-400 border-amber-500/25",
      icon: Sparkles,
      text: "Medium Grounding",
    },
    low: {
      bg: "bg-white/[0.04] text-slate-400 border-white/[0.08]",
      icon: ShieldAlert,
      text: "Low Grounding (Estimate)",
    },
  };

  const current = styles[norm] || styles.high;
  const Icon = current.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-mono font-semibold border uppercase tracking-wider",
        current.bg,
        className,
      )}
    >
      <Icon className="w-3 h-3" />
      {score !== undefined ? `${Math.round(score * 100)}% Verifiable` : current.text}
    </span>
  );
};
