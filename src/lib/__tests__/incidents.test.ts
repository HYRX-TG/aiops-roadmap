import { describe, it, expect } from "vitest";
import { matchIncidentsToNodes, type IncidentAlert, type MatchableNode } from "../incidents";

const nodes: MatchableNode[] = [
  { id: "aiops-rca", title: "根因分析", category: "concept", tags: ["rca"] },
  { id: "k8s-db-pool", title: "数据库连接池", category: "practice", tags: ["mysql"] },
  { id: "pay-gateway", title: "支付网关", category: "practice", tags: ["payment"] },
  { id: "linux-basic", title: "Linux 基础命令", category: "concept", tags: [] },
];

const alert = (over: Partial<IncidentAlert>): IncidentAlert => ({
  runId: "r1", level: "P1", service: "", title: "t", alertname: "", status: "done", ...over,
});

describe("matchIncidentsToNodes — 实时告警 → 知识节点染色", () => {
  it("服务名经别称桥接到中文标题节点", () => {
    const m = matchIncidentsToNodes([alert({ service: "payment", title: "支付回调失败" })], nodes);
    expect(m.get("pay-gateway")?.level).toBe("P1");
    expect(m.get("pay-gateway")?.sampleTitle).toBe("支付回调失败");
  });

  it("服务名直接命中标签", () => {
    const m = matchIncidentsToNodes([alert({ service: "mysql", title: "连接池耗尽" })], nodes);
    expect(m.has("k8s-db-pool")).toBe(true);
    expect(m.has("linux-basic")).toBe(false);
  });

  it("同节点多告警累计计数并取最高等级", () => {
    const m = matchIncidentsToNodes([
      alert({ service: "payment", level: "P2", title: "轻微抖动" }),
      alert({ service: "payment", level: "P0", title: "支付大面积失败" }),
    ], nodes);
    expect(m.get("pay-gateway")?.count).toBe(2);
    expect(m.get("pay-gateway")?.level).toBe("P0");
  });

  it("无命中返回空 map；无告警也返回空 map", () => {
    expect(matchIncidentsToNodes([alert({ service: "kafka" })], nodes).size).toBe(0);
    expect(matchIncidentsToNodes([], nodes).size).toBe(0);
  });

  it("短服务名（api/db）按词边界匹配，不误伤含子串的节点", () => {
    // 复盘修复点：曾经的纯 includes 子串匹配会让 service="api" 把
    // 所有含 "api" 的节点全部染红（甚至 "rapid"/"capital"）。
    const apiNodes: MatchableNode[] = [
      { id: "rest-api", title: "REST API 设计", category: "concept", tags: [] },
      { id: "rapid-dev", title: "Rapid 开发流程", category: "concept", tags: [] },
      { id: "capital-flow", title: "资金流 Capital", category: "concept", tags: [] },
    ];
    const m = matchIncidentsToNodes([alert({ service: "api", title: "接口错误率飙高" })], apiNodes);
    expect(m.has("rest-api")).toBe(true);      // 真·API 节点命中
    expect(m.has("rapid-dev")).toBe(false);    // "rapid" 含 api 但不是 API
    expect(m.has("capital-flow")).toBe(false); // "capital" 含 api 但不是 API
  });

  it("中文别称仍按子串匹配（中文无词边界）", () => {
    const m = matchIncidentsToNodes([alert({ service: "payment", title: "x" })], nodes);
    expect(m.has("pay-gateway")).toBe(true);   // 标题「支付网关」含别称「支付」
  });
});
