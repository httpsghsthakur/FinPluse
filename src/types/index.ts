export type AccountType = "checking" | "savings" | "credit" | "investment";

export interface Account {
  id: string;
  name: string;
  type: AccountType;
  balance: number;
  currency: string;
  institution: string;
  mask: string;
  color: string;
  lastSynced: string;
  isActive: boolean;
}

export type TransactionStatus = "settled" | "pending";

export interface Transaction {
  id: string;
  date: string;
  merchant: string;
  categoryId: string;
  accountId: string;
  amount: number; // negative for expense, positive for income
  status: TransactionStatus;
  isRecurring: boolean;
  isAnomaly?: boolean;
  anomalyReason?: string;
  notes?: string;
  tags?: string[];
}

export type CategoryType = "expense" | "income" | "transfer";

export interface Category {
  id: string;
  name: string;
  icon: string;
  color: string;
  type?: CategoryType;
  monthlyBudget?: number;
  defaultMonthlyBudget?: number;
  isSystem?: boolean;
  isCustom?: boolean;
}

export interface Budget {
  id: string;
  categoryId: string;
  monthlyLimit: number;
  spent: number;
  month: string; // YYYY-MM
  predictedSpend: number;
}

export interface BudgetCategory {
  categoryId: string;
  categoryName: string;
  icon: string;
  color: string;
  spent: number;
  budget: number;
  remaining: number;
  aiPacingAlert?: string;
}

export interface BudgetSummary {
  totalBudget: number;
  totalSpent: number;
  pctUsed: number;
  totalRemaining: number;
  daysLeftInMonth: number;
}

export interface GoalBoost {
  id: string;
  goalId: string;
  amount: number;
  source: string;
  reason?: string;
}

export interface Goal {
  id: string;
  name: string;
  targetAmount: number;
  currentAmount: number;
  deadline: string; // YYYY-MM-DD
  category: string;
  linkedAccountId: string;
  monthlyContribution: number;
  color: string;
  icon: string;
  isCompleted: boolean;
  boostSuggestion?: string;
}

export interface ForecastEvent {
  id: string;
  date: string;
  type: "payday" | "recurring_bill" | "goal_contrib" | "custom";
  title: string;
  amount: number;
  accountId: string;
}

export interface ForecastPoint {
  date: string;
  actualBalance: number | null;
  forecastedBalance: number;
  lowerBound: number;
  upperBound: number;
  isActual: boolean;
  events: ForecastEvent[];
}

export type InsightSeverity = "info" | "warning" | "alert" | "success";
export type InsightType = "alert" | "trend" | "win" | "tip";

export interface GroundedMetric {
  label: string;
  value: string;
}

export interface Insight {
  id: string;
  title: string;
  description: string;
  severity: InsightSeverity;
  type: InsightType;
  date: string;
  isDismissed: boolean;
  isLiked?: boolean;
  whyExplanation: string;
  groundedData: GroundedMetric[];
  actionLabel?: string;
  actionPath?: string;
}

export interface WeeklyDigest {
  weekRange: string;
  weekLabel?: string;
  summaryTitle: string;
  totalIncome: number;
  totalExpenses: number;
  netSavings: number;
  topCategoryName: string;
  topCategorySpend: number;
  vsLastWeekPct: number;
  bullets: string[];
  actionableTip: string;
  anomaliesDetectedCount: number;
}

export interface ChatMessage {
  id: string;
  role?: "user" | "assistant";
  sender?: "user" | "ai";
  content?: string;
  text?: string;
  timestamp: string;
  groundedData?: GroundedMetric[];
  confidence?: "High" | "Medium" | "Low";
  confidenceBand?: "high" | "medium" | "low" | "High" | "Medium" | "Low";
  confidenceScore?: number;
  isStreaming?: boolean;
  quickActions?: {
    label: string;
    action?: string;
    path?: string;
  }[];
}

export interface Scenario {
  id?: string;
  name: string;
  monthlyIncomeDelta?: number;
  monthlyExpenseDelta?: number;
  incomeChangePct?: number; // e.g. +10 or -20
  oneTimeExpense: number; // e.g. 5000
  monthlySavingsChange?: number; // e.g. +200
  expenseCutCategory?: string;
  expenseCutPct?: number; // e.g. 20
  monthsWithoutIncome: number; // e.g. 3
  createdAt?: string;
}

export type SimulationScenario = Scenario;

export interface ScenarioResultPoint {
  month: string;
  baseline: number;
  scenario: number;
}

export interface GoalImpact {
  goalId: string;
  goalName: string;
  originalMonths: number;
  newMonths: number;
  delayedMonths: number;
  impactMonths?: number;
  newTargetDate?: string;
}

export interface ScenarioResult {
  scenarioId: string;
  baselineRunwayMonths: number;
  scenarioRunwayMonths: number;
  baselineNetWorth12m: number;
  scenarioNetWorth12m: number;
  monthlyPoints: ScenarioResultPoint[];
  goalImpacts: GoalImpact[];
}

export type SimulationResult = ScenarioResult;

export type CurrencyCode = "USD" | "EUR" | "GBP" | "INR";

export interface UserProfile {
  name: string;
  email: string;
  avatarUrl: string;
  currency: CurrencyCode;
  theme: "dark" | "light";
  firstDayOfMonth: number;
  notificationsEnabled: boolean;
  chatPersonality: "concise" | "balanced" | "detailed";
  shareDataForAnalytics: boolean;
  is2FAEnabled: boolean;
  pinCode: string;
}

export interface DashboardSummary {
  netWorth: number;
  netWorthMomPct: number;
  monthlySpending: number;
  monthlyBudgetTotal: number;
  monthlySpendVsBudgetPct: number;
  cashRunwayMonths: number;
  savingsRatePct: number;
  savingsRateMomDelta: number;
  totalLiquidCash: number;
  totalDebt: number;
  cashFlowHistory: {
    month: string;
    income: number;
    expenses: number;
    savings: number;
  }[];
  categorySpend: {
    categoryId: string;
    categoryName: string;
    color: string;
    amount: number;
    percentage: number;
    budget: number;
  }[];
  recentTransactions: Transaction[];
  upcomingBills: {
    id: string;
    merchant: string;
    amount: number;
    dueDate: string;
    categoryId: string;
    accountName: string;
    daysAway: number;
  }[];
  lowBalanceAlert: {
    hasLowBalance: boolean;
    date?: string;
    predictedBalance?: number;
    threshold?: number;
    suggestedAction?: string;
  };
}
