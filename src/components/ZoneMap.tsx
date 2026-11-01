"use client";

import { useCallback, useMemo, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  ReactFlow,
  Background,
  Handle,
  Position,
  type Node,
  type Edge,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { Zone, ZoneEdge, SearchableNode } from "@/lib/types";
import { getCompletedCount, getLastNode, getResumePref, setResumePref } from "@/lib/progress";
import type { LastNode } from "@/lib/progress";
import EntryPointSelector from "./EntryPointSelector";
import { useT } from "@/lib/i18n";
import SearchModal from "./SearchModal";
import HelpModal from "./HelpModal";
import ResumeModal from "./ResumeModal";

interface ZoneMapProps {
  zones: Zone[];
  zoneEdges: ZoneEdge[];
  zoneNodeIds: Record<string, string[]>;
  searchableNodes: SearchableNode[];
}


function ZoneNode({ data }: { data: Record<string, unknown> }) {
  const t = useT();
  const zone = data as unknown as Zone & {
    nodeCount: number;
    completedCount: number;
  };
  const progress =
    zone.nodeCount > 0
      ? Math.round((zone.completedCount / zone.nodeCount) * 100)
      : 0;

  return (
    <div
      className={`rounded-2xl border-2 p-5 min-w-[220px] max-w-[260px] shadow-lg transition-all ${
        zone.active
          ? "cursor-pointer hover:shadow-xl hover:scale-[1.02]"
          : "opacity-50 cursor-default"
      }`}
      style={{ borderColor: zone.color, backgroundColor: `${zone.color}10` }}
    >
      <Handle type="target" position={Position.Top} className="!bg-transparent !border-0 !w-0 !h-0" />
      <div
        className="text-xs font-bold uppercase tracking-wider mb-1"
        style={{ color: zone.color }}
      >
        {zone.active ? t("home.startExploring") : t("home.comingSoon")}
      </div>
      <h3 className="text-base font-bold text-gray-900 dark:text-gray-100 mb-1">
        {zone.title}
      </h3>
      <p className="text-sm italic text-gray-600 dark:text-gray-400 mb-3">
        &ldquo;{zone.coreQuestion}&rdquo;
      </p>
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500 dark:text-gray-400">
          {zone.nodeCount} {t("home.topics")}
        </span>
        {zone.active && zone.nodeCount > 0 && (
          <div className="flex items-center gap-2">
            <div className="w-16 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{ width: `${progress}%`, backgroundColor: zone.color }}
              />
            </div>
            <span className="text-xs text-gray-500">{progress}%</span>
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-transparent !border-0 !w-0 !h-0" />
    </div>
  );
}

const nodeTypes = { zone: ZoneNode };

export default function ZoneMap({
  zones,
  zoneEdges,
  zoneNodeIds,
  searchableNodes,
}: ZoneMapProps) {
  const router = useRouter();
  const t = useT();
  const [showEntrySelector, setShowEntrySelector] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [completedCounts, setCompletedCounts] = useState<Record<string, number>>({});
  const [resumeCandidate, setResumeCandidate] = useState<LastNode | null>(null);
  const [showResumeToast, setShowResumeToast] = useState(false);
  const [continueTarget, setContinueTarget] = useState<LastNode | null>(null);
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    const counts: Record<string, number> = {};
    for (const [zoneId, nodeIds] of Object.entries(zoneNodeIds)) {
      counts[zoneId] = getCompletedCount(nodeIds);
    }
    setCompletedCounts(counts);
  }, [zoneNodeIds]);

  // Resume logic — check on mount
  useEffect(() => {
    const lastNode = getLastNode();
    if (!lastNode) return;

    const SESSION_KEY = "infra-roadmap-session-active";
    const isReturningUser = !sessionStorage.getItem(SESSION_KEY);
    sessionStorage.setItem(SESSION_KEY, "1");

    if (isReturningUser) {
      // New session — show modal or auto-navigate based on pref
      const pref = getResumePref();
      if (pref === "always") {
        setShowResumeToast(true);
        const timer = setTimeout(() => {
          router.push(`/${lastNode.zoneId}?focus=${lastNode.nodeId}`);
        }, 800);
        return () => clearTimeout(timer);
      }
      if (pref === "ask") {
        setResumeCandidate(lastNode);
        setContinueTarget(lastNode); // fallback if modal dismissed
      }
      // pref === "never" — no UI at all
      return;
    }

    // In-session (back from zone) — show continue button
    setContinueTarget(lastNode);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    try {
      if (localStorage.getItem("infra-roadmap-help-seen") !== "true") {
        setShowHelp(true);
      }
    } catch {
      // ignore
    }
  }, []);

  // First-run onboarding — only show once, never blocks return visits
  useEffect(() => {
    try {
      if (localStorage.getItem("aiops-roadmap-onboarded") !== "true") {
        setShowOnboarding(true);
      }
    } catch {
      // ignore
    }
  }, []);

  const dismissOnboarding = () => {
    try {
      localStorage.setItem("aiops-roadmap-onboarded", "true");
    } catch {
      // ignore
    }
    setShowOnboarding(false);
  };

  const dismissHelp = () => {
    try {
      localStorage.setItem("infra-roadmap-help-seen", "true");
    } catch {
      // ignore
    }
    setShowHelp(false);
  };

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setShowSearch((prev) => !prev);
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, []);

  const initialNodes: Node[] = useMemo(
    () =>
      zones.map((zone) => ({
        id: zone.id,
        type: "zone",
        position: zone.position,
        data: {
          ...zone,
          nodeCount: zoneNodeIds[zone.id]?.length ?? 0,
          completedCount: completedCounts[zone.id] ?? 0,
        },
      })),
    [zones, zoneNodeIds, completedCounts]
  );

  const initialEdges: Edge[] = useMemo(
    () =>
      zoneEdges.map((e, i) => ({
        id: `zone-edge-${i}`,
        source: e.from,
        target: e.to,
        animated: true,
        style: { stroke: "#94a3b8", strokeWidth: 2 },
      })),
    [zoneEdges]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  // Sync nodes when completedCounts change (useNodesState only initializes once)
  useEffect(() => {
    setNodes(initialNodes);
  }, [completedCounts]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const zone = zones.find((z) => z.id === node.id);
      if (zone?.active) {
        router.push(`/${zone.id}`);
      }
    },
    [zones, router]
  );

  const handleEntrySelect = (zone: string, nodeId: string) => {
    setShowEntrySelector(false);
    const targetZone = zones.find((z) => z.id === zone);
    if (targetZone?.active) {
      router.push(`/${zone}?node=${nodeId}`);
    }
  };

  const totalCompleted = Object.values(completedCounts).reduce((a, b) => a + b, 0);
  const totalNodes = Object.values(zoneNodeIds).reduce((a, ids) => a + ids.length, 0);
  const overallPct = totalNodes > 0 ? Math.round((totalCompleted / totalNodes) * 100) : 0;
  const isFreshStart = totalCompleted === 0;

  return (
    <div className="w-full h-full relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
      </ReactFlow>

      {/* Top bar */}
      <div className="absolute top-4 left-4 right-4 flex items-center justify-between pointer-events-none">
        <div className="shrink-0">
          <h1 className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
            AIOps 知识图谱
          </h1>
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400 hidden sm:block">
            {t("home.tagline")}
          </p>
          {totalNodes > 0 && (
            <div className="hidden sm:flex items-center gap-2 mt-2">
              <div className="flex items-center gap-1.5 text-xs font-medium text-gray-500 dark:text-gray-400">
                <span>🎓 {t("home.mastered")}</span>
                <div className="w-20 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-emerald-500 transition-all"
                    style={{ width: `${overallPct}%` }}
                  />
                </div>
                <span className="tabular-nums">{overallPct}%</span>
                <span className="text-gray-400 dark:text-gray-500">（{totalCompleted}/{totalNodes}）</span>
              </div>
            </div>
          )}
        </div>
        {isFreshStart && (
          <button
            onClick={() => router.push("/aiops")}
            className="hidden md:flex pointer-events-auto items-center gap-1.5 px-3 py-1.5 rounded-full bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 text-teal-700 dark:text-teal-300 text-xs font-medium hover:bg-teal-100 dark:hover:bg-teal-950/70 transition-colors"
          >
            🤖 {t("home.recommendAiops")}
          </button>
        )}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSearch(true)}
            className="pointer-events-auto px-3 py-2 rounded-xl bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border border-gray-200 dark:border-gray-700 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 shadow-sm transition-colors flex items-center gap-2"
          >
            <span>🔍</span>
            <span className="hidden sm:inline">{t("common.search")}</span>
            <kbd className="hidden sm:inline text-xs border border-gray-200 dark:border-gray-600 rounded px-1">⌘K</kbd>
          </button>
          <button
            onClick={() => setShowHelp(true)}
            className="pointer-events-auto w-9 h-9 rounded-xl bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 shadow-sm transition-colors flex items-center justify-center font-semibold"
            title={t("common.help")}
            aria-label={t("common.help")}
          >
            ?
          </button>
          <button
            onClick={() => router.push("/settings")}
            className="pointer-events-auto w-9 h-9 rounded-xl bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 shadow-sm transition-colors flex items-center justify-center"
            title={t("common.settings")}
            aria-label={t("common.settings")}
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </button>
          {continueTarget && !resumeCandidate && (
            <button
              onClick={() => router.push(`/${continueTarget.zoneId}?focus=${continueTarget.nodeId}`)}
              className="pointer-events-auto hidden sm:flex px-4 py-2 rounded-xl bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border border-blue-300 dark:border-blue-700 text-sm font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/30 shadow-sm transition-colors items-center gap-1.5"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M12 5l7 7-7 7" />
              </svg>
              {t("resume.resume")}
            </button>
          )}
          <button
            onClick={() => setShowEntrySelector(true)}
            className="pointer-events-auto px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors shadow-lg"
          >
            <span className="hidden sm:inline">{t("home.whereToStart")}</span>
            <span className="sm:hidden">{t("home.start")}</span>
          </button>
        </div>
      </div>

      {/* Bottom bar — hidden on mobile */}
      <div className="absolute bottom-4 left-4 hidden sm:flex items-stretch gap-2 pointer-events-none">
        <a
          href="https://github.com/MansoorMajeed/infra-roadmap"
          target="_blank"
          rel="noopener noreferrer"
          className="pointer-events-auto px-4 rounded-lg bg-white/70 dark:bg-gray-900/70 backdrop-blur-sm border border-gray-200 dark:border-gray-700 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors flex items-center"
        >
          ★ GitHub 源码
        </a>
        <a
          href="https://blog.esc.sh"
          target="_blank"
          rel="noopener noreferrer"
          className="pointer-events-auto px-4 rounded-lg bg-white/70 dark:bg-gray-900/70 backdrop-blur-sm border border-gray-200 dark:border-gray-700 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors flex items-center"
        >
          博客
        </a>
        <a
          href="https://blog.esc.sh/#/portal/signup"
          target="_blank"
          rel="noopener noreferrer"
          className="pointer-events-auto px-4 rounded-lg bg-white/70 dark:bg-gray-900/70 backdrop-blur-sm border border-gray-200 dark:border-gray-700 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors flex items-center"
        >
          订阅更新
        </a>
      </div>

      {/* Mobile continue button — bottom */}
      {continueTarget && !resumeCandidate && (
        <div className="absolute bottom-4 left-4 right-4 sm:hidden flex justify-center pointer-events-none">
          <button
            onClick={() => router.push(`/${continueTarget.zoneId}?focus=${continueTarget.nodeId}`)}
            className="pointer-events-auto px-5 py-2.5 rounded-xl bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm border border-blue-300 dark:border-blue-700 text-sm font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-950/30 shadow-lg transition-colors flex items-center gap-2"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M12 5l7 7-7 7" />
            </svg>
            继续：{continueTarget.nodeTitle}
          </button>
        </div>
      )}

      <SearchModal
        nodes={searchableNodes}
        isOpen={showSearch}
        onClose={() => setShowSearch(false)}
      />

      {showEntrySelector && (
        <EntryPointSelector
          onSelect={handleEntrySelect}
          onClose={() => setShowEntrySelector(false)}
        />
      )}

      {showHelp && (
        <HelpModal
          onClose={dismissHelp}
          onShowEntrySelector={() => {
            dismissHelp();
            setShowEntrySelector(true);
          }}
        />
      )}

      {resumeCandidate && (
        <ResumeModal
          lastNode={resumeCandidate}
          onResume={() => {
            setResumeCandidate(null);
            router.push(`/${resumeCandidate.zoneId}?focus=${resumeCandidate.nodeId}`);
          }}
          onDismiss={() => setResumeCandidate(null)}
          onAlways={() => {
            setResumePref("always");
            setResumeCandidate(null);
            router.push(`/${resumeCandidate.zoneId}?focus=${resumeCandidate.nodeId}`);
          }}
          onNever={() => {
            setResumePref("never");
            setResumeCandidate(null);
          }}
        />
      )}

      {showResumeToast && (
        <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 px-5 py-3 rounded-xl bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 text-sm font-medium shadow-lg">
          正在回到上次的位置...
        </div>
      )}

      {/* First-run onboarding */}
      {showOnboarding && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm animate-slide-up">
          <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-md w-full p-7 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3 mb-1">
              <span className="text-3xl">👋</span>
              <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {t("home.welcome")}
              </h2>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 leading-relaxed mb-5">
              {t("home.intro")}
            </p>
            <ol className="space-y-3 mb-6">
              {[
                { icon: "🗺️", t: t("home.clickZone"), d: t("home.clickZoneHint") },
                { icon: "📖", t: t("home.clickNode"), d: t("home.clickNodeHint") },
                { icon: "💡", t: t("home.clickQuestion"), d: t("home.clickQuestionHint") },
              ].map((s, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span className="flex items-center justify-center w-7 h-7 shrink-0 rounded-full bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 text-sm font-bold">
                    {i + 1}
                  </span>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {s.icon} {s.t}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{s.d}</p>
                  </div>
                </li>
              ))}
            </ol>
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  dismissOnboarding();
                  setShowEntrySelector(true);
                }}
                className="flex-1 py-2.5 px-4 rounded-xl text-sm font-semibold bg-blue-600 text-white hover:bg-blue-700 shadow-sm transition-colors"
              >
                从 AIOps 开始 →
              </button>
              <button
                onClick={dismissOnboarding}
                className="px-3 py-2.5 text-sm font-medium text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              >
                跳过
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
