import React, { useState } from "react";
import { Database, ChevronDown, ChevronUp } from "lucide-react";
import { GroundedMetric } from "../../types";
import { cn } from "../../lib/utils/cn";

interface CitationChipProps {
  groundedData: GroundedMetric[];
  className?: string;
}

export const CitationChip: React.FC<CitationChipProps> = ({
  groundedData,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!groundedData || groundedData.length === 0) return null;

  return (
    <div className={cn("inline-block text-xs font-mono", className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/25 transition-all cursor-pointer text-[11px] font-semibold"
      >
        <Database className="w-3 h-3 text-emerald-400" />
        <span>Grounded data ({groundedData.length} signals)</span>
        {isOpen ? (
          <ChevronUp className="w-3 h-3" />
        ) : (
          <ChevronDown className="w-3 h-3" />
        )}
      </button>

      {isOpen && (
        <div className="mt-2 p-3.5 bg-[#0a0a0a]/95 backdrop-blur-xl border border-white/[0.08] rounded-xl space-y-2 shadow-2xl max-w-sm animate-fadeIn">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1 font-mono">
            Grounding Evidence Signals
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {groundedData.map((item, idx) => (
              <div
                key={idx}
                className="bg-white/[0.02] p-2 rounded-lg border border-white/[0.04]"
              >
                <div className="text-[9px] text-slate-400 font-mono truncate">{item.label}</div>
                <div className="font-semibold text-slate-200 truncate font-mono text-[11px] mt-0.5">
                  {item.value}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
