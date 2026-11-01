// AIOps 自研「薄层」引擎（纯前端可运行等价实现）
//
// 为什么是纯前端模块而不是 /api/ai 路由？
//   本项目用 Next.js `output: "export"` 做纯静态导出，不支持服务端 Route Handler。
//   因此把「编排 + 护栏」逻辑收敛进这个客户端安全的模块，构建/部署零依赖。
//
// 生产落地（面试怎么说）：
//   真实部署时，这部分逻辑应放在你自有的后端 /api/ai（或单独的编排服务），
//   由它统一代理并持有密钥：夜莺 MCP → HolmesGPT → RAGFlow → Dify → StackStorm。
//   前端只发 { nodeId, action }，后端返回下面的结构化结果。护栏（evaluateAction）
//   在服务端才是真正的强制关卡——本文件里的调用只是演示等价逻辑。

import { evaluateAction, ACTION_RISK, type ApprovalDecision } from "@/lib/guardrails";

export type AiActionState =
  | "done"
  | "pending_approval"
  | "approved"
  | "blocked"
  | "failed";

export interface AiResult {
  summary?: string; // 🟢 已知（基于真实数据）
  inferred?: string[]; // 🟡 推测（AI 推断）
  uncertain?: string[]; // ⚪ 无法确认（缺少证据）
  recommendation?: string; // 💡 建议
  evidence?: string[]; // 证据
  sources?: string[]; // 知识来源
  plan?: string[]; // 执行计划（dry-run）
  blastRadius?: string; // 爆炸半径
  requiresApprover?: string; // 审批人
  runId?: string; // 后端工作流 run id（审批回传用）
  backendAction?: string; // 后端护栏动作名（rollback/scale_up/...）
}

// ── 后端模式（真数据）：配置了后端地址时优先走真实研判链路 ──
//
// 后端 = backend/ 目录的 FastAPI 服务（7源接入→去重降噪→P0-P3分流→
// 持久化工作流→RAGFlow→研判→护栏→dry-run 计划）。未配置或后端不可达时，
// 自动回退到下面的 mock 演示逻辑——演示永不因网络问题挂掉。
const BACKEND_URL_KEY = "aiops-roadmap-backend-url";

export function getBackendUrl(): string {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem(BACKEND_URL_KEY) ?? "";
}

export function setBackendUrl(url: string): void {
  if (typeof window === "undefined") return;
  if (url.trim()) window.localStorage.setItem(BACKEND_URL_KEY, url.trim());
  else window.localStorage.removeItem(BACKEND_URL_KEY);
}

interface ResearchResponse {
  run_id?: string;
  status?: string;
  skipped?: boolean;
  context?: {
    verdict?: { known?: string[]; inferred?: string[]; uncertain?: string[]; recommendation?: string; sources?: string[] };
    rag_hits?: { document?: string }[];
    guardrail?: { allowed?: boolean; needs_approval?: boolean; reason?: string; tier?: number };
    plan?: { action?: string; steps?: string[]; blast_radius?: string; approver?: string; state?: string };
  };
}

/** 真后端联调的三种结局——显式区分，杜绝"静默降级"：
 *  ok           真链路跑通，返回真实研判
 *  skipped      分级走了 P2/P3（不进 LLM 主链路）——真分流，不是故障
 *  unavailable  联调失败（网络/超时/HTTP 错误）——必须让 UI 显示警示 */
type BackendOutcome =
  | { kind: "ok"; response: AiResponse }
  | { kind: "skipped" }
  | { kind: "unavailable"; error: string };

