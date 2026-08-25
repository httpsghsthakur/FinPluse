with open(r'src\components\ui\KpiCard.tsx', 'w', encoding='utf-8') as f:
    f.write("""import React, { useEffect, useState } from 'react';
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
}) => {
  const currency = useUserStore((s) => s.profile.currency);
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let start = 0;
    const end = value;
    const duration = 600;
    const steps = 24;
    const increment = (end - start) / steps;
    let currentStep = 0;

    const timer = setInterval(() => {
      currentStep++;
      if (currentStep >= steps) {
        setDisplayValue(end);
        clearInterval(timer);
      } else {
        start += increment;
        setDisplayValue(start);
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
        'group relative bg-[#050505] border border-white/[0.08] hover:border-white/[0.2] p-5 transition-colors duration-200',
        onClick ? 'cursor-pointer' : ''
      )}
    >
      {/* Corner accent */}
      <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-white/[0.3]" />
      
      <div className="flex items-start justify-between gap-2 mb-4">
        <span className="font-mono text-[10px] font-bold uppercase tracking-[0.2em] text-[#a1a1aa]">
          {title}
        </span>
        {Icon && (
          <div className="p-1.5 bg-[#141414] border border-white/[0.08] text-white">
            <Icon className="w-3.5 h-3.5" />
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-2 mb-3">
        <div className="text-2xl lg:text-3xl font-bold font-mono tracking-tighter text-white tabular-nums">
          {formattedDisplay}
        </div>
        {badge && (
          <span className="font-mono text-[9px] uppercase tracking-wider px-1.5 py-0.5 bg-white/[0.05] text-white border border-white/[0.1]">
            {badge.text}
          </span>
        )}
      </div>

      <div className="flex items-center justify-between gap-2 text-xs text-[#a1a1aa]">
        {changePct !== undefined ? (
          <div className="flex items-center gap-2">
            <span
              className={cn(
                'inline-flex items-center font-mono text-[10px] px-1.5 py-0.5 border',
                isPositive
                  ? 'text-blue-400 bg-blue-500/10 border-blue-500/30'
                  : isNegative
                    ? 'text-rose-400 bg-rose-500/10 border-rose-500/30'
                    : 'text-[#a1a1aa] bg-white/[0.05] border-white/[0.1]'
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
};""")
