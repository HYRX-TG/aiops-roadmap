"use client";

import dynamic from "next/dynamic";
import type { Zone, ZoneEdge, SearchableNode } from "@/lib/types";

// ssr:false 的 loading 回调在组件渲染上下文之外，取不到 useT()；
// 这里用中性骨架（无文案），避免出现"永远中文"的加载提示。
const ZoneMap = dynamic(() => import("@/components/ZoneMap"), {
  ssr: false,
  loading: () => (
    <div className="w-screen h-screen flex items-center justify-center">
      <div className="h-4 w-32 rounded bg-gray-200 dark:bg-gray-800 animate-pulse" />
    </div>
  ),
});

interface HomeClientProps {
  zones: Zone[];
  zoneEdges: ZoneEdge[];
  zoneNodeIds: Record<string, string[]>;
  searchableNodes: SearchableNode[];
}

export default function HomeClient({
  zones,
  zoneEdges,
  zoneNodeIds,
  searchableNodes,
}: HomeClientProps) {
  return (
    <div className="w-screen h-screen">
      <ZoneMap
        zones={zones}
        zoneEdges={zoneEdges}
        zoneNodeIds={zoneNodeIds}
        searchableNodes={searchableNodes}
      />
    </div>
  );
}
