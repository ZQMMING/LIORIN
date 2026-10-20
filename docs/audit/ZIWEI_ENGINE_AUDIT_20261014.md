# 紫微引擎整体审计报告

- **日期**：2026-10-14
- **范围**：紫微引擎全量（外围 5 文件 2,904 行 + `ziwei/` 子包 42 文件 15,745 行 ≈ **18,649 行**）
- **深度**：只读勘查 + 实测验证 + **边审边修**
- **环境**：`D:/shuntian/.venv/Scripts/python.exe`（managed python 3.13 缺 jsonschema，不可用）

---

## 一、引擎结构总览

三层架构（铁律：算 → 辨 → 解，逐层单向）：

| 层     | 入口                                                                    | 核心文件                                                                                                                                                                                |
| ----- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **算** | `ZiweiEngine.full_chart()`                                            | `ziwei_engine.py`(1374)、`ziwei_dependency_adapter.py`(475)、`ziwei_palace_resolution.py`(497)、`ziwei_method_profile.py`(286)、`ziwei_adapter.py`(272)                                 |
| **辨** | `compute_multi_method_signals()`                                      | `multi_method.py`(274)、`method_graphs.py`(538)、`rule_graph.py`(177)、`qintian/combinations.py`(3609)、`nihai_assertions.py`(812)、`pattern_rules.py`(317)、`feixing_rule_graph.py`(130) |
| **解** | `build_life_reading()` / `build_answer()` / `build_domain_readings()` | `interpretation.py`(2437)、`answer_layer.py`(1035)、`domain_reading.py`(1007)、`palace_star_verdicts.py`(507)、`dimension_bridge.py`(296)                                               |
| 桥/证据  | —                                                                     | `dataset_bridge.py`(515)、`evidence_producer.py`(268)、`z14/evidence_collector.py`(287)                                                                                               |

---

## 二、已修复缺陷（7 项）

### P1-1 · `_PATTERN_IDS` 幻影规则「杀狼同宫」

- **位置**：`rules/multi_method.py` L146-156
- **证据**：硬编码 41 条（自述「与 PATTERN_DEFS 同名同步」），而 `rule_graph.PATTERN_DEFS` 实为 **40 条**，多出幻影「杀狼同宫」（DEFS 中只有「破狼同宫」）。`_wrap_sanhe` 用它推导 unmatched 全集 → `SANHE-PATTERN-杀狼同宫` **恒被判为未匹配**，污染未匹配统计。
- **修复**：改为 `_PATTERN_IDS = [(d[0],) for d in PATTERN_DEFS]` 直接派生，从根上杜绝失配。
- **验证**：`len(_PATTERN_IDS) == 40` ✓

### P1-2 · `answer_layer` 宫位规则缺 brightness/煞吉事实 → 四档亮度判定整体失效

- **位置**：`rules/method_graphs.py` L458-459（facts 生产端）↔ `rules/answer_layer.py` L218-220 / L998-1033（消费端）
- **证据**：消费端取 `facts["brightness"]`/`has_煞`/`has_吉`，但生产端 facts 只有 `{palace, stars}` → `bright` 恒 `""`、煞吉恒 False → 四档判定（庙/旺/利/陷）恒走 `else` 分支，**只输出 mixed**。
- **修复**：`match_palace_rules` 补 `brightness`（取自 `chart.palaces[宫]["brightness"]`，由 `full_chart` 注入）、`has_煞`/`has_吉`（新增 `SHA_STARS`/`JI_STARS` 六煞六吉常量）。
- **验证**：命宫七杀（庙+有煞）现输出 `verdict_type=shadow`（此前恒 `mixed`）✓

### P1-3 · 「交友 / 仆役」命名不一致 → 北派多条规则静默漏检

- **位置**：`rules/qintian/combinations.py`（`ZW_PALACES_ORDER` L55、`OPPOSITE_PAIRS` L1216、`YIN_PALACES` L1220/L1637、`dec_liuqin`/`OPP` L1846/L1849/L1863）；`rules/qintian/features.py` L95
- **证据**：该文件用书之「交友」，而 `chart.palaces` / `flying_transforms`（iztro）用「仆役」→ `_palace_index("仆役")` 返回 **-1**；`OPPOSITE_PAIRS` 等**直接字面量比对**处，「兄弟↔交友」永不匹配 → 空宫双忌、对宫互飞、大限六亲、阴阳宫等多条规则静默漏检。
- **修复**：`ZW_PALACES_ORDER` 统一为「仆役」；新增 `_PALACE_NAME_ALIAS`（「交友」→「仆役」）并在 `_palace_index` 归一化；4 处直接比对字面量改「仆役」；`features.OPPOSITE_PAIRS` 同步。
- **验证**：`_palace_index("仆役") == 8` ✓；`QTN-CMB-029` 新命中「大限夫妻化忌冲本命**仆役**」（此前漏检）✓

