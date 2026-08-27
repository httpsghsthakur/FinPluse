import React from "react";
import { LucideIcon, FolderSearch } from "lucide-react";
import { cn } from "../../lib/utils/cn";

interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon: Icon = FolderSearch,
  actionLabel,
  onAction,
  className,
}) => {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 md:p-12 text-center rounded-2xl border border-dashed border-white/[0.08] bg-white/[0.01] glass-card-static",
        className,
      )}
    >
      <div className="p-3.5 rounded-2xl bg-white/[0.04] border border-white/[0.06] text-slate-400 mb-4 shadow-inner">
        <Icon className="w-8 h-8 text-emerald-400" />
      </div>
      <h3 className="text-base font-bold text-white mb-1 font-display">{title}</h3>
      <p className="text-xs text-slate-400 max-w-sm mb-6 leading-relaxed">
        {description}
      </p>
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-2 text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-xl transition-all shadow-lg shadow-emerald-500/20 cursor-pointer btn-glow"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
};