async function runBackend(nodeId: string, action: string): Promise<BackendOutcome> {
  const base = getBackendUrl();
  if (!base) return { kind: "unavailable", error: "未配置后端地址" };
  try {
    const resp = await fetch(`${base.replace(/\/+$/, "")}/api/research`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source: "alertmanager",
        alert: {
          // source 是 UnifiedAlert 的必填字段：漏了它后端 from_dict 直接 TypeError→500，
          // 而这里 catch 后静默回退 mock——界面看着正常，其实全是演示文案（复盘头号事故）。
          source: "alertmanager",
          alertname: nodeId,
          title: nodeId,
          description: `知识节点演练告警：${nodeId}`,
          severity: action === "execute" ? "critical" : "warning",
          labels: { env: "prod", service: nodeId.replace(/^aiops-/, "") || "unknown" },
        },
      }),
      signal: AbortSignal.timeout(8000),
    });
    // 不再静默 return null：HTTP 错误要喊出来，否则 DevTools 之外无人发现链路是断的
    if (!resp.ok) {
      const detail = await resp.text().catch(() => "");
      console.error(`[AIOps] /api/research ${resp.status}: ${detail.slice(0, 200)}`);
      throw new Error(`后端返回 ${resp.status}（详见控制台）`);
    }
    const data: ResearchResponse = await resp.json();
    if (data.skipped || !data.context) {
      // 分级走了非 research 路由（P2/P3）——这不是错误，是真分流
      return { kind: "skipped" };
    }
    const ctx = data.context;
    const v = ctx.verdict ?? {};
    const plan = ctx.plan;
    const g = ctx.guardrail ?? {};
    const result: AiResult = {
      summary: Array.isArray(v.known) ? v.known.join("；") : undefined,
      inferred: v.inferred,
      uncertain: v.uncertain,
      recommendation: v.recommendation,
      sources: v.sources ?? (ctx.rag_hits ?? [])
        .map((h) => h.document)
        .filter((d): d is string => Boolean(d)),
      plan: plan?.steps,
      blastRadius: plan?.blast_radius,
      requiresApprover: plan?.approver,
      runId: data.run_id,
      backendAction: plan?.action,
    };
    return {
      kind: "ok",
      response: {
        ok: true,
        action,
        state: plan ? "pending_approval" : "done",
        readOnly: !plan,
        tier: (g.tier as number) ?? (plan ? 3 : 1),
        decision: {
          allowed: Boolean(g.allowed) && !plan,
          needsApproval: Boolean(g.needs_approval) || Boolean(plan),
          reason: g.reason || (plan ? "后端护栏判定：需人工审批" : "只读研判，直接放行"),
          tier: (g.tier as 1 | 2 | 3 | 4) ?? (plan ? 3 : 1),
        },
        result,
      },
    };
  } catch (err) {
    // 后端不可达/超时/HTTP 错误：回退 mock，但把原因带出去给 UI 警示
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`[AIOps] 真后端联调失败，回退演示数据：${msg}`);
    return { kind: "unavailable", error: msg };
  }
}

