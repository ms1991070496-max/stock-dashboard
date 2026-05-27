"""Stock search, info, K-line, quote endpoints."""

import asyncio
import logging
import time
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from core.cache.manager import get_cache
from core.config import settings
from core.fetchers.demo_data import (
    DEMO_STOCKS,
    get_demo_info,
    get_demo_kline,
    get_demo_realtime,
    search_demo,
)
from core.fetchers.router import get_router
from core.schemas import KLineItem, QuoteItem, StockInfo

logger = logging.getLogger(__name__)
router_api = APIRouter(prefix="/api/v1/stocks", tags=["stocks"])


def _real_quote(code: str) -> dict:
    """Get real quote via Tencent Finance."""
    try:
        from core.fetchers.tencent_fetcher import _tx_fetch
        return _tx_fetch(code)
    except Exception:
        return get_demo_realtime(code)


@router_api.get("/batch")
async def batch_quote(codes: str = "", fast: bool = True):
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if not code_list:
        return {}
    results = {}
    for code in code_list:
        results[code] = get_demo_realtime(code) if fast else _real_quote(code)
    return results


@router_api.get("/search", response_model=list[StockInfo])
async def search_stocks(q: str = Query(..., min_length=1, description="股票名称或代码")):
    fetcher = get_router()
    cache = get_cache()
    cache_key = f"search:{q}"

    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        results = await fetcher.search_stocks(q)
    except Exception as e:
        logger.warning(f"Search failed for '{q}': {e}")
        results = []

    if not results:
        results = search_demo(q)

    cache.set(cache_key, results, ttl=300)
    return results


@router_api.get("/{code}/info", response_model=StockInfo)
async def get_stock_info(code: str):
    try:
        from core.fetchers.tencent_fetcher import _tx_fetch
        q = _tx_fetch(code)
        return StockInfo(code=code, name=q['name'], market=_detect_mkt(code), sector="", industry="")
    except Exception:
        return StockInfo(**get_demo_info(code))


def _detect_mkt(code: str) -> str:
    code = code.strip().upper()
    if code.endswith((".SS", ".SZ")): return "cn"
    if code.endswith(".HK"): return "hk"
    if code.isdigit():
        if len(code) == 6: return "cn"
        if len(code) in (4, 5): return "hk"
    return "us"


@router_api.get("/{code}/kline", response_model=list[KLineItem])
async def get_stock_kline(
    code: str,
    days: int = Query(default=365, ge=1, le=3650, description="数据天数"),
):
    start = date.today() - timedelta(days=days)

    try:
        from core.fetchers.tencent_fetcher import TencentFetcher
        tx = TencentFetcher()
        df = await tx.fetch_kline(code, start_date=start)
        if df is not None and not df.empty:
            records = df.to_dict("records")
            for r in records:
                r["date"] = r["date"] if isinstance(r["date"], date) else str(r["date"])[:10]
            return [KLineItem(**r) for r in records]
    except Exception as e:
        logger.warning(f"K-line fetch failed for {code}: {e}")

    records = get_demo_kline(code, days)
    return [KLineItem(**r) for r in records]


@router_api.get("/{code}/quote", response_model=QuoteItem)
async def get_stock_quote(code: str, fast: bool = False):
    if fast:
        return QuoteItem(**get_demo_realtime(code), updated_at=None)
    return QuoteItem(**_real_quote(code), updated_at=None)


@router_api.get("/{code}/financials")
async def get_stock_financials(code: str):
    market = get_router().detect_market(code)
    try:
        df = await get_router().fetch_financials(code, market)
        if df is not None and not df.empty:
            return df.to_dict("records")
    except Exception as e:
        logger.warning(f"Financials failed for {code}: {e}")
    return []
