/** Demo data mirroring core/fetchers/demo_data.py — for Vercel serverless runtime. */

const DEMO_STOCKS: Record<string, { name: string; market: string; startPrice: number; volatility: number; seed: number }> = {
  // A股
  "600519": { name: "贵州茅台", market: "cn", startPrice: 1800, volatility: 0.015, seed: 519 },
  "000858": { name: "五粮液", market: "cn", startPrice: 150, volatility: 0.02, seed: 858 },
  "300750": { name: "宁德时代", market: "cn", startPrice: 200, volatility: 0.025, seed: 750 },
  "002594": { name: "比亚迪", market: "cn", startPrice: 280, volatility: 0.022, seed: 594 },
  "601899": { name: "紫金矿业", market: "cn", startPrice: 18, volatility: 0.025, seed: 899 },
  "600036": { name: "招商银行", market: "cn", startPrice: 42, volatility: 0.018, seed: 36 },
  // 美股
  "AAPL": { name: "Apple Inc.", market: "us", startPrice: 220, volatility: 0.015, seed: 42 },
  "MSFT": { name: "Microsoft", market: "us", startPrice: 450, volatility: 0.015, seed: 43 },
  "GOOGL": { name: "Alphabet (Google)", market: "us", startPrice: 180, volatility: 0.018, seed: 44 },
  "TSLA": { name: "Tesla", market: "us", startPrice: 250, volatility: 0.035, seed: 45 },
  "NVDA": { name: "NVIDIA", market: "us", startPrice: 130, volatility: 0.03, seed: 46 },
  "META": { name: "Meta Platforms", market: "us", startPrice: 600, volatility: 0.02, seed: 47 },
  "AMZN": { name: "Amazon", market: "us", startPrice: 220, volatility: 0.018, seed: 48 },
  // 港股
  "0700": { name: "腾讯控股", market: "hk", startPrice: 480, volatility: 0.02, seed: 700 },
  "9988": { name: "阿里巴巴-SW", market: "hk", startPrice: 130, volatility: 0.025, seed: 88 },
  "1810": { name: "小米集团-W", market: "hk", startPrice: 40, volatility: 0.028, seed: 10 },
  "3690": { name: "美团-W", market: "hk", startPrice: 160, volatility: 0.03, seed: 90 },
  "9618": { name: "京东集团-SW", market: "hk", startPrice: 140, volatility: 0.025, seed: 18 },
  "9888": { name: "百度集团-SW", market: "hk", startPrice: 100, volatility: 0.025, seed: 888 },
  "2015": { name: "理想汽车-W", market: "hk", startPrice: 100, volatility: 0.035, seed: 15 },
};

const SEARCH_ALIASES: Record<string, string[]> = {
  "小米": ["1810"], "腾讯": ["0700"], "阿里": ["9988"], "美团": ["3690"],
  "京东": ["9618"], "百度": ["9888"], "理想": ["2015"], "比亚迪": ["002594"],
  "茅台": ["600519"], "五粮液": ["000858"], "宁德": ["300750"], "紫金": ["601899"],
  "招商": ["600036"], "谷歌": ["GOOGL"], "脸书": ["META"], "亚马逊": ["AMZN"],
  "微软": ["MSFT"], "英伟达": ["NVDA"], "特斯拉": ["TSLA"],
};

// Simple deterministic PRNG
function mulberry32(seed: number) {
  return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}

/** Box-Muller transform: uniform → normal(mean, std) */
function normalRand(rand: () => number, mean = 0, std = 1): number {
  const u1 = rand() || 0.0001;
  const u2 = rand() || 0.0001;
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  return z * std + mean;
}

