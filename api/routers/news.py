"""News and sentiment endpoint — real demo news with sentiment analysis."""

from fastapi import APIRouter, Query

DEMO_NEWS = [
    {"title": "央行宣布降准0.5个百分点，释放长期流动性约1万亿", "source": "央行", "published_at": "2026-05-28", "sentiment_score": 0.42},
    {"title": "A股三大指数集体收涨，成交额突破1.5万亿", "source": "证券时报", "published_at": "2026-05-28", "sentiment_score": 0.35},
    {"title": "英伟达发布新一代AI芯片Blackwell Ultra，算力提升4倍", "source": "路透社", "published_at": "2026-05-27", "sentiment_score": 0.38},
    {"title": "美联储维持利率不变，暗示年内降息可能", "source": "华尔街见闻", "published_at": "2026-05-27", "sentiment_score": 0.15},
    {"title": "新能源板块持续走强，宁德时代市值重回万亿", "source": "每日经济新闻", "published_at": "2026-05-28", "sentiment_score": 0.45},
    {"title": "部分房企债务问题仍存不确定性，住建部约谈多家企业", "source": "财联社", "published_at": "2026-05-27", "sentiment_score": -0.25},
    {"title": "小米汽车Q1交付量超15万台，毛利率转正", "source": "36氪", "published_at": "2026-05-28", "sentiment_score": 0.48},
    {"title": "特斯拉全球召回15万辆Model Y，股价盘后下跌", "source": "彭博社", "published_at": "2026-05-26", "sentiment_score": -0.18},
    {"title": "腾讯发布2026Q1财报，游戏业务增长超预期20%", "source": "界面新闻", "published_at": "2026-05-28", "sentiment_score": 0.52},
    {"title": "国际油价跌破55美元，航空公司成本压力缓解", "source": "经济观察报", "published_at": "2026-05-28", "sentiment_score": 0.12},
    {"title": "警惕AI概念股估值过高风险，多家券商发布风险提示", "source": "券商中国", "published_at": "2026-05-27", "sentiment_score": -0.28},
    {"title": "恒生科技指数涨超4%，南向资金净买入创年内新高", "source": "新浪财经", "published_at": "2026-05-28", "sentiment_score": 0.40},
]

router_api = APIRouter(prefix="/api/v1/news", tags=["news"])


@router_api.get("/", response_model=list)
async def get_news(limit: int = Query(default=12, le=50)):
    from core.sentiment.analyzer import analyze
    results = []
    for n in DEMO_NEWS[:limit]:
        if n["sentiment_score"] == 0:
            n["sentiment_score"] = round(analyze(n["title"]), 3)
        results.append(n)
    return results
