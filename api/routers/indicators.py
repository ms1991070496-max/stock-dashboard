"""Technical indicator computation endpoint."""

from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from core.fetchers.demo_data import get_demo_kline
from core.fetchers.router import get_router
from core.indicators import compute_all
from core.schemas import IndicatorResult

router_api = APIRouter(prefix="/api/v1/indicators", tags=["indicators"])


@router_api.get("/{code}", response_model=IndicatorResult)
async def get_indicators(
    code: str,
    days: int = Query(default=365, ge=30, le=3650),
):
    try:
        from core.fetchers.tencent_fetcher import TencentFetcher
        tx = TencentFetcher()
        start = date.today() - timedelta(days=days)
        df = await tx.fetch_kline(code, start_date=start)
        if df is not None and not df.empty:
            klines = df.to_dict("records")
    except Exception:
        klines = get_demo_kline(code, days)

    indicators = compute_all(klines)

    return IndicatorResult(
        code=code,
        name=code,
        klines=klines,
        **indicators,
    )
