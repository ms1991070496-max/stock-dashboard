const BASE = "";

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export async function searchStocks(q: string): Promise<import("./types").StockInfo[]> {
  return fetchJson(`/api/v1/stocks/search?q=${encodeURIComponent(q)}`);
}

export async function getStockInfo(code: string): Promise<import("./types").StockInfo> {
  return fetchJson(`/api/v1/stocks/${code}/info`);
}

export async function getStockKline(code: string, days = 365): Promise<import("./types").KLineItem[]> {
  return fetchJson(`/api/v1/stocks/${code}/kline?days=${days}`);
}

export async function getStockQuote(code: string): Promise<import("./types").QuoteItem> {
  return fetchJson(`/api/v1/stocks/${code}/quote`);
}

export async function getIndicators(code: string, days = 365): Promise<import("./types").IndicatorResult> {
  return fetchJson(`/api/v1/indicators/${code}?days=${days}`);
}

export async function getNews(market = "cn", limit = 30): Promise<import("./types").NewsItem[]> {
  return fetchJson(`/api/v1/news?market=${market}&limit=${limit}`);
}
