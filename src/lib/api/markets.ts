import { API_CONFIG } from "./config";

export interface IndexItem {
  name: string;
  symbol: string;
  value: string;
  ltp: number;
  change: string;
  changePct: string;
  change_percent: number;
  isUp: boolean;
  status: string;
  isIndian?: boolean;
}

export interface SectorItem {
  name: string;
  performance: string;
  changePct: number;
  isUp: boolean;
  weight: string;
}

export interface MarketOverview {
  name?: string;
  symbol: string;
  value?: string;
  ltp?: number;
  change?: number | string;
  changePct?: string;
  change_percent?: number;
  isUp?: boolean;
  status: string;
}

export interface MarketDataResponse {
  data: MarketOverview[];
  indices?: IndexItem[];
  sectors?: SectorItem[];
  timestamp?: number;
}

export interface StockItem {
  symbol: string;
  name: string;
  instrument_key: string;
  ticker: string;
  ltp: number;
  price: number;
  change: number;
  change_percent: number;
  high?: number;
  low?: number;
  volume: number;
  is_up: boolean;
}

export interface PredictionItem {
  symbol: string;
  name: string;
  instrument_key?: string;
  direction: "UP" | "DOWN" | "NEUTRAL";
  probability: number;
  probabilities?: {
    UP: number;
    DOWN: number;
    NEUTRAL: number;
  };
  volatility: "LOW" | "MODERATE" | "HIGH";
  volatility_value?: number;
  expectedReturn: string;
  timeframe: string;
}

export interface ModelMetricsResponse {
  status: string;
  data: {
    dataset_split?: {
      train_rows: number;
      train_date_range: [string, string];
      val_rows: number;
      val_date_range: [string, string];
      test_rows: number;
      test_date_range: [string, string];
    };
    xgboost_3class_test_metrics?: {
      accuracy: number;
      macro_avg_precision: number;
      macro_avg_recall: number;
      macro_avg_f1: number;
      per_class: Record<string, { precision: number; recall: number; f1_score: number; support: number }>;
      confusion_matrix: number[][];
      classes: string[];
    };
    naive_baselines?: {
      majority_class: { class_chosen: string; accuracy: number; macro_f1: number };
      momentum_5d_persistence: { accuracy: number; macro_f1: number };
    };
    top_features?: Array<{ feature: string; importance: number }>;
    limitations?: string;
  };
}

export const marketApi = {
  async getOverview(): Promise<MarketDataResponse> {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/markets/overview`, {
        headers: {
          Accept: "application/json",
          Authorization: `Bearer ${localStorage.getItem("token") || ""}`,
        },
      });
      if (!response.ok) throw new Error("Failed to fetch market overview");
      return response.json();
    } catch (e) { throw e; }
  },

  async getTopStocks(): Promise<{ data: StockItem[] }> {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/markets/stocks/top`, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("Failed to fetch top stocks");
      return response.json();
    } catch (e) { throw e; }
  },

  async getPredictions(): Promise<{ data: PredictionItem[]; model_name: string }> {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/markets/predictions`, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("Failed to fetch predictions");
      return response.json();
    } catch (e) { throw e; }
  },

  async getMetrics(): Promise<ModelMetricsResponse> {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/markets/metrics`, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("Failed to fetch metrics");
      return response.json();
    } catch (e) { throw e; }
  },

  async searchStocks(q: string): Promise<{ data: Array<{ symbol: string; name: string; instrument_key: string; sector?: string; ticker?: string }> }> {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/markets/stocks/search?q=${encodeURIComponent(q)}`, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("Failed to search stocks");
      return response.json();
    } catch (e) { throw e; }
  },

  async getStockQuote(symbolOrKey: string): Promise<{ data: StockItem }> {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/markets/stocks/${encodeURIComponent(symbolOrKey)}`, {
        headers: { Accept: "application/json" },
      });
      if (!response.ok) throw new Error("Failed to fetch stock quote");
      return response.json();
    } catch (e) { throw e; }
  },

  async getStockCandles(
    symbolOrKey: string,
    fromDate?: string,
    toDate?: string,
    includeTechnicals = true
  ): Promise<{ data: Array<{ timestamp: string; open: number; high: number; low: number; close: number; volume: number; rsi?: number; sma_20?: number; sma_50?: number }> }> {
    const to = toDate || new Date().toISOString().split("T")[0];
    const from = fromDate || new Date(Date.now() - 90 * 86400000).toISOString().split("T")[0];
    try {
      const url = `${API_CONFIG.BASE_URL}/markets/stocks/${encodeURIComponent(symbolOrKey)}/candles?from_date=${from}&to_date=${to}&include_technicals=${includeTechnicals}`;
      const response = await fetch(url, { headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error("Failed to fetch stock candles");
      return response.json();
    } catch (e) { throw e; }
  },
};
