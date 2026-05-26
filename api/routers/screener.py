"""Stock screener endpoint."""

from fastapi import APIRouter, Query

from core.screener.conditions import PRESET_CONDITIONS, Condition, run_screen

router_api = APIRouter(prefix="/api/v1/screener", tags=["screener"])


@router_api.get("/presets")
async def list_presets():
    return {
        name: [{"field": c.field, "operator": c.operator, "value": c.value, "label": c.label}
               for c in conds]
        for name, conds in PRESET_CONDITIONS.items()
    }


@router_api.post("/run")
async def run_screener(
    conditions: list[Condition],
    market: str = Query(default="all"),
):
    # Phase 1: uses demo data pool
    from core.fetchers.demo_data import DEMO_STOCKS, get_demo_realtime

    pool = []
    for code, info in DEMO_STOCKS.items():
        if market != "all" and info["market"] != market:
            continue
        quote = get_demo_realtime(code)
        pool.append({
            "code": code,
            "name": info["name"],
            "market": info["market"],
            "price": quote["price"],
            "change_pct": quote["change_pct"],
            "pe": None,
            "pb": None,
            "rsi14": None,
            "roe": None,
        })

    results = run_screen(pool, conditions)
    return {"total": len(results), "results": results}
