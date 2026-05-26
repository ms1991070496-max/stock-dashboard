import { NextRequest, NextResponse } from "next/server";
import { getDemoInfo } from "@/lib/demo-data";

export function GET(req: NextRequest, { params }: { params: { code: string } }) {
  return NextResponse.json(getDemoInfo(params.code));
}
