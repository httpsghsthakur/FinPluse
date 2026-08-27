import React, { useState } from "react";
import {
  Building2,
  Lock,
  CheckCircle2,
  ShieldCheck,
  ArrowRight,
  Loader2,
} from "lucide-react";
import { Modal } from "./Modal";
import { useUIStore } from "../../lib/store/useUIStore";
import { api } from "../../lib/api";

const POPULAR_INSTITUTIONS = [
  { name: "Chase Bank", color: "#3B82F6", type: "checking", mask: "4821" },
  { name: "Bank of America", color: "#EF4444", type: "checking", mask: "1904" },
  { name: "Wells Fargo", color: "#DC2626", type: "checking", mask: "8310" },
  {
    name: "Marcus by Goldman Sachs",
    color: "#10B981",
    type: "savings",
    mask: "9034",
  },
  { name: "American Express", color: "#F59E0B", type: "credit", mask: "1004" },
  { name: "Capital One", color: "#6366F1", type: "credit", mask: "5520" },
  {
    name: "Fidelity Investments",
    color: "#059669",
    type: "investment",
    mask: "3349",
  },
  { name: "Robinhood", color: "#22C55E", type: "investment", mask: "7721" },
];

export const PlaidModal: React.FC<{ onAccountAdded?: () => void }> = ({
  onAccountAdded,
}) => {
  const { isPlaidModalOpen, closePlaidModal, showToast } = useUIStore();
  const [selectedInst, setSelectedInst] = useState<
    (typeof POPULAR_INSTITUTIONS)[0] | null
  >(null);
  const [step, setStep] = useState<
    "select" | "credentials" | "connecting" | "success"
  >("select");
  const [username, setUsername] = useState("demo_user");
  const [password, setPassword] = useState("••••••••••");

  const handleSelect = (inst: (typeof POPULAR_INSTITUTIONS)[0]) => {
    setSelectedInst(inst);
    setStep("credentials");
  };

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInst) return;

    setStep("connecting");

    try {
      await api.connectAccount({
        name: `${selectedInst.name} ${selectedInst.type.toUpperCase()}`,
        type: selectedInst.type as any,
        balance:
          selectedInst.type === "credit"
            ? -850.4
            : selectedInst.type === "savings"
              ? 12400.0
              : 4520.0,
        currency: "USD",
        institution: selectedInst.name,
        mask: selectedInst.mask,
        color: selectedInst.color,
      });

      setStep("success");
      setTimeout(() => {
        showToast({
          type: "success",
          title: "Account Connected",
          description: `Successfully synced with ${selectedInst.name}.`,
        });
        closePlaidModal();
        setStep("select");
        setSelectedInst(null);
        if (onAccountAdded) onAccountAdded();
      }, 1200);
    } catch (err) {
      setStep("credentials");
      showToast({
        type: "error",
        title: "Connection Failed",
        description: "Unable to connect to financial institution.",
      });
    }
  };

  const handleClose = () => {
    closePlaidModal();
    setStep("select");
    setSelectedInst(null);
  };

  return (
    <Modal
      isOpen={isPlaidModalOpen}
      onClose={handleClose}
      title="Connect Financial Account"
      description="Secure 256-bit encrypted bank connection via Plaid API protocol"
      maxWidth="md"
    >
      {step === "select" && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 p-3 bg-emerald-500/[0.04] border border-emerald-500/15 rounded-xl text-xs text-slate-300">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>
              Finpluse uses end-to-end read-only tokens. Your credentials are
              never stored.
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2.5 max-h-[300px] overflow-y-auto pr-1">
            {POPULAR_INSTITUTIONS.map((inst) => (
              <button
                key={inst.name}
                onClick={() => handleSelect(inst)}
                className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.06] hover:border-emerald-500/30 hover:bg-white/[0.04] transition-all text-left group cursor-pointer"
              >
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold text-white shrink-0 shadow-sm"
                  style={{ backgroundColor: inst.color }}
                >
                  <Building2 className="w-4 h-4" />
                </div>
                <div className="truncate">
                  <div className="text-xs font-semibold text-slate-200 group-hover:text-emerald-400 transition-colors truncate">
                    {inst.name}
                  </div>
                  <div className="text-[10px] text-slate-400 capitalize font-mono">
                    {inst.type}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {step === "credentials" && selectedInst && (
        <form onSubmit={handleConnect} className="space-y-4">
          <div className="flex items-center gap-3 p-3 bg-white/[0.02] border border-white/[0.06] rounded-xl">
            <div
              className="w-9 h-9 rounded-lg flex items-center justify-center text-white"
              style={{ backgroundColor: selectedInst.color }}
            >
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <div className="text-sm font-semibold text-slate-200">
                {selectedInst.name}
              </div>
              <div className="text-[11px] text-slate-400 font-mono">
                Direct OAuth 2.0 Handshake
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1 font-mono uppercase tracking-wider text-[10px]">
                User ID / Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-white/[0.03] border border-white/[0.06] rounded-xl text-xs text-slate-100 placeholder-slate-500 input-glow"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1 font-mono uppercase tracking-wider text-[10px]">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-white/[0.03] border border-white/[0.06] rounded-xl text-xs text-slate-100 placeholder-slate-500 input-glow"
                required
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-3 border-t border-white/[0.06]">
            <button
              type="button"
              onClick={() => setStep("select")}
              className="text-xs text-slate-400 hover:text-slate-200 cursor-pointer transition-colors"
            >
              Back
            </button>
            <button
              type="submit"
              className="flex items-center gap-1.5 px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-emerald-500/20 cursor-pointer btn-glow"
            >
              <span>Authenticate & Link</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      )}

      {step === "connecting" && (
        <div className="py-8 flex flex-col items-center justify-center text-center space-y-3">
          <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
          <div className="text-sm font-semibold text-slate-200">
            Verifying secure OAuth credentials...
          </div>
          <div className="text-xs text-slate-400 max-w-xs font-mono text-[11px]">
            Establishing encrypted TLS socket with {selectedInst?.name} gateway.
          </div>
        </div>
      )}

      {step === "success" && (
        <div className="py-8 flex flex-col items-center justify-center text-center space-y-3">
          <CheckCircle2 className="w-10 h-10 text-emerald-400 animate-bounce" />
          <div className="text-sm font-bold text-slate-100">
            Account Linked Successfully!
          </div>
          <div className="text-xs text-slate-400 font-mono text-[11px]">
            Importing recent transactions and balances...
          </div>
        </div>
      )}
    </Modal>
  );
};
