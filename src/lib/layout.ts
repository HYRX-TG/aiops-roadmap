import Dagre from "@dagrejs/dagre";
import { type Node, type Edge, MarkerType } from "@xyflow/react";
import type { RoadmapNode, Zone, NodeStatus } from "@/lib/types";

// ---------------------------------------------------------------------------
// Graph traversal helpers
// ---------------------------------------------------------------------------

export function findRoots(roadmapNodes: RoadmapNode[]): string[] {
  const nodeIds = new Set(roadmapNodes.map((n) => n.frontmatter.id));
  const hasIncoming = new Set<string>();

  for (const n of roadmapNodes) {
    for (const edge of n.frontmatter.edges.to ?? []) {
      if (nodeIds.has(edge.id)) hasIncoming.add(edge.id);
    }
  }

  return roadmapNodes
    .map((n) => n.frontmatter.id)
    .filter((id) => !hasIncoming.has(id));
}

export function getChildren(nodeId: string, roadmapNodes: RoadmapNode[]): string[] {
  const nodeIds = new Set(roadmapNodes.map((n) => n.frontmatter.id));
  const node = roadmapNodes.find((n) => n.frontmatter.id === nodeId);
  if (!node?.frontmatter.edges.to) return [];
  return node.frontmatter.edges.to.map((e) => e.id).filter((id) => nodeIds.has(id));
}

export function getDescendants(nodeId: string, roadmapNodes: RoadmapNode[]): Set<string> {
  const descendants = new Set<string>();
  const queue = getChildren(nodeId, roadmapNodes);
  while (queue.length > 0) {
    const child = queue.shift()!;
    if (descendants.has(child)) continue;
    descendants.add(child);
    queue.push(...getChildren(child, roadmapNodes));
  }
  return descendants;
}

export function getInitialVisibleNodes(roadmapNodes: RoadmapNode[]): Set<string> {
  const roots = findRoots(roadmapNodes);

  // 环图回退：所有节点都有入边（如 aiops 分区 rag→overview 闭环）时
  // findRoots 返回空，图会整个空白。此时选入边最少的节点作为入口，
  // 平手时优先 id 含 overview/intro/start 的节点。
  let entryIds = roots;
  if (entryIds.length === 0 && roadmapNodes.length > 0) {
    const inDeg = new Map<string, number>();
    for (const n of roadmapNodes) inDeg.set(n.frontmatter.id, 0);
    const nodeIds = new Set(roadmapNodes.map((n) => n.frontmatter.id));
    for (const n of roadmapNodes) {
      for (const edge of n.frontmatter.edges.to ?? []) {
        if (nodeIds.has(edge.id)) {
          inDeg.set(edge.id, (inDeg.get(edge.id) ?? 0) + 1);
        }
      }
    }
    const minIn = Math.min(...inDeg.values());
    const candidates = roadmapNodes
      .filter((n) => inDeg.get(n.frontmatter.id) === minIn)
      .map((n) => n.frontmatter.id);
    const preferred = candidates.find((id) =>
      /overview|intro|start|index/.test(id)
    );
    entryIds = [preferred ?? candidates[0]];
  }

  const visible = new Set(entryIds);
  for (const rootId of entryIds) {
    for (const childId of getChildren(rootId, roadmapNodes)) {
      visible.add(childId);
    }
  }
  return visible;
}

function hasVisibleChildren(
  nodeId: string,
  roadmapNodes: RoadmapNode[],
  visibleIds: Set<string>
): boolean {
  return getChildren(nodeId, roadmapNodes).some((id) => visibleIds.has(id));
}

function isRoot(nodeId: string, roadmapNodes: RoadmapNode[]): boolean {
  return findRoots(roadmapNodes).includes(nodeId);
}

// ---------------------------------------------------------------------------
// Layout
// ---------------------------------------------------------------------------