### P2-4 · `domain_reading` 贪狼忌破财分支永不可达

- **位置**：`rules/domain_reading.py` L992
- **证据**：`elif star == "贪狼"` 嵌在 `if star in ("擎羊","陀罗","火星","铃星","地空","地劫")` 内，而外层元组不含「贪狼」→ 该分支**永不成立**，「贪狼忌破财」风险与建议从不产出。
- **修复**：贪狼是欲望/桃花星非煞星，移出外层 if 独立判定。
- **验证**：案例盘财运风险现含「贪狼忌代表欲望无底洞，冲动消费、投机投资持续破财」✓

### P2-5 · `feixing_rule_graph` 缺 `Literal` 导入

- **位置**：`rules/feixing_rule_graph.py` L21 / L120
- **证据**：L120 用 `Literal["in","out","self"]`，但 typing 仅导入 `Any`；被 `from __future__ import annotations` 掩盖，`get_type_hints()` 实测抛 `NameError`。
- **修复**：`from typing import Any, Literal`。
- **验证**：`get_type_hints(FlyingTransformFact)` 正常 ✓

### P2-6 · `combinations` 检测器异常静默吞噬（无日志）

- **位置**：`rules/qintian/combinations.py` L2494-2500 / L2508-2513
- **证据**：`except Exception: pass` —— 60 条检测器任一报错被吞，命中数静默减少且**无任何痕迹**。
- **修复**：补 `logger.warning(..., exc_info=True)`（draft 用 debug）；新增模块级 logger。
- **说明**：fail-closed 语义保留（单条失败不影响整体），仅增加可观测性。

### P2-7 · `get_lixin_mutagen` 用 `id()` 比对（代码质量）

- **位置**：`rules/qintian/features.py` L119-121
- **证据**：`id(ft)` 比对，但 `get_self_mutagen`（源自 `palace_stems`）与 `get_xiangxin_mutagen`（源自 `flying_transforms`）各自新建对象，id 恒不相等 → 过滤恒不生效。
- **修复**：改为按飞化四要素（值）比对。
- **说明**：经分析，两者 `target_palace` 定义上不同（本宫 vs 对宫）→ **key 空间不相交**，故本盘无行为差异。此修复属**代码质量改进**（防未来数据源变化），非功能缺陷。

---

## 三、待裁决项（2 项，未擅自修改）

### 待裁决-1 · `SANHE_TREND_DIMENSION` 缺 5 键

- **位置**：`rules/answer_layer.py` L117-135
- **实测**：`STAR_JUDGMENTS` 有 5 个 trend 未登记 —— `善/智`(天机)、`财/刚`(武曲)、`桃花/欲`(贪狼)、`印/福`(天相)、`杀/成败`(七杀)；`PATTERN_JUDGMENTS` 缺 1 键（`财/刚`）。
- **为何不修**：缺键时兜底值（JUDG→「命宫」、PATTERN→「格局」）**语义本身合理**（坐命断语本就讲命宫；格局本属体用层）。补键会把这些断语改判到宫位维，属**行为变更**，且与既有测试 `test_ziwei_answer_layer_p12.TestAnswerLayerZ74f` 断言冲突（该测试 L82 docstring 与 L103 断言本身自相矛盾）。需设计裁决。
- **建议**：明确「坐命断语是否应按 trend 拆维」这一机制设计后，再决定补键或改兜底。

### 待裁决-2 · `PATTERN_DEFS` 两组星组重复 → 同盘双命中

- **位置**：`rules/rule_graph.py` L82 vs L117、L95 vs L119
- **实测**：
  - `{"紫微","天府"}` → 「天府朝垣」(L82) 与「紫府同宫」(L117)，且 L82 描述自己写「紫府同宫，稳重富贵」→ 疑为**定义误写**。
  - `{"天同","天梁"}` → 「天同天梁」(L95) 与「同梁同宫」(L119)，描述几乎相同。
