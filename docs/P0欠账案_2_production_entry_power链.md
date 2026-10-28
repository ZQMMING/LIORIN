# P0欠账案_2：production_entry power链静默瘫痪

> ## 🟢 销账（2026-09-29 接手核对）
> **本案"病灶"已不存在，文档描述的是修复前的旧状态，特此销账，防止按错误前提"再修"。**
> - 第 62 行 import 的 `daymaster_power_queries` **并非已删模块**：`engines/common/daymaster_power_queries.py` 存在且 FROZEN，`run_queries`（第 150 行）返回 40 条 query，正常 import。
> - 第 74 行 `run_queries(network)` 所在的 `_build_l1_queries`（第 50 行）**没有任何 try/except 包裹**——若 import 真失败会直接炸出而非"静默瘫痪/必走 except"。
> - 实测（主仓库 venv）：`production_entry(1983命例)` gate_passed=True，L1 queries=40（supported 18 / not_supported 22 / unknown 0），wuxing_power 注入成功，zhenglun 五段全活。
> - **遗留真缺陷（非本案）**：`production_entry.py:212` 在 except 块用 `sys.stderr` 但全文件未 `import sys`，一旦算辩解链抛异常该 handler 会先抛 `NameError`。已随本次接手修复（顶部补 `import sys`）。
> - **口径提示**：文档/治理多处写"38 Query"，代码实际返回 40 条，接手时按 40 为准。

## 现状（描述的是 2026-09 前旧状态，现已失效）
- `production_entry.py` 第62行import已删模块 `daymaster_power_queries`
- 第74行活调用 `run_queries(network)`
- 外层try吞ImportError → `_build_power_network` 静默瘫痪
- 每次启动必走except，用户无感

## 归因
静默瘫痪型（与transit_power案同型：P0只删叶节点，活链底下的根没断）

## 影响面
- `run_queries` 全部调用点待grep统计
- except吞了之后的兜底行为待写进案卷

## 修复方向
与transit_power案合并——power体系根重建，按章程改纯规则

## 状态
冻结，与案1同批排期

## 系统性漏洞记录
P0清除"只删引用、未验启动路径覆盖"——以后删模块的标准动作补一条：**启动入口全量跑一遍看有没有ImportError被吞**
