"use client";

import { useState } from "react";

const PRESETS = [
  { key: "value_stocks", label: "价值股 (低PE + 低PB + 高ROE)" },
  { key: "growth_stocks", label: "成长股 (高ROE + 合理PE)" },
  { key: "oversold", label: "超卖反弹 (RSI < 30)" },
  { key: "overbought", label: "超买警示 (RSI > 70)" },
];

export default function ScreenerPage() {
  const [preset, setPreset] = useState("");
  const [results, setResults] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(false);

  const handleRun = async () => {
    setLoading(true);
    try {
      const body = preset
        ? { preset }
        : { conditions: [] };
      const res = await fetch(`/api/v1/screener/run?market=all`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          preset
            ? { conditions: getPresetConditions(preset) }
            : { conditions: [] }
        ),
      });
      const data = await res.json();
      setResults(data.results ?? []);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">🔎 选股器</h1>
      <p className="text-sm text-[#8890a0] mb-6">预设策略快速筛选 · 自定义条件即将上线</p>

      <div className="flex gap-3 mb-6">
        <select
          value={preset}
          onChange={(e) => setPreset(e.target.value)}
          className="px-3 py-2 bg-[#1a1d2e] border border-[#2a2d3e] rounded-lg text-sm text-white outline-none focus:border-[#6366f1] min-w-[300px]"
        >
          <option value="">选择预设策略</option>
          {PRESETS.map((p) => (
            <option key={p.key} value={p.key}>
              {p.label}
            </option>
          ))}
        </select>
        <button
          onClick={handleRun}
          disabled={loading || !preset}
          className="px-6 py-2 bg-[#6366f1] hover:bg-[#5558e6] text-white text-sm rounded-lg transition-colors disabled:opacity-50"
        >
          {loading ? "筛选中..." : "开始筛选"}
        </button>
      </div>

      {results.length > 0 && (
        <div className="overflow-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#2a2d3e]">
                <th className="text-left py-2 px-3 text-[#8890a0] font-medium">名称</th>
                <th className="text-right py-2 px-3 text-[#8890a0] font-medium">代码</th>
                <th className="text-right py-2 px-3 text-[#8890a0] font-medium">价格</th>
                <th className="text-right py-2 px-3 text-[#8890a0] font-medium">涨跌幅</th>
                <th className="text-right py-2 px-3 text-[#8890a0] font-medium">市场</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => {
                const change = (r.change_pct as number) ?? 0;
                const color =
                  change > 0 ? "text-[#ef4444]" : change < 0 ? "text-[#22c55e]" : "";
                return (
                  <tr key={i} className="border-b border-[#1a1d2e] hover:bg-[#141725]">
                    <td className="py-2 px-3">
                      <a href={`/stock/${r.code}`} className="hover:text-[#6366f1] transition-colors">
                        {r.name as string}
                      </a>
                    </td>
                    <td className="text-right py-2 px-3 text-[#8890a0]">{r.code as string}</td>
                    <td className={`text-right py-2 px-3 font-mono`}>¥{(r.price as number)?.toFixed(2)}</td>
                    <td className={`text-right py-2 px-3 ${color}`}>
                      {change > 0 ? "+" : ""}
                      {change.toFixed(2)}%
                    </td>
                    <td className="text-right py-2 px-3 text-[#8890a0]">{r.market as string}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {results.length === 0 && !loading && (
        <div className="text-center py-12 text-[#8890a0]">
          选择策略并点击「开始筛选」查看结果
        </div>
      )}
    </div>
  );
}

function getPresetConditions(
  preset: string
): Array<{ field: string; operator: string; value: number }> {
  const map: Record<string, Array<{ field: string; operator: string; value: number }>> = {
    value_stocks: [
      { field: "pe", operator: "lt", value: 15 },
      { field: "pb", operator: "lt", value: 1.5 },
      { field: "roe", operator: "gt", value: 10 },
    ],
    growth_stocks: [
      { field: "roe", operator: "gt", value: 15 },
      { field: "pe", operator: "lt", value: 40 },
    ],
    oversold: [{ field: "rsi14", operator: "lt", value: 30 }],
    overbought: [{ field: "rsi14", operator: "gt", value: 70 }],
  };
  return map[preset] ?? [];
}
