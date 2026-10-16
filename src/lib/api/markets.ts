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

export interface CandleData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  sma_20?: number | null;
  sma_50?: number | null;
  ema_20?: number | null;
  ema_50?: number | null;
  rsi?: number | null;
  rsi_14?: number | null;
  macd?: number | null;
  macd_signal?: number | null;
  macd_histogram?: number | null;
}

export interface ForecastPoint {
  date: string;
  predicted: number;
  lower?: number;
  upper?: number;
}

export interface EvaluationMetrics {
  mae: number;
  rmse: number;
  test_points?: number;
  evaluation_period?: string;
}

export interface ProphetForecastResponse {
  status: "success" | "error";
  model: string;
  horizon_days: number;
  history_points: number;
  last_actual_price: number;
  projected_price: number;
  projected_change_percent: number;
  forecast: ForecastPoint[];
  metrics?: EvaluationMetrics | null;
  message?: string;
}

export interface LSTMForecastResponse {
  status: "success" | "error";
  model: string;
  horizon_days: number;
  history_points: number;
  last_actual_price: number;
  projected_price: number;
  projected_change_percent: number;
  forecast: ForecastPoint[];
  metrics?: EvaluationMetrics | null;
  parameters?: {
    sequence_length: number;
    epochs: number;
    batch_size: number;
  };
  message?: string;
}

export interface StockAnalyticsResponse {
  symbol: string;
  timeframe: string;
  quote: StockItem;
  candles: CandleData[];
  indicators_summary: {
    has_sma: boolean;
    has_ema: boolean;
    has_rsi: boolean;
    has_macd: boolean;
  };
  prophet_forecast?: ProphetForecastResponse | null;
  lstm_forecast?: LSTMForecastResponse | null;
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
  ): Promise<{ data: CandleData[] }> {
    const to = toDate || new Date().toISOString().split("T")[0];
    const from = fromDate || new Date(Date.now() - 90 * 86400000).toISOString().split("T")[0];
    try {
      const url = `${API_CONFIG.BASE_URL}/markets/stocks/${encodeURIComponent(symbolOrKey)}/candles?from_date=${from}&to_date=${to}&include_technicals=${includeTechnicals}`;
      const response = await fetch(url, { headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error("Failed to fetch stock candles");
      return response.json();
    } catch (e) { throw e; }
  },

  async getProphetForecast(symbolOrKey: string, horizonDays = 30): Promise<ProphetForecastResponse> {
    const url = `${API_CONFIG.BASE_URL}/markets/stocks/${encodeURIComponent(symbolOrKey)}/forecast/prophet?horizon_days=${horizonDays}`;
    const response = await fetch(url, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("Failed to fetch Prophet forecast");
    return response.json();
  },

  async getLstmForecast(symbolOrKey: string, horizonDays = 14, seqLength = 15): Promise<LSTMForecastResponse> {
    const url = `${API_CONFIG.BASE_URL}/markets/stocks/${encodeURIComponent(symbolOrKey)}/forecast/lstm?horizon_days=${horizonDays}&seq_length=${seqLength}`;
    const response = await fetch(url, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("Failed to fetch LSTM forecast");
    return response.json();
  },

  async getStockAnalytics(symbolOrKey: string, timeframe = "6M"): Promise<StockAnalyticsResponse> {
    const url = `${API_CONFIG.BASE_URL}/markets/stocks/${encodeURIComponent(symbolOrKey)}/analytics?timeframe=${encodeURIComponent(timeframe)}`;
    const response = await fetch(url, { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("Failed to fetch stock analytics");
    return response.json();
  },
};
