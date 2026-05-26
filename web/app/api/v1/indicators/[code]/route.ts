import { NextRequest, NextResponse } from "next/server";
import { getDemoKline, computeIndicators, getDemoInfo } from "@/lib/demo-data";

export function GET(req: NextRequest, { params }: { params: { code: string } }) {
  const days = parseInt(req.nextUrl.searchParams.get("days") || "365");
  const klines = getDemoKline(params.code, Math.min(days, 3650));
  const info = getDemoInfo(params.code);
  const ind = computeIndicators(klines);

  return NextResponse.json({
    code: params.code,
    name: info.name,
    klines,
    ...ind,
  });
}
