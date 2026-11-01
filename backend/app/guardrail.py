"""护栏网关（guardrails.ts 的服务端强制关卡移植版）。

前端那份只是演示等价逻辑；写操作的真正强制关卡必须在服务端——
密钥不出后端，审批不落前端。原则：
  1. 只读自动放行；写/执行默认需人工审批
  2. 变更冻结窗口禁止自动执行
  3. 风险分级 T1-T4 + 爆炸半径上限约束
  4. 每个决策必须给 reason（给人看 + 给审计看）
"""
from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field, asdict

from .models import now_iso

BLAST_RANK = {"pod": 1, "node": 2, "namespace": 3, "service": 3,
              "cluster": 4, "global": 5}

# 动作风险登记表（与前端 ACTION_RISK 对齐，并补充真实运维动作）
ACTION_RISK: dict[str, dict] = {
    "diagnose":  {"tier": 1, "blast_radius": "pod",       "read_only": True,  "label": "AI 诊断（只读 RCA）"},
    "runbook":   {"tier": 1, "blast_radius": "pod",       "read_only": True,  "label": "取 Runbook（只读检索）"},
    "observe":   {"tier": 1, "blast_radius": "pod",       "read_only": True,  "label": "持续观测"},
    "scale_up":  {"tier": 2, "blast_radius": "namespace", "read_only": False, "label": "扩容"},
    "rollback":  {"tier": 3, "blast_radius": "namespace", "read_only": False, "label": "回滚发布"},
    "restart":   {"tier": 3, "blast_radius": "namespace", "read_only": False, "label": "重启服务"},
    "drain":     {"tier": 4, "blast_radius": "node",      "read_only": False, "label": "节点隔离/摘流"},
    # fail-closed：识别不出动作 ≠ 只读。未分类建议一律按最高风险送审批。
    # （曾经的 bug：detect_action 返回 None 时回落 observe → read_only → 直接放行，
    #   "建议删除生产数据库"这种文本会被无声放行。安全网关必须 fail-closed。）
    "unclassified": {"tier": 4, "blast_radius": "cluster", "read_only": False,
                     "label": "未识别动作（fail-closed：一律需审批）"},
}

CONFIG = {"freeze_window": False, "auto_approve_tier": 1, "blast_radius_max": "namespace"}


def config_from_env() -> dict:
    """从环境变量覆盖默认护栏配置（生产里冻结窗口必须能由值班开关控制，
    而不是写死在代码里——复盘缺口：freeze_window 硬编码 False，没有配置入口）。"""
    cfg: dict = {}
    fw = os.environ.get("AIOPS_FREEZE_WINDOW", "").strip().lower()
    if fw:
        cfg["freeze_window"] = fw in ("1", "true", "yes", "on")
    tier = os.environ.get("AIOPS_AUTO_APPROVE_TIER", "").strip()
    if tier.isdigit():
        cfg["auto_approve_tier"] = int(tier)
    blast = os.environ.get("AIOPS_BLAST_RADIUS_MAX", "").strip()
    if blast in BLAST_RANK:
        cfg["blast_radius_max"] = blast
    return cfg


@dataclass
class ApprovalDecision:
    allowed: bool
    needs_approval: bool
    reason: str
    tier: int
    action: str = ""
    blast_radius: str = ""


