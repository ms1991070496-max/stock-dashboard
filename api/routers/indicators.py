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
    market = get_router().detect_market(code)
    klines = None

    try:
        start = date.today() - timedelta(days=days)
        df = await get_router().fetch_kline(code, market, start_date=start)
        if df is not None and not df.empty:
            klines = df.to_dict("records")
    except Exception:
        pass

    if not klines:
        klines = get_demo_kline(code, days)

    indicators = compute_all(klines)

    return IndicatorResult(
        code=code,
        name=code,
        klines=klines,
        **indicators,
    )
