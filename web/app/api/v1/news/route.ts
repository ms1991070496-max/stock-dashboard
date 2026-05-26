import { NextRequest, NextResponse } from "next/server";

const DEMO_NEWS = [
  { title: "央行宣布降准0.5个百分点，释放长期流动性", source: "证券时报", published_at: "2026-05-26", sentiment_score: 0.35 },
  { title: "A股三大指数集体收涨，成交额突破万亿", source: "第一财经", published_at: "2026-05-26", sentiment_score: 0.28 },
  { title: "美联储维持利率不变，暗示年内降息可能", source: "华尔街见闻", published_at: "2026-05-25", sentiment_score: 0.15 },
  { title: "新能源板块持续走强，宁德时代创新高", source: "每日经济新闻", published_at: "2026-05-26", sentiment_score: 0.42 },
  { title: "港股恒生科技指数涨超3%", source: "新浪财经", published_at: "2026-05-26", sentiment_score: 0.30 },
  { title: "部分房企债务问题仍存不确定性", source: "财联社", published_at: "2026-05-25", sentiment_score: -0.22 },
  { title: "苹果发布新一代AI芯片，算力提升5倍", source: "彭博社", published_at: "2026-05-25", sentiment_score: 0.38 },
  { title: "特斯拉全球召回12万辆Model Y", source: "路透社", published_at: "2026-05-24", sentiment_score: -0.18 },
  { title: "腾讯发布2026Q1财报，游戏业务增长超预期", source: "36氪", published_at: "2026-05-26", sentiment_score: 0.45 },
  { title: "国际油价跌破60美元，航空公司成本压力缓解", source: "经济观察报", published_at: "2026-05-26", sentiment_score: 0.12 },
  { title: "警惕AI概念股估值过高风险", source: "券商中国", published_at: "2026-05-25", sentiment_score: -0.25 },
  { title: "小米汽车交付量突破10万台", source: "界面新闻", published_at: "2026-05-26", sentiment_score: 0.48 },
];

export function GET(req: NextRequest) {
  const limit = parseInt(req.nextUrl.searchParams.get("limit") || "30");
  return NextResponse.json(DEMO_NEWS.slice(0, limit));
}
