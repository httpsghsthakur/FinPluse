import React, { useState, useEffect } from "react";
import { User, Sliders, Tag, Database, Bot, Shield, Info, Plus, Trash2, Edit2, RefreshCw, Download, AlertTriangle, CheckCircle2, ExternalLink } from "lucide-react";
import { useUserStore } from "../lib/store/useUserStore";
import { useUIStore } from "../lib/store/useUIStore";
import { Category, Account, CurrencyCode } from "../types";
import { api } from "../lib/api";
import { CategoryIcon } from "../components/ui/CategoryIcon";
import { Modal } from "../components/ui/Modal";
import { formatCurrency, formatDate } from "../lib/utils/formatters";

type SettingsTab = "profile" | "preferences" | "categories" | "datasources" | "ai" | "security" | "about";

export const SettingsPage: React.FC = () => {
  const { profile, updateProfile, setCurrency, toggleTheme } = useUserStore();
  const { openPlaidModal, showToast } = useUIStore();
  const [activeTab, setActiveTab] = useState<SettingsTab>("profile");
  const [categories, setCategories] = useState<Category[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [isResetConfirmOpen, setIsResetConfirmOpen] = useState(false);
  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false);
  const [categoryName, setCategoryName] = useState("");
  const [categoryColor, setCategoryColor] = useState("#10B981");
  const [categoryBudget, setCategoryBudget] = useState("400");
  const [editingCategoryId, setEditingCategoryId] = useState<string | null>(null);

  const loadSettingsData = async () => {
    try {
      const [cats, accs] = await Promise.all([api.getCategories(), api.getAccounts()]);
      setCategories(cats);
      setAccounts(accs);
    } catch (e) { console.error(e); }
  };

  useEffect(() => { loadSettingsData(); }, []);

  const handleSaveCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!categoryName.trim()) return;
    try {
      if (editingCategoryId) {
        await api.updateCategory(editingCategoryId, { name: categoryName, color: categoryColor, defaultMonthlyBudget: parseFloat(categoryBudget) || 300 });
        showToast({ type: "success", title: "Category Updated" });
      } else {
        await api.createCategory({ name: categoryName, color: categoryColor, icon: "Tag", defaultMonthlyBudget: parseFloat(categoryBudget) || 300, isCustom: true });
        showToast({ type: "success", title: "New Category Created" });
      }
      setIsCategoryModalOpen(false);
      setCategoryName("");
      setEditingCategoryId(null);
      loadSettingsData();
    } catch (err) { showToast({ type: "error", title: "Failed to save category" }); }
  };

  const handleDeleteCategory = async (id: string) => {
    try { await api.deleteCategory(id); showToast({ type: "info", title: "Category Removed" }); loadSettingsData(); }
    catch (err) { showToast({ type: "error", title: "Could not delete default category" }); }
  };

  const handleExportFullJSON = async () => {
    try {
      const data = await api.exportAllData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", `Finpluse_Vault_Backup_${new Date().toISOString().slice(0, 10)}.json`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      showToast({ type: "success", title: "Vault JSON Exported", description: "Full backup file saved locally." });
    } catch (err) { showToast({ type: "error", title: "Export failed" }); }
  };

  const handleResetSandbox = async () => {
    try {
      await api.resetAllData();
      setIsResetConfirmOpen(false);
      showToast({ type: "info", title: "Sandbox Reset", description: "Regenerated fresh 6-month financial baseline data." });
      loadSettingsData();
    } catch (err) { showToast({ type: "error", title: "Reset failed" }); }
  };

  const TABS = [
    { id: "profile", label: "User Profile", icon: User },
    { id: "preferences", label: "Preferences", icon: Sliders },
    { id: "categories", label: "Categories & Budgets", icon: Tag },
    { id: "datasources", label: "Connected Banks", icon: Database },
    { id: "ai", label: "Copilot AI Engine", icon: Bot },
    { id: "security", label: "Security & Vault", icon: Shield },
    { id: "about", label: "Architecture", icon: Info },
  ];

  return (
    <div className="space-y-6">
      <div className="animate-fadeInUp">
        <h1 className="text-2xl font-bold tracking-tight text-white font-display">Settings & Vault Config</h1>
        <p className="text-xs text-slate-400 mt-0.5">Manage identity, category budgets, bank connections, privacy models, and telemetry data</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* Tab Selector */}
        <div className="md:col-span-1 space-y-1 animate-fadeInUp stagger-1">
          {TABS.map((tab, i) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button key={tab.id} onClick={() => setActiveTab(tab.id as SettingsTab)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-semibold transition-all text-left cursor-pointer relative ${
                  isActive ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-bold" : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]"
                }`}
                style={{ animationDelay: `${i * 0.04}s` }}>
                {isActive && <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-emerald-500 rounded-r" />}
                <Icon className="w-4 h-4 shrink-0" /><span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Content Panel */}
        <div className="md:col-span-3 glass-card rounded-2xl p-6 md:p-8 space-y-6 animate-fadeInUp stagger-2">
          {activeTab === "profile" && (
            <div className="space-y-6">
              <div className="flex items-center gap-4 pb-6 border-b border-white/[0.04]">
                <img src={profile.avatarUrl} alt={profile.name} className="w-16 h-16 rounded-xl object-cover border-2 border-emerald-500/30" />
                <div>
                  <h2 className="text-base font-bold text-white">{profile.name}</h2>
                  <p className="text-xs text-slate-400">{profile.email}</p>
                  <span className="inline-block mt-1 text-[10px] font-mono font-bold px-2 py-0.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">Active Plan: Pro Lifetime Sandbox</span>
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Full Name</label>
                  <input type="text" value={profile.name} onChange={(e) => updateProfile({ name: e.target.value })}
                    className="w-full px-3.5 py-2.5 bg-white/[0.03] border border-white/[0.06] rounded-xl text-xs text-slate-200 input-glow" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
                  <input type="email" value={profile.email} onChange={(e) => updateProfile({ email: e.target.value })}
                    className="w-full px-3.5 py-2.5 bg-white/[0.03] border border-white/[0.06] rounded-xl text-xs text-slate-200 input-glow" />
                </div>
              </div>
            </div>
          )}

          {activeTab === "preferences" && (
            <div className="space-y-6">
              <h2 className="text-sm font-bold text-white">Global Formatting & Display</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Base Currency</label>
                  <select value={profile.currency} onChange={(e) => setCurrency(e.target.value as CurrencyCode)}
                    className="w-full px-3.5 py-2.5 bg-white/[0.03] border border-white/[0.06] rounded-xl text-xs text-slate-200 input-glow cursor-pointer">
                    <option value="USD">USD ($ - United States Dollar)</option>
                    <option value="EUR">EUR (€ - Euro)</option>
                    <option value="GBP">GBP (£ - British Pound)</option>
                    <option value="INR">INR (₹ - Indian Rupee)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Theme Interface</label>
                  <button onClick={toggleTheme}
                    className="w-full px-3.5 py-2.5 bg-white/[0.03] border border-white/[0.06] rounded-xl text-xs text-slate-200 hover:border-white/[0.12] text-left flex items-center justify-between cursor-pointer transition-all">
                    <span className="capitalize">{profile.theme} Mode</span>
                    <span className="text-[11px] text-emerald-400 font-semibold">Click to switch</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === "categories" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div><h2 className="text-sm font-bold text-white">Custom Spending Categories</h2><p className="text-xs text-slate-400">Manage tags and default baseline budgets</p></div>
                <button onClick={() => { setEditingCategoryId(null); setCategoryName(""); setCategoryColor("#10B981"); setCategoryBudget("400"); setIsCategoryModalOpen(true); }}
                  className="flex items-center gap-1.5 px-3.5 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold rounded-xl transition-all cursor-pointer btn-glow">
                  <Plus className="w-3.5 h-3.5 stroke-[2.5]" /><span>Add Category</span>
                </button>
              </div>
              <div className="space-y-2">
                {categories.map((cat, i) => (
                  <div key={cat.id} className="p-3.5 rounded-xl bg-white/[0.02] border border-white/[0.04] hover:border-white/[0.08] flex items-center justify-between gap-3 text-xs transition-all animate-fadeInUp" style={{ animationDelay: `${i * 0.03}s` }}>
                    <div className="flex items-center gap-3">
                      <CategoryIcon name={cat.icon} color={cat.color} size="sm" />
                      <div><span className="font-semibold text-slate-200">{cat.name}</span><div className="text-[11px] text-slate-400 font-mono">Default: {formatCurrency(cat.defaultMonthlyBudget)}</div></div>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <button onClick={() => { setEditingCategoryId(cat.id); setCategoryName(cat.name); setCategoryColor(cat.color); setCategoryBudget(String(cat.defaultMonthlyBudget)); setIsCategoryModalOpen(true); }}
                        className="p-2 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 transition-all cursor-pointer"><Edit2 className="w-3.5 h-3.5" /></button>
                      {cat.isCustom && (
                        <button onClick={() => handleDeleteCategory(cat.id)}
                          className="p-2 rounded-lg bg-white/[0.04] hover:bg-rose-500/10 text-slate-400 hover:text-rose-400 transition-all cursor-pointer"><Trash2 className="w-3.5 h-3.5" /></button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === "datasources" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div><h2 className="text-sm font-bold text-white">Linked Accounts & Plaid Feeds</h2><p className="text-xs text-slate-400">Encrypted token connections with hourly refresh</p></div>
                <button onClick={openPlaidModal} className="flex items-center gap-1.5 px-3.5 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold rounded-xl transition-all cursor-pointer btn-glow">
                  <Plus className="w-3.5 h-3.5 stroke-[2.5]" /><span>Link New Bank</span>
                </button>
              </div>
              <div className="space-y-3">
                {accounts.map((acc, i) => (
                  <div key={acc.id} className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] hover:border-white/[0.08] flex items-center justify-between gap-4 text-xs transition-all animate-fadeInUp" style={{ animationDelay: `${i * 0.05}s` }}>
                    <div>
                      <div className="flex items-center gap-2"><span className="font-bold text-slate-100">{acc.institutionName}</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-lg bg-white/[0.04] text-slate-300 border border-white/[0.06]">•••• {acc.mask}</span></div>
                      <div className="text-[11px] text-slate-400 mt-0.5">{acc.name} • Last synced <span className="font-mono text-slate-300">{formatDate(acc.lastSynced, "MMM d, p")}</span></div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold font-mono text-white">{formatCurrency(acc.balance)}</div>
                      <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1 justify-end"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Active</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === "ai" && (
            <div className="space-y-4">
              <h2 className="text-sm font-bold text-white">Copilot Reasoning Configuration</h2>
              <p className="text-xs text-slate-400">Control AI tone, grounding constraints, and telemetry exposure.</p>
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] space-y-3 text-xs">
                <div className="flex items-center justify-between">
                  <div><div className="font-semibold text-slate-200">Grounded Citation Enforcer</div><div className="text-slate-400 text-[11px]">Strictly forbid speculative answers without verifiable citations.</div></div>
                  <input type="checkbox" defaultChecked className="accent-emerald-500 w-4 h-4 cursor-pointer" />
                </div>
                <div className="flex items-center justify-between pt-2 border-t border-white/[0.04]">
                  <div><div className="font-semibold text-slate-200">Zero-Retention Data Policy</div><div className="text-slate-400 text-[11px]">No financial balances are transmitted to external cloud training.</div></div>
                  <span className="font-mono text-[10px] text-emerald-400 bg-emerald-500/15 px-2 py-0.5 rounded-lg border border-emerald-500/25 font-bold">Enforced</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === "security" && (
            <div className="space-y-6">
              <h2 className="text-sm font-bold text-white">Data Vault & Encryption</h2>
              <div className="space-y-3">
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] flex items-center justify-between gap-4 text-xs">
                  <div><div className="font-semibold text-slate-200">Export Complete Financial Vault</div><div className="text-slate-400 text-[11px]">Download all transactions, goals, and forecast models as JSON.</div></div>
                  <button onClick={handleExportFullJSON} className="px-3.5 py-2 bg-white/[0.04] hover:bg-white/[0.08] text-slate-200 text-xs font-semibold rounded-xl border border-white/[0.06] flex items-center gap-1.5 cursor-pointer transition-all">
                    <Download className="w-3.5 h-3.5 text-indigo-400" /><span>Download JSON</span>
                  </button>
                </div>
                <div className="p-4 rounded-xl glass-card-danger flex items-center justify-between gap-4 text-xs">
                  <div><div className="font-semibold text-rose-300">Reset Local Sandbox Data</div><div className="text-slate-400 text-[11px]">Clear current database and reseed 6 months of demo accounts.</div></div>
                  <button onClick={() => setIsResetConfirmOpen(true)} className="px-3.5 py-2 bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 text-xs font-semibold rounded-xl border border-rose-500/30 cursor-pointer transition-all">Reset Sandbox</button>
                </div>
                <div className="p-4 rounded-xl bg-indigo-500/[0.04] border border-indigo-500/15 flex items-center justify-between gap-4 text-xs">
                  <div><div className="font-semibold text-indigo-300">Load Custom CSV Data</div><div className="text-slate-400 text-[11px]">Wipe existing transactions and replace with your uploaded CSV.</div></div>
                  <label className="px-3.5 py-2 bg-indigo-500/15 hover:bg-indigo-500/25 text-indigo-300 text-xs font-semibold rounded-xl border border-indigo-500/30 cursor-pointer inline-flex items-center transition-all">
                    <span>Upload CSV</span>
                    <input type="file" accept=".csv" className="hidden" onChange={async (e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        const reader = new FileReader();
                        reader.onload = async (event) => {
                          try { const text = event.target?.result as string; await api.replaceTransactionsFromCSV(text);
                            showToast({ type: "success", title: "Data Loaded", description: "Replaced transactions with CSV data." }); loadSettingsData();
                          } catch (err) { showToast({ type: "error", title: "Upload failed" }); }
                        };
                        reader.readAsText(file);
                      }
                    }} />
                  </label>
                </div>
              </div>
            </div>
          )}

          {activeTab === "about" && (
            <div className="space-y-4 text-xs leading-relaxed text-slate-300">
              <h2 className="text-sm font-bold text-white">Finpluse Architecture</h2>
              <p>Finpluse is built with clean layer separation. All visual pages and widgets interact with the domain model exclusively via the <code className="font-mono text-emerald-400">src/lib/api/</code> unified abstraction.</p>
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04] space-y-2 font-mono text-[11px]">
                <div className="text-emerald-400 font-semibold">// How to connect your real REST/GraphQL backend:</div>
                <div className="text-slate-400">Open <span className="text-slate-200">src/lib/api/config.ts</span> and toggle:</div>
                <div className="text-indigo-300">export const API_CONFIG = &#123; USE_MOCK: false, BASE_URL: 'https://api.yourbank.com' &#125;;</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Category Modal */}
      <Modal isOpen={isCategoryModalOpen} onClose={() => setIsCategoryModalOpen(false)} title={editingCategoryId ? "Edit Category" : "Create New Category"} description="Define category properties for machine categorization" maxWidth="sm">
        <form onSubmit={handleSaveCategory} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Category Name</label>
            <input type="text" required placeholder="e.g. Pet Care, Photography, Gaming" value={categoryName} onChange={(e) => setCategoryName(e.target.value)}
              className="w-full px-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-xl text-xs text-slate-200 input-glow" />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Default Monthly Budget</label>
            <input type="number" required value={categoryBudget} onChange={(e) => setCategoryBudget(e.target.value)}
              className="w-full px-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-xl text-xs font-mono text-slate-200 input-glow" />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Color Accent</label>
            <div className="flex gap-2">
              {["#10B981", "#6366F1", "#F59E0B", "#EF4444", "#EC4899", "#06B6D4", "#8B5CF6"].map((color) => (
                <button key={color} type="button" onClick={() => setCategoryColor(color)}
                  className={`w-7 h-7 rounded-lg transition-all cursor-pointer ${categoryColor === color ? "ring-2 ring-white scale-110" : "hover:scale-105"}`}
                  style={{ backgroundColor: color }} />
              ))}
            </div>
          </div>
          <div className="flex items-center justify-end gap-2 pt-2">
            <button type="button" onClick={() => setIsCategoryModalOpen(false)} className="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 cursor-pointer transition-colors">Cancel</button>
            <button type="submit" className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-xs rounded-xl btn-glow cursor-pointer transition-all">Save Category</button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={isResetConfirmOpen} onClose={() => setIsResetConfirmOpen(false)} title="Reset Financial Sandbox?" description="This will clear all local storage and reseed clean mock accounts." maxWidth="sm">
        <div className="space-y-4">
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/25 text-xs text-rose-300 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>This will reset custom categories, manual expenses, and goal boost transactions.</span>
          </div>
          <div className="flex items-center justify-end gap-2 pt-2">
            <button type="button" onClick={() => setIsResetConfirmOpen(false)} className="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 cursor-pointer">Cancel</button>
            <button type="button" onClick={handleResetSandbox} className="px-4 py-2 bg-rose-500 hover:bg-rose-400 text-white font-semibold text-xs rounded-xl cursor-pointer btn-glow transition-all">Confirm Reset</button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
