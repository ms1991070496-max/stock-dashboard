"""News and sentiment endpoint."""

import logging

from fastapi import APIRouter, Query

from core.cache.manager import get_cache
from core.config import settings
from core.fetchers.router import get_router
from core.schemas import NewsItem
from core.sentiment.analyzer import batch_analyze

logger = logging.getLogger(__name__)
router_api = APIRouter(prefix="/api/v1/news", tags=["news"])


@router_api.get("/", response_model=list[NewsItem])
async def get_news(
    code: str | None = Query(default=None, description="股票代码，不传则返回全市场"),
    market: str = Query(default="cn"),
    limit: int = Query(default=30, le=100),
):
    cache = get_cache()
    cache_key = f"news:{market}:{code or 'all'}:{limit}"

    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        raw = await get_router().fetch_news(code, market, limit)
    except Exception as e:
        logger.warning(f"News fetch failed: {e}")
        raw = []

    # Compute sentiment
    if raw:
        titles = [n.get("title", "") for n in raw]
        scores = batch_analyze(titles)
        for i, score in enumerate(scores):
            raw[i]["sentiment_score"] = round(score, 3)

    items = [NewsItem(**n) for n in raw]
    cache.set(cache_key, [i.model_dump() for i in items], ttl=settings.cache_ttl_news)
    return items
