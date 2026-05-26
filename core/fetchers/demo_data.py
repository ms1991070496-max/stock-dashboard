"""Demo data generator for fallback when APIs are unavailable."""

import random
from datetime import date, timedelta

import numpy as np


def generate_kline(days: int = 365, start_price: float = 100.0, volatility: float = 0.02, seed: int = 42) -> list[dict]:
    """Generate realistic-looking K-line data."""
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0005, volatility, days)
    prices = start_price * np.exp(np.cumsum(returns))

    today = date.today()
    klines = []
    for i in range(days):
        d = today - timedelta(days=days - i - 1)
        close = float(prices[i])
        intraday_range = close * rng.uniform(0.005, 0.03)
        high = close + rng.uniform(0, intraday_range)
        low = close - rng.uniform(0, intraday_range)
        open_p = low + rng.uniform(0, high - low)
        volume = rng.integers(1_000_000, 50_000_000)

        klines.append({
            "date": d,
            "open": round(float(open_p), 2),
            "high": round(float(high), 2),
            "low": round(float(low), 2),
            "close": round(float(close), 2),
            "volume": int(volume),
            "amount": round(float(close * volume / 100), 2),
            "turnover_rate": round(rng.uniform(0.1, 3.0), 2),
        })
    return klines


DEMO_STOCKS = {
    # A股
    "600519": {"name": "贵州茅台", "market": "cn", "start_price": 1800, "volatility": 0.015, "seed": 519},
    "000858": {"name": "五粮液", "market": "cn", "start_price": 150, "volatility": 0.02, "seed": 858},
    "300750": {"name": "宁德时代", "market": "cn", "start_price": 200, "volatility": 0.025, "seed": 750},
    "002594": {"name": "比亚迪", "market": "cn", "start_price": 280, "volatility": 0.022, "seed": 594},
    "601899": {"name": "紫金矿业", "market": "cn", "start_price": 18, "volatility": 0.025, "seed": 899},
    "600036": {"name": "招商银行", "market": "cn", "start_price": 42, "volatility": 0.018, "seed": 36},
    # 美股
    "AAPL": {"name": "Apple Inc.", "market": "us", "start_price": 220, "volatility": 0.015, "seed": 42},
    "MSFT": {"name": "Microsoft", "market": "us", "start_price": 450, "volatility": 0.015, "seed": 43},
    "GOOGL": {"name": "Alphabet (Google)", "market": "us", "start_price": 180, "volatility": 0.018, "seed": 44},
    "TSLA": {"name": "Tesla", "market": "us", "start_price": 250, "volatility": 0.035, "seed": 45},
    "NVDA": {"name": "NVIDIA", "market": "us", "start_price": 130, "volatility": 0.03, "seed": 46},
    "META": {"name": "Meta Platforms", "market": "us", "start_price": 600, "volatility": 0.02, "seed": 47},
    "AMZN": {"name": "Amazon", "market": "us", "start_price": 220, "volatility": 0.018, "seed": 48},
    # 港股
    "0700": {"name": "腾讯控股", "market": "hk", "start_price": 480, "volatility": 0.02, "seed": 700},
    "9988": {"name": "阿里巴巴-SW", "market": "hk", "start_price": 130, "volatility": 0.025, "seed": 88},
    "1810": {"name": "小米集团-W", "market": "hk", "start_price": 40, "volatility": 0.028, "seed": 10},
    "3690": {"name": "美团-W", "market": "hk", "start_price": 160, "volatility": 0.03, "seed": 90},
    "9618": {"name": "京东集团-SW", "market": "hk", "start_price": 140, "volatility": 0.025, "seed": 18},
    "9888": {"name": "百度集团-SW", "market": "hk", "start_price": 100, "volatility": 0.025, "seed": 888},
    "2015": {"name": "理想汽车-W", "market": "hk", "start_price": 100, "volatility": 0.035, "seed": 15},
}

# Search aliases: keyword → list of matching codes
SEARCH_ALIASES: dict[str, list[str]] = {
    "小米": ["1810"],
    "腾讯": ["0700"],
    "阿里": ["9988"],
    "美团": ["3690"],
    "京东": ["9618"],
    "百度": ["9888"],
    "理想": ["2015"],
    "比亚迪": ["002594"],
    "茅台": ["600519"],
    "五粮液": ["000858"],
    "宁德": ["300750"],
    "紫金": ["601899"],
    "招商": ["600036"],
    "谷歌": ["GOOGL"],
    "脸书": ["META"],
    "meta": ["META"],
    "亚马": ["AMZN"],
    "amazon": ["AMZN"],
    "apple": ["AAPL"],
    "微软": ["MSFT"],
    "英伟达": ["NVDA"],
    "特斯拉": ["TSLA"],
    "nvidia": ["NVDA"],
    "tesla": ["TSLA"],
}


def get_demo_kline(code: str, days: int = 365) -> list[dict]:
    stock = DEMO_STOCKS.get(code, {"start_price": 100, "volatility": 0.02, "seed": 0})
    return generate_kline(days, stock["start_price"], stock["volatility"], stock["seed"])


def get_demo_info(code: str) -> dict:
    stock = DEMO_STOCKS.get(code, {"name": code, "market": "us"})
    sectors = {"cn": "可选消费", "us": "Technology", "hk": "资讯科技"}
    return {
        "code": code,
        "name": stock["name"],
        "market": stock["market"],
        "sector": sectors.get(stock["market"], ""),
        "industry": "",
    }


def get_demo_realtime(code: str) -> dict:
    stock = DEMO_STOCKS.get(code, {"name": code, "market": "us", "start_price": 100})
    price = stock["start_price"] * (1 + random.uniform(-0.05, 0.05))
    change_pct = random.uniform(-3, 3)
    return {
        "code": code,
        "name": stock["name"],
        "price": round(price, 2),
        "change_pct": round(change_pct, 2),
        "volume": random.randint(1_000_000, 50_000_000),
    }


def search_demo(keyword: str) -> list[dict]:
    results = []
    seen = set()
    kw = keyword.strip()

    # 1. Check aliases first (exact or partial match)
    for alias, codes in SEARCH_ALIASES.items():
        if kw.lower() in alias.lower() or kw in alias:
            for code in codes:
                if code in DEMO_STOCKS and code not in seen:
                    seen.add(code)
                    info = DEMO_STOCKS[code]
                    results.append(_stock_result(code, info))

    # 2. Match against code and name
    kw_upper = kw.upper()
    for code, info in DEMO_STOCKS.items():
        if code in seen:
            continue
        if (kw_upper in code.upper()
                or kw in info["name"]
                or kw.lower() in info["name"].lower()):
            seen.add(code)
            results.append(_stock_result(code, info))

    return results


def _stock_result(code: str, info: dict) -> dict:
    return {
        "code": code,
        "name": info["name"],
        "market": info["market"],
        "price": round(info["start_price"] * random.uniform(0.95, 1.05), 2),
        "change_pct": round(random.uniform(-3, 3), 2),
    }
