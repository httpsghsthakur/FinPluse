import {
  Account,
  Budget,
  Category,
  ChatMessage,
  DashboardSummary,
  ForecastEvent,
  ForecastPoint,
  Goal,
  Insight,
  Scenario,
  ScenarioResult,
  Transaction,
  WeeklyDigest,
} from "../../types";
import { API_CONFIG } from "./config";
import { generateAICopilotResponse } from "./mock/aiEngine";
import {
  generateSeedTransactions,
  INITIAL_ACCOUNTS,
  INITIAL_CATEGORIES,
  INITIAL_GOALS,
  INITIAL_INSIGHTS,
  loadStoredData,
  saveStoredData,
  StorageData,
} from "./mock/seed";
import { runWhatIfSimulation } from "./mock/simulator";
import {
  addDays,
  addMonths,
  format,
  getDaysInMonth,
  isAfter,
  isBefore,
  parseISO,
  startOfMonth,
  subDays,
  subMonths,
} from "date-fns";

import { supabaseAuth } from "../supabase";

// Helper to execute authenticated backend requests
async function apiFetch(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const url = `${API_CONFIG.BASE_URL}${path}`;
  const authHeaders = await supabaseAuth.getHeaders();
  const headers = {
    ...authHeaders,
    ...(options.headers || {}),
  };
  return fetch(url, { ...options, headers });
}

// Helper to simulate realistic network latency for mock mode
async function delay(ms?: number): Promise<void> {
  const duration =
    ms ??
    Math.floor(
      API_CONFIG.SIMULATED_LATENCY_MIN_MS +
        Math.random() *
          (API_CONFIG.SIMULATED_LATENCY_MAX_MS -
            API_CONFIG.SIMULATED_LATENCY_MIN_MS),
    );
  return new Promise((resolve) => setTimeout(resolve, duration));
}

export interface TransactionFilters {
  search?: string;
  categoryIds?: string[];
  accountIds?: string[];
  startDate?: string;
  endDate?: string;
  minAmount?: number;
  maxAmount?: number;
  anomalyOnly?: boolean;
  recurringOnly?: boolean;
  sortBy?: "date" | "amount" | "merchant";
  sortOrder?: "asc" | "desc";
  page?: number;
  limit?: number;
}

export interface PaginatedTransactions {
  transactions: Transaction[];
  total: number;
  page: number;
  totalPages: number;
}

