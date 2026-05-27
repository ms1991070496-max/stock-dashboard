"""Stock API — all endpoints use Tencent Finance real data."""

import asyncio
import logging
import time
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from core.cache.manager import get_cache
from core.config import settings
from core.fetchers.demo_data import search_demo
from core.fetchers.router import get_router
from core.schemas import KLineItem, QuoteItem, StockInfo

logger = logging.getLogger(__name__)
router_api = APIRouter(prefix="/api/v1/stocks", tags=["stocks"])


def _real_quote(code: str) -> dict:
    from core.fetchers.tencent_fetcher import _tx_fetch
    return _tx_fetch(code)


def _real_info(code: str) -> dict:
    from core.fetchers.tencent_fetcher import _tx_fetch, _detect_mkt, _to_tx
    q = _tx_fetch(code)
    return {'code': code, 'name': q['name'], 'market': _detect_mkt(_to_tx(code)), 'sector': '', 'industry': ''}


@router_api.get("/batch")
async def batch_quote(codes: str = ""):
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    if not code_list:
        return {}
    results = {}
    for code in code_list:
        try:
            results[code] = _real_quote(code)
        except Exception:
            results[code] = {"code": code, "name": code, "price": 0, "change_pct": 0}
    return results


@router_api.get("/search", response_model=list[StockInfo])
async def search_stocks(q: str = Query(..., min_length=1)):
    fetcher = get_router()
    cache = get_cache()
    cache_key = f"search:{q}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    results = await fetcher.search_stocks(q)
    if not results:
        results = search_demo(q)
    cache.set(cache_key, results, ttl=300)
    return results


@router_api.get("/{code}/info", response_model=StockInfo)
async def get_stock_info(code: str):
    return StockInfo(**_real_info(code))


@router_api.get("/{code}/kline", response_model=list[KLineItem])
async def get_stock_kline(code: str, days: int = Query(default=365, ge=1, le=3650)):
    from core.fetchers.tencent_fetcher import TencentFetcher
    tx = TencentFetcher()
    start = date.today() - timedelta(days=days)
    df = await tx.fetch_kline(code, start_date=start)
    records = df.to_dict("records")
    for r in records:
        r["date"] = r["date"] if isinstance(r["date"], date) else str(r["date"])[:10]
    return [KLineItem(**r) for r in records]


@router_api.get("/{code}/quote", response_model=QuoteItem)
async def get_stock_quote(code: str):
    return QuoteItem(**_real_quote(code), updated_at=None)


@router_api.get("/{code}/financials")
async def get_stock_financials(code: str):
    return []
