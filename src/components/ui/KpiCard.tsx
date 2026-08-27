import React, { useEffect, useState } from 'react';
import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '../../lib/utils/cn';
import { useUserStore } from '../../lib/store/useUserStore';
import { formatCurrency } from '../../lib/utils/formatters';

interface KpiCardProps {
  title: string;
  value: number;
  prefix?: string;
  suffix?: string;
  isCurrency?: boolean;
  changePct?: number;
  changePeriodText?: string;
  icon?: LucideIcon;
  subtext?: string;
  badge?: {
    text: string;
    variant?: 'emerald' | 'indigo' | 'amber' | 'rose' | 'slate';
  };
  onClick?: () => void;
  delay?: number;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  prefix = '',
  suffix = '',
  isCurrency = true,
  changePct,
  changePeriodText = 'vs last period',
  icon: Icon,
  subtext,
  badge,
  onClick,
  delay = 0,
}) => {
  const currency = useUserStore((s) => s.profile.currency);
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let start = 0;
    const end = value;
    const duration = 800;
    const steps = 30;
    const increment = (end - start) / steps;
    let currentStep = 0;

    const timer = setInterval(() => {
      currentStep++;
      if (currentStep >= steps) {
        setDisplayValue(end);
        clearInterval(timer);
      } else {
        const eased = 1 - Math.pow(1 - currentStep / steps, 3); // ease-out cubic
        setDisplayValue(start + (end - start) * eased);
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [value]);

  const formattedDisplay = isCurrency
    ? formatCurrency(displayValue, currency, { showDecimals: true })
    : `${prefix}${displayValue.toLocaleString('en-US', { maximumFractionDigits: 1 })}${suffix}`;

  const isPositive = (changePct ?? 0) > 0;
  const isNegative = (changePct ?? 0) < 0;

  return (
    <div
      onClick={onClick}
      className={cn(
        'group relative glass-card corner-accent p-5 rounded-xl animate-fadeInUp',
        onClick ? 'cursor-pointer' : ''
      )}
      style={{ animationDelay: `${delay}ms` }}
    >
      {/* Hover glow effect */}
      <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-emerald-500/0 to-cyan-500/0 group-hover:from-emerald-500/[0.03] group-hover:to-cyan-500/[0.02] transition-all duration-500 pointer-events-none" />
      
      <div className="flex items-start justify-between gap-2 mb-4 relative z-10">
        <span className="font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-[#a1a1aa]">
          {title}
        </span>
        {Icon && (
          <div className="p-1.5 bg-white/[0.04] border border-white/[0.06] text-white rounded-lg group-hover:border-emerald-500/20 group-hover:bg-emerald-500/[0.06] transition-all duration-300">
            <Icon className="w-3.5 h-3.5" />
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-2 mb-3 relative z-10">
        <div className="text-2xl lg:text-3xl font-bold font-mono tracking-tighter text-white tabular-nums">
          {formattedDisplay}
        </div>
        {badge && (
          <span className="font-mono text-[9px] uppercase tracking-wider px-1.5 py-0.5 bg-emerald-500/[0.08] text-emerald-400 border border-emerald-500/20 rounded-md">
            {badge.text}
          </span>
        )}
      </div>

      <div className="flex items-center justify-between gap-2 text-xs text-[#a1a1aa] relative z-10">
        {changePct !== undefined ? (
          <div className="flex items-center gap-2">
            <span
              className={cn(
                'inline-flex items-center font-mono text-[10px] px-1.5 py-0.5 border rounded-md',
                isPositive
                  ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/25'
                  : isNegative
                    ? 'text-rose-400 bg-rose-500/10 border-rose-500/25'
                    : 'text-[#a1a1aa] bg-white/[0.04] border-white/[0.08]'
              )}
            >
              {isPositive ? (
                <TrendingUp className="w-3 h-3 mr-1" />
              ) : isNegative ? (
                <TrendingDown className="w-3 h-3 mr-1" />
              ) : (
                <Minus className="w-3 h-3 mr-1" />
              )}
              {isPositive ? '+' : ''}
              {changePct.toFixed(1)}%
            </span>
            <span className="font-mono text-[9px] uppercase tracking-wider truncate">
              {changePeriodText}
            </span>
          </div>
        ) : subtext ? (
          <span className="font-mono text-[9px] uppercase tracking-wider truncate">{subtext}</span>
        ) : null}
      </div>
    </div>
  );
};