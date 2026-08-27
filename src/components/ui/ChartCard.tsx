import React from "react";
import { cn } from "../../lib/utils/cn";

interface ChartCardProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  footerNote?: string;
  className?: string;
  children: React.ReactNode;
}

export const ChartCard: React.FC<ChartCardProps> = ({
  title,
  subtitle,
  actions,
  footerNote,
  className,
  children,
}) => {
  return (
    <div
      className={cn(
        "glass-card rounded-2xl p-5 md:p-6 transition-all duration-300 flex flex-col justify-between animate-fadeInUp",
        className,
      )}
    >
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <div>
            {/* Title with accent line */}
            <h3 className="text-base font-bold text-white tracking-tight flex items-center gap-2">
              <span className="w-1 h-4 bg-emerald-500 rounded-full opacity-60" />
              {title}
            </h3>
            {subtitle && (
              <p className="text-xs text-slate-400 mt-0.5 ml-3">{subtitle}</p>
            )}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>

        <div className="w-full relative min-h-[260px] flex items-center justify-center">
          {children}
        </div>
      </div>

      {footerNote && (
        <div className="mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between text-xs text-slate-400">
          <span>{footerNote}</span>
        </div>
      )}
    </div>
  );
};
