"""Stock Detail Page — K-line chart + technical indicators + financials"""

import asyncio
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.config import settings
from core.database import init_db, SessionLocal
from core.models import Stock, KLine, FinancialReport, Watchlist
from core.fetchers.router import get_router
from core.fetchers.demo_data import get_demo_kline, get_demo_info
from core.cache.manager import get_cache
from core.indicators import compute_all
from core.sentiment.analyzer import analyze
from core.schemas import KLineItem

logger = logging.getLogger(__name__)
init_db()
router = get_router()
cache = get_cache()

st.set_page_config(page_title="个股分析", page_icon="🔍", layout="wide")

# ── Stock selector ───────────────────────────────────
stock_code = st.session_state.get("selected_stock", "")

col_search, col_period = st.columns([3, 1])
with col_search:
    code_input = st.text_input("股票代码", value=stock_code, placeholder="600519 / AAPL / 0700.HK", key="code_input")
    if code_input:
        stock_code = code_input.strip().upper()

if not stock_code:
    st.info("请在上方输入股票代码，或从大盘页搜索进入")
    st.stop()

market = router.detect_market(stock_code)
flag = {"cn": "🇨🇳", "us": "🇺🇸", "hk": "🇭🇰"}.get(market, "")

# ── Fetch data ───────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_stock_data(_code: str, _market: str):
    try:
        return asyncio.run(router.fetch_stock_info(_code, _market))
    except Exception:
        return get_demo_info(_code)

@st.cache_data(ttl=settings.cache_ttl_kline, show_spinner=False)
def fetch_kline_data(_code: str, _market: str, _days: int):
    try:
        start = date.today() - timedelta(days=_days)
        df = asyncio.run(router.fetch_kline(_code, _market, start_date=start))
        if df is not None and not df.empty:
            records = df.to_dict("records")
            for r in records:
                r["date"] = r["date"] if isinstance(r["date"], date) else pd.Timestamp(r["date"]).date()
                r["open"] = float(r["open"])
                r["close"] = float(r["close"])
                r["high"] = float(r["high"])
                r["low"] = float(r["low"])
                r["volume"] = int(r["volume"])
            return records
    except Exception:
        pass
    return get_demo_kline(_code, _days)

@st.cache_data(ttl=settings.cache_ttl_financial, show_spinner=False)
def fetch_financial_data(_code: str, _market: str):
    return asyncio.run(router.fetch_financials(_code, _market))

# Load data
info = fetch_stock_data(stock_code, market)
days = st.session_state.get("kline_days", 365)
klines = fetch_kline_data(stock_code, market, days)
indicators = compute_all(klines) if klines else {}

# ── Header ───────────────────────────────────────────
st.title(f"{flag} {info.get('name', stock_code)}")
st.caption(f"{stock_code} | {info.get('sector', '')} · {info.get('industry', '')} | 数据延迟约15分钟")

# Watchlist button
db = SessionLocal()
try:
    stock_in_db = db.query(Stock).filter(Stock.code == stock_code).first()
    is_watched = False
    if stock_in_db:
        is_watched = db.query(Watchlist).filter(Watchlist.stock_id == stock_in_db.id).first() is not None

    if is_watched:
        if st.button("⭐ 已关注", key="unwatch"):
            db.query(Watchlist).filter(Watchlist.stock_id == stock_in_db.id).delete()
            db.commit()
            st.rerun()
    else:
        if st.button("☆ 加入自选", key="watch"):
            if not stock_in_db:
                stock_in_db = Stock(code=stock_code, name=info.get("name", stock_code), market=market)
                db.add(stock_in_db)
                db.flush()
            db.add(Watchlist(stock_id=stock_in_db.id))
            db.commit()
            st.rerun()
finally:
    db.close()

# ── K-line chart ─────────────────────────────────────
st.divider()
st.subheader("📊 K线图与技术指标")

# Time period selector
period_col1, period_col2, period_col3 = st.columns([1, 1, 4])
with period_col1:
    if st.button("1个月", use_container_width=True):
        st.session_state["kline_days"] = 30
        st.cache_data.clear()
        st.rerun()
with period_col2:
    if st.button("3个月", use_container_width=True):
        st.session_state["kline_days"] = 90
        st.cache_data.clear()
        st.rerun()
with period_col3:
    if st.button("1年", use_container_width=True):
        st.session_state["kline_days"] = 365
        st.cache_data.clear()
        st.rerun()

if not klines:
    st.warning("暂无K线数据")
