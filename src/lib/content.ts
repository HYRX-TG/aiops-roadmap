import fs from "fs";
import path from "path";
import matter from "gray-matter";
import type {
  RoadmapNode,
  NodeFrontmatter,
  ZonesConfig,
  Zone,
} from "./types";
import { NodeFrontmatterSchema, ZonesConfigSchema } from "./validation";

const contentDir = path.join(process.cwd(), "content");

export function getZonesConfig(): ZonesConfig {
  const filePath = path.join(contentDir, "_zones.yaml");
  const fileContents = fs.readFileSync(filePath, "utf8");
  // Use gray-matter to parse the YAML file (wrapping it as if it were all frontmatter)
  const { data } = matter(`---\n${fileContents}\n---`);
  const result = ZonesConfigSchema.safeParse(data);
  if (!result.success) {
    throw new Error(`Invalid _zones.yaml: ${result.error.message}`);
  }
  return result.data as ZonesConfig;
}

export function getZone(zoneId: string): Zone | undefined {
  const config = getZonesConfig();
  return config.zones.find((z) => z.id === zoneId);
}

function parseContent(rawContent: string): {
  summary: string;
  deepDive: string;
  resources: string;
  summaryZh: string;
  deepDiveZh: string;
  resourcesZh: string;
  uiZh: string[];
} {
  const deepDiveMarker = "<!-- DEEP_DIVE -->";
  const resourcesMarker = "<!-- RESOURCES -->";
  const zhSummaryMarker = "<!-- ZH_SUMMARY -->";
  const zhDeepDiveMarker = "<!-- ZH_DEEP_DIVE -->";
  const zhResourcesMarker = "<!-- ZH_RESOURCES -->";
  const zhUiMarker = "<!-- ZH_UI -->";

  // 中文块整体位于英文区之后：按首个 ZH 标记切分英文区与中文区
  const firstZhIdx = rawContent.search(/<!--\s*ZH_/i);
  const enPart = firstZhIdx === -1 ? rawContent : rawContent.slice(0, firstZhIdx);
  const zhPart = firstZhIdx === -1 ? "" : rawContent.slice(firstZhIdx);

  // ── 英文三段 ──
  const deepDiveIdx = enPart.indexOf(deepDiveMarker);
  const resourcesIdx = enPart.indexOf(resourcesMarker);
  let summary = "";
  let deepDive = "";
  let resources = "";

  if (deepDiveIdx === -1 && resourcesIdx === -1) {
    summary = enPart.trim();
  } else {
    summary = enPart
      .slice(0, deepDiveIdx !== -1 ? deepDiveIdx : resourcesIdx)
      .trim();
    if (deepDiveIdx !== -1) {
      const deepDiveEnd = resourcesIdx !== -1 ? resourcesIdx : enPart.length;
      deepDive = enPart
        .slice(deepDiveIdx + deepDiveMarker.length, deepDiveEnd)
        .trim();
    }
    if (resourcesIdx !== -1) {
      resources = enPart.slice(resourcesIdx + resourcesMarker.length).trim();
    }
  }

  // ── 中文三段 ──
  let summaryZh = "";
  let deepDiveZh = "";
  let resourcesZh = "";
  let uiZh: string[] = [];
  if (zhPart) {
    const zsIdx = zhPart.indexOf(zhSummaryMarker);
    const zdIdx = zhPart.indexOf(zhDeepDiveMarker);
    const zrIdx = zhPart.indexOf(zhResourcesMarker);
    const zuIdx = zhPart.indexOf(zhUiMarker);
    if (zsIdx !== -1) {
      const zsEnd = [zdIdx, zrIdx, zuIdx].find((i) => i !== -1) ?? zhPart.length;
      summaryZh = zhPart.slice(zsIdx + zhSummaryMarker.length, zsEnd).trim();
    }
    if (zdIdx !== -1) {
      const zdEnd = [zrIdx, zuIdx].find((i) => i !== -1) ?? zhPart.length;
      deepDiveZh = zhPart.slice(zdIdx + zhDeepDiveMarker.length, zdEnd).trim();
    }
    if (zrIdx !== -1) {
      const zrEnd = zuIdx !== -1 ? zuIdx : zhPart.length;
      resourcesZh = zhPart.slice(zrIdx + zhResourcesMarker.length, zrEnd).trim();
    }
    if (zuIdx !== -1) {
      const uiText = zhPart.slice(zuIdx + zhUiMarker.length);
      const numRe = /^\s*(\d+)\s*[.、)．:：]\s*(.*)$/;
      // 兼容 CRLF：Windows 下写入的文件行尾带 \r，直接 split("\n") 会残留
      for (const line of uiText.split(/\r?\n/)) {
        const m = numRe.exec(line);
        if (m) {
          uiZh.push(m[2].trim());
        } else if (line.trim() && uiZh.length > 0) {
          uiZh[uiZh.length - 1] += " " + line.trim();
        }
      }
    }
  }

  return { summary, deepDive, resources, summaryZh, deepDiveZh, resourcesZh, uiZh };
}

