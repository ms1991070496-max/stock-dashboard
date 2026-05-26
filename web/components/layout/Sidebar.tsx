"use client";

import { useRouter, usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "大盘概览", icon: "📈" },
  { href: "/screener", label: "选股器", icon: "🔎" },
  { href: "/news", label: "新闻情绪", icon: "📰" },
];

export function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();

  return (
    <aside className="w-56 h-screen bg-[#141725] border-r border-[#2a2d3e] flex flex-col p-4 shrink-0">
      <div
        className="text-lg font-bold mb-8 cursor-pointer flex items-center gap-2"
        onClick={() => router.push("/")}
      >
        📊 股票分析
      </div>

      <nav className="flex flex-col gap-1 flex-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <button
              key={item.href}
              onClick={() => router.push(item.href)}
              className={`text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-[#6366f1]/20 text-[#818cf8] font-medium"
                  : "text-[#8890a0] hover:bg-[#1a1d2e] hover:text-white"
              }`}
            >
              <span className="mr-2">{item.icon}</span>
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="text-xs text-[#8890a0] mt-4 pt-4 border-t border-[#2a2d3e]">
        v0.2.0 · FastAPI + Next.js
      </div>
    </aside>
  );
}
