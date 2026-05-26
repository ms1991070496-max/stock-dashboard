"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { getStockInfo, getStockKline, getStockQuote, getIndicators } from "@/lib/api";
import { KLineChart } from "@/components/charts/KLineChart";
import type { StockInfo, KLineItem, QuoteItem, IndicatorResult } from "@/lib/types";

const MARKET_FLAG: Record<string, string> = { cn: "🇨🇳", us: "🇺🇸", hk: "🇭🇰" };

export default function StockDetailPage() {
  const params = useParams();
  const router = useRouter();
  const code = params.code as string;

  const [info, setInfo] = useState<StockInfo | null>(null);
  const [quote, setQuote] = useState<QuoteItem | null>(null);
  const [indicators, setIndicators] = useState<IndicatorResult | null>(null);
  const [days, setDays] = useState(365);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      getStockInfo(code).catch(() => null),
      getStockQuote(code).catch(() => null),
      getIndicators(code, days).catch(() => null),
    ]).then(([i, q, ind]) => {
      setInfo(i);
      setQuote(q);
      setIndicators(ind);
      setLoading(false);
    });
  }, [code, days]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-[#8890a0]">加载中...</p>
      </div>
    );
  }

  if (!info) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <p className="text-[#8890a0]">未找到股票: {code}</p>
        <button onClick={() => router.back()} className="text-sm text-[#6366f1] hover:underline">
          ← 返回
        </button>
      </div>
    );
  }

  const flag = MARKET_FLAG[info.market] ?? "";
  const change = quote?.change_pct ?? 0;
  const changeColor = change > 0 ? "#ef4444" : change < 0 ? "#22c55e" : "#8890a0";

  // Indicator values
  const hasIndicators = indicators && indicators.klines.length > 0;
  const lastIdx = hasIndicators ? indicators.klines.length - 1 : -1;
  const lastRSI = hasIndicators && indicators.rsi14[lastIdx] != null ? indicators.rsi14[lastIdx]! : null;
  const lastK = hasIndicators && indicators.kdj_k?.[lastIdx] != null ? indicators.kdj_k[lastIdx]! : null;
  const lastD = hasIndicators && indicators.kdj_d?.[lastIdx] != null ? indicators.kdj_d[lastIdx]! : null;
  const lastJ = hasIndicators && indicators.kdj_j?.[lastIdx] != null ? indicators.kdj_j[lastIdx]! : null;

  // Build chart data
  const chartData = hasIndicators
    ? {
        dates: indicators.klines.map((k) => k.date),
        open: indicators.klines.map((k) => k.open),
        high: indicators.klines.map((k) => k.high),
        low: indicators.klines.map((k) => k.low),
        close: indicators.klines.map((k) => k.close),
        volume: indicators.klines.map((k) => k.volume),
        ma5: indicators.ma5,
        ma10: indicators.ma10,
        ma20: indicators.ma20,
        macd_dif: indicators.macd_dif,
        macd_dea: indicators.macd_dea,
        macd_hist: indicators.macd_hist,
      }
    : null;

  return (
    <div>
      {/* Back */}
      <button
        onClick={() => router.push("/")}
        className="text-sm text-[#8890a0] hover:text-white mb-4 inline-block"
      >
        ← 返回大盘
      </button>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">
            {flag} {info.name}
          </h1>
          <p className="text-sm text-[#8890a0]">
            {info.code} · {info.sector} {info.industry}
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold">
            {quote ? `¥${quote.price.toFixed(2)}` : "—"}
          </div>
          <div className="text-sm" style={{ color: changeColor }}>
            {quote
              ? `${change > 0 ? "+" : ""}${change.toFixed(2)}%`
              : "—"}
          </div>
        </div>
      </div>

      {/* Time period */}
      <div className="flex gap-2 mb-4">
        {[30, 90, 180, 365].map((d) => (
          <button
            key={d}
            onClick={() => setDays(d)}
            className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${
              days === d
                ? "bg-[#6366f1]/20 border-[#6366f1] text-[#818cf8]"
                : "border-[#2a2d3e] text-[#8890a0] hover:border-[#444]"
            }`}
          >
            {d >= 365 ? `${d / 365}年` : d >= 30 ? `${d / 30}月` : `${d}天`}
          </button>
        ))}
      </div>

      {/* Chart */}
      {chartData ? (
        <div className="mb-6">
          <KLineChart data={chartData} />
        </div>
      ) : (
        <div className="h-[600px] bg-[#1a1d2e] rounded-lg flex items-center justify-center mb-6">
          <p className="text-[#8890a0]">暂无K线数据</p>
        </div>
      )}

      {/* Indicator panel */}
      {hasIndicators && (
        <div className="grid grid-cols-6 gap-3 mb-6">
          <MetricBox label="收盘价" value={indicators.klines[lastIdx].close.toFixed(2)} />
          <MetricBox
            label="RSI(14)"
            value={lastRSI != null ? lastRSI.toFixed(1) : "—"}
            extra={
              lastRSI != null
                ? lastRSI > 70
                  ? "超买"
                  : lastRSI < 30
                  ? "超卖"
                  : "—"
                : undefined
            }
          />
          <MetricBox label="KDJ-K" value={lastK != null ? lastK.toFixed(1) : "—"} />
          <MetricBox label="KDJ-D" value={lastD != null ? lastD.toFixed(1) : "—"} />
          <MetricBox label="KDJ-J" value={lastJ != null ? lastJ.toFixed(1) : "—"}
            extra={lastJ != null ? (lastJ > 100 ? "超买" : lastJ < 0 ? "超卖" : undefined) : undefined}
          />
          <MetricBox
            label="MA5"
            value={indicators.ma5[lastIdx] != null ? indicators.ma5[lastIdx]!.toFixed(2) : "—"}
          />
        </div>
      )}
    </div>
  );
}

function MetricBox({
  label,
  value,
  extra,
}: {
  label: string;
  value: string;
  extra?: string;
}) {
  return (
    <div className="bg-[#1a1d2e] border border-[#2a2d3e] rounded-lg p-3">
      <div className="text-xs text-[#8890a0]">{label}</div>
      <div className="text-lg font-bold mt-1">{value}</div>
      {extra && extra !== "—" && (
        <div className={`text-xs mt-0.5 ${extra === "超买" ? "text-[#ef4444]" : "text-[#22c55e]"}`}>
          {extra}
        </div>
      )}
    </div>
  );
}
