import { NextRequest, NextResponse } from "next/server";
import { getDemoKline } from "@/lib/demo-data";

export function GET(req: NextRequest, { params }: { params: { code: string } }) {
  const days = parseInt(req.nextUrl.searchParams.get("days") || "365");
  return NextResponse.json(getDemoKline(params.code, Math.min(days, 3650)));
}
