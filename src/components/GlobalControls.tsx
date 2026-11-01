"use client";

import { useEffect, useState } from "react";
import { useLang } from "@/lib/i18n";

export default function GlobalControls() {
  const { lang, setLang } = useLang();
  const [dark, setDark] = useState(false);

  // 同步当前实际主题（class 由防 FOUC 脚本 / 切换函数管理）
  useEffect(() => {
    setDark(document.documentElement.classList.contains("dark"));
  }, []);

  const toggleTheme = () => {
    const next = !dark;
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("theme", next ? "dark" : "light");
    } catch {
      /* ignore */
    }
    setDark(next);
  };

  const toggleLang = () => {
    setLang(lang === "zh" ? "en" : "zh");
  };

  return (
    <div className="fixed top-3 right-3 z-[60] flex items-center gap-2">
      <button
        onClick={toggleLang}
        className="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white/90 dark:bg-gray-900/90 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800 backdrop-blur transition-colors shadow-sm"
        title={lang === "zh" ? "Switch to English" : "切换到中文"}
      >
        {lang === "zh" ? "中" : "EN"}
      </button>
      <button
        onClick={toggleTheme}
        className="p-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white/90 dark:bg-gray-900/90 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800 backdrop-blur transition-colors shadow-sm"
        title={dark ? "切换到浅色" : "切换到深色"}
      >
        <span className="text-base leading-none">{dark ? "🌙" : "☀️"}</span>
      </button>
    </div>
  );
}
