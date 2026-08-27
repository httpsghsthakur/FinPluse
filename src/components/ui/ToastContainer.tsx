import React from "react";
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from "lucide-react";
import { useUIStore } from "../../lib/store/useUIStore";
import { cn } from "../../lib/utils/cn";

export const ToastContainer: React.FC = () => {
  const { toasts, dismissToast } = useUIStore();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2.5 max-w-sm w-full px-4 pointer-events-none">
      {toasts.map((toast) => {
        const type = toast.type || "info";

        const icons = {
          success: (
            <div className="p-1 rounded-md bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shrink-0">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          ),
          warning: (
            <div className="p-1 rounded-md bg-amber-500/15 text-amber-400 border border-amber-500/30 shrink-0">
              <AlertTriangle className="w-4 h-4" />
            </div>
          ),
          error: (
            <div className="p-1 rounded-md bg-rose-500/15 text-rose-400 border border-rose-500/30 shrink-0">
              <XCircle className="w-4 h-4" />
            </div>
          ),
          info: (
            <div className="p-1 rounded-md bg-indigo-500/15 text-indigo-400 border border-indigo-500/30 shrink-0">
              <Info className="w-4 h-4" />
            </div>
          ),
        };

        const borders = {
          success: "border-emerald-500/30 bg-[#0a0a0a]/95 shadow-[0_10px_30px_rgba(16,185,129,0.15)]",
          warning: "border-amber-500/30 bg-[#0a0a0a]/95 shadow-[0_10px_30px_rgba(245,158,11,0.15)]",
          error: "border-rose-500/30 bg-[#0a0a0a]/95 shadow-[0_10px_30px_rgba(244,63,94,0.15)]",
          info: "border-indigo-500/30 bg-[#0a0a0a]/95 shadow-[0_10px_30px_rgba(99,102,241,0.15)]",
        };

        return (
          <div
            key={toast.id}
            className={cn(
              "pointer-events-auto flex items-start gap-3 p-4 rounded-xl border backdrop-blur-2xl transition-all duration-300 animate-slideInRight relative overflow-hidden",
              borders[type],
            )}
          >
            {/* Top accent glow line */}
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/[0.15] to-transparent" />
            
            {icons[type]}
            <div className="flex-1 text-xs">
              <div className="font-semibold text-slate-100 font-sans tracking-tight">
                {toast.title}
              </div>
              {toast.description && (
                <div className="text-slate-400 mt-0.5 leading-relaxed text-[11px]">
                  {toast.description}
                </div>
              )}
            </div>
            <button
              onClick={() => dismissToast(toast.id)}
              className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/[0.06] transition-colors cursor-pointer"
              aria-label="Dismiss notification"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
};