export function generateKline(days: number, startPrice: number, volatility: number, seed: number) {
  const rand = mulberry32(seed);
  let price = startPrice;
  const today = new Date();
  const klines = [];

  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().slice(0, 10);

    const ret = normalRand(rand, 0.0005, volatility);
    price = price * Math.exp(ret);

    const intraRange = price * (0.005 + rand() * 0.025);
    const high = price + rand() * intraRange;
    const low = price - rand() * intraRange;
    const open = low + rand() * (high - low);
    const volume = Math.floor(1_000_000 + rand() * 49_000_000);

    klines.push({
      date: dateStr, open: round(open), high: round(high),
      low: round(low), close: round(price), volume,
      amount: round(price * volume / 100), turnover_rate: round(rand() * 3, 2),
    });
  }
  return klines;
}

export function getDemoKline(code: string, days = 365) {
  const stock = DEMO_STOCKS[code] || { startPrice: 100, volatility: 0.02, seed: 0 };
  return generateKline(days, stock.startPrice, stock.volatility, stock.seed);
}

export function getDemoInfo(code: string) {
  const stock = DEMO_STOCKS[code] || { name: code, market: "us" };
  return { code, name: stock.name, market: stock.market, sector: "", industry: "" };
}

export function getDemoQuote(code: string) {
  const stock = DEMO_STOCKS[code] || { name: code, market: "us", startPrice: 100, volatility: 0.02, seed: 0 };
  const klines = generateKline(2, stock.startPrice, stock.volatility, stock.seed);
  const today = klines[klines.length - 1];
  const yesterday = klines[klines.length - 2];
  const price = today.close;
  const preClose = yesterday.close;
  const changePct = round(((price - preClose) / preClose) * 100, 2);
  return {
    code, name: stock.name, price, change_pct: changePct,
    volume: today.volume,
    high: today.high, low: today.low, open: today.open, pre_close: preClose,
  };
}

export function searchDemo(keyword: string) {
  const results: Array<{ code: string; name: string; market: string; price: number; change_pct: number }> = [];
  const seen = new Set<string>();
  const kw = keyword.trim();

  // Aliases
  for (const [alias, codes] of Object.entries(SEARCH_ALIASES)) {
    if (kw.includes(alias) || alias.includes(kw)) {
      for (const code of codes) {
        if (!seen.has(code) && DEMO_STOCKS[code]) {
          seen.add(code);
          const q = getDemoQuote(code);
          results.push({ code, name: q.name, market: DEMO_STOCKS[code].market, price: q.price, change_pct: q.change_pct });
        }
      }
    }
  }

  // Direct match
  const kwUpper = kw.toUpperCase();
  for (const [code, info] of Object.entries(DEMO_STOCKS)) {
    if (seen.has(code)) continue;
    if (code.includes(kwUpper) || info.name.includes(kw) || info.name.toUpperCase().includes(kwUpper)) {
      const q = getDemoQuote(code);
      results.push({ code, name: info.name, market: info.market, price: q.price, change_pct: q.change_pct });
    }
  }
  return results;
}

function round(v: number, d = 2) { return Number(v.toFixed(d)); }

/** Compute SMA */
function sma(data: number[], period: number): (number | null)[] {
  const result: (number | null)[] = new Array(data.length).fill(null);
  if (data.length < period) return result;
  let sum = 0;
  for (let i = 0; i < period; i++) sum += data[i];
  result[period - 1] = sum / period;
  for (let i = period; i < data.length; i++) {
    sum = sum - data[i - period] + data[i];
    result[i] = sum / period;
  }
  return result;
}

/** Compute EMA */
function ema(data: number[], period: number): (number | null)[] {
  const result: (number | null)[] = new Array(data.length).fill(null);
  if (data.length < period) return result;
  const k = 2 / (period + 1);
  result[period - 1] = data.slice(0, period).reduce((a, b) => a + b, 0) / period;
  for (let i = period; i < data.length; i++) {
    result[i] = (data[i] - result[i - 1]!) * k + result[i - 1]!;
  }
  return result;
}