export function layoutNodes(
  roadmapNodes: RoadmapNode[],
  visibleIds: Set<string>,
  progressMap: Map<string, NodeStatus>,
  onExpand: (nodeId: string) => void,
  onCollapse: (nodeId: string) => void,
  previousNodes?: Node[],
  anchorNodeId?: string | null,
  zones: Zone[] = []
): Node[] {
  const visibleNodes = roadmapNodes.filter((n) => visibleIds.has(n.frontmatter.id));
  const allNodeIds = new Set(roadmapNodes.map((n) => n.frontmatter.id));
  const zoneMap = new Map(zones.map((z) => [z.id, z]));

  const nodeWidth = 200;
  const nodeHeight = 90;
  const qNodeWidth = 180;
  const qNodeHeight = 40;

  // Build dagre graph
  const g = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "TB", ranksep: 120, nodesep: 100, edgesep: 60 });

  for (const n of visibleNodes) {
    g.setNode(n.frontmatter.id, { width: nodeWidth, height: nodeHeight });
  }

  // Track zone portals needed and Q node data
  const portalZoneIds = new Set<string>();
  const qEdgeData = new Map<
    string,
    { question: string; detail?: string; questionZh?: string; detailZh?: string }
  >();

  for (const n of visibleNodes) {
    const edgesTo = n.frontmatter.edges.to ?? [];
    edgesTo.forEach((edge, edgeIdx) => {
      if (visibleIds.has(edge.id)) {
        // Intra-zone edge: inject a question node between source and target
        const qId = `q-${n.frontmatter.id}-${edge.id}`;
        qEdgeData.set(qId, {
          question: edge.question,
          detail: edge.detail,
          questionZh: n.edgeQuestionsZh?.[edgeIdx] || undefined,
          detailZh: n.edgeDetailsZh?.[edgeIdx] || undefined,
        });
        if (!g.hasNode(qId)) {
          g.setNode(qId, { width: qNodeWidth, height: qNodeHeight });
        }
        g.setEdge(n.frontmatter.id, qId);
        g.setEdge(qId, edge.id);
      } else if (edge.zone) {
        // Cross-zone edge: inject a portal node into the layout
        const portalId = `zone-portal-${edge.zone}`;
        if (!portalZoneIds.has(edge.zone)) {
          portalZoneIds.add(edge.zone);
          g.setNode(portalId, { width: nodeWidth, height: nodeHeight });
        }
        g.setEdge(n.frontmatter.id, portalId);
      }
    });
  }

  Dagre.layout(g);

  // Anchor the layout so the clicked node stays in place.
  // If no specific anchor, fall back to centroid of shared nodes.
  const prevPosMap = new Map<string, { x: number; y: number }>();
  if (previousNodes) {
    for (const pn of previousNodes) prevPosMap.set(pn.id, pn.position);
  }

  let offsetX = 0;
  let offsetY = 0;
  if (prevPosMap.size > 0) {
    const anchorId =
      anchorNodeId && prevPosMap.has(anchorNodeId) && g.node(anchorNodeId)
        ? anchorNodeId
        : null;

    if (anchorId) {
      const prev = prevPosMap.get(anchorId)!;
      const dagrePos = g.node(anchorId);
      offsetX = prev.x - (dagrePos.x - nodeWidth / 2);
      offsetY = prev.y - (dagrePos.y - nodeHeight / 2);
    } else {
      let sumDx = 0;
      let sumDy = 0;
      let count = 0;
      for (const n of visibleNodes) {
        const id = n.frontmatter.id;
        const prev = prevPosMap.get(id);
        if (prev) {
          const dagrePos = g.node(id);
          sumDx += prev.x - (dagrePos.x - nodeWidth / 2);
          sumDy += prev.y - (dagrePos.y - nodeHeight / 2);
          count++;
        }
      }
      if (count > 0) {
        offsetX = sumDx / count;
        offsetY = sumDy / count;
      }
    }
  }

  // Convert dagre positions (center-based) to React Flow positions (top-left)
  const flowNodes: Node[] = [];

  for (const n of visibleNodes) {
    const nodeId = n.frontmatter.id;
    const pos = g.node(nodeId);
    const status = progressMap.get(nodeId) ?? "not-started";

    const childrenInZone = (n.frontmatter.edges.to || [])
      .map((e) => e.id)
      .filter((id) => allNodeIds.has(id));
    const hasHiddenChildren = childrenInZone.some((id) => !visibleIds.has(id));
    const canCollapse =
      !hasHiddenChildren &&
      !isRoot(nodeId, roadmapNodes) &&
      hasVisibleChildren(nodeId, roadmapNodes, visibleIds);

    flowNodes.push({
      id: nodeId,
      type: "roadmapNode",
      position: {
        x: pos.x - nodeWidth / 2 + offsetX,
        y: pos.y - nodeHeight / 2 + offsetY,
      },
      data: {
        label: n.frontmatter.title,
        titleZh: n.titleZh,
        titleEn: n.titleEn,
        difficulty: n.frontmatter.difficulty,
        category: n.frontmatter.category,
        status,
        hasHiddenChildren,
        canCollapse,
        onExpand,
        onCollapse,
        nodeId,
      },
    });
  }

  // Inject question nodes
  for (const [qId, edgeData] of qEdgeData) {
    const pos = g.node(qId);
    if (!pos) continue;
    flowNodes.push({
      id: qId,
      type: "questionNode",
      position: {
        x: pos.x - qNodeWidth / 2 + offsetX,
        y: pos.y - qNodeHeight / 2 + offsetY,
      },
      data: {
        question: edgeData.question,
        detail: edgeData.detail || "",
        questionZh: edgeData.questionZh || "",
        detailZh: edgeData.detailZh || "",
      },
    });
  }

  // Inject zone portal nodes
  for (const zoneId of portalZoneIds) {
    const portalId = `zone-portal-${zoneId}`;
    const zone = zoneMap.get(zoneId);
    const pos = g.node(portalId);
    if (!pos || !zone) continue;
    flowNodes.push({
      id: portalId,
      type: "zonePortalNode",
      position: {
        x: pos.x - nodeWidth / 2 + offsetX,
        y: pos.y - nodeHeight / 2 + offsetY,
      },
      data: {
        zoneId,
        zoneTitle: zone.title,
        zoneColor: zone.color,
      },
    });
  }

  return flowNodes;
}

