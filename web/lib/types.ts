export interface StockInfo {
  code: string;
  name: string;
  market: "cn" | "us" | "hk";
  sector: string;
  industry: string;
}

export interface KLineItem {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount: number;
  turnover_rate: number;
}

export interface QuoteItem {
  code: string;
  name: string;
  price: number;
  change_pct: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  pre_close: number;
}

export interface IndicatorResult {
  code: string;
  name: string;
  klines: KLineItem[];
  ma5: (number | null)[];
  ma10: (number | null)[];
  ma20: (number | null)[];
  ma60: (number | null)[];
  macd_dif: (number | null)[];
  macd_dea: (number | null)[];
  macd_hist: (number | null)[];
  rsi6: (number | null)[];
  rsi14: (number | null)[];
  rsi24: (number | null)[];
  boll_upper: (number | null)[];
  boll_mid: (number | null)[];
  boll_lower: (number | null)[];
  kdj_k: (number | null)[];
  kdj_d: (number | null)[];
  kdj_j: (number | null)[];
  obv: (number | null)[];
}

export interface NewsItem {
  title: string;
  source: string;
  url: string;
  published_at: string | null;
  sentiment_score: number;
}
