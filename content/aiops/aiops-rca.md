---
id: aiops-rca
title: 根因分析：HolmesGPT 式诊断思路
title_en: "Root Cause Analysis: the HolmesGPT Approach"
zone: aiops
difficulty: 3
tags: [RCA, 根因分析, HolmesGPT, 提示词, 大模型]
category: practice
milestones:
  - 能描述"告警 + 上下文 + 工具"三段式诊断输入
  - 能讲清为什么要用工具调用而不是直接问模型
  - 能举一个本项目的 RCA 提示词结构
edges:
  to:
    - id: aiops-guardrail
      question: 分析出根因后，怎么安全地执行修复？
---

## RCA 不是"问模型一句就行"

很多人以为根因分析 = 把报错贴给大模型。真实场景里，**报错只是一句话，上下文才是关键**：同一句 "OOMKilled"，背后可能是内存泄漏、也可能是突发流量、也可能是隔壁服务把节点挤爆了。

HolmesGPT 的核心思路值得借鉴：**给模型"调用工具查上下文"的能力，而不是只给一段静态文本。**

## 三段式输入

```
1. 触发：一条告警（来自夜莺）
2. 上下文工具：
   - get_recent_alerts(服务)      → 最近有没有相关告警
   - query_metric(cpu/mem/... )   → 异常时段指标曲线
   - get_deploy_events(服务)      → 故障前有没有发版/变更
   - kubectl_describe / 日志检索  → Pod 状态与报错
3. 知识：RAGFlow 检索到的同类故障复盘 + runbook
```

模型在**推理过程中**自己决定先查哪个工具，逐步缩小范围，最后给出根因假设 + 建议动作。

<!-- DEEP_DIVE -->

## 提示词骨架（面试可讲）

```
你是资深 SRE。下面有一条告警和一组可调用的工具。
请按"收集证据 → 提出假设 → 验证假设 → 给出结论"的步骤推理。
只能基于工具返回的真实数据下结论，不要编造。
最后输出：根因假设（按可能性排序）+ 建议动作（标注风险等级）。
```

关键约束：**"只基于工具返回的真实数据，禁止编造"**——这是防止模型幻觉的核心护栏，也是 RCA 可信任的前提。

## 难点

- **工具太多模型会乱**：工具描述要清晰，必要时先做一层筛选；
- **时间窗口**：指标和日志要按故障时间对齐，否则查到的是无关数据；
- **误报 vs 漏报**：宁可多给假设并标注置信度，也不要只给一个武断结论。

<!-- RESOURCES -->

## 参考资料

- [HolmesGPT GitHub](https://github.com/robustintelligence/holmesgpt)
- [kubectl 官方文档](https://kubernetes.io/docs/reference/kubectl/)
- [根因分析中的 LLM 工具调用实践](https://github.com/robustintelligence/holmesgpt)
