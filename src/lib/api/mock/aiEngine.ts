import { ChatMessage, GroundedMetric } from "../../../types";
import { StorageData } from "./seed";
import { formatCurrency, formatPercent } from "../../utils/formatters";
import { subDays, parseISO, isBefore } from "date-fns";

interface AIResponseResult {
  content: string;
  groundedData?: GroundedMetric[];
  confidence?: "High" | "Medium" | "Low";
  quickActions?: {
    label: string;
    action: string;
    path?: string;
  }[];
}

export function generateAICopilotResponse(
  query: string,
  data: StorageData,
  personality: "concise" | "balanced" | "detailed" = "balanced",
): AIResponseResult {
  const q = query.toLowerCase();

  // Compute live financial figures from data
  const totalChecking =
    data.accounts.find((a) => a.type === "checking")?.balance || 0;
  const totalSavings =
    data.accounts.find((a) => a.type === "savings")?.balance || 0;
  const totalCredit =
    data.accounts.find((a) => a.type === "credit")?.balance || 0;
  const liquidCash = totalChecking + totalSavings;
  const netWorth = liquidCash + totalCredit; // totalCredit is negative

  // ── Compute 30-day spending & income from REAL date-filtered transactions ──
  const today = new Date();
  const thirtyDaysAgo = subDays(today, 30);

  const recent30DaysTx = data.transactions.filter((t) => {
    const d = parseISO(t.date);
    return !isBefore(d, thirtyDaysAgo);
  });

  const totalExpense30d = Math.abs(
    recent30DaysTx
      .filter((t) => t.amount < 0 && t.categoryId !== "cat-transfers")
      .reduce((acc, t) => acc + t.amount, 0),
  );
  const totalIncome30d = recent30DaysTx
    .filter((t) => t.amount > 0)
    .reduce((acc, t) => acc + t.amount, 0);
  const monthlyBurn = totalExpense30d > 0 ? totalExpense30d : 0;
  const runwayMonths =
    monthlyBurn > 0 ? (liquidCash / monthlyBurn).toFixed(1) : "N/A";
  const savingsRate =
    totalIncome30d > 0
      ? Math.max(0, ((totalIncome30d - totalExpense30d) / totalIncome30d) * 100)
      : 0;

  // Category breakdown from REAL filtered transactions
  const diningTx = recent30DaysTx.filter((t) => t.categoryId === "cat-dining");
  const diningSpend = Math.abs(diningTx.reduce((acc, t) => acc + t.amount, 0));
  const diningBudget =
    data.categories.find((c) => c.id === "cat-dining")?.monthlyBudget || 8000;

  const groceryTx = recent30DaysTx.filter(
    (t) => t.categoryId === "cat-groceries",
  );
  const grocerySpend = Math.abs(
    groceryTx.reduce((acc, t) => acc + t.amount, 0),
  );

  const shoppingTx = recent30DaysTx.filter(
    (t) => t.categoryId === "cat-shopping",
  );
  const shoppingSpend = Math.abs(
    shoppingTx.reduce((acc, t) => acc + t.amount, 0),
  );

  // 1. "Can I afford" / "afford" query
  if (
    q.includes("afford") ||
    q.includes("buy") ||
    q.includes("purchase") ||
    q.includes("get") ||
    q.includes("spend")
  ) {
    let amountToTest = 0;
    let itemName = "Proposed Purchase";

    // Multiplier parsing (50k, 1.5L, 2 Lakh, etc.)
    const kMatch = q.match(/(\d+(?:\.\d+)?)\s*(?:k|thousand)/);
    const lMatch = q.match(/(\d+(?:\.\d+)?)\s*(?:l|lac|lakh|lakhs)/);
    const crMatch = q.match(/(\d+(?:\.\d+)?)\s*(?:cr|crore|crores)/);
    const numMatch = q.match(/(?:₹|\$|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)/);

    if (kMatch) {
      amountToTest = parseFloat(kMatch[1]) * 1000;
    } else if (lMatch) {
      amountToTest = parseFloat(lMatch[1]) * 100000;
    } else if (crMatch) {
      amountToTest = parseFloat(crMatch[1]) * 10000000;
    } else if (numMatch && parseFloat(numMatch[1].replace(/,/g, "")) > 10) {
      amountToTest = parseFloat(numMatch[1].replace(/,/g, ""));
    } else {
      // Semantic item lookup
      const itemPrices: [RegExp, number, string][] = [
        [/\b(iphone\s*1[567]?(?:\s*pro(?:\s*max)?)?|flagship\s*phone)\b/, 125000, "Flagship Smartphone"],
        [/\b(phone|smartphone|mobile|android|pixel|samsung)\b/, 65000, "New Smartphone"],
        [/\b(macbook\s*(?:pro|air|m[1-4])?|gaming\s*laptop)\b/, 145000, "Laptop / MacBook"],
        [/\b(laptop|computer|pc|ipad|tablet)\b/, 75000, "Personal Computer / Tablet"],
        [/\b(car|suv|sedan|vehicle|automobile)\b/, 850000, "New Car / Vehicle"],
        [/\b(bike|motorcycle|scooter|ev\s*scooter)\b/, 130000, "Two-Wheeler / Bike"],
        [/\b(trip|vacation|holiday|bali|europe|flight|tour)\b/, 95000, "Vacation / Travel Trip"],
        [/\b(watch|apple\s*watch|smartwatch)\b/, 42000, "Smartwatch / Wearable"],
        [/\b(ps5|playstation|xbox|gaming\s*console)\b/, 55000, "Gaming Console"],
        [/\b(tv|television|oled|projector)\b/, 65000, "Smart TV / Home Entertainment"],
        [/\b(dinner|party|club|restaurant|fine\s*dining)\b/, 4500, "Dining Outing"],
        [/\b(shoes|sneakers|jacket|clothes|shopping)\b/, 8500, "Retail / Apparel"],
        [/\b(gym|cult|fitness\s*membership)\b/, 18000, "Annual Gym Membership"],
      ];

      for (const [pattern, price, label] of itemPrices) {
        if (pattern.test(q)) {
          amountToTest = price;
          itemName = label;
          break;
        }
      }

      if (!amountToTest) {
        amountToTest = 45000;
        itemName = "Discretionary Purchase";
      }
    }

    const postPurchaseChecking = totalChecking - amountToTest;
    const isSafe = postPurchaseChecking > 25000;

    if (personality === "concise") {
      return {
        content: isSafe
          ? `**Yes, you can afford ${itemName} (${formatCurrency(amountToTest)}).** Your checking account retains **${formatCurrency(postPurchaseChecking)}**, and your overall cash runway remains **${runwayMonths} months**.`
          : `**Caution on purchasing ${itemName} (${formatCurrency(amountToTest)}).** This would reduce your checking cushion to **${formatCurrency(postPurchaseChecking)}**, dropping below your ideal 1-month liquid reserve (₹25,000).`,
        groundedData: [
          { label: "Proposed Purchase", value: formatCurrency(amountToTest) },
          { label: "Current Checking", value: formatCurrency(totalChecking) },
          {
            label: "Post-Purchase Buffer",
            value: formatCurrency(postPurchaseChecking),
          },
          { label: "Liquid Runway", value: `${runwayMonths} Mo` },
        ],
        confidence: "High",
        quickActions: [
          {
            label: "Simulate in What-If",
            action: "navigate",
            path: "/app/simulator",
          },
          {
            label: "View Checking Balance",
            action: "navigate",
            path: "/app/forecast",
          },
        ],
      };
    }

    return {
      content: `### Affordability Assessment: ${itemName} (${formatCurrency(amountToTest)})
Based on your real-time liquidity and automated cash-flow obligations:

1. **Checking Account Liquidity**: You currently hold **${formatCurrency(totalChecking)}** in your primary checking.
2. **Buffer After Purchase**: Deducting ${formatCurrency(amountToTest)} leaves **${formatCurrency(postPurchaseChecking)}** in liquid checking reserves.
3. **Emergency Runway**: Your total savings (${formatCurrency(totalSavings)}) guarantees **${runwayMonths} months of liquid runway**.
4. **Recommendation**: ${
        isSafe
          ? `**Comfortable to proceed.** Your safety cushion remains well above baseline, and this purchase fits cleanly within your cash-flow plan.`
          : `**Exercise caution.** Consider delaying until your next paycheck, or transferring from discretionary allocation.`
      }`,
      groundedData: [
        { label: "Proposed Item", value: formatCurrency(amountToTest) },
        { label: "Checking Balance", value: formatCurrency(totalChecking) },
        { label: "Savings Backup", value: formatCurrency(totalSavings) },
        { label: "Monthly Burn Rate", value: formatCurrency(monthlyBurn) },
      ],
      confidence: "High",
      quickActions: [
        {
          label: "Simulate Purchase Impact",
          action: "navigate",
          path: "/app/simulator",
        },
        { label: "Check Upcoming Bills", action: "navigate", path: "/app" },
      ],
    };
  }

  // 2. Spending comparison / "how is my spending"
  if (
    q.includes("spending") ||
    q.includes("spent") ||
    q.includes("dining") ||
    q.includes("groceries") ||
    q.includes("breakdown")
  ) {
    const isDiningOver = diningSpend > diningBudget;
    return {
      content: `### Monthly Spending & Category Health

Here is your verified 30-day outflow breakdown across top active categories:

- **Dining & Drinks**: **${formatCurrency(diningSpend)}** (${isDiningOver ? "Over budget by " + formatCurrency(diningSpend - diningBudget) : "Within limit of " + formatCurrency(diningBudget)})
- **Groceries**: **${formatCurrency(grocerySpend)}** (Target: ${formatCurrency(data.categories.find((c) => c.id === "cat-groceries")?.monthlyBudget || 0)})
- **Shopping & Gear**: **${formatCurrency(shoppingSpend)}** (Target: ${formatCurrency(data.categories.find((c) => c.id === "cat-shopping")?.monthlyBudget || 0)})
- **Total Discretionary Burn**: **${formatCurrency(totalExpense30d)}**

${
  isDiningOver
    ? `> **AI Alert**: Dining pace is currently **${((diningSpend / diningBudget) * 100).toFixed(0)}% of your monthly budget**. We recommend swapping 2 weekend dinners for cooking to save ~₹1,500 this month.`
    : `> **On Track**: Your overall spending pace is well within your calculated income baseline.`
}`,
      groundedData: [
        { label: "30-Day Outflows", value: formatCurrency(totalExpense30d) },
        { label: "Dining Spend", value: formatCurrency(diningSpend) },
        { label: "Dining Budget", value: formatCurrency(diningBudget) },
        { label: "Savings Rate", value: formatPercent(savingsRate, false) },
      ],
      confidence: "High",
      quickActions: [
        { label: "Open Budgets", action: "navigate", path: "/app/budgets" },
        {
          label: "View Dining Transactions",
          action: "navigate",
          path: "/app/transactions",
        },
      ],
    };
  }

  // 3. Runway / Net Worth / Cash Flow query
  if (
    q.includes("runway") ||
    q.includes("net worth") ||
    q.includes("cash flow") ||
    q.includes("balance")
  ) {
    return {
      content: `### Net Worth & Runway Diagnostics

- **Total Net Worth**: **${formatCurrency(netWorth)}**
- **Liquid Cash Reserves**: **${formatCurrency(liquidCash)}** (Checking: ${formatCurrency(totalChecking)} + Savings: ${formatCurrency(totalSavings)})
- **Credit Card Liability**: **${formatCurrency(Math.abs(totalCredit))}**
- **Calculated Cash Runway**: **${runwayMonths} months** without any new income.
- **Current Savings Rate**: **${savingsRate.toFixed(1)}%** based on last 30 days of real transactions.

Your financial cushion is ${Number(runwayMonths) >= 6 ? "in the **top tier (6+ months threshold)**" : `at **${runwayMonths} months** — consider building reserves`}.`,
      groundedData: [
        { label: "Net Worth", value: formatCurrency(netWorth) },
        { label: "Liquid Cash", value: formatCurrency(liquidCash) },
        { label: "Monthly Burn", value: formatCurrency(monthlyBurn) },
        { label: "Runway", value: `${runwayMonths} Months` },
      ],
      confidence: "High",
      quickActions: [
        {
          label: "Open Cash Flow Forecast",
          action: "navigate",
          path: "/app/forecast",
        },
        { label: "Review Accounts", action: "navigate", path: "/app/settings" },
      ],
    };
  }

  // 4. Goals / Savings query
  if (
    q.includes("goal") ||
    q.includes("emergency fund") ||
    q.includes("save") ||
    q.includes("trip") ||
    q.includes("house")
  ) {
    const goalsList = data.goals
      .map((g) => {
        const pct = ((g.currentAmount / g.targetAmount) * 100).toFixed(0);
        const remaining = g.targetAmount - g.currentAmount;
        const monthsLeft = (remaining / (g.monthlyContribution || 100)).toFixed(
          1,
        );
        return `- **${g.name}**: **${formatCurrency(g.currentAmount)}** of ${formatCurrency(g.targetAmount)} (${pct}%) — ETA **~${monthsLeft} months** at ${formatCurrency(g.monthlyContribution)}/mo`;
      })
      .join("\n");

    return {
      content: `### Savings Goals Trajectory

Here is the progress and estimated completion timeline for your active goals:

${goalsList}

**Optimization Tip**: Review your spending categories to identify potential reallocation toward your highest-priority goal.`,
      groundedData: [
        { label: "Active Goals", value: `${data.goals.length}` },
        {
          label: "Total Saved for Goals",
          value: formatCurrency(
            data.goals.reduce((a, b) => a + b.currentAmount, 0),
          ),
        },
        {
          label: "Monthly Goal Outflows",
          value: formatCurrency(
            data.goals.reduce((a, b) => a + b.monthlyContribution, 0),
          ),
        },
      ],
      confidence: "High",
      quickActions: [
        { label: "Manage Goals", action: "navigate", path: "/app/goals" },
        {
          label: "Adjust Contributions",
          action: "navigate",
          path: "/app/budgets",
        },
      ],
    };
  }

  // 5. General fallback financial inquiry
  return {
    content: `### Finpluse AI Financial Assessment

Here is a live snapshot grounded in your connected accounts:

- **Net Worth**: **${formatCurrency(netWorth)}** across ${data.accounts.length} linked accounts.
- **Available Liquidity**: **${formatCurrency(liquidCash)}** (${runwayMonths} months cash runway).
- **Current Savings Rate**: **${savingsRate.toFixed(1)}%** of monthly income.
- **30-Day Spending**: **${formatCurrency(totalExpense30d)}** across ${recent30DaysTx.filter((t) => t.amount < 0).length} expense transactions.

Feel free to ask me to analyze specific transactions, test a what-if scenario, or compute your goal achievement dates!`,
    groundedData: [
      { label: "Net Worth", value: formatCurrency(netWorth) },
      { label: "Liquid Runway", value: `${runwayMonths} Mo` },
      { label: "Transactions (30d)", value: `${recent30DaysTx.length}` },
      { label: "Connected Accounts", value: `${data.accounts.length}` },
    ],
    confidence: "High",
    quickActions: [
      {
        label: "Explore What-If Simulator",
        action: "navigate",
        path: "/app/simulator",
      },
      {
        label: "View Insights Feed",
        action: "navigate",
        path: "/app/insights",
      },
    ],
  };
}
