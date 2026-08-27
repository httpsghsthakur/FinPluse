import React from "react";
import { cn } from "../../lib/utils/cn";

const Skeleton = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => {
  return (
    <div
      className={cn(
        "rounded-xl skeleton-shimmer",
        className,
      )}
      {...props}
    />
  );
};

export const KpiSkeleton: React.FC = () => {
  return (
    <div className="glass-card-static rounded-xl p-5 space-y-3">
      <div className="flex justify-between items-center">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-7 w-7 rounded-lg" />
      </div>
      <Skeleton className="h-8 w-36" />
      <div className="flex gap-2">
        <Skeleton className="h-4 w-16 rounded-md" />
        <Skeleton className="h-4 w-24 rounded-md" />
      </div>
    </div>
  );
};

export const ChartSkeleton: React.FC<{ height?: string }> = ({
  height = "h-[320px]",
}) => {
  return (
    <div className="glass-card-static rounded-2xl p-6 space-y-4">
      <div className="flex justify-between items-center">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-8 w-28 rounded-lg" />
      </div>
      <Skeleton className={cn("w-full rounded-xl", height)} />
    </div>
  );
};

export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => {
  return (
    <div className="glass-card-static rounded-2xl p-4 space-y-3">
      <Skeleton className="h-10 w-full rounded-lg" />
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="flex items-center justify-between gap-4 py-2 border-b border-white/[0.04] last:border-0"
          style={{ animationDelay: `${i * 0.05}s` }}
        >
          <div className="flex items-center gap-3">
            <Skeleton className="h-8 w-8 rounded-lg" />
            <div className="space-y-1.5">
              <Skeleton className="h-3.5 w-32" />
              <Skeleton className="h-2.5 w-20" />
            </div>
          </div>
          <Skeleton className="h-4 w-20 rounded-md" />
        </div>
      ))}
    </div>
  );
};
