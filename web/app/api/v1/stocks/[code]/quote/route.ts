import { NextRequest, NextResponse } from "next/server";
import { getDemoQuote } from "@/lib/demo-data";

export function GET(_req: NextRequest, { params }: { params: { code: string } }) {
  return NextResponse.json(getDemoQuote(params.code));
}