/** Compute all technical indicators */
export function computeIndicators(klines: Array<{ open: number; high: number; low: number; close: number; volume: number }>) {
  const n = klines.length;
  const close = klines.map(k => k.close);
  const high = klines.map(k => k.high);
  const low = klines.map(k => k.low);
  const volume = klines.map(k => k.volume);

  const ma5 = sma(close, 5);
  const ma10 = sma(close, 10);
  const ma20 = sma(close, 20);
  const ma60 = sma(close, 60);

  // MACD
  const ema12 = ema(close, 12);
  const ema26 = ema(close, 26);
  const dif = close.map((_, i) => ema12[i] != null && ema26[i] != null ? ema12[i]! - ema26[i]! : null);
  const dea = ema(dif.map(v => v ?? 0), 9);
  const hist = dif.map((v, i) => v != null && dea[i] != null ? v - dea[i]! : null);

  // RSI
  const rsi14 = rsi(close, 14);
  const rsi6 = rsi(close, 6);
  const rsi24 = rsi(close, 24);

  // Bollinger
  const bollMid = ma20;
  const bollUpper: (number | null)[] = new Array(n).fill(null);
  const bollLower: (number | null)[] = new Array(n).fill(null);
  for (let i = 19; i < n; i++) {
    const slice = close.slice(i - 19, i + 1);
    const avg = slice.reduce((a, b) => a + b, 0) / 20;
    const std = Math.sqrt(slice.reduce((s, v) => s + (v - avg) ** 2, 0) / 20);
    bollUpper[i] = avg + 2 * std;
    bollLower[i] = avg - 2 * std;
  }

  // KDJ
  const kdjRes: { k: (number | null)[]; d: (number | null)[]; j: (number | null)[] } = { k: new Array(n).fill(null), d: new Array(n).fill(null), j: new Array(n).fill(null) };
  const rsv: (number | null)[] = new Array(n).fill(null);
  for (let i = 8; i < n; i++) {
    const h = Math.max(...high.slice(i - 8, i + 1));
    const l = Math.min(...low.slice(i - 8, i + 1));
    rsv[i] = h !== l ? ((close[i] - l) / (h - l)) * 100 : 50;
  }
  const kSm = sma(rsv.map(v => v ?? 50), 3);
  const dSm = sma(kSm.map(v => v ?? 50), 3);
  for (let i = 0; i < n; i++) {
    kdjRes.k[i] = kSm[i];
    kdjRes.d[i] = dSm[i];
    if (kSm[i] != null && dSm[i] != null) kdjRes.j[i] = 3 * kSm[i]! - 2 * dSm[i]!;
  }

  // OBV
  const obv: (number | null)[] = new Array(n).fill(null);
  obv[0] = volume[0];
  for (let i = 1; i < n; i++) {
    if (close[i] > close[i - 1]) obv[i] = obv[i - 1]! + volume[i];
    else if (close[i] < close[i - 1]) obv[i] = obv[i - 1]! - volume[i];
    else obv[i] = obv[i - 1];
  }

  return { ma5, ma10, ma20, ma60, macd_dif: dif, macd_dea: dea, macd_hist: hist, rsi6, rsi14, rsi24, boll_upper: bollUpper, boll_mid: bollMid, boll_lower: bollLower, kdj_k: kdjRes.k, kdj_d: kdjRes.d, kdj_j: kdjRes.j, obv };
}

function rsi(close: number[], period: number): (number | null)[] {
  const n = close.length;
  const result: (number | null)[] = new Array(n).fill(null);
  if (n <= period) return result;

  const gains: number[] = [];
  const losses: number[] = [];
  for (let i = 1; i < n; i++) {
    const delta = close[i] - close[i - 1];
    gains.push(delta > 0 ? delta : 0);
    losses.push(delta < 0 ? -delta : 0);
  }

  let avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period;
  let avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period;
  result[period] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);

  for (let i = period + 1; i < n; i++) {
    avgGain = (avgGain * (period - 1) + gains[i - 1]) / period;
    avgLoss = (avgLoss * (period - 1) + losses[i - 1]) / period;
    result[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  }
  return result;
}