class GuardrailService:
    """带审计日志的护栏服务（线程安全）。"""

    def __init__(self, config: dict | None = None):
        self.config = dict(CONFIG)
        self.config.update(config_from_env())   # 环境变量优先于代码默认
        if config:
            self.config.update(config)          # 显式传参最高优先（测试用）
        self._lock = threading.Lock()
        self.audit: list[dict] = []

    def set_config(self, **fields) -> dict:
        """运行期调整护栏配置（值班开关：大促/故障中拉冻结窗）。每项变更都留审计。"""
        with self._lock:
            for k, v in fields.items():
                if k in self.config and v is not None:
                    self.config[k] = v
            snapshot = dict(self.config)
            self.audit.append({"ts": now_iso(), "event": "config_changed",
                               "config": snapshot})
        return snapshot

    def evaluate(self, action: str) -> ApprovalDecision:
        risk = ACTION_RISK.get(action)
        if risk is None:
            return self._decide(action, tier=4, blast_radius="cluster", read_only=False,
                                unknown=True)
        return self._decide(action, tier=risk["tier"], blast_radius=risk["blast_radius"],
                            read_only=risk["read_only"], unknown=False)

    def evaluate_spec(self, action: str, tier: int, blast_radius: str,
                      read_only: bool = False) -> ApprovalDecision:
        """按「显式风险规格」判定（自动修复登记表走这里）。

        为什么需要它：自动修复登记表有自己的 tier / blast_radius，
        如果它不复用护栏，就会出现"计划上写需审批、引擎却已自动下单"的分叉
        （复盘实测：护栏判 scale_up 需审批，引擎却下单了 kill_noisy_neighbor）。
        两种动作来源必须走同一套判定函数。
        """
        return self._decide(action, tier=tier, blast_radius=blast_radius,
                            read_only=read_only, unknown=False)

    def evaluate_auto(self, action: str, tier: int, blast_radius: str,
                      max_tier: int, max_blast: str) -> ApprovalDecision:
        """自动修复的「是否允许无人执行」判定（策略参数由修复引擎提供）。

        与 evaluate() 的区别：evaluate() 回答"要不要人批"；这里回答
        "在无人值守的前提下，是否允许这一类动作自动执行"。硬约束始终来自护栏：
          - 冻结窗口一律禁止自动（配置优先级最高）
          - 爆炸半径不得超过护栏自己的 blast_radius_max（硬顶，不能被自动策略放宽）
        软约束来自修复策略：tier ≤ max_tier、blast ≤ max_blast。
        每个判定都进护栏审计（谁在什么策略下放行了哪类动作）。
        """
        hard_max = self.config["blast_radius_max"]
        eff_blast_cap = min(
            (max_blast, hard_max),
            key=lambda b: BLAST_RANK.get(b, 99))
        if self.config["freeze_window"]:
            d = ApprovalDecision(False, True, "变更冻结窗口内禁止自动执行（护栏硬约束）",
                                 tier, action, blast_radius)
        elif BLAST_RANK.get(blast_radius, 99) > BLAST_RANK.get(eff_blast_cap, 0):
            d = ApprovalDecision(False, True,
                                 f"爆炸半径 {blast_radius} 超过自动上限 {eff_blast_cap}，需人工审批",
                                 tier, action, blast_radius)
        elif tier > max_tier:
            d = ApprovalDecision(False, True,
                                 f"风险 T{tier} 超过自动修复阈值 T{max_tier}，需人工审批",
                                 tier, action, blast_radius)
        else:
            d = ApprovalDecision(True, False,
                                 f"通过自动修复闸门（T{tier}/T{max_tier}，{blast_radius}≤{eff_blast_cap}）",
                                 tier, action, blast_radius)
        with self._lock:
            self.audit.append({"ts": now_iso(), "auto": True, **asdict(d)})
        return d

    def _decide(self, action: str, tier: int, blast_radius: str,
                read_only: bool, unknown: bool) -> ApprovalDecision:
        if unknown:
            d = ApprovalDecision(False, False, f"未知动作：{action}", 4, action)
        elif read_only:
            d = ApprovalDecision(True, False, "只读操作，直接放行", tier, action, blast_radius)
        elif self.config["freeze_window"]:
            d = ApprovalDecision(False, True, "处于变更冻结窗口，已拦截自动执行，需走紧急审批",
                                 tier, action, blast_radius)
        elif tier > self.config["auto_approve_tier"]:
            d = ApprovalDecision(False, True,
                                 f"风险等级 T{tier} 超过自动放行阈值 T{self.config['auto_approve_tier']}，需人工审批",
                                 tier, action, blast_radius)
        elif BLAST_RANK.get(blast_radius, 9) > BLAST_RANK.get(self.config["blast_radius_max"], 9):
            d = ApprovalDecision(False, True,
                                 f"爆炸半径 {blast_radius} 超过上限 {self.config['blast_radius_max']}，需人工审批",
                                 tier, action, blast_radius)
        else:
            d = ApprovalDecision(True, False, "通过护栏，可自动执行", tier, action, blast_radius)
        with self._lock:
            self.audit.append({"ts": now_iso(), **asdict(d)})
        return d

    # ── 从研判建议文本识别动作（关键词 → 动作登记表）──────────
    # 识别不出时返回 None，调用方必须 fail-closed（映射 unclassified → T4 需审批），
    # 绝不能回落 observe（只读放行）——那是安全网关最不该出现的失败方向。
    _KEYWORDS = [("回滚", "rollback"), ("rollback", "rollback"),
                 ("扩容", "scale_up"), ("scale", "scale_up"),
                 ("重启", "restart"), ("restart", "restart"),
                 ("摘流", "drain"), ("隔离", "drain"),
                 ("观测", "observe"), ("观察", "observe")]

    def detect_action(self, text: str) -> str | None:
        low = text.lower()
        for kw, act in self._KEYWORDS:
            if kw in low:
                return act
        return None

    def classify(self, text: str) -> str:
        """fail-closed 分类：未命中关键词 → unclassified（T4，需审批）。"""
        return self.detect_action(text) or "unclassified"

    def stats(self) -> dict:
        with self._lock:
            decisions = [a for a in self.audit if "allowed" in a]
            return {"total": len(decisions),
                    "blocked": sum(1 for a in decisions if not a["allowed"]),
                    "config_changes": sum(1 for a in self.audit if a.get("event") == "config_changed"),
                    "freeze_window": self.config["freeze_window"],
                    "auto_approve_tier": self.config["auto_approve_tier"],
                    "blast_radius_max": self.config["blast_radius_max"]}