class ApiClient {
  // ── Accounts ──────────────────────────────────────────────────
  async getAccounts(): Promise<Account[]> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/accounts`);
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to fetch accounts`);
      return res.json();
    }
    await delay();
    const data = loadStoredData();
    return data.accounts;
  }

  async syncAccount(accountId: string): Promise<Account> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/accounts/${accountId}/sync`, {
        method: "POST",
      });
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to sync account`);
      return res.json();
    }
    await delay(600);
    const data = loadStoredData();
    const accIndex = data.accounts.findIndex((a) => a.id === accountId);
    if (accIndex === -1) throw new Error("Account not found");
    data.accounts[accIndex].lastSynced = new Date().toISOString();
    saveStoredData(data);
    return data.accounts[accIndex];
  }

  async connectAccount(
    newAccount: Omit<Account, "id" | "lastSynced" | "isActive">,
  ): Promise<Account> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/accounts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newAccount),
      });
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to connect account`);
      return res.json();
    }
    await delay(800);
    const data = loadStoredData();
    const created: Account = {
      ...newAccount,
      id: `acc-${Date.now()}`,
      lastSynced: new Date().toISOString(),
      isActive: true,
    };
    data.accounts.push(created);
    saveStoredData(data);
    return created;
  }

  async disconnectAccount(accountId: string): Promise<void> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/accounts/${accountId}`, {
        method: "DELETE",
      });
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to disconnect account`);
      return;
    }
    await delay();
    const data = loadStoredData();
    data.accounts = data.accounts.filter((a) => a.id !== accountId);
    saveStoredData(data);
  }

  // ── Transactions ──────────────────────────────────────────────
  async getTransactions(
    filters?: TransactionFilters,
  ): Promise<PaginatedTransactions> {
    if (!API_CONFIG.USE_MOCK) {
      const params = new URLSearchParams();
      if (filters?.search) params.append("search", filters.search);
      if (filters?.categoryIds && filters.categoryIds.length > 0)
        params.append("categoryIds", filters.categoryIds.join(","));
      if (filters?.accountIds && filters.accountIds.length > 0)
        params.append("accountIds", filters.accountIds.join(","));
      if (filters?.startDate) params.append("startDate", filters.startDate);
      if (filters?.endDate) params.append("endDate", filters.endDate);
      if (filters?.minAmount !== undefined)
        params.append("minAmount", String(filters.minAmount));
      if (filters?.maxAmount !== undefined)
        params.append("maxAmount", String(filters.maxAmount));
      if (filters?.anomalyOnly) params.append("anomalyOnly", "true");
      if (filters?.recurringOnly) params.append("recurringOnly", "true");
      if (filters?.sortBy) params.append("sortBy", filters.sortBy);
      if (filters?.sortOrder) params.append("sortOrder", filters.sortOrder);
      if (filters?.page) params.append("page", String(filters.page));
      if (filters?.limit) params.append("limit", String(filters.limit));

      const res = await apiFetch(`/transactions?${params.toString()}`);
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to fetch transactions`);
      return res.json();
    }

    await delay();
    const data = loadStoredData();
    let list = [...data.transactions];

    if (filters?.search) {
      const term = filters.search.toLowerCase();
      list = list.filter(
        (t) =>
          t.merchant.toLowerCase().includes(term) ||
          t.notes?.toLowerCase().includes(term) ||
          t.amount.toString().includes(term),
      );
    }

    if (filters?.categoryIds && filters.categoryIds.length > 0) {
      list = list.filter((t) => filters.categoryIds!.includes(t.categoryId));
    }

    if (filters?.accountIds && filters.accountIds.length > 0) {
      list = list.filter((t) => filters.accountIds!.includes(t.accountId));
    }

    if (filters?.startDate) {
      list = list.filter(
        (t) =>
          isAfter(parseISO(t.date), parseISO(filters.startDate!)) ||
          t.date === filters.startDate,
      );
    }

    if (filters?.endDate) {
      list = list.filter(
        (t) =>
          isBefore(parseISO(t.date), parseISO(filters.endDate!)) ||
          t.date === filters.endDate,
      );
    }

    if (filters?.anomalyOnly) {
      list = list.filter((t) => t.isAnomaly);
    }

    if (filters?.recurringOnly) {
      list = list.filter((t) => t.isRecurring);
    }

    if (filters?.minAmount !== undefined) {
      list = list.filter((t) => Math.abs(t.amount) >= filters.minAmount!);
    }

    if (filters?.maxAmount !== undefined) {
      list = list.filter((t) => Math.abs(t.amount) <= filters.maxAmount!);
    }

    // Sort
    const sortBy = filters?.sortBy || "date";
    const sortOrder = filters?.sortOrder || "desc";

    list.sort((a, b) => {
      let comp = 0;
      if (sortBy === "date")
        comp = new Date(b.date).getTime() - new Date(a.date).getTime();
      else if (sortBy === "amount")
        comp = Math.abs(b.amount) - Math.abs(a.amount);
      else if (sortBy === "merchant")
        comp = a.merchant.localeCompare(b.merchant);
      return sortOrder === "asc" ? -comp : comp;
    });

    const page = filters?.page || 1;
    const limit = filters?.limit || 20;
    const total = list.length;
    const totalPages = Math.ceil(total / limit) || 1;
    const paginated = list.slice((page - 1) * limit, page * limit);

    return {
      transactions: paginated,
      total,
      page,
      totalPages,
    };
  }

  async updateTransaction(
    id: string,
    updates: Partial<Transaction>,
  ): Promise<Transaction> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/transactions/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
      });
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to update transaction`);
      return res.json();
    }

    await delay();
    const data = loadStoredData();
    const idx = data.transactions.findIndex((t) => t.id === id);
    if (idx === -1) throw new Error("Transaction not found");
    data.transactions[idx] = { ...data.transactions[idx], ...updates };
    saveStoredData(data);
    return data.transactions[idx];
  }

  async addTransaction(tx: Omit<Transaction, "id">): Promise<Transaction> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/transactions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(tx),
      });
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to add transaction`);
      return res.json();
    }

    await delay();
    const data = loadStoredData();
    const newTx: Transaction = {
      ...tx,
      id: `tx-custom-${Date.now()}`,
    };
    data.transactions.unshift(newTx);
    saveStoredData(data);
    return newTx;
  }

  async importTransactionsCSV(
    csvText: string,
  ): Promise<{ importedCount: number }> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/transactions/import`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ csvText, csv_text: csvText }),
      });
      if (!res.ok) {
        const errorText = await res.text();
        console.error("CSV import error response:", res.status, errorText);
        throw new Error(`HTTP ${res.status}: ${errorText || "Failed to import CSV"}`);
      }
      const data = await res.json();
      return { importedCount: data.importedCount ?? data.imported_count ?? 0 };
    }

    await delay(700);
    const data = loadStoredData();
    const lines = csvText.trim().split("\n");
    let importedCount = 0;

    for (let i = 1; i < lines.length; i++) {
      const parts = lines[i]
        .split(",")
        .map((p) => p.trim().replace(/^["']|["']$/g, ""));
      if (parts.length >= 3) {
        const [dateStr, merchantStr, amountStr, catStr] = parts;
        const amount = parseFloat(amountStr);
        if (!isNaN(amount)) {
          data.transactions.unshift({
            id: `tx-import-${Date.now()}-${i}`,
            date: dateStr || format(new Date(), "yyyy-MM-dd"),
            merchant: merchantStr || "Imported Merchant",
            amount: amount < 0 ? amount : -amount,
            categoryId: catStr || "cat-other",
            accountId: "acc-checking",
            status: "settled",
            isRecurring: false,
          });
          importedCount++;
        }
      }
    }

    saveStoredData(data);
    return { importedCount };
  }

  async replaceTransactionsFromCSV(
    csvText: string,
  ): Promise<{ importedCount: number }> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/admin/replace_transactions_from_csv`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ csvText, csv_text: csvText }),
      });
      if (!res.ok) {
        const errorText = await res.text();
        console.error("CSV replace error response:", res.status, errorText);
        throw new Error(`HTTP ${res.status}: ${errorText || "Failed to replace transactions from CSV"}`);
      }
      const data = await res.json();
      return { importedCount: data.importedCount ?? data.imported_count ?? 0 };
    }

    await delay(700);
    const data = loadStoredData();
    data.transactions = []; // wipe existing transactions
    const lines = csvText.trim().split("\n");
    let importedCount = 0;

    for (let i = 1; i < lines.length; i++) {
      const parts = lines[i]
        .split(",")
        .map((p) => p.trim().replace(/^["']|["']$/g, ""));
      if (parts.length >= 3) {
        const [dateStr, merchantStr, amountStr, catStr] = parts;
        const amount = parseFloat(amountStr);
        if (!isNaN(amount)) {
          data.transactions.unshift({
            id: `tx-import-${Date.now()}-${i}`,
            date: dateStr || format(new Date(), "yyyy-MM-dd"),
            merchant: merchantStr || "Imported Merchant",
            amount: amount,
            categoryId: catStr || "cat-other",
            accountId: "acc-checking",
            status: "settled",
            isRecurring: false,
          });
          importedCount++;
        }
      }
    }

    saveStoredData(data);
    return { importedCount };
  }

  async exportTransactionsCSV(): Promise<string> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/transactions/export`);
      if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to export CSV`);
      return res.text();
    }

    const data = loadStoredData();
    const headers = [
      "Date",
      "Merchant",
      "Amount",
      "Category",
      "Account",
      "Status",
      "Recurring",
    ];
    const rows = data.transactions.map((t) => [
      t.date,
      `"${t.merchant.replace(/"/g, '""')}"`,
      t.amount,
      t.categoryId,
      t.accountId,
      t.status,
      t.isRecurring ? "Yes" : "No",
    ]);
    return [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
  }

  // ── Categories ────────────────────────────────────────────────
  async getCategories(): Promise<Category[]> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/categories`);
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to fetch categories`);
      return res.json();
    }
    await delay();
    const data = loadStoredData();
    return data.categories;
  }

  async addCategory(cat: Omit<Category, "id">): Promise<Category> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/categories`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cat),
      });
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to add category`);
      return res.json();
    }
    await delay();
    const data = loadStoredData();
    const created: Category = {
      ...cat,
      id: `cat-user-${Date.now()}`,
    };
    data.categories.push(created);
    saveStoredData(data);
    return created;
  }

  async updateCategory(
    id: string,
    updates: Partial<Category>,
  ): Promise<Category> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/categories/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
      });
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to update category`);
      return res.json();
    }
    await delay();
    const data = loadStoredData();
    const idx = data.categories.findIndex((c) => c.id === id);
    if (idx === -1) throw new Error("Category not found");
    data.categories[idx] = { ...data.categories[idx], ...updates };
    saveStoredData(data);
    return data.categories[idx];
  }

  async deleteCategory(id: string): Promise<void> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/categories/${id}`, { method: "DELETE" });
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to delete category`);
      return;
    }
    await delay();
    const data = loadStoredData();
    data.categories = data.categories.filter((c) => c.id !== id);
    saveStoredData(data);
  }

  // ── Budgets ───────────────────────────────────────────────────
  async getBudgets(month?: string): Promise<Budget[]> {
    if (!API_CONFIG.USE_MOCK) {
      const url = month
        ? `${API_CONFIG.BASE_URL}/budgets?month=${month}`
        : `${API_CONFIG.BASE_URL}/budgets`;
      const res = await fetch(url);
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to fetch budgets`);
      return res.json();
    }

    await delay();
    const targetMonth = month || format(new Date(), "yyyy-MM");
    const data = loadStoredData();

    const monthTx = data.transactions.filter(
      (t) => t.date.startsWith(targetMonth) && t.amount < 0,
    );
    const expenseCategories = data.categories.filter(
      (c) => c.type === "expense",
    );

    // Use real days in month instead of hardcoded 30
    const targetDate = parseISO(`${targetMonth}-01`);
    const actualDaysInMonth = getDaysInMonth(targetDate);
    const today = new Date();
    const isCurrentMonth = format(today, "yyyy-MM") === targetMonth;
    const elapsedDays = isCurrentMonth ? today.getDate() : actualDaysInMonth;

    return expenseCategories.map((cat) => {
      const spent = Math.abs(
        monthTx
          .filter((t) => t.categoryId === cat.id)
          .reduce((sum, t) => sum + t.amount, 0),
      );
      // Predict month-end spend based on daily pacing and actual days in month
      const pacing =
        elapsedDays > 0 ? (spent / elapsedDays) * actualDaysInMonth : spent;
      const predictedSpend = Math.round(pacing * 100) / 100;

      return {
        id: `bgt-${cat.id}-${targetMonth}`,
        categoryId: cat.id,
        monthlyLimit: cat.monthlyBudget || 0,
        spent: Math.round(spent * 100) / 100,
        month: targetMonth,
        predictedSpend,
      };
    });
  }

  async updateBudget(
    categoryId: string,
    monthlyLimit: number,
  ): Promise<Category> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/budgets/${categoryId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ monthlyLimit }),
      });
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to update budget`);
      return res.json();
    }
    await delay();
    return this.updateCategory(categoryId, { monthlyBudget: monthlyLimit });
  }

  // ── Goals ─────────────────────────────────────────────────────
  async getGoals(): Promise<Goal[]> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/goals`);
      if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to fetch goals`);
      return res.json();
    }
    await delay();
    const data = loadStoredData();
    return data.goals;
  }

  async addGoal(goal: Omit<Goal, "id" | "isCompleted">): Promise<Goal> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/goals`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(goal),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to add goal`);
      return res.json();
    }
    await delay();
    const data = loadStoredData();
    const created: Goal = {
      ...goal,
      id: `goal-${Date.now()}`,
      isCompleted: false,
    };
    data.goals.push(created);
    saveStoredData(data);
    return created;
  }

  async updateGoal(id: string, updates: Partial<Goal>): Promise<Goal> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/goals/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to update goal`);
      return res.json();
    }
    await delay();
    const data = loadStoredData();
    const idx = data.goals.findIndex((g) => g.id === id);
    if (idx === -1) throw new Error("Goal not found");
    data.goals[idx] = { ...data.goals[idx], ...updates };
    if (data.goals[idx].currentAmount >= data.goals[idx].targetAmount) {
      data.goals[idx].isCompleted = true;
    }
    saveStoredData(data);
    return data.goals[idx];
  }

  async deleteGoal(id: string): Promise<void> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/goals/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to delete goal`);
      return;
    }
    await delay();
    const data = loadStoredData();
    data.goals = data.goals.filter((g) => g.id !== id);
    saveStoredData(data);
  }

  async contributeToGoal(id: string, amount: number): Promise<Goal> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/goals/${id}/contribute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount }),
      });
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to contribute to goal`);
      return res.json();
    }
    await delay();
    const data = loadStoredData();
    const goal = data.goals.find((g) => g.id === id);
    if (!goal) throw new Error("Goal not found");

    goal.currentAmount += amount;
    if (goal.currentAmount >= goal.targetAmount) {
      goal.isCompleted = true;
    }

    data.transactions.unshift({
      id: `tx-goal-contrib-${Date.now()}`,
      date: format(new Date(), "yyyy-MM-dd"),
      merchant: `Goal Deposit: ${goal.name}`,
      categoryId: "cat-transfers",
      accountId: goal.linkedAccountId,
      amount: -amount,
      status: "settled",
      isRecurring: false,
      notes: `Automated boost to ${goal.name}`,
    });

    saveStoredData(data);
    return goal;
  }

  // ── Forecast ──────────────────────────────────────────────────
  async getForecast(
    days: 30 | 60 | 90 = 90,
  ): Promise<{ points: ForecastPoint[]; events: ForecastEvent[] }> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/forecast?days=${days}`);
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to fetch forecast`);
      return res.json();
    }

    await delay();
    const data = loadStoredData();
    const totalChecking =
      data.accounts.find((a) => a.type === "checking")?.balance || 0;
    const totalSavings =
      data.accounts.find((a) => a.type === "savings")?.balance || 0;
    const currentLiquid = totalChecking + totalSavings;

    // ── Derive daily burn from real transactions (last 90 days) ──
    const today = new Date();
    const ninetyDaysAgo = subDays(today, 90);
    const recentExpenses = data.transactions.filter(
      (t) =>
        t.amount < 0 &&
        t.categoryId !== "cat-transfers" &&
        !isBefore(parseISO(t.date), ninetyDaysAgo),
    );
    const totalRecentExpense = Math.abs(
      recentExpenses.reduce((sum, t) => sum + t.amount, 0),
    );
    const dailyBurnAverage =
      totalRecentExpense > 0 ? totalRecentExpense / 90 : 1000;

    // ── Derive recurring income (salary) from actual recurring income transactions ──
    const recurringIncome = data.transactions.filter(
      (t) => t.isRecurring && t.amount > 0,
    );
    // Get unique merchants and their typical amounts
    const incomeByMerchant = new Map<
      string,
      { amount: number; dayOfMonth: number[] }
    >();
    recurringIncome.forEach((t) => {
      const existing = incomeByMerchant.get(t.merchant);
      const dom = parseISO(t.date).getDate();
      if (existing) {
        existing.dayOfMonth.push(dom);
      } else {
        incomeByMerchant.set(t.merchant, {
          amount: t.amount,
          dayOfMonth: [dom],
        });
      }
    });

    // ── Derive recurring bills from actual recurring expense transactions ──
    const recurringBills = data.transactions.filter(
      (t) => t.isRecurring && t.amount < 0,
    );
    const billsByMerchant = new Map<
      string,
      { amount: number; dayOfMonth: number; categoryId: string }
    >();
    recurringBills.forEach((t) => {
      if (!billsByMerchant.has(t.merchant)) {
        billsByMerchant.set(t.merchant, {
          amount: Math.abs(t.amount),
          dayOfMonth: parseISO(t.date).getDate(),
          categoryId: t.categoryId,
        });
      }
    });

    const points: ForecastPoint[] = [];
    const events: ForecastEvent[] = [];

    // ── Build past 30-day actual balance by replaying transactions backwards ──
    let pastRunning = currentLiquid;
    const pastPoints: ForecastPoint[] = [];

    for (let d = 1; d <= 30; d++) {
      const pastDate = subDays(today, d);
      const dateStr = format(pastDate, "yyyy-MM-dd");

      // Find transactions on this date and reverse their effect
      const dayTx = data.transactions.filter((t) => t.date === dateStr);
      const dayNet = dayTx.reduce((sum, t) => sum + t.amount, 0);
      pastRunning -= dayNet; // Reverse the transaction to get prior balance

      pastPoints.unshift({
        date: dateStr,
        actualBalance: Math.round(pastRunning),
        forecastedBalance: Math.round(pastRunning),
        lowerBound: Math.round(pastRunning * 0.98),
        upperBound: Math.round(pastRunning * 1.02),
        isActual: true,
        events: [],
      });
    }
    points.push(...pastPoints);

    // ── Build future forecast ──
    let runningBalance = currentLiquid;

    for (let day = 0; day <= days; day++) {
      const futureDate = addDays(today, day);
      const dateStr = format(futureDate, "yyyy-MM-dd");
      const dayEvents: ForecastEvent[] = [];
      const dayOfMonth = futureDate.getDate();

      // Apply recurring income on detected pay days
      incomeByMerchant.forEach((info, merchant) => {
        const avgDay = Math.round(
          info.dayOfMonth.reduce((a, b) => a + b, 0) / info.dayOfMonth.length,
        );
        if (dayOfMonth === avgDay) {
          const ev: ForecastEvent = {
            id: `ev-income-${merchant.substring(0, 10)}-${day}`,
            date: dateStr,
            type: "payday",
            title: merchant,
            amount: info.amount,
            accountId: "acc-checking",
          };
          dayEvents.push(ev);
          events.push(ev);
          runningBalance += info.amount;
        }
      });

      // Apply recurring bills on detected bill days
      billsByMerchant.forEach((info, merchant) => {
        if (dayOfMonth === info.dayOfMonth) {
          const ev: ForecastEvent = {
            id: `ev-bill-${merchant.substring(0, 10)}-${day}`,
            date: dateStr,
            type: "recurring_bill",
            title: merchant,
            amount: -info.amount,
            accountId: "acc-checking",
          };
          dayEvents.push(ev);
          events.push(ev);
          runningBalance -= info.amount;
        }
      });

      // Apply daily discretionary burn
      runningBalance -= dailyBurnAverage;
      const uncertainty = day * (dailyBurnAverage * 0.3); // 30% daily uncertainty growth

      points.push({
        date: dateStr,
        actualBalance: day === 0 ? Math.round(currentLiquid) : null,
        forecastedBalance: Math.round(runningBalance),
        lowerBound: Math.round(runningBalance - uncertainty),
        upperBound: Math.round(runningBalance + uncertainty),
        isActual: day === 0,
        events: dayEvents,
      });
    }

    return { points, events };
  }

  // ── Insights ──────────────────────────────────────────────────
  async getInsights(): Promise<Insight[]> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/insights`);
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to fetch insights`);
      return res.json();
    }
    await delay();
    const data = loadStoredData();
    return data.insights;
  }

  async dismissInsight(id: string): Promise<void> {
    if (!API_CONFIG.USE_MOCK) {
      await apiFetch(`/insights/${id}/dismiss`, { method: "POST" });
      return;
    }
    await delay(150);
    const data = loadStoredData();
    const idx = data.insights.findIndex((i) => i.id === id);
    if (idx !== -1) {
      data.insights[idx].isDismissed = true;
      saveStoredData(data);
    }
  }

  async likeInsight(id: string): Promise<void> {
    if (!API_CONFIG.USE_MOCK) {
      await apiFetch(`/insights/${id}/like`, { method: "POST" });
      return;
    }
    await delay(150);
    const data = loadStoredData();
    const idx = data.insights.findIndex((i) => i.id === id);
    if (idx !== -1) {
      data.insights[idx].isLiked = !data.insights[idx].isLiked;
      saveStoredData(data);
    }
  }

  async getWeeklyDigest(): Promise<WeeklyDigest> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/insights/digest/weekly`);
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to fetch weekly digest`);
      return res.json();
    }
    await delay();
    const data = loadStoredData();
    const today = new Date();
    const weekStart = subDays(today, 7);
    const prevWeekStart = subDays(today, 14);

    // ── Current week transactions ──
    const weekTx = data.transactions.filter((t) => {
      const d = parseISO(t.date);
      return !isBefore(d, weekStart) && !isAfter(d, today);
    });

    const totalIncome = weekTx
      .filter((t) => t.amount > 0)
      .reduce((sum, t) => sum + t.amount, 0);
    const totalExpenses = Math.abs(
      weekTx
        .filter((t) => t.amount < 0 && t.categoryId !== "cat-transfers")
        .reduce((sum, t) => sum + t.amount, 0),
    );
    const netSavings = totalIncome - totalExpenses;

    // ── Previous week for comparison ──
    const prevWeekTx = data.transactions.filter((t) => {
      const d = parseISO(t.date);
      return !isBefore(d, prevWeekStart) && isBefore(d, weekStart);
    });
    const prevWeekExpenses = Math.abs(
      prevWeekTx
        .filter((t) => t.amount < 0 && t.categoryId !== "cat-transfers")
        .reduce((sum, t) => sum + t.amount, 0),
    );
    const vsLastWeekPct =
      prevWeekExpenses > 0
        ? Math.round(
            ((totalExpenses - prevWeekExpenses) / prevWeekExpenses) * 100 * 10,
          ) / 10
        : 0;

    // ── Top spending category this week ──
    const catSpendMap = new Map<string, number>();
    weekTx
      .filter((t) => t.amount < 0 && t.categoryId !== "cat-transfers")
      .forEach((t) => {
        catSpendMap.set(
          t.categoryId,
          (catSpendMap.get(t.categoryId) || 0) + Math.abs(t.amount),
        );
      });

    let topCategoryId = "";
    let topCategorySpend = 0;
    catSpendMap.forEach((amount, catId) => {
      if (amount > topCategorySpend) {
        topCategorySpend = amount;
        topCategoryId = catId;
      }
    });
    const topCategoryName =
      data.categories.find((c) => c.id === topCategoryId)?.name || "General";

    // ── Anomalies this week ──
    const anomaliesDetectedCount = weekTx.filter((t) => t.isAnomaly).length;

    // ── Dynamic week range label ──
    const weekRange = `${format(weekStart, "MMM d")} – ${format(today, "MMM d, yyyy")}`;

    // ── Generate contextual bullets from real data ──
    const bullets: string[] = [];

    if (vsLastWeekPct !== 0) {
      const direction = vsLastWeekPct < 0 ? "lower" : "higher";
      bullets.push(
        `Total spending was ${Math.abs(vsLastWeekPct)}% ${direction} than last week.`,
      );
    }

    const interestTx = weekTx.filter(
      (t) => t.amount > 0 && t.merchant.toLowerCase().includes("interest"),
    );
    if (interestTx.length > 0) {
      const interestTotal = interestTx.reduce((sum, t) => sum + t.amount, 0);
      bullets.push(
        `Earned ₹${interestTotal.toLocaleString("en-IN", { minimumFractionDigits: 2 })} in interest/yield income this week.`,
      );
    }

    if (anomaliesDetectedCount > 0) {
      const topAnomaly = weekTx.find((t) => t.isAnomaly);
      if (topAnomaly) {
        bullets.push(
          `${anomaliesDetectedCount} unusual transaction${anomaliesDetectedCount > 1 ? "s" : ""} flagged: ${topAnomaly.merchant} (₹${Math.abs(topAnomaly.amount).toLocaleString("en-IN")}).`,
        );
      }
    }

    if (bullets.length === 0) {
      bullets.push(
        `Processed ${weekTx.length} transactions this week across your connected accounts.`,
      );
    }

    // ── Actionable tip from real data ──
    const goalsWithRoom = data.goals.filter(
      (g) => !g.isCompleted && g.currentAmount < g.targetAmount,
    );
    const actionableTip =
      netSavings > 0 && goalsWithRoom.length > 0
        ? `Moving ₹${Math.min(Math.round(netSavings * 0.1), 5000).toLocaleString("en-IN")} from this week's surplus to your ${goalsWithRoom[0].name} goal can accelerate completion.`
        : `Review your spending patterns to identify potential savings opportunities.`;

    return {
      weekRange,
      weekLabel: weekRange,
      summaryTitle:
        netSavings > 0
          ? `Positive cash flow week — ₹${Math.round(netSavings).toLocaleString("en-IN")} net saved`
          : `Net outflow week — review spending patterns`,
      totalIncome: Math.round(totalIncome * 100) / 100,
      totalExpenses: Math.round(totalExpenses * 100) / 100,
      netSavings: Math.round(netSavings * 100) / 100,
      topCategoryName,
      topCategorySpend: Math.round(topCategorySpend * 100) / 100,
      vsLastWeekPct,
      bullets,
      actionableTip,
      anomaliesDetectedCount,
    };
  }

  // ── Dashboard Summary ─────────────────────────────────────────
  async getDashboardSummary(): Promise<DashboardSummary> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/dashboard/summary`);
      if (!res.ok)
        throw new Error(
          `HTTP ${res.status}: Failed to fetch dashboard summary`,
        );
      return res.json();
    }

    await delay();
    const data = loadStoredData();

    const checking =
      data.accounts.find((a) => a.type === "checking")?.balance || 0;
    const savings =
      data.accounts.find((a) => a.type === "savings")?.balance || 0;
    const credit = data.accounts.find((a) => a.type === "credit")?.balance || 0;

    const liquidCash = checking + savings;
    const totalDebt = Math.abs(credit);
    const netWorth = liquidCash - totalDebt;

    // ── Compute cashFlowHistory from REAL transactions (last 6 months) ──
    const today = new Date();
    const cashFlowHistory: {
      month: string;
      income: number;
      expenses: number;
      savings: number;
    }[] = [];

    for (let i = 5; i >= 0; i--) {
      const monthDate = subMonths(today, i);
      const monthPrefix = format(monthDate, "yyyy-MM");
      const monthLabel = format(monthDate, "MMM");

      const monthTransactions = data.transactions.filter((t) =>
        t.date.startsWith(monthPrefix),
      );

      const income = monthTransactions
        .filter((t) => t.amount > 0)
        .reduce((sum, t) => sum + t.amount, 0);

      const expenses = Math.abs(
        monthTransactions
          .filter((t) => t.amount < 0 && t.categoryId !== "cat-transfers")
          .reduce((sum, t) => sum + t.amount, 0),
      );

      cashFlowHistory.push({
        month: monthLabel,
        income: Math.round(income * 100) / 100,
        expenses: Math.round(expenses * 100) / 100,
        savings: Math.round((income - expenses) * 100) / 100,
      });
    }

    // ── Compute netWorthMomPct from monthly net deltas ──
    const currentMonthCF = cashFlowHistory[cashFlowHistory.length - 1];
    const prevMonthCF = cashFlowHistory[cashFlowHistory.length - 2];
    let netWorthMomPct = 0;
    if (prevMonthCF && prevMonthCF.savings !== 0) {
      netWorthMomPct =
        Math.round(
          ((currentMonthCF.savings - prevMonthCF.savings) /
            Math.abs(prevMonthCF.savings)) *
            100 *
            10,
        ) / 10;
    }

    // ── Compute current month spending from REAL transactions ──
    const currentMonthPrefix = format(today, "yyyy-MM");
    const monthTx = data.transactions.filter(
      (t) =>
        t.date.startsWith(currentMonthPrefix) &&
        t.amount < 0 &&
        t.categoryId !== "cat-transfers",
    );

    const totalMonthlySpend = Math.abs(
      monthTx.reduce((sum, t) => sum + t.amount, 0),
    );
    const totalBudget = data.categories.reduce(
      (sum, c) => sum + (c.monthlyBudget || 0),
      0,
    );

    // ── Compute monthlySpendVsBudgetPct ──
    const monthlySpendVsBudgetPct =
      totalBudget > 0
        ? Math.round(
            ((totalMonthlySpend - totalBudget) / totalBudget) * 100 * 10,
          ) / 10
        : 0;

    // ── Category spend from REAL transactions (no fake fallbacks) ──
    const categorySpend = data.categories
      .filter((c) => c.type === "expense")
      .map((cat) => {
        const spent = Math.abs(
          monthTx
            .filter((t) => t.categoryId === cat.id)
            .reduce((sum, t) => sum + t.amount, 0),
        );
        return {
          categoryId: cat.id,
          categoryName: cat.name,
          color: cat.color,
          amount: Math.round(spent * 100) / 100,
          percentage: Math.round((spent / (totalMonthlySpend || 1)) * 100),
          budget: cat.monthlyBudget || 0,
        };
      })
      .sort((a, b) => b.amount - a.amount);

    // ── Cash runway from REAL monthly burn ──
    const monthlyBurn =
      totalMonthlySpend > 0
        ? totalMonthlySpend
        : cashFlowHistory.length > 0
          ? cashFlowHistory.reduce((sum, m) => sum + m.expenses, 0) /
            cashFlowHistory.filter((m) => m.expenses > 0).length
          : 1;
    const cashRunwayMonths = Number((liquidCash / monthlyBurn).toFixed(1));

    // ── Savings rate from REAL income/expenses ──
    const currentMonthIncome = data.transactions
      .filter((t) => t.date.startsWith(currentMonthPrefix) && t.amount > 0)
      .reduce((sum, t) => sum + t.amount, 0);
    const savingsRatePct =
      currentMonthIncome > 0
        ? Math.round(
            ((currentMonthIncome - totalMonthlySpend) / currentMonthIncome) *
              100 *
              10,
          ) / 10
        : 0;

    // ── Savings rate MoM delta ──
    const prevMonthPrefix = format(subMonths(today, 1), "yyyy-MM");
    const prevMonthIncome = data.transactions
      .filter((t) => t.date.startsWith(prevMonthPrefix) && t.amount > 0)
      .reduce((sum, t) => sum + t.amount, 0);
    const prevMonthExpenses = Math.abs(
      data.transactions
        .filter(
          (t) =>
            t.date.startsWith(prevMonthPrefix) &&
            t.amount < 0 &&
            t.categoryId !== "cat-transfers",
        )
        .reduce((sum, t) => sum + t.amount, 0),
    );
    const prevSavingsRate =
      prevMonthIncome > 0
        ? ((prevMonthIncome - prevMonthExpenses) / prevMonthIncome) * 100
        : 0;
    const savingsRateMomDelta =
      Math.round((savingsRatePct - prevSavingsRate) * 10) / 10;

    // ── Upcoming bills from REAL recurring transactions ──
    const recurringExpenses = data.transactions.filter(
      (t) => t.isRecurring && t.amount < 0,
    );
    // Deduplicate by merchant to get unique recurring bills
    const merchantMap = new Map<string, Transaction>();
    recurringExpenses.forEach((t) => {
      const existing = merchantMap.get(t.merchant);
      if (!existing || new Date(t.date) > new Date(existing.date)) {
        merchantMap.set(t.merchant, t);
      }
    });

    const upcomingBills = Array.from(merchantMap.values())
      .map((t) => {
        // Estimate next due date: ~30 days after last occurrence
        const lastDate = parseISO(t.date);
        let nextDue = addDays(lastDate, 30);
        // If next due is in the past, shift forward
        while (isBefore(nextDue, today)) {
          nextDue = addDays(nextDue, 30);
        }
        const daysAway = Math.ceil(
          (nextDue.getTime() - today.getTime()) / (1000 * 60 * 60 * 24),
        );
        const acc = data.accounts.find((a) => a.id === t.accountId);

        return {
          id: `bill-${t.id}`,
          merchant: t.merchant,
          amount: Math.abs(t.amount),
          dueDate: format(nextDue, "yyyy-MM-dd"),
          categoryId: t.categoryId,
          accountName: acc ? `${acc.name} (${acc.mask})` : "Unknown",
          daysAway,
        };
      })
      .filter((b) => b.daysAway <= 30 && b.daysAway >= 0)
      .sort((a, b) => a.daysAway - b.daysAway)
      .slice(0, 5);

    // ── Low balance alert from forecast ──
    const projectedMinBalance = liquidCash - monthlyBurn * 2;
    const lowBalanceThreshold = monthlyBurn; // 1 month of expenses as threshold

    return {
      netWorth,
      netWorthMomPct,
      monthlySpending: Math.round(totalMonthlySpend * 100) / 100,
      monthlyBudgetTotal: totalBudget,
      monthlySpendVsBudgetPct,
      cashRunwayMonths,
      savingsRatePct,
      savingsRateMomDelta,
      totalLiquidCash: liquidCash,
      totalDebt,
      cashFlowHistory,
      categorySpend,
      recentTransactions: data.transactions.slice(0, 8),
      upcomingBills,
      lowBalanceAlert: {
        hasLowBalance: projectedMinBalance < lowBalanceThreshold,
        threshold: Math.round(lowBalanceThreshold),
        ...(projectedMinBalance < lowBalanceThreshold
          ? {
              date: format(addDays(today, 60), "yyyy-MM-dd"),
              predictedBalance: Math.round(projectedMinBalance),
            }
          : {}),
      },
    };
  }

  // ── Simulator ─────────────────────────────────────────────────
  async runSimulation(scenario: Scenario): Promise<ScenarioResult> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/simulator/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(scenario),
      });
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to run simulation`);
      return res.json();
    }

    await delay(400);
    const data = loadStoredData();
    return runWhatIfSimulation(scenario, data);
  }

  createCategory(cat: Omit<Category, "id">): Promise<Category> {
    return this.addCategory(cat);
  }

  // ── AI Copilot ────────────────────────────────────────────────
  async askCopilotStream(
    userMessage: string,
    personality: "concise" | "balanced" | "detailed" = "balanced",
    onTokenChunk?: (chunk: string) => void,
    onComplete?: (message: ChatMessage) => void,
  ): Promise<ChatMessage> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/copilot/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage, personality }),
      });
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to get copilot response`);
      const finalMsg: ChatMessage = await res.json();

      if (onTokenChunk) {
        const words = (finalMsg.content || "").split(" ");
        for (let i = 0; i < words.length; i++) {
          await new Promise((r) => setTimeout(r, 20));
          onTokenChunk(words[i] + (i === words.length - 1 ? "" : " "));
        }
      }

      if (onComplete) onComplete(finalMsg);
      return finalMsg;
    }

    const data = loadStoredData();
    const response = generateAICopilotResponse(userMessage, data, personality);

    if (onTokenChunk) {
      const words = response.content.split(" ");
      for (let i = 0; i < words.length; i++) {
        await new Promise((r) => setTimeout(r, 20 + Math.random() * 25));
        onTokenChunk(words[i] + (i === words.length - 1 ? "" : " "));
      }
    } else {
      await delay(600);
    }

    const finalMsg: ChatMessage = {
      id: `ai-msg-${Date.now()}`,
      role: "assistant",
      sender: "ai",
      content: response.content,
      text: response.content,
      timestamp: new Date().toISOString(),
      groundedData: response.groundedData,
      confidence: response.confidence,
      confidenceBand: response.confidence?.toLowerCase() as any,
      confidenceScore:
        response.confidence === "High"
          ? 0.96
          : response.confidence === "Medium"
            ? 0.82
            : 0.65,
      quickActions: response.quickActions,
    };

    if (onComplete) {
      onComplete(finalMsg);
    }

    return finalMsg;
  }

  async sendAIChatMessage(
    userMessage: string,
    personality: "concise" | "balanced" | "detailed" = "balanced",
    onTokenChunk?: (chunk: string) => void,
  ): Promise<ChatMessage> {
    return this.askCopilotStream(userMessage, personality, onTokenChunk);
  }

  // ── Admin & Data Management ───────────────────────────────────
  async resetAllData(): Promise<void> {
    if (!API_CONFIG.USE_MOCK) {
      await apiFetch(`/admin/reset`, { method: "POST" });
      return;
    }
    await delay(300);
    const freshData: StorageData = {
      accounts: INITIAL_ACCOUNTS,
      categories: INITIAL_CATEGORIES,
      goals: INITIAL_GOALS,
      transactions: generateSeedTransactions(),
      insights: INITIAL_INSIGHTS,
    };
    saveStoredData(freshData);
  }

  async exportAllData(): Promise<StorageData> {
    if (!API_CONFIG.USE_MOCK) {
      const res = await apiFetch(`/admin/export`);
      if (!res.ok)
        throw new Error(`HTTP ${res.status}: Failed to export all data`);
      return res.json();
    }
    return loadStoredData();
  }

  async exportAllDataJSON(): Promise<string> {
    const data = await this.exportAllData();
    return JSON.stringify(data, null, 2);
  }
}

export const api = new ApiClient();
