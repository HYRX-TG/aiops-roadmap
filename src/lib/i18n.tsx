"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

export type Lang = "zh" | "en";

/**
 * UI 外壳文案表。
 *
 * 为什么需要它：内容（节点正文）已经做了中英双语（ZH_* 块 + title_zh），
 * 但界面外壳（按钮/标题/提示）之前是硬编码中文——切到 EN 时只有正文变、
 * 外壳不变，看起来像"切换失败"。这里把外壳文案集中到一张表里。
 *
 * 约定：key 用英文语义名；缺 en 时回退 zh，缺两者时回退 key 本身，
 * 保证不会出现空白文案。
 */
const STRINGS: Record<string, { zh: string; en: string }> = {
  // ── 通用 ──
  "common.close": { zh: "关闭", en: "Close" },
  "common.back": { zh: "← 返回", en: "← Back" },
  "common.search": { zh: "搜索", en: "Search" },
  "common.settings": { zh: "设置", en: "Settings" },
  "common.help": { zh: "帮助", en: "Help" },
  "common.expandAll": { zh: "展开全部", en: "Expand all" },
  "common.collapseAll": { zh: "收起全部", en: "Collapse all" },
  "common.loadingGraph": { zh: "图谱加载中...", en: "Loading graph..." },
  "common.loadingMap": { zh: "地图加载中...", en: "Loading map..." },
  "common.view": { zh: "查看", en: "View" },
  "common.viewing": { zh: "查看中", en: "Viewing" },

  // ── 首页 / 分区图 ──
  "home.startExploring": { zh: "开始探索", en: "Start exploring" },
  "home.comingSoon": { zh: "敬请期待", en: "Coming soon" },
  "home.clickZone": { zh: "点分区进入", en: "Click a zone to enter" },
  "home.clickZoneHint": {
    zh: "首页每个彩色卡片是一个知识领域",
    en: "Each colored card on the home page is a knowledge zone",
  },
  "home.clickNode": { zh: "点节点看知识", en: "Click a node to read" },
  "home.clickNodeHint": {
    zh: "摘要 → 深入 → 里程碑，渐进式展开",
    en: "Summary → Deep dive → Milestones, revealed progressively",
  },
  "home.clickQuestion": { zh: "点问题气泡展开", en: "Click a question bubble" },
  "home.clickQuestionHint": {
    zh: "顺着「你会问什么」一路向下挖",
    en: "Follow “what would I ask next” as far as you like",
  },
  "home.notSureWhere": {
    zh: "不知道从哪开始？",
    en: "Not sure where to start?",
  },

  "home.topics": { zh: "个主题", en: "topics" },
  "home.tagline": {
    zh: "智能运维学习路径 — 点击分区开始探索",
    en: "An AIOps learning path — click a zone to start exploring",
  },
  "home.mastered": { zh: "已掌握", en: "Mastered" },
  "home.recommendAiops": {
    zh: "推荐：从 AIOps 智能运维开始",
    en: "Recommended: start with AIOps",
  },
  "home.whereToStart": { zh: "我从哪开始？", en: "Where do I start?" },
  "home.start": { zh: "开始", en: "Start" },
  "home.welcome": { zh: "欢迎来到 AIOps 知识图谱", en: "Welcome to the AIOps roadmap" },
  "home.intro": {
    zh: "用一棵会生长的知识树，把运维从「被动救火」学成「AI 闭环」。只需 3 步就能上手：",
    en: "Grow a knowledge tree and turn ops from firefighting into an AI-driven loop. Three steps to get going:",
  },

  // ── 帮助弹窗 ──
  "help.title": { zh: "使用说明", en: "How to use" },
  "help.subtitle": {
    zh: "一张可交互的技能地图：基础设施与 SRE",
    en: "An interactive skill map: infrastructure and SRE",
  },
  "help.step1.title": { zh: "点击任意主题打开它", en: "Click any topic to open it" },
  "help.step1.detail": {
    zh: "地图上的每个小方块都是一个主题。点击它即可阅读内容，并勾选完成里程碑。",
    en: "Every small box on the map is a topic. Click it to read the content and tick off milestones.",
  },
  "help.step2.title": {
    zh: "用问题方块选择你的路径",
    en: "Use question boxes to choose your path",
  },
  "help.step2.detail": {
    zh: "主题之间的小方块是问题——点击它会看到它将通向哪里，并选择你的下一个方向。",
    en: "The small boxes between topics are questions — click one to see where it leads and pick your next direction.",
  },
  "help.step3.title": { zh: "用 + 展开更多主题", en: "Use + to reveal more topics" },
  "help.step3.detail": {
    zh: "地图初始是紧凑的。点击任意主题方块上的 + 即可展开，查看接下来是什么。",
    en: "The map starts compact. Click the + on any topic box to expand and see what comes next.",
  },
  "help.step4.title": {
    zh: "随时把学过的主题标记为完成",
    en: "Mark topics as done whenever you finish",
  },
  "help.step4.detail": {
    zh: "打开一个主题，学完后点击“标记为已完成”。你的进度会保存在浏览器本地。",
    en: "Open a topic and click “Mark as complete” when done. Your progress is saved in your browser.",
  },

  // ── 入口选择 ──
  "entry.title": { zh: "你现在在什么位置？", en: "Where are you now?" },
  "entry.newbie": { zh: "我是技术纯新手", en: "I'm completely new to tech" },
  "entry.newbieDesc": {
    zh: "从零开始——代码是什么、计算机怎么工作、终端怎么用",
    en: "Start from zero — what code is, how computers work, how to use a terminal",
  },
  "entry.dev": { zh: "我会写代码，但不懂运维", en: "I code, but don't know ops" },
  "entry.devDesc": {
    zh: "你写过软件，却还没在真实服务器上跑过它",
    en: "You've written software but never run it on a real server",
  },
  "entry.linux": { zh: "我熟悉 Linux，想学云与 DevOps", en: "I know Linux, want cloud & DevOps" },
  "entry.linuxDesc": {
    zh: "习惯命令行，准备好扩展和运维服务",
    en: "Comfortable on the CLI, ready to scale and operate services",
  },
  "entry.sre": { zh: "我想学 SRE 与可靠性实践", en: "I want SRE & reliability practices" },
  "entry.sreDesc": {
    zh: "SLO、事故管理、on-call，以及如何专业地运维",
    en: "SLOs, incident management, on-call, and running things professionally",
  },
  "entry.selfhost": { zh: "我想自托管自己的服务", en: "I want to self-host my services" },
  "entry.selfhostDesc": {
    zh: "在自己掌控的硬件上跑应用——无订阅、隐私优先",
    en: "Run apps on hardware you control — no subscriptions, privacy first",
  },
  "entry.k8s": { zh: "我想学 Kubernetes", en: "I want to learn Kubernetes" },
  "entry.k8sDesc": {
    zh: "先从容器开始，再进入规模化编排",
    en: "Start with containers, then move to orchestration at scale",
  },
  "entry.aiops": { zh: "我想了解 AIOps / 智能运维", en: "I want to learn AIOps" },
  "entry.aiopsDesc": {
    zh: "在 SRE 与可观测性之上，用大模型实现监控、根因分析与自动化闭环",
    en: "On top of SRE and observability: LLM-driven monitoring, RCA, and closed-loop automation",
  },

  // ── 续学弹窗 ──
  "resume.title": { zh: "继续上次的学习？", en: "Resume where you left off?" },
  "resume.justNow": { zh: "刚刚", en: "just now" },
  "resume.minutesAgo": { zh: "{n} 分钟前", en: "{n} min ago" },
  "resume.hoursAgo": { zh: "{n} 小时前", en: "{n} h ago" },
  "resume.daysAgo": { zh: "{n} 天前", en: "{n} d ago" },
  "resume.always": { zh: "总是自动续学", en: "Always resume automatically" },
  "resume.ask": { zh: "每次都询问", en: "Ask every time" },
  "resume.never": { zh: "不再询问", en: "Never ask" },
  "resume.resume": { zh: "继续", en: "Resume" },
  "resume.startOver": { zh: "重新开始", en: "Start over" },

  // ── 设置页 ──
  "settings.title": { zh: "设置", en: "Settings" },
  "settings.export": { zh: "导出到文件", en: "Export to file" },
  "settings.import": { zh: "从文件导入", en: "Import from file" },
  "settings.downloaded": { zh: "已下载！", en: "Downloaded!" },
  "settings.fileTooLarge": { zh: "文件过大（最大 1MB）", en: "File too large (max 1MB)" },
  "settings.invalidArchive": { zh: "存档文件格式无效", en: "Invalid archive format" },
  "settings.parseFailed": {
    zh: "无法解析文件，请确认是有效的存档文件。",
    en: "Could not parse the file. Please make sure it is a valid archive.",
  },
  "settings.reset": { zh: "重置所有进度", en: "Reset all progress" },
  "settings.backendUrl": { zh: "AIOps 后端地址", en: "AIOps backend URL" },
  "settings.backendHint": {
    zh: "填写后 AI 助手面板走真实研判链路；留空则使用演示数据。",
    en: "When set, the AI panel uses the real diagnosis pipeline; leave empty for demo data.",
  },

  // ── AI 助手面板 ──
  "content.deepDive": { zh: "深入探究", en: "Deep dive" },
  "content.collapseDeepDive": { zh: "收起深入", en: "Collapse" },
  "content.milestones": { zh: "里程碑", en: "Milestones" },
  "content.resources": { zh: "参考资料", en: "Resources" },
  "content.markComplete": { zh: "标记为已完成", en: "Mark as complete" },
  "content.completed": { zh: "已完成", en: "Completed" },
  "content.difficulty1": { zh: "入门", en: "Beginner" },
  "content.difficulty2": { zh: "进阶", en: "Intermediate" },
  "content.difficulty3": { zh: "高级", en: "Advanced" },
  "content.catConcept": { zh: "概念", en: "Concept" },
  "content.catTool": { zh: "工具", en: "Tool" },
  "content.catPractice": { zh: "实践", en: "Practice" },
  "content.catPrinciple": { zh: "原理", en: "Principle" },
  "ai.diagnose": { zh: "诊断", en: "Diagnose" },
  "ai.runbook": { zh: "Runbook", en: "Runbook" },
  "ai.execute": { zh: "执行", en: "Execute" },
  "ai.thinking": { zh: "思考中…", en: "Thinking…" },
  "ai.known": { zh: "已知", en: "Known" },
  "ai.inferred": { zh: "推测", en: "Inferred" },
  "ai.uncertain": { zh: "无法确认", en: "Unconfirmed" },
  "ai.recommendation": { zh: "建议", en: "Recommendation" },
  "ai.sources": { zh: "知识来源", en: "Sources" },
  "ai.plan": { zh: "执行计划（dry-run）", en: "Execution plan (dry-run)" },
  "ai.blastRadius": { zh: "爆炸半径", en: "Blast radius" },
  "ai.approver": { zh: "审批人", en: "Approver" },
  "ai.approve": { zh: "确认执行", en: "Approve" },
  "ai.reject": { zh: "拒绝", en: "Reject" },
  "ai.degraded": {
    zh: "真后端联调失败，以下为演示数据（详见控制台）",
    en: "Backend call failed; showing demo data (see console)",
  },
};

