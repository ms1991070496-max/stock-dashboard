"use client";

import { useState, useEffect } from "react";
import { getNews } from "@/lib/api";
import type { NewsItem } from "@/lib/types";

export default function NewsPage() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [filter, setFilter] = useState<"all" | "positive" | "neutral" | "negative">("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getNews("cn", 30)
      .then(setNews)
      .catch(() => setNews([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered =
    filter === "all"
      ? news
      : news.filter((n) => {
          const s = n.sentiment_score;
          if (filter === "positive") return s > 0.05;
          if (filter === "negative") return s < -0.05;
          return s >= -0.05 && s <= 0.05;
        });

  const posCount = news.filter((n) => n.sentiment_score > 0.05).length;
  const negCount = news.filter((n) => n.sentiment_score < -0.05).length;
  const neuCount = news.length - posCount - negCount;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">📰 市场新闻与情绪</h1>
      <p className="text-sm text-[#8890a0] mb-6">
        AI 情绪分析辅助判断市场热度
      </p>

      {/* Stats */}
      {news.length > 0 && (
        <div className="grid grid-cols-4 gap-3 mb-6">
          <StatBox label="总新闻" value={news.length} />
          <StatBox label="😊 正面" value={posCount} sub={`${((posCount / news.length) * 100).toFixed(0)}%`} />
          <StatBox label="😐 中性" value={neuCount} sub={`${((neuCount / news.length) * 100).toFixed(0)}%`} />
          <StatBox
            label="😟 负面"
            value={negCount}
            sub={`${((negCount / news.length) * 100).toFixed(0)}%`}
            subColor="text-[#ef4444]"
          />
        </div>
      )}

      {/* Filter */}
      <div className="flex gap-2 mb-4">
        {[
          { key: "all", label: "全部" },
          { key: "positive", label: "😊 正面" },
          { key: "neutral", label: "😐 中性" },
          { key: "negative", label: "😟 负面" },
        ].map((f) => (
          <button
            key={f.key}
            onClick={() => setFilter(f.key as typeof filter)}
            className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${
              filter === f.key
                ? "bg-[#6366f1]/20 border-[#6366f1] text-[#818cf8]"
                : "border-[#2a2d3e] text-[#8890a0] hover:border-[#444]"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* News list */}
      {loading ? (
        <div className="text-center py-12 text-[#8890a0]">加载中...</div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-12 text-[#8890a0]">暂无新闻</div>
      ) : (
        <div className="flex flex-col gap-2">
          {filtered.map((n, i) => {
            const s = n.sentiment_score;
            const emoji = s > 0.05 ? "😊" : s < -0.05 ? "😟" : "😐";
            const color = s > 0.05 ? "#22c55e" : s < -0.05 ? "#ef4444" : "#8890a0";
            return (
              <div
                key={i}
                className="bg-[#1a1d2e] border border-[#2a2d3e] rounded-lg p-3 flex items-center gap-3 hover:border-[#444] transition-colors"
              >
                <span style={{ color, fontSize: "1.2em" }}>{emoji}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm truncate">{n.title}</div>
                  <div className="text-xs text-[#8890a0]">
                    {n.source} · {n.published_at ?? ""}
                  </div>
                </div>
                <span className="text-xs" style={{ color }}>
                  {s > 0 ? "+" : ""}
                  {s.toFixed(2)}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function StatBox({
  label,
  value,
  sub,
  subColor,
}: {
  label: string;
  value: number;
  sub?: string;
  subColor?: string;
}) {
  return (
    <div className="bg-[#1a1d2e] border border-[#2a2d3e] rounded-lg p-3">
      <div className="text-xs text-[#8890a0]">{label}</div>
      <div className="text-xl font-bold mt-1">{value}</div>
      {sub && <div className={`text-xs mt-0.5 ${subColor ?? ""}`}>{sub}</div>}
    </div>
  );
}