else:
    # Build chart
    dates = [k["date"] for k in klines]
    close_vals = [k["close"] for k in klines]
    high_vals = [k["high"] for k in klines]
    low_vals = [k["low"] for k in klines]
    open_vals = [k["open"] for k in klines]
    vol_vals = [k["volume"] for k in klines]

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.5, 0.25, 0.25],
        subplot_titles=("K线+MA", "成交量", "MACD/RSI"),
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=dates, open=open_vals, high=high_vals, low=low_vals, close=close_vals,
        name="K线", increasing_line_color="#ef4444", decreasing_line_color="#22c55e",
    ), row=1, col=1)

    # MAs
    for ma_key, ma_color, ma_width in [("ma5", "#f59e0b", 1), ("ma10", "#3b82f6", 1), ("ma20", "#8b5cf6", 1.5), ("ma60", "#6b7280", 1)]:
        ma_vals = indicators.get(ma_key, [])
        if ma_vals and any(v is not None for v in ma_vals):
            fig.add_trace(go.Scatter(x=dates, y=ma_vals, mode="lines", name=ma_key.upper(), line=dict(color=ma_color, width=ma_width)), row=1, col=1)

    # Volume
    colors = ["#ef4444" if close_vals[i] >= open_vals[i] else "#22c55e" for i in range(len(dates))]
    fig.add_trace(go.Bar(x=dates, y=vol_vals, name="成交量", marker_color=colors, opacity=0.5), row=2, col=1)

    # MACD
    macd_dif_vals = indicators.get("macd_dif", [])
    macd_dea_vals = indicators.get("macd_dea", [])
    macd_hist_vals = indicators.get("macd_hist", [])

    if any(v is not None for v in macd_dif_vals):
        hist_colors = ["#ef4444" if v and v >= 0 else "#22c55e" for v in macd_hist_vals]
        fig.add_trace(go.Bar(x=dates, y=macd_hist_vals, name="MACD柱", marker_color=hist_colors, opacity=0.5), row=3, col=1)
        fig.add_trace(go.Scatter(x=dates, y=macd_dif_vals, mode="lines", name="DIF", line=dict(color="#3b82f6", width=1)), row=3, col=1)
        fig.add_trace(go.Scatter(x=dates, y=macd_dea_vals, mode="lines", name="DEA", line=dict(color="#f59e0b", width=1)), row=3, col=1)

    fig.update_layout(
        height=700, template="plotly_dark",
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        showlegend=True,
        margin=dict(l=0, r=0, t=30, b=0),
    )
    fig.update_xaxes(showgrid=True, gridwidth=0.5, gridcolor="#333")
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor="#333")

    st.plotly_chart(fig, use_container_width=True)


# ── Indicator panel ──────────────────────────────────
st.divider()
st.subheader("📐 技术指标")

if klines:
    last_rsi = [v for v in indicators.get("rsi14", []) if v is not None]
    last_kdj_k = [v for v in indicators.get("kdj_k", []) if v is not None]
    last_kdj_d = [v for v in indicators.get("kdj_d", []) if v is not None]
    last_kdj_j = [v for v in indicators.get("kdj_j", []) if v is not None]

    last_close = close_vals[-1] if close_vals else 0
    last_ma5 = indicators["ma5"][-1] if indicators.get("ma5") and indicators["ma5"][-1] else 0
    last_ma20 = indicators["ma20"][-1] if indicators.get("ma20") and indicators["ma20"][-1] else 0

    metric_cols = st.columns(6)
    with metric_cols[0]:
        st.metric("收盘价", f"{last_close:.2f}")
    with metric_cols[1]:
        st.metric("MA5", f"{last_ma5:.2f}" if last_ma5 else "—", delta=f"{((last_close/last_ma5-1)*100):.1f}%" if last_ma5 else None)
    with metric_cols[2]:
        st.metric("RSI(14)", f"{last_rsi[-1]:.1f}" if last_rsi else "—",
                  delta="超卖" if last_rsi and last_rsi[-1] < 30 else ("超买" if last_rsi and last_rsi[-1] > 70 else None))
    with metric_cols[3]:
        k_val = last_kdj_k[-1] if last_kdj_k else 0
        st.metric("KDJ-K", f"{k_val:.1f}" if k_val else "—")
    with metric_cols[4]:
        d_val = last_kdj_d[-1] if last_kdj_d else 0
        st.metric("KDJ-D", f"{d_val:.1f}" if d_val else "—")
    with metric_cols[5]:
        j_val = last_kdj_j[-1] if last_kdj_j else 0
        st.metric("KDJ-J", f"{j_val:.1f}" if j_val else "—",
                  delta="超卖" if j_val and j_val < 0 else ("超买" if j_val and j_val > 100 else None))


# ── Financials ───────────────────────────────────────
st.divider()
st.subheader("💰 财务数据")

fin_df = fetch_financial_data(stock_code, market)
if fin_df is not None and not fin_df.empty:
    st.dataframe(fin_df, use_container_width=True, hide_index=True)
else:
    st.info("暂无财务数据")
