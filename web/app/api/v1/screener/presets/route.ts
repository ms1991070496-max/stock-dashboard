import { NextResponse } from "next/server";

const PRESETS = {
  value_stocks: [
    { field: "pe", operator: "lt", value: 15, label: "PE < 15" },
    { field: "pb", operator: "lt", value: 1.5, label: "PB < 1.5" },
    { field: "roe", operator: "gt", value: 10, label: "ROE > 10%" },
  ],
  growth_stocks: [
    { field: "roe", operator: "gt", value: 15, label: "ROE > 15%" },
    { field: "pe", operator: "lt", value: 40, label: "PE < 40" },
  ],
  oversold: [{ field: "rsi14", operator: "lt", value: 30, label: "RSI(14) < 30 (超卖)" }],
  overbought: [{ field: "rsi14", operator: "gt", value: 70, label: "RSI(14) > 70 (超买)" }],
};

export function GET() {
  return NextResponse.json(PRESETS);
}
