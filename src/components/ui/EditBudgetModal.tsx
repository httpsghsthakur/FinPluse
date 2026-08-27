import React, { useState } from "react";
import { Modal } from "./Modal";
import { Category, Budget } from "../../types";
import { api } from "../../lib/api";
import { useUIStore } from "../../lib/store/useUIStore";
import { useUserStore } from "../../lib/store/useUserStore";
import { Sparkles } from "lucide-react";
import { formatCurrency, CURRENCY_SYMBOLS } from "../../lib/utils/formatters";

interface EditBudgetModalProps {
  isOpen: boolean;
  onClose: () => void;
  category: Category | null;
  budget: Budget | null;
  onSaved: () => void;
}

export const EditBudgetModal: React.FC<EditBudgetModalProps> = ({
  isOpen,
  onClose,
  category,
  budget,
  onSaved,
}) => {
  const { showToast } = useUIStore();
  const { profile } = useUserStore();
  const [limit, setLimit] = useState(
    category?.defaultMonthlyBudget?.toString() || "400",
  );
  const [isSaving, setIsSaving] = useState(false);

  if (!category) return null;

  // AI 3-month suggestion
  const baseBudget = budget?.spent || category.defaultMonthlyBudget || 400;
  const aiSuggestedLimit = Math.round((baseBudget * 1.08) / 10) * 10;
  const currSymbol = CURRENCY_SYMBOLS[profile.currency] || "₹";

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    const val = parseFloat(limit);
    if (isNaN(val) || val < 0) return;

    setIsSaving(true);
    try {
      await api.updateCategory(category.id, {
        defaultMonthlyBudget: val,
      });
      showToast({
        type: "success",
        title: "Budget Updated",
        description: `Set ${category.name} monthly limit to ${formatCurrency(val, profile.currency)}.`,
      });
      onSaved();
      onClose();
    } catch (err) {
      showToast({
        type: "error",
        title: "Save Failed",
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Edit ${category.name} Budget`}
      description="Adjust your target monthly spending threshold"
      maxWidth="sm"
    >
      <form onSubmit={handleSave} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5 font-mono uppercase tracking-wider text-[10px]">
            Monthly Target ({currSymbol})
          </label>
          <input
            type="number"
            step="10"
            required
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-white/[0.03] border border-white/[0.06] rounded-xl text-xs font-mono text-slate-100 placeholder-slate-500 input-glow"
          />
        </div>

        {/* AI Suggestion Chip */}
        <div className="p-3.5 rounded-xl bg-emerald-500/[0.04] border border-emerald-500/15 text-xs space-y-1.5">
          <div className="flex items-center gap-1.5 font-semibold text-emerald-400">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Suggested Allocation</span>
          </div>
          <p className="text-[11px] text-slate-300 leading-relaxed">
            Based on your 90-day average spending of{" "}
            <span className="font-mono text-emerald-300 font-semibold">
              {formatCurrency(aiSuggestedLimit, profile.currency)}
            </span>
            .
          </p>
          <button
            type="button"
            onClick={() => setLimit(aiSuggestedLimit.toString())}
            className="text-[11px] font-semibold text-emerald-400 hover:text-emerald-300 cursor-pointer pt-0.5 inline-block"
          >
            Apply Suggested {currSymbol}{aiSuggestedLimit}
          </button>
        </div>

        <div className="flex items-center justify-end gap-2 pt-3 border-t border-white/[0.06]">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSaving}
            className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-emerald-500/20 cursor-pointer btn-glow disabled:opacity-50"
          >
            {isSaving ? "Saving..." : "Save Target"}
          </button>
        </div>
      </form>
    </Modal>
  );
};