// 审批回传：真后端模式下把「确认执行 / 拒绝」写回服务端护栏审计；
// mock 模式返回 null（前端本地状态即可）。
export async function submitApproval(
  runId: string,
  backendAction: string,
  decision: "approved" | "rejected",
): Promise<{ executed: boolean; msg: string } | null> {
  const base = getBackendUrl();
  if (!base || !runId) return null;
  try {
    const resp = await fetch(`${base.replace(/\/+$/, "")}/api/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ run_id: runId, action: backendAction, decision, approver: "SRE on-call" }),
      signal: AbortSignal.timeout(8000),
    });
    // 审批是写操作，失败必须喊出来（409=已审批过 / 400=action 不匹配 / 404=run 不存在）
    if (!resp.ok) {
      const detail = await resp.text().catch(() => "");
      console.error(`[AIOps] /api/approve ${resp.status}: ${detail.slice(0, 200)}`);
      return { executed: false, msg: `审批失败（${resp.status}）：${detail.slice(0, 120)}` };
    }
    const data = await resp.json();
    return { executed: Boolean(data.executed), msg: data.msg ?? "" };
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error(`[AIOps] 审批请求异常：${msg}`);
    return { executed: false, msg: `审批请求失败：${msg}` };
  }
}

export interface AiResponse {
  ok: boolean;
  action: string;
  state: AiActionState;
  readOnly: boolean;
  tier: number;
  decision: ApprovalDecision;
  result: AiResult;
  /** 真后端模式下联调失败 → 回退 mock 时置位，UI 必须显示"演示数据"警示条
   *  （复盘头号事故：静默降级让演示看起来一切正常，其实全是写死文案） */
  degradedFromBackend?: boolean;
  /** 分级走了非 research 路由（P2/P3 不进主链路）——真分流，不是错误 */
  skippedByRouting?: boolean;
}

interface AiRequest {
  nodeId: string;
  action: string;
}

// 模拟网络延迟，让 UI 的「思考中…」状态有意义
const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

export async function runAiEngine(req: AiRequest): Promise<AiResponse> {
  const { nodeId, action } = req;

  if (!ACTION_RISK[action]) {
    return {
      ok: false,
      action,
      state: "failed",
      readOnly: false,
      tier: 4,
      decision: { allowed: false, needsApproval: false, reason: `不支持的动作：${action}`, tier: 4 },
      result: {},
    };
  }

  // 真后端模式：配置了后端地址则优先走真实研判链路；
  // 联调失败 → 回退 mock，但响应带 degradedFromBackend 标记（UI 必须显示警示，不许静默）
  const backendOutcome = await runBackend(nodeId, action);
  if (backendOutcome.kind === "ok") return backendOutcome.response;
  const degradedError = backendOutcome.kind === "unavailable" ? backendOutcome.error : "";
  const skipped = backendOutcome.kind === "skipped";
  const resp = await mockResponse(nodeId, action, skipped);
  if (degradedError) resp.degradedFromBackend = true;
  return resp;
}

// ── mock / 降级响应（联调失败或未配后端时的演示数据）────────────
async function mockResponse(nodeId: string, action: string, skippedByRouting: boolean): Promise<AiResponse> {
  const risk = ACTION_RISK[action];
  const decision = evaluateAction(action);

  await delay(650); // 模拟调用夜莺 MCP / HolmesGPT / RAGFlow 的往返

  // 分级走了非 research 路由（P2/P3）：这是真分流，明说"没进大模型"，不装作研判过
  if (skippedByRouting) {
    return {
      ok: true, action, state: "done", readOnly: true, tier: 2, decision,
      skippedByRouting: true,
      result: {
        summary: "该告警分级未进 LLM 研判主链路（P2/P3 分流设计）：P0/P1 才消耗大模型推理。",
        recommendation: "如需强制研判，可在大盘对该告警点「⚡ 送研判」。",
      },
    };
  }

  // ── 只读类：诊断 / 取 Runbook ──────────────────────────────
  if (risk.readOnly) {
    if (action === "diagnose") {
      // 真实实现：调夜莺 MCP 拿告警+拓扑 → 调 HolmesGPT 做 RCA，把返回结构化。
      return {
        ok: true,
        action,
        state: "done",
        readOnly: true,
        tier: decision.tier,
        decision,
        result: {
          summary: `针对节点「${nodeId}」，结合实时告警与依赖拓扑，初步定位为「上游依赖超时引发的连锁变慢」。`,
          inferred: [
            "近 10 分钟有一次相关发布（deploy event），时间线与错误率抬升吻合",
            "下游服务 P99 延迟上升，但 CPU/内存未到瓶颈，更像外部依赖问题",
          ],
          uncertain: [
            "无法确认：当前未拿到该依赖的下游成功率指标（数据源未接入）",
            "无法确认：是否为灰度流量导致的局部问题",
          ],
          recommendation: "建议先回滚最近一次发布（T3，需人工审批），并补充该依赖的 SLO 监控。",
          evidence: [
            "alert: error_rate>5% 持续 8m",
            "deploy_event: svc-web v1.4.2 10m ago",
            "topology: svc-web → dep-payment",
          ],
        },
      };
    }

    // 真实实现：调 RAGFlow 检索公司 Runbook / 历史事故库。
    return {
      ok: true,
      action,
      state: "done",
      readOnly: true,
      tier: decision.tier,
      decision,
      result: {
        summary: `在知识库中找到与「${nodeId}」相关的 2 份 Runbook 与 1 起历史事故复盘。`,
        inferred: [
          "历史同类事故平均恢复时间 12 分钟，根因多为依赖超时",
          "标准处置顺序：确认影响面 → 回滚/扩容 → 验证 → 归档",
        ],
        uncertain: ["无法确认：当前环境是否与历史事故完全一致（拓扑可能有差异）"],
        recommendation: "按 Runbook「依赖超时处置 v2」执行，必要时升级到 on-call。",
        sources: ["runbook/依赖超时处置-v2.md", "incident/2026-03-payment-timeout.md"],
      },
    };
  }

  // ── 写/执行类：一键执行 / 自愈 ─────────────────────────────
  // 真实实现：调 Dify 生成计划 → StackStorm dry-run 预演 → 等人工审批 → 执行 → 回滚预案。
  // 设计铁律：所有写操作一律「先出计划、再等人批」，永不静默自动执行。
  const plan = [
    "kubectl rollout restart deploy/svc-web -n prod",
    "等待 60s 健康探针通过",
    "若错误率未回落，自动回滚到上一版本",
  ];
  return {
    ok: true,
    action,
    state: decision.allowed ? "approved" : "pending_approval",
    readOnly: false,
    tier: decision.tier,
    decision,
    result: {
      summary: "AI 已生成自愈方案，但执行权在你手里（人是主导）。",
      plan,
      blastRadius: risk.blastRadius,
      requiresApprover: "SRE on-call",
      inferred: ["回滚是该风险下的最小爆炸半径动作"],
      uncertain: ["执行后是否彻底恢复，需看 5 分钟错误率曲线确认"],
      recommendation: "请在下方审批：确认执行 / 修改计划 / 拒绝。",
    },
  };
}
