import { describe, it, expect, afterEach, vi } from "vitest";
import { evaluateAction, GUARDRAILS, ACTION_RISK } from "../guardrails";
import { runAiEngine, setBackendUrl } from "../aiEngine";

describe("evaluateAction — 护栏网关", () => {
  it("只读动作（diagnose / runbook）直接放行", () => {
    for (const action of ["diagnose", "runbook"]) {
      const d = evaluateAction(action);
      expect(d.allowed).toBe(true);
      expect(d.needsApproval).toBe(false);
      expect(ACTION_RISK[action].readOnly).toBe(true);
    }
  });

  it("执行动作（execute）默认需人工审批（T3 > 自动放行阈值 T1）", () => {
    const d = evaluateAction("execute");
    expect(d.allowed).toBe(false);
    expect(d.needsApproval).toBe(true);
    expect(d.reason).toContain("人工审批");
  });

  it("冻结窗口开启时，执行被拦截并给出原因", () => {
    const prev = GUARDRAILS.freezeWindow;
    GUARDRAILS.freezeWindow = true;
    try {
      const d = evaluateAction("execute");
      expect(d.needsApproval).toBe(true);
      expect(d.reason).toContain("冻结");
    } finally {
      GUARDRAILS.freezeWindow = prev;
    }
  });

  it("未知动作被拒绝", () => {
    const d = evaluateAction("self-destruct");
    expect(d.allowed).toBe(false);
    expect(d.tier).toBe(4);
  });
});

describe("runAiEngine — 编排返回结构（人是主导）", () => {
  it("diagnose 返回 已知/推测/无法确认 三段", async () => {
    const r = await runAiEngine({ nodeId: "aiops-rca", action: "diagnose" });
    expect(r.ok).toBe(true);
    expect(r.state).toBe("done");
    expect(r.readOnly).toBe(true);
    expect(r.result.summary).toBeTruthy();
    expect(Array.isArray(r.result.inferred) && r.result.inferred!.length).toBeGreaterThan(0);
    expect(Array.isArray(r.result.uncertain) && r.result.uncertain!.length).toBeGreaterThan(0);
  });

  it("runbook 返回知识来源", async () => {
    const r = await runAiEngine({ nodeId: "aiops-rag", action: "runbook" });
    expect(r.ok).toBe(true);
    expect(r.state).toBe("done");
    expect(Array.isArray(r.result.sources) && r.result.sources!.length).toBeGreaterThan(0);
  });

  it("execute 返回 待审批 + dry-run 计划 + 爆炸半径", async () => {
    const r = await runAiEngine({ nodeId: "aiops-guardrail", action: "execute" });
    expect(r.ok).toBe(true);
    expect(r.state).toBe("pending_approval");
    expect(Array.isArray(r.result.plan) && r.result.plan!.length).toBeGreaterThan(0);
    expect(r.result.blastRadius).toBeTruthy();
    expect(r.result.requiresApprover).toBeTruthy();
  });
});

describe("runAiEngine — 真后端模式（优先 /api/research，失败回退 mock）", () => {
  afterEach(() => {
    setBackendUrl("");
    vi.unstubAllGlobals();
  });

  it("后端可达：映射工作流 context 为结构化结果，透传 runId", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      run_id: "r-abc",
      status: "done",
      context: {
        verdict: { known: ["告警源 alertmanager"], inferred: ["疑似依赖超时"],
                   uncertain: ["未接入发布事件源"], recommendation: "建议先回滚最近发布",
                   sources: ["runbook/dependency-timeout-v2.md"] },
        guardrail: { allowed: false, needs_approval: true, reason: "T3 需人工审批", tier: 3 },
        plan: { action: "rollback", steps: ["kubectl rollout undo"], blast_radius: "namespace",
                approver: "SRE on-call" },
      },
    }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    setBackendUrl("http://127.0.0.1:8600");

    const r = await runAiEngine({ nodeId: "aiops-rca", action: "execute" });
    expect(fetchMock).toHaveBeenCalledOnce();
    expect(r.ok).toBe(true);
    expect(r.state).toBe("pending_approval");
    expect(r.result.summary).toContain("告警源");
    expect(r.result.plan).toEqual(["kubectl rollout undo"]);
    expect(r.result.runId).toBe("r-abc");
    expect(r.result.backendAction).toBe("rollback");
  });

  it("后端不可达：自动回退 mock，演示永不挂掉", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("connection refused")));
    setBackendUrl("http://127.0.0.1:1");
    const r = await runAiEngine({ nodeId: "aiops-rca", action: "diagnose" });
    expect(r.ok).toBe(true);
    expect(r.state).toBe("done");
    expect(r.result.summary).toBeTruthy();
  });

  it("后端不可达：必须打上 degradedFromBackend 标记（禁止静默降级）", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("connection refused")));
    setBackendUrl("http://127.0.0.1:1");
    const r = await runAiEngine({ nodeId: "aiops-rca", action: "diagnose" });
    // 复盘头号事故：catch 后静默 return null，界面一切正常但全是写死文案。
    // 现在必须让调用方知道"这是演示数据"。
    expect(r.degradedFromBackend).toBe(true);
  });

  it("后端 500（如 payload 漏 source）：回退 mock 且打标记，不静默", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response("Internal Server Error", { status: 500 })));
    setBackendUrl("http://127.0.0.1:8600");
    const r = await runAiEngine({ nodeId: "aiops-rca", action: "diagnose" });
    expect(r.ok).toBe(true);
    expect(r.degradedFromBackend).toBe(true);
  });

  it("后端返回 skipped（P2/P3 分流）：标记 skippedByRouting，不算失败", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({
      skipped: true, route: "batch",
    }), { status: 200 })));
    setBackendUrl("http://127.0.0.1:8600");
    const r = await runAiEngine({ nodeId: "aiops-rag", action: "runbook" });
    expect(r.ok).toBe(true);
    expect(r.skippedByRouting).toBe(true);
    expect(r.degradedFromBackend).toBeUndefined();
  });

  it("发给 /api/research 的 payload 必须带 alert.source（后端必填字段）", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({
      run_id: "r-xyz", status: "done",
      context: { verdict: { known: ["k"] }, guardrail: { allowed: true }, plan: null },
    }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    setBackendUrl("http://127.0.0.1:8600");
    await runAiEngine({ nodeId: "aiops-rca", action: "diagnose" });
    const body = JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string);
    expect(body.source).toBe("alertmanager");
    expect(body.alert.source).toBe("alertmanager");   // 曾经漏了这个 → TypeError → 500
  });

  it("未配置后端：直接走 mock", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    setBackendUrl("");
    await runAiEngine({ nodeId: "aiops-rag", action: "runbook" });
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
