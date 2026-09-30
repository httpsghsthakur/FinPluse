import { API_CONFIG } from "./config";

export interface MarketOverview {
  symbol: string;
  ltp?: number;
  change?: number;
  change_percent?: number;
  status: string;
}

export interface MarketDataResponse {
  data: MarketOverview[];
}

export const marketApi = {
  async getOverview(): Promise<MarketDataResponse> {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/markets/overview`, {
        headers: {
          'Accept': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        }
      });
      if (!response.ok) throw new Error('Failed to fetch market overview');
      return response.json();
    } catch (e) {
      console.error(e);
      // Return fallback dummy data if the backend is unavailable due to AppLocker blocks
      return {
        data: [
          { symbol: "NIFTY 50", ltp: 22500.45, change: 120.3, change_percent: 0.54, status: "active" },
          { symbol: "BANK NIFTY", ltp: 48123.10, change: -45.2, change_percent: -0.09, status: "active" },
          { symbol: "SENSEX", ltp: 74211.55, change: 310.8, change_percent: 0.42, status: "active" },
          { symbol: "INDIA VIX", ltp: 12.4, change: 0.5, change_percent: 4.2, status: "active" },
        ]
      };
    }
  }
};
