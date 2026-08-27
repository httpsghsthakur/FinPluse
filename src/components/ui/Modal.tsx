import React, { useEffect } from "react";
import { X } from "lucide-react";
import { cn } from "../../lib/utils/cn";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  maxWidth?: "sm" | "md" | "lg" | "xl";
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  maxWidth = "md",
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const maxWidthClasses = {
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-lg",
    xl: "max-w-xl",
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop with blur */}
      <div
        onClick={onClose}
        className="fixed inset-0 bg-black/60 backdrop-blur-lg transition-opacity animate-fadeIn"
      />

      {/* Dialog container with scale-in animation */}
      <div
        className={cn(
          "relative w-full bg-[#0a0a0a]/95 backdrop-blur-2xl border border-white/[0.08] rounded-2xl p-6 shadow-[0_25px_60px_rgba(0,0,0,0.5)] z-10 overflow-hidden animate-scaleIn",
          maxWidthClasses[maxWidth],
        )}
      >
        {/* Gradient glow at top */}
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-emerald-500/30 to-transparent" />
        
        {/* Corner accents */}
        <div className="absolute top-0 left-0 w-3 h-3 border-t border-l border-emerald-500/30" />
        <div className="absolute top-0 right-0 w-3 h-3 border-t border-r border-emerald-500/30" />

        <div className="flex items-start justify-between gap-4 mb-5">
          <div>
            <h2 className="text-lg font-bold text-slate-100 tracking-tight">
              {title}
            </h2>
            {description && (
              <p className="text-xs text-slate-400 mt-1">{description}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-white/[0.06] transition-all duration-200 cursor-pointer group"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5 group-hover:rotate-90 transition-transform duration-300" />
          </button>
        </div>

        <div>{children}</div>
      </div>
    </div>
  );
};
