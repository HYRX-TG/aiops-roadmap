// 护栏层：AI 动作的安全网关（人在回路的核心）
//
// 设计原则（来自 AIOps 平台调研：Bengal.Cloud「Humans in the Lead」、OpsMind、Dynatrace）：
// 1. 只读/低风险动作可自动放行；写/执行类动作默认需要人工审批。
// 2. 变更冻结窗口（大促/故障中）禁止自动执行，只允许走紧急审批。
// 3. 风险分级 + 爆炸半径约束，越界直接拦截。
// 4. 每个决策都要给出「原因」，既给人看，也给审计看。
//
// 注意：护栏只在服务端生效。前端永远不直连 LLM / OSS（密钥不出后端）。

export type RiskTier = 1 | 2 | 3 | 4; // 1 只读/低风险 · 2 中风险 · 3 高风险需审批 · 4 危险禁止
export type BlastRadius = "pod" | "node" | "namespace" | "cluster";

export interface GuardrailConfig {
  freezeWindow: boolean; // 变更冻结期：true 时禁止任何自动执行
  autoApproveTier: number; // 仅 tier <= 该值的动作可自动放行（默认仅只读）
  blastRadiusMax: BlastRadius; // 单次动作允许的最大爆炸半径
}

// 默认配置。真实部署时从环境变量 / 配置中心读取，并可按 zone / on-call 动态调整。
export const GUARDRAILS: GuardrailConfig = {
  freezeWindow: false,
  autoApproveTier: 1,
  blastRadiusMax: "namespace",
};

// 动作风险登记表：每个自研动作属于哪一档、爆炸半径多大、是否只读。
export const ACTION_RISK: Record<
  string,
  { tier: RiskTier; blastRadius: BlastRadius; readOnly: boolean; label: string }
> = {
  diagnose: { tier: 1, blastRadius: "pod", readOnly: true, label: "AI 诊断（只读 RCA）" },
  runbook: { tier: 1, blastRadius: "pod", readOnly: true, label: "取公司 Runbook（只读检索）" },
  execute: { tier: 3, blastRadius: "namespace", readOnly: false, label: "一键执行 / 自愈" },
};

export interface ApprovalDecision {
  allowed: boolean; // 是否允许自动执行（无需人）
  needsApproval: boolean; // 是否需要人工审批
  reason: string; // 决策原因（给人 + 审计）
  tier: RiskTier;
}

const RADIUS_RANK: Record<BlastRadius, number> = {
  pod: 1,
  node: 2,
  namespace: 3,
  cluster: 4,
};

// 护栏网关：所有写/执行操作都必须先过这一关。
export function evaluateAction(action: string): ApprovalDecision {
  const risk = ACTION_RISK[action];
  if (!risk) {
    return { allowed: false, needsApproval: false, reason: `未知动作：${action}`, tier: 4 };
  }

  // 只读动作：直接放行（diagnose / runbook）
  if (risk.readOnly) {
    return { allowed: true, needsApproval: false, reason: "只读操作，直接放行", tier: risk.tier };
  }

  // 写/执行类动作
  if (GUARDRAILS.freezeWindow) {
    return {
      allowed: false,
      needsApproval: true,
      reason: "处于变更冻结窗口，已拦截自动执行，需走紧急审批流程",
      tier: risk.tier,
    };
  }
  if (risk.tier > GUARDRAILS.autoApproveTier) {
    return {
      allowed: false,
      needsApproval: true,
      reason: `风险等级 T${risk.tier} 超过自动放行阈值 T${GUARDRAILS.autoApproveTier}，需人工审批`,
      tier: risk.tier,
    };
  }
  if (RADIUS_RANK[risk.blastRadius] > RADIUS_RANK[GUARDRAILS.blastRadiusMax]) {
    return {
      allowed: false,
      needsApproval: true,
      reason: `爆炸半径 ${risk.blastRadius} 超过上限 ${GUARDRAILS.blastRadiusMax}，需人工审批`,
      tier: risk.tier,
    };
  }
  return { allowed: true, needsApproval: false, reason: "通过护栏，可自动执行", tier: risk.tier };
}