// ---------------------------------------------------------------------------
// Edge builder
// ---------------------------------------------------------------------------

export function buildEdges(
  roadmapNodes: RoadmapNode[],
  visibleIds: Set<string>
): Edge[] {
  const edges: Edge[] = [];

  for (const node of roadmapNodes) {
    if (!visibleIds.has(node.frontmatter.id)) continue;
    for (const edge of node.frontmatter.edges.to ?? []) {
      const isPortal = !!edge.zone;

      if (isPortal) {
        const portalId = `zone-portal-${edge.zone}`;
        edges.push({
          id: `${node.frontmatter.id}-${portalId}-${edge.id}`,
          source: node.frontmatter.id,
          target: portalId,
          markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16, color: "#94a3b8" },
          style: { stroke: "#94a3b8", strokeWidth: 1.5 },
        });
      } else if (visibleIds.has(edge.id)) {
        const qId = `q-${node.frontmatter.id}-${edge.id}`;
        edges.push({
          id: `${node.frontmatter.id}-${qId}`,
          source: node.frontmatter.id,
          target: qId,
          style: { stroke: "#94a3b8", strokeWidth: 1.5 },
        });
        edges.push({
          id: `${qId}-${edge.id}`,
          source: qId,
          target: edge.id,
          markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16, color: "#94a3b8" },
          style: { stroke: "#94a3b8", strokeWidth: 1.5 },
        });
      }
    }
  }

  return edges;
}
