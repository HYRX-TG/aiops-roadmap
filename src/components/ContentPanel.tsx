"use client";

import { useState, useEffect, useCallback } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { RoadmapNode, NodeProgress } from "@/lib/types";
import { useLang, useT } from "@/lib/i18n";
import { runAiEngine, submitApproval, getBackendUrl, setBackendUrl } from "@/lib/aiEngine";

const markdownComponents = {
  a: ({ href, children, ...props }: React.ComponentPropsWithoutRef<"a">) => (
    <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
      {children}
    </a>
  ),
};
import { getNodeProgress, setNodeStatus, toggleMilestone, setLastNode } from "@/lib/progress";

interface ContentPanelProps {
  node: RoadmapNode | null;
  onClose: () => void;
  onNavigate: (nodeId: string) => void;
  onProgressChange: () => void;
  zoneId: string;
  zoneTitle: string;
}

export default function ContentPanel({
  node,
  onClose,
  onNavigate,
  onProgressChange,
  zoneId,
  zoneTitle,
}: ContentPanelProps) {
  const { lang } = useLang();
  const t = useT();
  const [showDeepDive, setShowDeepDive] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [celebrate, setCelebrate] = useState(false);
  const [progress, setProgress] = useState<NodeProgress>({
    status: "not-started",
    milestones: [],
  });

  const refreshProgress = useCallback(() => {
    if (node) {
      setProgress(getNodeProgress(node.frontmatter.id));
    }
  }, [node]);

  useEffect(() => {
    refreshProgress();
    setShowDeepDive(false);
    if (node) {
      setLastNode(node.frontmatter.id, zoneId, node.frontmatter.title, zoneTitle);
    }
  }, [refreshProgress, node, zoneId, zoneTitle]);

  // Close on Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!node) return null;

  const { frontmatter, summary, deepDive, resources } = node;
  const showTitle =
    lang === "zh" ? (node.titleZh || frontmatter.title) : (node.titleEn || frontmatter.title);
  // 自研 aiops 分区是中文原创内容，没有英文正文；EN 模式下如实标注，
  // 而不是假装已翻译（宁可显示边界，也不让读者以为是翻译没加载）。
  const zhOnlyContent = lang === "en" && !node.summaryZh && /[一-鿿]/.test(summary);
  const showSummary =
    lang === "zh" && node.summaryZh ? node.summaryZh : summary;
  const deepDiveText =
    lang === "zh" && node.deepDiveZh ? node.deepDiveZh : deepDive;
  const showResources =
    lang === "zh" && node.resourcesZh ? node.resourcesZh : resources;

  const handleToggleMilestone = (index: number) => {
    toggleMilestone(frontmatter.id, index);
    refreshProgress();
    onProgressChange();
  };

  const handleMarkComplete = () => {
    const newStatus = progress.status === "completed" ? "not-started" : "completed";
    setNodeStatus(frontmatter.id, newStatus);
    refreshProgress();
    onProgressChange();
    if (newStatus === "completed") {
      setCelebrate(true);
      window.setTimeout(() => setCelebrate(false), 2600);
    }
  };

  // Upstream edit link only makes sense for the forked (non-aiops) zones.
  const isSelfAuthored = zoneId === "aiops";
  const editUrl = `https://github.com/MansoorMajeed/infra-roadmap/edit/main/content/${frontmatter.zone}/${frontmatter.id}.md`;

  const difficultyLabel = { 1: t("content.difficulty1"), 2: t("content.difficulty2"), 3: t("content.difficulty3") };
  const categoryLabel: Record<string, string> = {
    concept: t("content.catConcept"),
    tool: t("content.catTool"),
    practice: t("content.catPractice"),
    principle: t("content.catPrinciple"),
  };
  const difficultyColor = {
    1: "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
    2: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300",
    3: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/40 z-50"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-0 sm:p-4 pointer-events-none">
        <div
          className={`bg-white dark:bg-gray-900 shadow-2xl w-full flex flex-col pointer-events-auto border border-gray-200 dark:border-gray-700 transition-all duration-200 ${
            isExpanded
              ? "max-w-full max-h-full h-full rounded-none sm:m-4 sm:rounded-2xl sm:max-h-[calc(100vh-2rem)] sm:max-w-[calc(100vw-2rem)]"
              : "max-w-2xl max-h-[100vh] h-full rounded-none sm:max-h-[85vh] sm:h-auto sm:rounded-2xl"
          }`}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-start justify-between p-6 pb-4 border-b border-gray-100 dark:border-gray-800">
            <div className="flex-1 pr-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 leading-tight">
                {showTitle}
              </h2>
              <div className="flex flex-wrap gap-2 mt-2">
                <span
                  className={`text-xs font-medium px-2.5 py-1 rounded-full ${difficultyColor[frontmatter.difficulty]}`}
                >
                  {difficultyLabel[frontmatter.difficulty]}
                </span>
                <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400">
                  {categoryLabel[frontmatter.category] ?? frontmatter.category}
                </span>
                {frontmatter.tags.slice(0, 3).map((tag) => (
                  <span
                    key={tag}
                    className="text-xs px-2 py-1 rounded-full bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                title={isExpanded ? "收起" : "展开"}
              >
                {isExpanded ? (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 9L4 4m0 0v4m0-4h4m7 11l5 5m0 0v-4m0 4h-4" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 3h6m0 0v6m0-6L14 10M9 21H3m0 0v-6m0 6l7-7" />
                  </svg>
                )}
              </button>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto overscroll-contain p-6">
          <div className={`space-y-6 ${isExpanded ? "max-w-3xl mx-auto" : ""}`}>
            {zhOnlyContent && (
              <div className="flex items-start gap-2 rounded-lg border border-amber-200 dark:border-amber-800/60 bg-amber-50 dark:bg-amber-950/30 px-3 py-2">
                <span className="text-sm shrink-0">🌐</span>
                <p className="text-xs text-amber-800 dark:text-amber-300 leading-relaxed">
                  This section is original Chinese content (self-authored AIOps notes);
                  an English translation is not available yet.
                </p>
              </div>
            )}

            {/* Summary */}
            <div className="content-prose">
              <Markdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{showSummary}</Markdown>
            </div>

            {/* Deep Dive */}
            {deepDiveText && (
              <div>
                <button
                  onClick={() => setShowDeepDive(!showDeepDive)}
                  className="flex items-center gap-2 text-sm font-semibold text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
                >
                  <svg
                    className={`w-4 h-4 transition-transform ${showDeepDive ? "rotate-90" : ""}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  {showDeepDive ? t("content.collapseDeepDive") : t("content.deepDive")}
                </button>
                {showDeepDive && (
                  <div className="mt-4 pl-4 border-l-2 border-blue-200 dark:border-blue-800">
                    <div className="content-prose">
                      <Markdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{deepDiveText}</Markdown>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Divider */}
            {(frontmatter.milestones.length > 0 || showResources) && (
              <hr className="border-gray-100 dark:border-gray-800" />
            )}

            {/* Milestones */}
            {frontmatter.milestones.length > 0 && (
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-3">
                  {t("content.milestones")}
                </h3>
                <ul className="space-y-2.5">
                  {frontmatter.milestones.map((milestone, i) => {
                    const milestoneText =
                      lang === "zh" && node.milestonesZh?.[i]
                        ? node.milestonesZh[i]
                        : milestone;
                    return (
                      <li key={i} className="flex items-start gap-3">
                        <input
                          type="checkbox"
                          checked={progress.milestones[i] || false}
                          onChange={() => handleToggleMilestone(i)}
                          className="mt-0.5 w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                        />
                        <span
                          className={`text-sm leading-relaxed ${
                            progress.milestones[i]
                              ? "text-gray-400 line-through"
                              : "text-gray-700 dark:text-gray-300"
                          }`}
                        >
                          {milestoneText}
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {/* Resources */}
            {showResources && (
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-3">
                  {t("content.resources")}
                </h3>
                <div className="content-prose content-prose-links">
                  <Markdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{showResources}</Markdown>
                </div>
              </div>
            )}

            {/* Divider */}
            {frontmatter.edges.to && frontmatter.edges.to.length > 0 && (
              <hr className="border-gray-100 dark:border-gray-800" />
            )}

            {/* Where to go next */}
            {frontmatter.edges.to && frontmatter.edges.to.length > 0 && (
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-3">
                  下一步去哪？
                </h3>
                <div className="space-y-2">
                  {frontmatter.edges.to.map((edge, i) => {
                    const questionText =
                      lang === "zh" && node.edgeQuestionsZh?.[i]
                        ? node.edgeQuestionsZh[i]
                        : edge.question;
                    return (
                      <button
                        key={edge.id}
                        onClick={() => onNavigate(edge.id)}
                        className="w-full text-left p-4 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700 hover:bg-blue-50/50 dark:hover:bg-blue-950/20 transition-all group"
                      >
                        <p className="text-sm italic text-gray-500 dark:text-gray-400 leading-relaxed">
                          &ldquo;{questionText}&rdquo;
                        </p>
                        <p className="text-sm font-semibold text-blue-600 dark:text-blue-400 mt-1.5 group-hover:text-blue-700 dark:group-hover:text-blue-300">
                          → {edge.id
                            .split("-")
                            .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                            .join(" ")}
                        </p>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* AI 助手面板：仅自研 aiops 分区展示（自研功能主入口） */}
            {isSelfAuthored && (
              <AiAssistantPanel nodeId={frontmatter.id} />
            )}
          </div>
          </div>

          {/* Footer */}
          <div className={`p-4 border-t border-gray-100 dark:border-gray-800 ${isExpanded ? "flex justify-center" : ""}`}>
          <div className={`space-y-2 ${isExpanded ? "max-w-3xl w-full" : ""}`}>
            <button
              onClick={handleMarkComplete}
              className={`w-full py-2.5 px-4 rounded-xl text-sm font-semibold transition-colors ${
                progress.status === "completed"
                  ? "bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 border border-green-200 dark:border-green-800 hover:bg-green-100 dark:hover:bg-green-900/30"
                  : "bg-blue-600 text-white hover:bg-blue-700 shadow-sm"
              }`}
            >
              {progress.status === "completed"
                ? "✓ 已完成 — 点击撤销"
                : "标记为已完成"}
            </button>
            {!isSelfAuthored && (
              <a
                href={editUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full py-2 px-4 rounded-xl text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M17.263 2.177a1.75 1.75 0 0 1 2.474 0l2.086 2.086a1.75 1.75 0 0 1 0 2.474L10.98 17.58a1.75 1.75 0 0 1-.765.455l-4.473 1.286a.75.75 0 0 1-.926-.927l1.287-4.473a1.75 1.75 0 0 1 .455-.764L17.263 2.177z" />
                </svg>
                在 GitHub 上改进此页
              </a>
            )}
          </div>
          </div>
        </div>
      </div>

      {/* Completion celebration toast */}
      {celebrate && (
        <div className="fixed top-6 left-1/2 -translate-x-1/2 z-[70] px-5 py-3 rounded-xl bg-emerald-600 text-white text-sm font-semibold shadow-lg flex items-center gap-2 animate-slide-up">
          🎉 完成！已掌握「{showTitle}」
        </div>
      )}
    </>
  );
}

// ───────────────────────────────────────────────────────────
// AIOps 自研「AI 助手」面板（仅 aiops 分区渲染）
// 设计来自运维平台调研：人是主导（已知/推测/无法确认）、高危操作有摩擦、状态清晰。
// 真实接线在 /api/ai：夜莺 MCP → HolmesGPT → RAGFlow → Dify → StackStorm。
// ───────────────────────────────────────────────────────────
interface AiResult {
  summary?: string;
  inferred?: string[];
  uncertain?: string[];
  recommendation?: string;
  evidence?: string[];
  sources?: string[];
  plan?: string[];
  blastRadius?: string;
  requiresApprover?: string;
  runId?: string;        // 后端工作流 run id（真后端模式下审批回传）
  backendAction?: string; // 后端护栏动作名（rollback/scale_up/...）
}

type AiState = "idle" | "loading" | "done" | "pending_approval" | "failed";

function AiAssistantPanel({ nodeId }: { nodeId: string }) {
  const [aiState, setAiState] = useState<AiState>("idle");
  const [aiAction, setAiAction] = useState<string>("");
  const [res, setRes] = useState<AiResult | null>(null);
  const [err, setErr] = useState<string>("");
  const [approval, setApproval] = useState<"pending" | "approved" | "rejected">("pending");
  const [approveMsg, setApproveMsg] = useState<string>("");
  // 真后端联调失败 → 回退演示数据时必须显示警示（杜绝"界面正常但其实全是 mock"的静默降级）
  const [degraded, setDegraded] = useState<string>("");

  const run = async (action: string) => {
    setAiAction(action);
    setAiState("loading");
    setErr("");
    setDegraded("");
    setApproval("pending");
    setApproveMsg("");
    try {
      const data = await runAiEngine({ nodeId, action });
      if (!data.ok) {
        setAiState("failed");
        setErr(data.decision.reason || "请求失败");
        return;
      }
      setRes(data.result as AiResult);
      setDegraded(data.degradedFromBackend ? "真后端联调失败，以下为演示数据（详见控制台）" : "");
      const s = data.state;
      setAiState(s === "pending_approval" ? "pending_approval" : s === "done" ? "done" : "failed");
    } catch {
      setAiState("failed");
      setErr("执行出错，请重试");
    }
  };

  const List = ({ items, color }: { items: string[]; color: string }) => (
    <ul className="space-y-1.5">
      {items.map((it, i) => (
        <li key={i} className={`text-sm leading-relaxed ${color}`}>
          · {it}
        </li>
      ))}
    </ul>
  );

  return (
    <div className="rounded-2xl border border-teal-200 dark:border-teal-800 bg-teal-50/60 dark:bg-teal-950/20 p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg">🤖</span>
          <h3 className="text-sm font-bold text-teal-700 dark:text-teal-300">AI 助手 · 智能运维闭环</h3>
        </div>
        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-teal-100 dark:bg-teal-900/50 text-teal-600 dark:text-teal-400">
          演示
        </span>
      </div>
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-4 leading-relaxed">
        把「监控接入 → 根因分析 → 取知识 → 编排执行」串起来。执行权始终在你手里——
        AI 只给建议，高危操作必须人工审批。
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-4">
        <button
          onClick={() => run("diagnose")}
          disabled={aiState === "loading"}
          className="py-2.5 px-3 rounded-xl text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          🤖 AI 诊断
        </button>
        <button
          onClick={() => run("runbook")}
          disabled={aiState === "loading"}
          className="py-2.5 px-3 rounded-xl text-sm font-semibold bg-teal-600 text-white hover:bg-teal-700 disabled:opacity-50 transition-colors"
        >
          📚 取 Runbook
        </button>
        <button
          onClick={() => run("execute")}
          disabled={aiState === "loading"}
          className="py-2.5 px-3 rounded-xl text-sm font-semibold bg-amber-500 text-white hover:bg-amber-600 disabled:opacity-50 transition-colors"
          title="高危操作，需人工审批"
        >
          ⚡ 一键执行（待审批）
        </button>
      </div>

      {aiState === "loading" && (
        <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 py-2">
          <span className="inline-block w-4 h-4 border-2 border-gray-300 border-t-teal-500 rounded-full animate-spin" />
          思考中…（{aiAction === "execute" ? "生成执行计划并过护栏" : "调取实时数据与知识"}）
        </div>
      )}

      {aiState === "failed" && (
        <div className="text-sm text-red-600 dark:text-red-400 py-2">⚠️ {err || "出错了"}</div>
      )}

      {degraded && (
        <div className="text-xs font-semibold text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-700 rounded-xl px-3 py-2 mb-3">
          ⚠️ {degraded}
        </div>
      )}

      {res && (aiState === "done" || aiState === "pending_approval") && (
        <div className="space-y-3">
          {res.summary && (
            <div className="rounded-xl bg-white/70 dark:bg-gray-800/60 p-3 border border-gray-200 dark:border-gray-700">
              <p className="text-[11px] font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 mb-1">
                🟢 已知（基于真实数据）
              </p>
              <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{res.summary}</p>
            </div>
          )}
          {res.inferred && res.inferred.length > 0 && (
            <div className="rounded-xl bg-white/70 dark:bg-gray-800/60 p-3 border border-gray-200 dark:border-gray-700">
              <p className="text-[11px] font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400 mb-1">
                🟡 推测（AI 推断）
              </p>
              <List items={res.inferred} color="text-gray-700 dark:text-gray-300" />
            </div>
          )}
          {res.uncertain && res.uncertain.length > 0 && (
            <div className="rounded-xl bg-white/70 dark:bg-gray-800/60 p-3 border border-gray-200 dark:border-gray-700">
              <p className="text-[11px] font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1">
                ⚪ 无法确认（缺少证据）
              </p>
              <List items={res.uncertain} color="text-gray-500 dark:text-gray-400" />
            </div>
          )}

          {aiState === "pending_approval" && res.plan && (
            <div className="rounded-xl bg-amber-50 dark:bg-amber-950/20 p-3 border border-amber-300 dark:border-amber-800">
              <p className="text-[11px] font-bold uppercase tracking-wider text-amber-700 dark:text-amber-400 mb-1">
                ⚡ 执行计划（dry-run · 待审批）
              </p>
              <ol className="space-y-1.5 list-decimal list-inside text-sm text-gray-700 dark:text-gray-300">
                {res.plan.map((step, i) => (
                  <li key={i} className="leading-relaxed">{step}</li>
                ))}
              </ol>
              <div className="flex flex-wrap gap-2 mt-2 text-[11px]">
                {res.blastRadius && (
                  <span className="px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300">
                    爆炸半径：{res.blastRadius}
                  </span>
                )}
                {res.requiresApprover && (
                  <span className="px-2 py-0.5 rounded-full bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-300">
                    审批人：{res.requiresApprover}
                  </span>
                )}
              </div>
            </div>
          )}

          {res.recommendation && (
            <div className="rounded-xl bg-emerald-50 dark:bg-emerald-950/20 p-3 border border-emerald-300 dark:border-emerald-800">
              <p className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 dark:text-emerald-400 mb-1">
                💡 建议
              </p>
              <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{res.recommendation}</p>
            </div>
          )}

          {(res.evidence || res.sources) && (
            <div className="text-[11px] text-gray-400 dark:text-gray-500">
              证据：{(res.evidence || res.sources || []).join(" · ")}
            </div>
          )}

          {aiState === "pending_approval" && (
            <div className="pt-1">
              {approval === "pending" ? (
                <div className="flex gap-2">
                  <button
                    onClick={async () => {
                      setApproval("approved");
                      // 真后端模式：把审批决定写回服务端护栏审计；mock 模式仅本地状态
                      if (res?.runId && res?.backendAction) {
                        const r = await submitApproval(res.runId, res.backendAction, "approved");
                        setApproveMsg(r ? `后端回执：${r.msg}` : "后端不可达，审批仅在本地记录");
                      }
                    }}
                    className="flex-1 py-2 rounded-xl text-sm font-semibold bg-emerald-600 text-white hover:bg-emerald-700 transition-colors"
                  >
                    ✅ 确认执行
                  </button>
                  <button
                    onClick={async () => {
                      setApproval("rejected");
                      if (res?.runId && res?.backendAction) {
                        await submitApproval(res.runId, res.backendAction, "rejected");
                        setApproveMsg("已拒绝，决定已同步后端审计");
                      }
                    }}
                    className="flex-1 py-2 rounded-xl text-sm font-semibold bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                  >
                    ❌ 拒绝
                  </button>
                </div>
              ) : approval === "approved" ? (
                <div className="text-sm text-emerald-600 dark:text-emerald-400 font-medium">
                  ✓ 已提交执行（{getBackendUrl() ? "后端已放行，真实环境由 StackStorm/Ansible 承接并回传状态" : "演示：真实环境将交由 StackStorm 执行并持续回传状态"}）
                  {approveMsg && <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1">{approveMsg}</div>}
                </div>
              ) : (
                <div className="text-sm text-gray-500 dark:text-gray-400 font-medium">
                  已拒绝，未做任何变更。
                  {approveMsg && <div className="text-[11px] text-gray-400 dark:text-gray-500 mt-1">{approveMsg}</div>}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-3">
        逻辑：src/lib/aiEngine.ts（真后端优先，mock 兜底）。后端 = backend/ 目录 FastAPI：
        7源接入→去重降噪→P0-P3分流→持久化工作流→RAGFlow→研判→护栏→dry-run 计划，密钥不出服务端。
        在下方填后端地址即可切真数据模式。
      </p>
      <div className="flex items-center gap-2 mt-2">
        <input
          type="text"
          defaultValue={getBackendUrl()}
          placeholder="后端地址，如 http://127.0.0.1:8600（留空 = 演示模式）"
          className="flex-1 text-xs px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-teal-500"
          onBlur={(e) => setBackendUrl(e.target.value)}
        />
      </div>
    </div>
  );
}
