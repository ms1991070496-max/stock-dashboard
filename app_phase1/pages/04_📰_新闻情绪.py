"""News Feed + Sentiment Analysis"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.config import settings
from core.fetchers.router import get_router
from core.cache.manager import get_cache
from core.sentiment.analyzer import analyze, batch_analyze

st.set_page_config(page_title="新闻情绪", page_icon="📰", layout="wide")

router = get_router()
cache = get_cache()

st.title("📰 市场新闻与情绪分析")
st.caption("聚合财经新闻，AI情绪分析辅助决策")

# Fetch news
@st.cache_data(ttl=settings.cache_ttl_news, show_spinner=False)
def fetch_news():
    cn_news = asyncio.run(router.fetch_news(market="cn", limit=30))
    for n in cn_news:
        n["market_tag"] = "🇨🇳 A股"
    return cn_news

with st.spinner("加载新闻..."):
    news_list = fetch_news()

if not news_list:
    st.info("暂无新闻数据，请检查网络后刷新")
    st.stop()

# Sentiment scores
if "sentiment_scores" not in st.session_state or st.button("🔄 刷新情绪分析"):
    texts = [n.get("title", "") + " " + n.get("content", "")[:200] for n in news_list]
    scores = batch_analyze(texts)
    st.session_state["sentiment_scores"] = scores

scores = st.session_state.get("sentiment_scores", [0] * len(news_list))

# Overall sentiment
pos_count = sum(1 for s in scores if s > 0.05)
neg_count = sum(1 for s in scores if s < -0.05)
neu_count = len(scores) - pos_count - neg_count

st.subheader("📊 市场情绪概览")
metric_cols = st.columns(4)
with metric_cols[0]:
    st.metric("总新闻数", len(news_list))
with metric_cols[1]:
    st.metric("😊 正面", pos_count, delta=f"{pos_count/len(news_list)*100:.0f}%" if news_list else None)
with metric_cols[2]:
    st.metric("😐 中性", neu_count, delta=f"{neu_count/len(news_list)*100:.0f}%" if news_list else None)
with metric_cols[3]:
    st.metric("😟 负面", neg_count, delta=f"{neg_count/len(news_list)*100:.0f}%" if news_list else None, delta_color="inverse")

# News list
st.divider()
st.subheader("📋 新闻列表")

sentiment_filter = st.radio("情绪筛选", ["全部", "😊 正面", "😐 中性", "😟 负面"], horizontal=True)

for i, (news, score) in enumerate(zip(news_list, scores)):
    if sentiment_filter == "😊 正面" and score <= 0.05:
        continue
    if sentiment_filter == "😐 中性" and (score > 0.05 or score < -0.05):
        continue
    if sentiment_filter == "😟 负面" and score >= -0.05:
        continue

    emoji = "😊" if score > 0.05 else "😟" if score < -0.05 else "😐"
    color = "#22c55e" if score > 0.05 else "#ef4444" if score < -0.05 else "#888"

    with st.container(border=True):
        c1, c2 = st.columns([9, 1])
        with c1:
            st.markdown(f"**{news.get('market_tag', '')} | {news.get('title', '')}**")
            st.caption(f"来源: {news.get('source', '')} | {news.get('published_at', '')}")
        with c2:
            st.markdown(f"<span style='font-size:1.5em;color:{color}'>{emoji}</span>", unsafe_allow_html=True)
            st.caption(f"{score:+.2f}")
