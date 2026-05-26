"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { searchStocks, getStockQuote } from "@/lib/api";
import type { StockInfo, QuoteItem } from "@/lib/types";

const MARKET_FLAG: Record<string, string> = { cn: "🇨🇳", us: "🇺🇸", hk: "🇭🇰" };
const CURRENCY: Record<string, string> = { cn: "¥", us: "$", hk: "HK$" };

const DEFAULT_INDICES = [
  { code: "600519", name: "贵州茅台", market: "cn" },
  { code: "300750", name: "宁德时代", market: "cn" },
  { code: "AAPL", name: "Apple", market: "us" },
  { code: "NVDA", name: "NVIDIA", market: "us" },
  { code: "TSLA", name: "Tesla", market: "us" },
  { code: "0700", name: "腾讯", market: "hk" },
  { code: "1810", name: "小米集团", market: "hk" },
  { code: "9988", name: "阿里巴巴", market: "hk" },
];

export default function HomePage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<StockInfo[]>([]);
  const [quotes, setQuotes] = useState<Record<string, QuoteItem>>({});
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);

  // Load quotes for default indices
  useEffect(() => {
    Promise.all(DEFAULT_INDICES.map((s) => getStockQuote(s.code).catch(() => null)))
      .then((items) => {
        const map: Record<string, QuoteItem> = {};
        items.forEach((item, i) => {
          if (item) map[DEFAULT_INDICES[i].code] = item;
        });
        setQuotes(map);
      });
  }, []);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const r = await searchStocks(query);
      setResults(r);

      // Fetch quotes for search results
      const qs: Record<string, QuoteItem> = {};
      await Promise.all(
        r.map(async (s) => {
          try {
            qs[s.code] = await getStockQuote(s.code);
          } catch {}
        })
      );
      setQuotes((prev) => ({ ...prev, ...qs }));
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  }, [query]);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">📈 股票分析看板</h1>
      <p className="text-sm text-[#8890a0] mb-6">多市场覆盖 (A股·美股·港股) | 技术分析 · 基本面 · 情绪</p>

      {/* Search */}
      <div className="flex gap-2 mb-6">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="搜索股票名称或代码 (茅台 / AAPL / 腾讯 ...)"
          className="flex-1 px-4 py-2 bg-[#1a1d2e] border border-[#2a2d3e] rounded-lg text-sm text-white placeholder-[#8890a0] outline-none focus:border-[#6366f1]"
        />
        <button
          onClick={handleSearch}
          disabled={searching}
          className="px-6 py-2 bg-[#6366f1] hover:bg-[#5558e6] text-white text-sm rounded-lg transition-colors"
        >
          {searching ? "搜索中..." : "搜索"}
        </button>
      </div>

      {/* Search results */}
      {results.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-medium text-[#8890a0] mb-3">
            搜索结果 ({results.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {results.map((s) => (
              <StockCard
                key={s.code}
                stock={s}
                quote={quotes[s.code]}
                onClick={() => router.push(`/stock/${s.code}`)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Market snapshot */}
      <h2 className="text-sm font-medium text-[#8890a0] mb-3">市场快照</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3 mb-6">
        {DEFAULT_INDICES.map((s) => {
          const q = quotes[s.code];
          const change = q?.change_pct ?? 0;
          const colorClass =
            change > 0 ? "text-[#ef4444]" : change < 0 ? "text-[#22c55e]" : "text-[#8890a0]";
          return (
            <div
              key={s.code}
              className="bg-[#1a1d2e] border border-[#2a2d3e] rounded-lg p-3 cursor-pointer hover:border-[#6366f1] transition-colors"
              onClick={() => router.push(`/stock/${s.code}`)}
            >
              <div className="text-xs text-[#8890a0]">
                {MARKET_FLAG[s.market]} {s.name}
              </div>
              <div className="text-sm font-bold mt-1">
                {q ? `${CURRENCY[s.market]}${q.price.toFixed(2)}` : "—"}
              </div>
              <div className={`text-xs mt-0.5 ${colorClass}`}>
                {q ? `${change > 0 ? "+" : ""}${change.toFixed(2)}%` : "—"}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StockCard({
  stock,
  quote,
  onClick,
}: {
  stock: StockInfo;
  quote?: QuoteItem;
  onClick: () => void;
}) {
  const change = quote?.change_pct ?? 0;
  const colorClass =
    change > 0 ? "text-[#ef4444]" : change < 0 ? "text-[#22c55e]" : "text-[#8890a0]";
  return (
    <div
      className="bg-[#1a1d2e] border border-[#2a2d3e] rounded-lg p-4 cursor-pointer hover:border-[#6366f1] transition-colors"
      onClick={onClick}
    >
      <div className="flex justify-between items-start">
        <div>
          <div className="font-medium text-sm">
            {MARKET_FLAG[stock.market]} {stock.name}
          </div>
          <div className="text-xs text-[#8890a0]">{stock.code}</div>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold">
            {quote ? `${CURRENCY[stock.market]}${quote.price.toFixed(2)}` : "—"}
          </div>
          <div className={`text-xs ${colorClass}`}>
            {quote ? `${change > 0 ? "+" : ""}${change.toFixed(2)}%` : "—"}
          </div>
        </div>
      </div>
    </div>
  );
}