export function getNodesByZone(zoneId: string): RoadmapNode[] {
  const zoneDir = path.join(contentDir, zoneId);

  if (!fs.existsSync(zoneDir)) {
    return [];
  }

  const files = fs.readdirSync(zoneDir).filter((f) => f.endsWith(".md"));

  return files.map((file) => {
    const filePath = path.join(zoneDir, file);
    const fileContents = fs.readFileSync(filePath, "utf8");
    const { data, content } = matter(fileContents);
    const result = NodeFrontmatterSchema.safeParse(data);
    if (!result.success) {
      throw new Error(
        `Invalid frontmatter in ${file}: ${result.error.message}`
      );
    }
    const {
      summary,
      deepDive,
      resources,
      summaryZh,
      deepDiveZh,
      resourcesZh,
      uiZh,
    } = parseContent(content);

    // ZH_UI 编号列表按固定顺序还原：milestones → 每条 edge 的 question（有 detail 再跟一条 detail）
    const fm = result.data as NodeFrontmatter;
    const milestonesZh: string[] = [];
    const edgeQuestionsZh: string[] = [];
    const edgeDetailsZh: string[] = [];
    let k = 0;
    for (let i = 0; i < fm.milestones.length && k < uiZh.length; i++, k++) {
      milestonesZh.push(uiZh[k]);
    }
    for (const edge of fm.edges.to ?? []) {
      if (k < uiZh.length) {
        edgeQuestionsZh.push(uiZh[k++]);
      } else {
        edgeQuestionsZh.push("");
      }
      if (edge.detail) {
        edgeDetailsZh.push(k < uiZh.length ? uiZh[k++] : "");
      } else {
        edgeDetailsZh.push("");
      }
    }

    return {
      frontmatter: result.data as NodeFrontmatter,
      summary,
      deepDive,
      resources,
      titleZh: result.data.title_zh,
      titleEn: result.data.title_en,
      summaryZh,
      deepDiveZh,
      resourcesZh,
      milestonesZh,
      edgeQuestionsZh,
      edgeDetailsZh,
    };
  });
}

export function getNode(zoneId: string, nodeId: string): RoadmapNode | undefined {
  const nodes = getNodesByZone(zoneId);
  return nodes.find((n) => n.frontmatter.id === nodeId);
}

export function getAllNodes(): RoadmapNode[] {
  const config = getZonesConfig();
  return config.zones.flatMap((zone) => getNodesByZone(zone.id));
}

export function getZoneNodeCount(zoneId: string): number {
  return getNodesByZone(zoneId).length;
}

export function validateEdgeReferences(): void {
  const config = getZonesConfig();
  const allNodeIds = new Set(
    config.zones.flatMap((z) => getNodesByZone(z.id).map((n) => n.frontmatter.id))
  );

  for (const zone of config.zones) {
    if (!zone.active) continue;
    const nodes = getNodesByZone(zone.id);

    for (const node of nodes) {
      if (node.frontmatter.edges.to) {
        for (const edge of node.frontmatter.edges.to) {
          // Cross-zone edges to inactive zones won't have content yet — skip them
          if (!allNodeIds.has(edge.id)) continue;
        }
      }
    }
  }
}
