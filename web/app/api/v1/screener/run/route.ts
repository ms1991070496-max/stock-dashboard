import { NextRequest, NextResponse } from "next/server";
import { getDemoQuote } from "@/lib/demo-data";

const DEMO_CODES = ["600519", "000858", "300750", "002594", "601899", "600036", "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "META", "AMZN", "0700", "9988", "1810", "3690", "9618", "9888", "2015"];

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}));
  const conditions: Array<{ field: string; operator: string; value: number }> = body.conditions || [];
  const market = req.nextUrl.searchParams.get("market") || "all";

  const results: Array<Record<string, unknown>> = [];
  for (const code of DEMO_CODES) {
    const q = getDemoQuote(code);
    if (market !== "all") {
      const m = code.match(/^\d{6}$/) ? "cn" : /^\d{4,5}$/.test(code) ? "hk" : "us";
      if (m !== market) continue;
    }
    results.push({
      code, name: q.name, market: code.match(/^\d{6}$/) ? "cn" : /^\d{4,5}$/.test(code) ? "hk" : "us",
      price: q.price, change_pct: q.change_pct,
    });
  }

  return NextResponse.json({ total: results.length, results });
}
