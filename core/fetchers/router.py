import logging
from datetime import date
from typing import Optional

import pandas as pd

from core.fetchers.base import BaseFetcher
from core.fetchers.tencent_fetcher import TencentFetcher

logger = logging.getLogger(__name__)

def _make_chain() -> dict[str, list[BaseFetcher]]:
    tx = TencentFetcher()
    chain = {"cn": [tx], "us": [tx], "hk": [tx]}
    try:
        from core.fetchers.akshare_fetcher import AkShareFetcher
        chain["cn"].append(AkShareFetcher())
    except ImportError: pass
    try:
        from core.fetchers.yfinance_fetcher import YFinanceFetcher
        chain["us"].append(YFinanceFetcher())
        chain["hk"].append(YFinanceFetcher())
    except ImportError: pass
    return chain

FETCHER_CHAIN = _make_chain()


class FetcherRouter:
    def __init__(self, chains: dict[str, list[BaseFetcher]] | None = None):
        self._chains = chains or FETCHER_CHAIN

    def _chain_for(self, market: str) -> list[BaseFetcher]:
        return self._chains.get(market, [YFinanceFetcher()])

    async def fetch_kline(self, code: str, market: str, start_date: date | None = None, end_date: date | None = None) -> pd.DataFrame:
        last_err = None
        for fetcher in self._chain_for(market):
            try:
                return await fetcher.fetch_kline(code, start_date, end_date)
            except Exception as e:
                last_err = e
                logger.warning(f"{fetcher.name} kline failed ({code}): {e}")
        raise RuntimeError(f"All fetchers failed for {code} kline: {last_err}")

    async def fetch_realtime(self, code: str, market: str) -> dict:
        for fetcher in self._chain_for(market):
            try:
                return await fetcher.fetch_realtime(code)
            except Exception as e:
                logger.warning(f"{fetcher.name} realtime failed ({code}): {e}")
        return {"code": code, "name": code, "price": 0, "change_pct": 0}

    async def fetch_stock_info(self, code: str, market: str) -> dict:
        for fetcher in self._chain_for(market):
            try:
                return await fetcher.fetch_stock_info(code)
            except Exception as e:
                logger.warning(f"{fetcher.name} info failed ({code}): {e}")
        return {"code": code, "name": code, "market": market}

    async def fetch_financials(self, code: str, market: str) -> pd.DataFrame:
        for fetcher in self._chain_for(market):
            try:
                df = await fetcher.fetch_financials(code)
                if not df.empty:
                    return df
            except Exception as e:
                logger.warning(f"{fetcher.name} financials failed ({code}): {e}")
        return pd.DataFrame()

    async def search_stocks(self, keyword: str, market: str = "all") -> list[dict]:
        results = []
        markets = ["cn", "us", "hk"] if market == "all" else [market]
        for mkt in markets:
            for fetcher in self._chain_for(mkt):
                try:
                    results.extend(await fetcher.search_stocks(keyword))
                    break
                except Exception as e:
                    logger.warning(f"{fetcher.name} search failed: {e}")
        return results

    async def fetch_news(self, code: str | None = None, market: str = "cn", limit: int = 20) -> list[dict]:
        for fetcher in self._chain_for(market):
            try:
                news = await fetcher.fetch_news(code, limit)
                if news:
                    return news
            except Exception as e:
                logger.warning(f"{fetcher.name} news failed: {e}")
        return []

    @staticmethod
    def detect_market(code: str) -> str:
        code = code.strip().upper()
        if code.endswith((".SS", ".SZ")):
            return "cn"
        if code.endswith(".HK"):
            return "hk"
        if code.isdigit():
            if len(code) == 6:
                return "cn"
            if len(code) in (4, 5):
                return "hk"
        return "us"


_router: FetcherRouter | None = None


def get_router() -> FetcherRouter:
    global _router
    if _router is None:
        _router = FetcherRouter()
    return _router
