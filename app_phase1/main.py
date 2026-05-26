"""Stock Analysis Dashboard — Market Overview & Watchlist"""

import asyncio
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.config import settings
from core.database import init_db, SessionLocal
from core.models import Stock, KLine, Watchlist
from core.fetchers.router import get_router, FetcherRouter
from core.fetchers.demo_data import search_demo, get_demo_realtime
from core.cache.manager import get_cache, CacheManager
from core.indicators import compute_all
from core.schemas import KLineItem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
init_db()
router = get_router()
cache = get_cache()

st.set_page_config(
    page_title="股票分析看板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📈 股票分析看板")
st.caption(f"数据更新: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 多市场覆盖 (A股·美股·港股)")

# ── Sidebar ──────────────────────────────────────────
with st.sidebar:
    st.header("🔍 搜索股票")
    search_keyword = st.text_input("输入名称或代码", placeholder="例如: 茅台 / AAPL / 腾讯")

    st.divider()
    st.header("⭐ 自选股")

    db = SessionLocal()
    try:
        watchlist_stocks = db.query(Stock).join(Watchlist, Watchlist.stock_id == Stock.id).all()
        if not watchlist_stocks:
            st.info("还没有自选股，搜索并添加吧")
    finally:
        db.close()

    if watchlist_stocks:
        for ws in watchlist_stocks:
            col1, col2 = st.columns([4, 1])
            with col1:
                flag = {"cn": "🇨🇳", "us": "🇺🇸", "hk": "🇭🇰"}.get(ws.market, "")
                if st.button(f"{flag} {ws.name} ({ws.code})", key=f"wl_{ws.code}", use_container_width=True):
                    st.session_state["selected_stock"] = ws.code
                    st.switch_page("pages/02_🔍_个股分析.py")
            with col2:
                if st.button("✕", key=f"rm_{ws.code}"):
                    db2 = SessionLocal()
                    try:
                        db2.query(Watchlist).filter(Watchlist.stock_id == ws.id).delete()
                        db2.commit()
                        st.rerun()
                    finally:
                        db2.close()


# ── Handle search ────────────────────────────────────
if search_keyword:
    st.subheader(f"搜索结果: \"{search_keyword}\"")

    if "search_cache" in st.session_state and st.session_state.get("search_term") == search_keyword:
        results = st.session_state["search_cache"]
    else:
        with st.spinner("搜索中..."):
            try:
                results = asyncio.run(router.search_stocks(search_keyword))
            except Exception:
                results = []
            if not results:
                results = search_demo(search_keyword)
            st.session_state["search_cache"] = results
            st.session_state["search_term"] = search_keyword

    if not results:
        st.warning("未找到匹配的股票")
    else:
        cols = st.columns(3)
        for i, r in enumerate(results[:12]):
            with cols[i % 3]:
                flag = {"cn": "🇨🇳", "us": "🇺🇸", "hk": "🇭🇰"}.get(r.get("market", ""), "")
                price = r.get("price", 0)
                change = r.get("change_pct", 0)
                color = "#ef4444" if change > 0 else "#22c55e" if change < 0 else "#888"

                with st.container(border=True):
                    st.markdown(f"**{flag} {r['name']}**")
                    st.caption(r["code"])
                    st.markdown(f"<span style='font-size:1.2em;font-weight:bold;color:{color}'>¥{price:.2f} {change:+.2f}%</span>", unsafe_allow_html=True)

                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("📊 分析", key=f"ana_{r['code']}", use_container_width=True):
                            st.session_state["selected_stock"] = r["code"]
                            st.switch_page("pages/02_🔍_个股分析.py")
                    with c2:
                        if st.button("⭐ 关注", key=f"fav_{r['code']}", use_container_width=True):
                            _add_to_watchlist(r["code"], r["name"], r["market"])
                            st.rerun()


# ── Market overview ──────────────────────────────────
st.divider()
st.subheader("📊 市场快照")

def _build_market_table():
    major_indices = [
        ("000001", "cn", "上证指数", "SH000001"),
        ("399001", "cn", "深证成指", "SZ399001"),
        ("399006", "cn", "创业板指", "SZ399006"),
        ("000688", "cn", "科创50", "SH000688"),
        ("AAPL", "us", "Apple", None),
        ("MSFT", "us", "Microsoft", None),
        ("GOOGL", "us", "Google", None),
        ("TSLA", "us", "Tesla", None),
        ("0700", "hk", "腾讯控股", None),
        ("9988", "hk", "阿里巴巴", None),
    ]

    cache_key = "market_snapshot"
    cached = cache.get(cache_key)

    if cached:
        return cached

    async def _fetch_all():
        tasks = []
        for code, mkt, name, ak_code in major_indices:
            if ak_code:
                tasks.append(router.fetch_realtime(ak_code, mkt))
            else:
                tasks.append(router.fetch_realtime(code, mkt))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        combined = []
        for (code, mkt, name, _), r in zip(major_indices, results):
            if isinstance(r, Exception) or r.get("price", 0) == 0:
                demo = get_demo_realtime(code)
                demo["name"] = name
                combined.append(demo)
            else:
                r["name"] = name
                combined.append(r)
        return combined

    try:
        data = asyncio.run(_fetch_all())
    except Exception:
        data = []
        for code, mkt, name, _ in major_indices:
            demo = get_demo_realtime(code)
            demo["name"] = name
            data.append(demo)
    df = pd.DataFrame(data)
    if not df.empty:
        cache.set(cache_key, df.to_dict("records"), ttl=settings.cache_ttl_quote)
    return data

market_data = _build_market_table()

if market_data:
    metric_cols = st.columns(len(market_data))
    for i, item in enumerate(market_data):
        with metric_cols[i]:
            change = item.get("change_pct", 0)
            color = "#ef4444" if change > 0 else "#22c55e" if change < 0 else "#888"
            st.metric(
                label=f"{item.get('name', '')}",
                value=f"{item.get('price', '—')}",
                delta=f"{change:+.2f}%" if isinstance(change, (int, float)) and change != 0 else None,
            )


# ── Helper ───────────────────────────────────────────
def _add_to_watchlist(code: str, name: str, market: str):
    db = SessionLocal()
    try:
        stock = db.query(Stock).filter(Stock.code == code).first()
        if not stock:
            stock = Stock(code=code, name=name, market=market)
            db.add(stock)
            db.flush()
        exists = db.query(Watchlist).filter(Watchlist.stock_id == stock.id).first()
        if not exists:
            db.add(Watchlist(stock_id=stock.id))
            db.commit()
            st.toast(f"已添加 {name} 到自选股")
    finally:
        db.close()
