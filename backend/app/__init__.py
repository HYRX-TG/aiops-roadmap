"""AIOps 研判后端 — 核心包。

设计原则：
- 核心逻辑（归一化/去重/门控/分流/工作流/研判）全部为纯 Python stdlib 实现，
  可脱离 Web 框架单测；FastAPI 仅作为薄适配层。
- 每个 stage 都输出统计计数，供 bench/flood.py 汇总量化指标。
"""
