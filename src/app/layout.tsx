import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import { LanguageProvider } from "@/lib/i18n";
import GlobalControls from "@/components/GlobalControls";

export const metadata: Metadata = {
  title: "AIOps 知识图谱 — 智能运维学习路径",
  description:
    "一张可交互、基于图谱的学习路线图，覆盖基础设施、SRE 与 DevOps，并在其之上延伸出由大模型驱动的 AIOps 智能运维闭环。无论你是前端开发、AI 辅助编程者，还是运维新手——都能从“代码是什么”一路探索到生产级基础设施与智能运维。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="antialiased">
        {/* 防闪屏：在首屏渲染前根据 localStorage / 系统偏好提前加 .dark */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('theme');if(t==='dark'||(!t&&window.matchMedia('(prefers-color-scheme: dark)').matches)){document.documentElement.classList.add('dark');}}catch(e){}})();`,
          }}
        />
        <LanguageProvider>
          {children}
          <GlobalControls />
        </LanguageProvider>
        {process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN &&
          process.env.NEXT_PUBLIC_PLAUSIBLE_SCRIPT_URL && (
            <Script
              defer
              data-domain={process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN}
              src={process.env.NEXT_PUBLIC_PLAUSIBLE_SCRIPT_URL}
            />
          )}
      </body>
    </html>
  );
}
