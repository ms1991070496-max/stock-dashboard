"""Technical indicator computation endpoint — real Tencent data only."""

from datetime import date, timedelta

from fastapi import APIRouter, Query

from core.indicators import compute_all
from core.schemas import IndicatorResult

router_api = APIRouter(prefix="/api/v1/indicators", tags=["indicators"])


@router_api.get("/{code}", response_model=IndicatorResult)
async def get_indicators(code: str, days: int = Query(default=365, ge=30, le=3650)):
    from core.fetchers.tencent_fetcher import TencentFetcher
    tx = TencentFetcher()
    start = date.today() - timedelta(days=days)
    df = await tx.fetch_kline(code, start_date=start)
    klines = df.to_dict("records")
    indicators = compute_all(klines)
    return IndicatorResult(code=code, name=code, klines=klines, **indicators)
