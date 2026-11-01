/**
 * 实时告警 → 知识图谱节点染色。
 *
 * 这是我们相对同类「后台研判系统」的差异化能力：把后端的实时研判告警
 * 映射到前端知识节点上，让「学这个知识点」和「它正在线上出事」同屏。
 *
 * 数据流：后端 /api/alerts（最近研判 run）→ 按 service/告警名匹配知识节点
 * → NodeCard 染红 + 🚨 徽标。未配置后端时该能力静默关闭。
 */

export interface IncidentAlert {
  runId: string;
  level: string; // P0 / P1 / P2 / P3
  service: string;
  title: string;
  alertname: string;
  status: string; // 工作流状态 done/failed/...
}

export interface NodeIncident {
  level: string; // 该节点命中的最高等级
  count: number; // 命中告警条数
  sampleTitle: string; // 代表性告警标题
}

/** 服务名 → 中文别称（知识图谱标题是中文，需要桥接） */
const SERVICE_ALIASES: Record<string, string[]> = {
  payment: ["支付", "收银台", "资金"],
  order: ["订单", "下单", "交易"],
  api: ["api", "接口"],
  gateway: ["网关", "接入层"],
  auth: ["登录", "认证", "鉴权"],
  mysql: ["数据库", "db", "存储"],
  redis: ["缓存", "cache"],
  cart: ["购物车"],
  search: ["搜索", "检索"],
  notify: ["通知", "消息"],
  kafka: ["消息队列", "mq"],
};

const LEVEL_RANK: Record<string, number> = { P0: 0, P1: 1, P2: 2, P3: 3 };

/** 转义正则元字符（token 可能含 - . 等） */
function escapeRe(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * 词匹配：ASCII 词按**词边界**匹配，中文别称按子串匹配。
 *
 * 曾经的坑：纯 `haystack.includes(token)` 子串匹配——service="api" 时
 * 会把所有含 "api" 的节点（REST API、API 网关、甚至 "rapid"）全部染红，误报夸张。
 * 中文没有词边界，所以别称仍用子串；ASCII 服务名必须整词匹配。
 */
function tokenMatches(haystack: string, token: string): boolean {
  if (/^[\x21-\x7e]+$/.test(token)) {
    const re = new RegExp(`(^|[^a-z0-9])${escapeRe(token.toLowerCase())}([^a-z0-9]|$)`, "i");
    return re.test(haystack);
  }
  return haystack.includes(token.toLowerCase());
}

export interface MatchableNode {
  id: string;
  title: string;
  category?: string;
  tags?: string[];
}

/** 从后端拉取实时告警；失败/未配置返回空数组（前端静默降级）。 */
export async function fetchIncidents(baseUrl: string): Promise<IncidentAlert[]> {
  if (!baseUrl) return [];
  try {
    const resp = await fetch(`${baseUrl.replace(/\/+$/, "")}/api/alerts?limit=50`, {
      signal: AbortSignal.timeout(6000),
    });
    if (!resp.ok) return [];
    const data = await resp.json();
    const items = Array.isArray(data?.items) ? data.items : [];
    return items.map((it: Record<string, unknown>) => ({
      runId: String(it.run_id ?? ""),
      level: String(it.level ?? "P2"),
      service: String(it.service ?? ""),
      title: String(it.title ?? ""),
      alertname: String(it.alertname ?? ""),
      status: String(it.status ?? ""),
    }));
  } catch {
    return [];
  }
}

/**
 * 告警 → 知识节点匹配（纯函数，可单测）。
 * 规则：节点文本（id+标题+分类+标签）包含服务名或其任一中英文别称即命中。
 */
export function matchIncidentsToNodes(
  alerts: IncidentAlert[],
  nodes: MatchableNode[]
): Map<string, NodeIncident> {
  const result = new Map<string, NodeIncident>();
  if (alerts.length === 0) return result;

  // 预计算每个告警的匹配词表
  const alertTokens = alerts.map((a) => {
    const tokens = new Set<string>();
    const svc = a.service.toLowerCase().trim();
    // 短服务名（api/db/mq）极易误命中，要求长度 ≥3 且按词边界匹配
    if (svc.length >= 2) {
      tokens.add(svc);
      for (const alias of SERVICE_ALIASES[svc] ?? []) tokens.add(alias.toLowerCase());
    }
    const name = a.alertname.toLowerCase().trim();
    if (name.length >= 4) tokens.add(name);
    return { alert: a, tokens: [...tokens] };
  });

  for (const node of nodes) {
    const haystack = [node.id, node.title, node.category ?? "", ...(node.tags ?? [])]
      .join(" ")
      .toLowerCase();
    for (const { alert, tokens } of alertTokens) {
      if (tokens.some((t) => tokenMatches(haystack, t))) {
        const prev = result.get(node.id);
        if (!prev) {
          result.set(node.id, { level: alert.level, count: 1, sampleTitle: alert.title });
        } else {
          prev.count += 1;
          if ((LEVEL_RANK[alert.level] ?? 9) < (LEVEL_RANK[prev.level] ?? 9)) {
            prev.level = alert.level;
            prev.sampleTitle = alert.title;
          }
        }
      }
    }
  }
  return result;
}
