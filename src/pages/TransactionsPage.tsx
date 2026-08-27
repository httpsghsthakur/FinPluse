import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Search,
  Download,
  UploadCloud,
  Plus,
  AlertTriangle,
  RefreshCw,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Transaction, Category, Account } from "../types";
import { CategoryIcon } from "../components/ui/CategoryIcon";
import { AmountText } from "../components/ui/AmountText";
import { TableSkeleton } from "../components/ui/Skeletons";
import { EmptyState } from "../components/ui/EmptyState";
import { api, TransactionFilters } from "../lib/api";
import { useUIStore } from "../lib/store/useUIStore";
import { formatDate } from "../lib/utils/formatters";

export const TransactionsPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const { openTxDetail, openAddTxModal, openCsvImportModal, showToast } = useUIStore();

  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);

  const [search, setSearch] = useState(searchParams.get("q") || "");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedAccount, setSelectedAccount] = useState<string>("all");
  const [anomalyOnly, setAnomalyOnly] = useState(false);
  const [recurringOnly, setRecurringOnly] = useState(false);
  const [sortBy, setSortBy] = useState<"date" | "amount" | "merchant">("date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  useEffect(() => {
    const q = searchParams.get("q");
    if (q !== null && q !== search) {
      setSearch(q);
      setPage(1);
    }
  }, [searchParams]);

  const fetchTransactions = async () => {
    setIsLoading(true);
    try {
      const filters: TransactionFilters = {
        search: search || undefined,
        categoryIds: selectedCategory !== "all" ? [selectedCategory] : undefined,
        accountIds: selectedAccount !== "all" ? [selectedAccount] : undefined,
        anomalyOnly: anomalyOnly || undefined,
        recurringOnly: recurringOnly || undefined,
        sortBy,
        sortOrder,
        page,
        limit: 25,
      };

      const [res, catList, accList] = await Promise.all([
        api.getTransactions(filters),
        api.getCategories(),
        api.getAccounts(),
      ]);

      setTransactions(res.transactions);
      setTotal(res.total);
      setTotalPages(res.totalPages);
      setCategories(catList);
      setAccounts(accList);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, [search, selectedCategory, selectedAccount, anomalyOnly, recurringOnly, sortBy, sortOrder, page]);

  const handleExportCSV = async () => {
    try {
      const csv = await api.exportTransactionsCSV();
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", `Finpluse_Transactions_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      showToast({ type: "success", title: "Export Downloaded", description: "Downloaded full transaction log as CSV." });
    } catch (e) {
      showToast({ type: "error", title: "Export Failed" });
    }
  };

  const handleQuickCategoryChange = async (e: React.MouseEvent, txId: string, newCategoryId: string) => {
    e.stopPropagation();
    try {
      await api.updateTransaction(txId, { categoryId: newCategoryId });
      const catName = categories.find((c) => c.id === newCategoryId)?.name;
      showToast({ type: "success", title: "Category Reassigned", description: `AI is retraining on your correction to ${catName}.` });
      fetchTransactions();
    } catch (err) {
      showToast({ type: "error", title: "Update Failed" });
    }
  };

  return (
    <div className="space-y-6">
      {/* ═══ Header ═══ */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-fadeInUp">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white font-display">
            Transactions
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Indexed{" "}
            <span className="text-emerald-400 font-mono font-semibold">{total}</span>{" "}
            total transactions with continuous anomaly detection
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={openCsvImportModal}
            className="flex items-center gap-1.5 px-3 py-2 glass-card text-slate-200 text-xs font-semibold rounded-xl transition-all cursor-pointer hover:border-white/[0.12]"
          >
            <UploadCloud className="w-3.5 h-3.5 text-emerald-400" />
            <span>Import CSV</span>
          </button>

          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 px-3 py-2 glass-card text-slate-200 text-xs font-semibold rounded-xl transition-all cursor-pointer hover:border-white/[0.12]"
          >
            <Download className="w-3.5 h-3.5 text-indigo-400" />
            <span>Export CSV</span>
          </button>

          <button
            onClick={openAddTxModal}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs rounded-xl transition-all cursor-pointer btn-glow"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            <span>Add Transaction</span>
          </button>
        </div>
      </div>

      {/* ═══ Filter Bar ═══ */}
      <div className="glass-card rounded-2xl p-5 space-y-3 animate-fadeInUp stagger-1">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
            <input
              type="text"
              placeholder="Search merchant or notes..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              className="w-full pl-9 pr-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-xl text-xs text-slate-200 placeholder-slate-500 input-glow transition-all"
            />
          </div>

          <select
            value={selectedCategory}
            onChange={(e) => { setSelectedCategory(e.target.value); setPage(1); }}
            className="w-full px-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-xl text-xs text-slate-200 input-glow cursor-pointer"
          >
            <option value="all">All Categories</option>
            {categories.map((c) => (<option key={c.id} value={c.id}>{c.name}</option>))}
          </select>

          <select
            value={selectedAccount}
            onChange={(e) => { setSelectedAccount(e.target.value); setPage(1); }}
            className="w-full px-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-xl text-xs text-slate-200 input-glow cursor-pointer"
          >
            <option value="all">All Accounts</option>
            {accounts.map((a) => (<option key={a.id} value={a.id}>{a.name} (•••• {a.mask})</option>))}
          </select>

          <div className="flex items-center gap-2">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="flex-1 px-3 py-2 bg-white/[0.03] border border-white/[0.06] rounded-xl text-xs text-slate-200 input-glow cursor-pointer"
            >
              <option value="date">Sort by Date</option>
              <option value="amount">Sort by Amount</option>
              <option value="merchant">Sort by Merchant</option>
            </select>
            <button
              onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
              className="p-2 bg-white/[0.03] border border-white/[0.06] hover:border-white/[0.12] text-slate-300 rounded-xl cursor-pointer transition-all"
            >
              <ArrowUpDown className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3 pt-2 border-t border-white/[0.04] text-xs">
          <button
            onClick={() => { setAnomalyOnly(!anomalyOnly); setPage(1); }}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg border text-xs transition-all cursor-pointer ${
              anomalyOnly
                ? "bg-rose-500/15 text-rose-300 border-rose-500/30 font-semibold"
                : "bg-white/[0.02] text-slate-400 border-white/[0.06] hover:text-slate-200"
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
            <span>Spike Anomalies Only</span>
          </button>

          <button
            onClick={() => { setRecurringOnly(!recurringOnly); setPage(1); }}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-lg border text-xs transition-all cursor-pointer ${
              recurringOnly
                ? "bg-indigo-500/15 text-indigo-300 border-indigo-500/30 font-semibold"
                : "bg-white/[0.02] text-slate-400 border-white/[0.06] hover:text-slate-200"
            }`}
          >
            <RefreshCw className="w-3.5 h-3.5 text-indigo-400" />
            <span>Recurring Bills & Subs</span>
          </button>
        </div>
      </div>

      {/* ═══ Transactions Table ═══ */}
      <div className="glass-card rounded-2xl overflow-hidden animate-fadeInUp stagger-2">
        {isLoading ? (
          <TableSkeleton rows={10} />
        ) : transactions.length === 0 ? (
          <EmptyState
            title="No Transactions Found"
            description="No records match your active filters. Try clearing search or category constraints."
            actionLabel="Clear Filters"
            onAction={() => {
              setSearch(""); setSelectedCategory("all"); setSelectedAccount("all");
              setAnomalyOnly(false); setRecurringOnly(false);
            }}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-white/[0.02] border-b border-white/[0.06] text-slate-400 uppercase font-mono text-[10px] sticky top-0 z-10">
                <tr>
                  <th className="py-3 px-4 font-medium">Merchant / Payee</th>
                  <th className="py-3 px-4 font-medium">Date</th>
                  <th className="py-3 px-4 font-medium">Category (Auto AI)</th>
                  <th className="py-3 px-4 font-medium">Account</th>
                  <th className="py-3 px-4 font-medium text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {transactions.map((tx, i) => {
                  const cat = categories.find((c) => c.id === tx.categoryId);
                  const acc = accounts.find((a) => a.id === tx.accountId);
                  return (
                    <tr
                      key={tx.id}
                      onClick={() => openTxDetail(tx.id)}
                      className="hover:bg-white/[0.03] transition-all cursor-pointer group animate-fadeInUp"
                      style={{ animationDelay: `${i * 0.03}s` }}
                    >
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-3">
                          <CategoryIcon name={cat?.icon || "Tag"} color={cat?.color || "#10B981"} size="sm" />
                          <div>
                            <div className="font-semibold text-slate-100 group-hover:text-emerald-400 transition-colors">
                              {tx.merchant}
                            </div>
                            <div className="flex items-center gap-2 mt-0.5">
                              {tx.isRecurring && (
                                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/25">Recurring</span>
                              )}
                              {tx.isAnomaly && (
                                <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-rose-500/15 text-rose-300 border border-rose-500/25 animate-pulse-glow" title={tx.anomalyReason}>
                                  Anomaly Spike
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-slate-400 font-mono whitespace-nowrap">
                        {formatDate(tx.date, "MMM d, yyyy")}
                      </td>
                      <td className="py-3 px-4">
                        <select
                          value={tx.categoryId}
                          onClick={(e) => e.stopPropagation()}
                          onChange={(e) => handleQuickCategoryChange(e as any, tx.id, e.target.value)}
                          className="bg-white/[0.03] border border-white/[0.06] text-slate-300 text-[11px] rounded-lg px-2 py-1 focus:outline-none input-glow cursor-pointer"
                        >
                          {categories.map((c) => (<option key={c.id} value={c.id}>{c.name}</option>))}
                        </select>
                      </td>
                      <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                        <span className="font-medium text-slate-300">{acc?.name.split(" ")[0]}</span>{" "}
                        <span className="font-mono text-[10px]">••••{acc?.mask}</span>
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-semibold">
                        <AmountText amount={tx.amount} colored />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        <div className="p-4 border-t border-white/[0.06] flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing Page{" "}
            <span className="font-mono font-semibold text-slate-200">{page}</span>{" "}
            of{" "}
            <span className="font-mono font-semibold text-slate-200">{totalPages}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="p-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] disabled:opacity-40 text-slate-300 hover:text-white cursor-pointer transition-all hover:border-white/[0.12]"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages}
              className="p-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] disabled:opacity-40 text-slate-300 hover:text-white cursor-pointer transition-all hover:border-white/[0.12]"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
