"""Stock Screener — multi-condition filtering"""

import asyncio
import sys
from pathlib import Path

import streamlit as st

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.screener.conditions import PRESET_CONDITIONS, Condition, run_screen

st.set_page_config(page_title="选股器", page_icon="🔎", layout="wide")

st.title("🔎 选股器")
st.caption("设置筛选条件，快速发现符合条件的股票")

# Presets
st.subheader("快速筛选模板")
preset = st.selectbox("选择预设策略", ["自定义", "价值股 (低PE+低PB+高ROE)", "成长股 (高ROE+合理PE)", "超卖反弹 (RSI < 30)", "超买警示 (RSI > 70)"])

conditions: list[Condition] = []
if preset.startswith("价值股"):
    conditions = PRESET_CONDITIONS["value_stocks"]
elif preset.startswith("成长股"):
    conditions = PRESET_CONDITIONS["growth_stocks"]
elif preset.startswith("超卖"):
    conditions = PRESET_CONDITIONS["oversold"]
elif preset.startswith("超买"):
    conditions = PRESET_CONDITIONS["overbought"]

st.divider()
st.subheader("自定义条件")

# Current conditions display
if conditions:
    for i, cond in enumerate(conditions):
        st.text(f"  {i+1}. {cond.label}")

# Manual condition builder
with st.expander("+ 添加自定义条件"):
    col1, col2, col3 = st.columns(3)
    with col1:
        field = st.selectbox("指标", ["pe", "pb", "roe", "rsi14", "market_cap", "eps", "change_pct"])
    with col2:
        operator = st.selectbox("比较", ["gt (> 大于)", "lt (< 小于)", "gte (>= 大于等于)", "lte (<= 小于等于)"])
    with col3:
        value = st.number_input("阈值", value=0.0, step=1.0)

    if st.button("添加条件", use_container_width=True):
        op = operator.split()[0]
        conditions.append(Condition(field=field, operator=op, value=value))
        st.rerun()

if st.button("清除所有条件", use_container_width=True):
    conditions = []
    st.rerun()

# Market selection for screener
st.divider()
market_filter = st.selectbox("市场", ["全部", "A股", "美股", "港股"])

# Run screener button
if st.button("🚀 开始筛选", type="primary", use_container_width=True, disabled=not conditions):
    with st.spinner("筛选中..."):
        # In Phase 1, we use a small curated pool for demo
        # Full market scan will be added in Phase 2 with local DB
        st.info("⚠️ Phase 1 为演示模式，使用预设股票池。完整市场扫描将在 Phase 2 实现。")
        st.markdown("""
        选股器将在 Phase 2 中接入完整数据源：
        - A股全市场扫描 (AkShare)
        - 美股基本面筛选 (yfinance)
        - 技术指标交叉筛选
        - 结果导出 Excel
        """)
