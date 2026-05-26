"""Simple sentiment analysis: VADER for English, keyword-based for Chinese."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

CN_POSITIVE = {"涨", "增", "利好", "增长", "突破", "创新高", "盈利", "买入", "回购", "分红",
                "业绩", "超预期", "上升", "反弹", "涨停", "牛市", "回暖"}
CN_NEGATIVE = {"跌", "减", "利空", "下降", "跌破", "创新低", "亏损", "卖出", "减持", "暴雷",
                "违约", "下滑", "崩盘", "跌停", "熊市", "衰退", "风险", "警告"}


def analyze_cn(text: str) -> float:
    if not text:
        return 0.0
    pos = sum(1 for w in CN_POSITIVE if w in text)
    neg = sum(1 for w in CN_NEGATIVE if w in text)
    if pos + neg == 0:
        return 0.0
    return (pos - neg) / (pos + neg) * 0.5


def analyze_en(text: str) -> float:
    if not text:
        return 0.0
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        analyzer = SentimentIntensityAnalyzer()
        scores = analyzer.polarity_scores(text)
        return scores["compound"] * 0.5
    except ImportError:
        return 0.0


def analyze(text: str) -> float:
    has_cn = any("一" <= c <= "鿿" for c in text)
    if has_cn:
        return analyze_cn(text)
    return analyze_en(text)


def batch_analyze(texts: list[str]) -> list[float]:
    return [analyze(t) for t in texts]
