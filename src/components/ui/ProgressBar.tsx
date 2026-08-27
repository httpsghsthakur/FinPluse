import React from "react";
import { cn } from "../../lib/utils/cn";

interface ProgressBarProps {
  value: number;
  max?: number;
  color?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
  showPercent?: boolean;
  warnThreshold?: number;
  dangerThreshold?: number;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  color,
  size = "md",
  className,
  showPercent = false,
  warnThreshold = 80,
  dangerThreshold = 100,
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  const rawPercentage = (value / max) * 100;

  // Auto determine color based on budget thresholds if color not explicitly passed
  let barColor = color;
  if (!barColor) {
    if (rawPercentage >= dangerThreshold) {
      barColor = "#EF4444";
    } else if (rawPercentage >= warnThreshold) {
      barColor = "#F59E0B";
    } else {
      barColor = "#10B981";
    }
  }

  const heightClasses = {
    sm: "h-1.5",
    md: "h-2.5",
    lg: "h-4",
  };

  return (
    <div className={cn("w-full", className)}>
      <div
        className={cn(
          "w-full bg-white/[0.04] rounded-full overflow-hidden relative",
          heightClasses[size],
        )}
      >
        {/* Animated fill bar */}
        <div
          className="h-full rounded-full transition-all duration-700 ease-out relative animate-progress-fill"
          style={{
            width: `${percentage}%`,
            backgroundColor: barColor,
            boxShadow: `0 0 12px ${barColor}30, 0 0 4px ${barColor}20`,
          }}
        >
          {/* Glowing tip */}
          {percentage > 5 && (
            <div
              className="absolute right-0 top-0 bottom-0 w-2 rounded-full animate-glow-tip"
              style={{
                backgroundColor: barColor,
                boxShadow: `0 0 8px ${barColor}80, 0 0 16px ${barColor}40`,
              }}
            />
          )}
        </div>
      </div>
      {showPercent && (
        <div className="flex justify-between items-center mt-1 text-xs text-slate-400 font-mono">
          <span>{rawPercentage.toFixed(0)}%</span>
          <span>
            {value} / {max}
          </span>
        </div>
      )}
    </div>
  );
};
