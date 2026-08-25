import React, { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import {
  Wallet,
  CreditCard,
  Clock,
  PiggyBank,
  TrendingUp,
  Sparkles,
  ArrowRight,
  AlertTriangle,
  Calendar,
  ChevronRight,
  Bot,
  Plus,
  RefreshCw,
} from "lucide-react";
import { KpiCard } from "../components/ui/KpiCard";
import { ChartCard } from "../components/ui/ChartCard";
import { ShareInsightModal } from "../components/ui/ShareInsightModal";
import { CategoryIcon } from "../components/ui/CategoryIcon";
import { AmountText } from "../components/ui/AmountText";
import { ProgressBar } from "../components/ui/ProgressBar";
import {
  KpiSkeleton,
  ChartSkeleton,
  TableSkeleton,
} from "../components/ui/Skeletons";
import { CitationChip } from "../components/ui/CitationChip";
import { DashboardSummary, Insight } from "../types";
import { api } from "../lib/api";
import { useUIStore } from "../lib/store/useUIStore";
import { formatDate, formatCurrency } from "../lib/utils/formatters";
import { useUserStore } from "../lib/store/useUserStore";
import { CURRENCY_SYMBOLS } from "../lib/utils/formatters";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from "recharts";

export const DashboardPage: React.FC = () => {
  const { openTxDetail, openAddTxModal } = useUIStore();
  const { profile } = useUserStore();
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [expandedInsightId, setExpandedInsightId] = useState<string | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(true);

  const loadDashboard = async () => {
    setIsLoading(true);
    try {
      const [summary, insList] = await Promise.all([
        api.getDashboardSummary(),
        api.getInsights(),
      ]);
      setData(summary);
      setInsights(insList.filter((i) => !i.isDismissed).slice(0, 3));
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  if (isLoading || !data) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiSkeleton />
          <KpiSkeleton />
          <KpiSkeleton />
          <KpiSkeleton />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ChartSkeleton height="h-[300px]" />
          </div>
          <ChartSkeleton height="h-[300px]" />
        </div>
        <TableSkeleton rows={6} />
      </div>
    );
  }

  const avgSavings = data.cashFlowHistory.length
    ? data.cashFlowHistory.reduce((acc, curr) => acc + curr.savings, 0) /
      data.cashFlowHistory.length
    : 0;

  return (
    <div className="space-y-6">
      {/* Low-Balance Alert Banner if active */}
      {data.lowBalanceAlert.hasLowBalance && (
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
            <div className="text-xs">
              <span className="font-bold text-amber-300">
                Low Balance Forecast Warning:{" "}
              </span>
              <span className="text-slate-200">
                Checking balance projected to dip below{" "}
                {formatCurrency(
                  data.lowBalanceAlert.threshold || 0,
                  profile.currency,
                )}{" "}
                on {data.lowBalanceAlert.date}.
              </span>
            </div>
          </div>
          <NavLink
            to="/app/forecast"
            className="px-3 py-1.5 rounded-xl bg-amber-500 text-slate-950 text-xs font-semibold hover:bg-amber-400 transition-colors shrink-0"
          >
            Review Forecast
          </NavLink>
        </div>
      )}

      {/* 4 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Net Worth"
          value={data.netWorth}
          changePct={data.netWorthMomPct}
          changePeriodText="MoM"
          icon={Wallet}
          badge={{ text: "Compounding", variant: "emerald" }}
        />
        <KpiCard
          title="Monthly Spend"
          value={data.monthlySpending}
          changePct={data.monthlySpendVsBudgetPct}
          changePeriodText={`vs Budget (${formatCurrency(data.monthlyBudgetTotal, profile.currency)})`}
          icon={CreditCard}
        />
        <KpiCard
          title="Cash Runway"
          value={data.cashRunwayMonths}
          isCurrency={false}
          suffix=" Months"
          subtext="Liquid checking + HYSA reserves"
          icon={Clock}
          badge={{ text: "Safe Tier", variant: "emerald" }}
        />
        <KpiCard
          title="Savings Rate"
          value={data.savingsRatePct}
          isCurrency={false}
          suffix="%"
          changePct={data.savingsRateMomDelta}
          changePeriodText="vs last month"
          icon={PiggyBank}
        />
      </div>

      {/* Main Charts Row: Cash Flow History & Spending Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cash Flow Area Chart (6 Months) */}
        <div className="lg:col-span-2">
          <ChartCard
            title="Cash Flow Dynamics"
            subtitle="6-Month Income vs Expenses Comparison"
            footerNote={`Net savings averaged ${avgSavings >= 0 ? "+" : ""}${formatCurrency(avgSavings, profile.currency)}/month across this period.`}
            actions={
              <div className="flex items-center gap-3 text-xs font-mono">
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-400" />{" "}
                  Income
                </span>
                <span className="flex items-center gap-1.5 text-rose-400">
                  <span className="w-2 h-2 rounded-full bg-rose-400" /> Expenses
                </span>
              </div>
            }
          >
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={data.cashFlowHistory}
                  margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="incomeGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop
                        offset="5%"
                        stopColor="#10B981"
                        stopOpacity={0.35}
                      />
                      <stop
                        offset="95%"
                        stopColor="#10B981"
                        stopOpacity={0.0}
                      />
                    </linearGradient>
                    <linearGradient
                      id="expenseGrad"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop offset="5%" stopColor="#F43F5E" stopOpacity={0.3} />
                      <stop
                        offset="95%"
                        stopColor="#F43F5E"
                        stopOpacity={0.0}
                      />
                    </linearGradient>
                  </defs>
                  <XAxis
                    dataKey="month"
                    stroke="#64748B"
                    fontSize={11}
                    tickLine={false}
                  />
                  <YAxis
                    stroke="#64748B"
                    fontSize={11}
                    tickLine={false}
                    tickFormatter={(v) =>
                      `${CURRENCY_SYMBOLS[profile.currency] || "₹"}${v / 1000}k`
                    }
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0F172A",
                      borderColor: "#334155",
                      borderRadius: 12,
                    }}
                    formatter={(val: any) => [
                      `${CURRENCY_SYMBOLS[profile.currency] || "₹"}${Number(val).toLocaleString()}`,
                      "",
                    ]}
                  />
                  <Area
                    type="monotone"
                    dataKey="income"
                    stroke="#10B981"
                    strokeWidth={2.5}
                    fill="url(#incomeGrad)"
                  />
                  <Area
                    type="monotone"
                    dataKey="expenses"
                    stroke="#F43F5E"
                    strokeWidth={2.5}
                    fill="url(#expenseGrad)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>
        </div>

        {/* Spending by Category Donut & Top List */}
        <div className="lg:col-span-1">
          <ChartCard
            title="Spending by Category"
            subtitle="Current billing cycle distribution"
            actions={
              <NavLink
                to="/app/budgets"
                className="text-xs text-emerald-400 hover:underline"
              >
                View Budgets
              </NavLink>
            }
          >
            <div className="flex flex-col gap-4 w-full">
              <div className="h-44 w-full relative flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#0F172A",
                        borderColor: "#334155",
                        borderRadius: 12,
                      }}
                      formatter={(val: any) => [
                        `${CURRENCY_SYMBOLS[profile.currency] || "₹"}${Number(val).toLocaleString()}`,
                        "Spent",
                      ]}
                    />
                    <Pie
                      data={data.categorySpend.slice(0, 5)}
                      dataKey="amount"
                      nameKey="categoryName"
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={75}
                      paddingAngle={3}
                    >
                      {data.categorySpend.slice(0, 5).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Top 4 categories breakdown */}
              <div className="space-y-2">
                {data.categorySpend.slice(0, 4).map((cat) => (
                  <div key={cat.categoryId} className="text-xs space-y-1">
                    <div className="flex justify-between items-center text-slate-300">
                      <span className="flex items-center gap-1.5 truncate">
                        <span
                          className="w-2 h-2 rounded-full shrink-0"
                          style={{ backgroundColor: cat.color }}
                        />
                        <span className="truncate">{cat.categoryName}</span>
                      </span>
                      <span className="font-mono font-medium">
                        {formatCurrency(cat.amount, profile.currency)}
                      </span>
                    </div>
                    <ProgressBar
                      value={cat.amount}
                      max={cat.budget || cat.amount}
                      color={cat.color}
                      size="sm"
                    />
                  </div>
                ))}
              </div>
            </div>
          </ChartCard>
        </div>
      </div>

      {/* AI Insights Chips Card */}
      <div className="bg-slate-900/40 backdrop-blur-md border border-slate-800/60 rounded-[28px] p-5 md:p-6 space-y-4 shadow-[0_10px_30px_rgba(0,0,0,0.2)]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100">
                Live AI Financial Signals
              </h3>
              <p className="text-xs text-slate-400">
                Automated detections grounded in your daily cash telemetry
              </p>
            </div>
          </div>
          <NavLink
            to="/app/insights"
            className="text-xs font-semibold text-emerald-400 hover:underline flex items-center gap-1"
          >
            <span>Full Insights Feed</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </NavLink>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {insights.map((insight) => {
            const isExpanded = expandedInsightId === insight.id;
            const borderColors = {
              alert: "border-rose-500/30 bg-rose-950/20 backdrop-blur-sm",
              warning: "border-amber-500/30 bg-amber-950/20 backdrop-blur-sm",
              success:
                "border-emerald-500/30 bg-emerald-950/20 backdrop-blur-sm",
              info: "border-indigo-500/30 bg-indigo-950/20 backdrop-blur-sm",
            };

            return (
              <div
                key={insight.id}
                className={`p-4 rounded-2xl border transition-all ${borderColors[insight.severity]} space-y-2`}
              >
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-xs font-bold text-slate-200 leading-snug">
                    {insight.title}
                  </h4>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  {insight.description}
                </p>

                <div className="pt-1 flex items-center justify-between text-xs">
                  <button
                    onClick={() =>
                      setExpandedInsightId(isExpanded ? null : insight.id)
                    }
                    className="text-[11px] text-emerald-400 hover:underline font-medium cursor-pointer"
                  >
                    {isExpanded ? "Hide explanation" : "Why this alert?"}
                  </button>
                  {insight.actionPath && (
                    <NavLink
                      to={insight.actionPath}
                      className="text-[11px] text-slate-300 hover:text-white flex items-center gap-0.5"
                    >
                      <span>{insight.actionLabel || "View"}</span>
                      <ArrowRight className="w-3 h-3" />
                    </NavLink>
                  )}
                </div>

                {isExpanded && (
                  <div className="mt-2 p-2.5 bg-slate-900/90 rounded-xl border border-slate-800 text-[11px] text-slate-300 space-y-2 animate-fadeIn">
                    <div>{insight.whyExplanation}</div>
                    <CitationChip groundedData={insight.groundedData} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Bottom Grid: Recent Transactions & Upcoming Bills */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Transactions Table */}
        <div className="lg:col-span-2 bg-slate-900/40 backdrop-blur-md border border-slate-800/60 rounded-[28px] p-5 md:p-6 space-y-4 shadow-[0_10px_30px_rgba(0,0,0,0.2)]">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-100">
                Recent Transactions
              </h3>
              <p className="text-xs text-slate-400">
                Real-time sync across connected accounts
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={openAddTxModal}
                className="px-2.5 py-1 rounded-xl bg-slate-800/60 hover:bg-slate-700/60 text-slate-200 text-xs font-semibold border border-slate-700/50 flex items-center gap-1 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5 text-emerald-400" />
                <span>Add</span>
              </button>
              <NavLink
                to="/app/transactions"
                className="text-xs text-emerald-400 hover:underline"
              >
                View All
              </NavLink>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800/80 text-slate-400 uppercase font-mono text-[10px]">
                  <th className="pb-2.5 font-semibold">Merchant</th>
                  <th className="pb-2.5 font-semibold">Date</th>
                  <th className="pb-2.5 font-semibold">Category</th>
                  <th className="pb-2.5 font-semibold text-right">Amount</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {data.recentTransactions.map((tx) => (
                  <tr
                    key={tx.id}
                    onClick={() => openTxDetail(tx.id)}
                    className="hover:bg-slate-800/30 transition-colors cursor-pointer group"
                  >
                    <td className="py-2.5 pr-3">
                      <div className="font-semibold text-slate-200 group-hover:text-emerald-400 transition-colors truncate max-w-[180px]">
                        {tx.merchant}
                      </div>
                      {tx.isAnomaly && (
                        <span className="inline-block text-[9px] font-mono px-1 rounded bg-rose-500/20 text-rose-400 border border-rose-500/30">
                          Anomaly
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 text-slate-400 font-mono whitespace-nowrap">
                      {formatDate(tx.date, "MMM d")}
                    </td>
                    <td className="py-2.5 text-slate-400 capitalize truncate max-w-[120px]">
                      {tx.categoryId.replace("cat-", "").replace("-", " ")}
                    </td>
                    <td className="py-2.5 text-right font-mono font-medium">
                      <AmountText amount={tx.amount} colored />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Upcoming Bills (Next 14 Days) */}
        <div className="lg:col-span-1 bg-slate-900/40 backdrop-blur-md border border-slate-800/60 rounded-[28px] p-5 md:p-6 space-y-4 shadow-[0_10px_30px_rgba(0,0,0,0.2)]">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-100">
                Upcoming Bills
              </h3>
              <p className="text-xs text-slate-400">Next 14 days auto-debits</p>
            </div>
            <NavLink
              to="/app/forecast"
              className="text-xs text-emerald-400 hover:underline"
            >
              Forecast
            </NavLink>
          </div>

          <div className="space-y-3">
            {data.upcomingBills.map((bill) => (
              <div
                key={bill.id}
                className="p-3 rounded-2xl bg-slate-800/30 border border-slate-700/40 flex items-center justify-between gap-3"
              >
                <div className="flex items-center gap-2.5 truncate">
                  <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shrink-0">
                    <Calendar className="w-4 h-4" />
                  </div>
                  <div className="truncate">
                    <div className="text-xs font-semibold text-slate-200 truncate">
                      {bill.merchant}
                    </div>
                    <div className="text-[10px] text-slate-400">
                      Due in{" "}
                      <span className="text-amber-400 font-medium">
                        {bill.daysAway} days
                      </span>{" "}
                      ({formatDate(bill.dueDate, "MMM d")})
                    </div>
                  </div>
                </div>
                <div className="text-xs font-mono font-bold text-white shrink-0">
                  {formatCurrency(bill.amount, profile.currency)}
                </div>
              </div>
            ))}
          </div>

          {/* Ask Copilot Mini Card */}
          <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-950/30 to-teal-950/30 border border-emerald-500/25 text-xs space-y-2 backdrop-blur-sm">
            <div className="flex items-center gap-2 text-emerald-400 font-semibold">
              <Bot className="w-4 h-4" />
              <span>Need help planning cash flow?</span>
            </div>
            <p className="text-[11px] text-slate-300">
              Ask Copilot if you can afford additional expenses before your next
              paycheck on the 1st.
            </p>
            <NavLink
              to="/app/copilot"
              className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-400 hover:underline pt-1"
            >
              <span>Ask AI Copilot</span>
              <ArrowRight className="w-3 h-3" />
            </NavLink>
          </div>
        </div>
      </div>
      <ShareInsightModal 
        isOpen={shareOpen} 
        onClose={() => setShareOpen(false)} 
        title="Financial Milestone Achieved!" 
        insight={`I've maintained a positive cash flow with a liquid balance of ${data ? formatCurrency(data.liquid_capital) : '$0'} this month using Finpluse's AI forecasting!`}
      />
    </div>
  );
};