- **影响**：`_match_patterns` 以 `required_stars <= sanfang_set` 匹配，紫微+天府坐命会**同时命中两条**，重复计数。
- **为何不修**：格局定义属命理内容，需《紫微斗数全书》格局篇权威依据 + 用户裁决（合并 / 区分星组 / 删除其一），不宜擅改。

---

## 四、文档修复（P3）

| 文件                          | 位置                      | 修正                                                                                                                          |
| --------------------------- | ----------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `ziwei/__init__.py`         | L15                     | 「答案层八维度」→「分层输出（12 宫位维 + 体用层）」                                                                                               |
| `rules/answer_layer.py`     | 模块 docstring、L18、L73    | 八维度/十五维 → 分层结构；旧 8 维标注 LEGACY                                                                                               |
| `rules/rule_graph.py`       | 模块 docstring、L132-147   | 「四派/Zhongzhou/Feixing」→ 两派（Z17 收敛后）                                                                                         |
| `rules/dimension_bridge.py` | L32/L47-59/L75/L97/L119 | 「15 维」→「12 宫位维」；体用项入跨维池                                                                                                     |
| `rules/interpretation.py`   | L1111、L1856-1857        | 「8 维对齐桥」→「12 宫位维对齐桥」                                                                                                        |
| `ziwei_engine.py`           | `full_chart` L970-983   | **双 docstring 缺陷**：两个连续字符串字面量，第一个吞掉详细说明（第二个成 dead code）→ 合并                                                                 |
| `ziwei_engine.py`           | `_stub` L1329-1342      | 无效农历转换：`Solar.fromYmd(y,m,d).getLunar().getSolar()` 是**恒等变换** → 改 `Lunar.fromYmd(...).getSolar()`（实测 1983-9-29 → 1983-11-3） |

---

## 五、未处理项（如实说明）

| 项                            | 位置                                                                                                                                                                                                                                                           | 说明                                                                                   |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| 死代码模块群                       | `pattern_rules.py`(ALL_PATTERNS=49)、`temporal_rules.py`、`temporal_facts.py`、`wuxing_rules.py`、`palace_relationship.py`、`child_limit_rules.py`、`nvming_rules.py`、`limit_advanced_rules.py`、`palace_general_rules.py`、`aux_star_verdicts.py`、`aux_star_ext.py` | `src/` 内零生产引用（仅测试可达）。**未删**：可能是预留资产，需确认后处理                                           |
| 判定表覆盖不足                      | `qintian/judgments.py` `JUDGMENT_MAPPING`=28 键                                                                                                                                                                                                               | 60 条 production 中 32 条落 neutral 分支；docstring 写「8 条」                                  |
| evidence_ref 悬空              | `method_graphs.py` L477/497/531                                                                                                                                                                                                                              | `ZW-PATTERN-*`/`ZW-SIHUAI-*`/`ZW-PALACE-*` 无注册表定义（`verification_status="candidate"`） |
| `VERDICT_INTERPRETATION` 组合键 | `answer_layer.py` L689-959                                                                                                                                                                                                                                   | 煞/辅组合键（如「火星铃星」）因 facts 仅主星而不可达                                                       |
| 斗君/斗数常数 docstring            | `combinations.py` L6、`evidence.py` L11 等多处                                                                                                                                                                                                                   | 数字滞后（「8 条」vs 60 等）                                                                   |

---

## 六、回归验证

| 项                    | 结果                                         |
| -------------------- | ------------------------------------------ |
| 紫微全量测试               | **552 passed / 0 failed**（33 个测试文件分 5 批跑完） |
| 健康检查                 | **40/40 PASS**（0 WARN / 0 FAIL）            |
| 外部案例校对（1983-11-03 女） | **21/21 通过**                               |

**沙箱限制说明**：`test_body_palace_only_six_homes` 需 480 次 node 子进程（iztro 排盘），在本沙箱稳定被拦（`WinError 5` / SIGTERM），**非代码缺陷**（已用小样本单独验证：身宫落宫恒在六寄宫内，逻辑正确）。

---

## 七、结论

- 紫微引擎三层架构接线完整，无死链；辨层**未发现**投票/加权/融合等铁律违反。
- 本轮修复 **7 项**（P1×3 / P2×4），均为**确定性缺陷**（幻影规则、字段缺失、命名不一致、不可达分支、缺失导入、静默吞噬）。
- **2 项待裁决**（trend 缺键、格局星组重复）涉及命理内容与行为变更，已列证据与建议，等待裁决。
- 文档滞后群已同步（7 处）。
