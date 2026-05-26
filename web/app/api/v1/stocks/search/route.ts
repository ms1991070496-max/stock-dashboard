import { NextRequest, NextResponse } from "next/server";
import { searchDemo } from "@/lib/demo-data";

export function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get("q") || "";
  if (!q.trim()) return NextResponse.json([]);
  return NextResponse.json(searchDemo(q));
}