function interpolate(s: string, vars?: Record<string, string | number>): string {
  if (!vars) return s;
  return s.replace(/\{(\w+)\}/g, (_, k) =>
    vars[k] !== undefined ? String(vars[k]) : `{${k}}`,
  );
}

interface LangCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  /** 取 UI 文案。缺 en 回退 zh，缺 key 回退 key 本身（开发期能立刻发现漏配）。 */
  t: (key: string, vars?: Record<string, string | number>) => string;
}

const LanguageContext = createContext<LangCtx>({
  lang: "zh",
  setLang: () => {},
  t: (k) => k,
});

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("zh");

  useEffect(() => {
    try {
      const saved = localStorage.getItem("lang");
      if (saved === "zh" || saved === "en") setLangState(saved);
    } catch {
      /* ignore */
    }
  }, []);

  // 语言变化时同步 <html lang>，让屏幕阅读器与浏览器翻译行为正确
  useEffect(() => {
    try {
      document.documentElement.lang = lang === "zh" ? "zh-CN" : "en";
    } catch {
      /* ignore */
    }
  }, [lang]);

  const setLang = (l: Lang) => {
    setLangState(l);
    try {
      localStorage.setItem("lang", l);
    } catch {
      /* ignore */
    }
  };

  const t = (key: string, vars?: Record<string, string | number>): string => {
    const entry = STRINGS[key];
    if (!entry) return key;
    const raw = lang === "en" ? entry.en || entry.zh : entry.zh || entry.en;
    return interpolate(raw, vars);
  };

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLang() {
  return useContext(LanguageContext);
}

/** 只取翻译函数的便捷钩子 */
export function useT() {
  return useContext(LanguageContext).t;
}
