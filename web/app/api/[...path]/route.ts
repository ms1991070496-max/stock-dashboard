import { NextRequest, NextResponse } from "next/server";

const BACKEND = "https://stock-dashboard.ji6q.onrender.com";

export async function GET(req: NextRequest) {
  const url = `${BACKEND}${req.nextUrl.pathname}${req.nextUrl.search}`;

  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(30000) });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (e: any) {
    return NextResponse.json({ error: e.message || "Backend unreachable" }, { status: 502 });
  }
}
