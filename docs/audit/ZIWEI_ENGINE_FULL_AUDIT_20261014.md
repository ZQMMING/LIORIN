# 紫微引擎全面深度审核报告

- **日期**：2026-10-14
- **范围**：紫微引擎全量（外围 5 文件 2,904 行 + `ziwei/` 子包 42 文件 15,745 行 ≈ **18,649 行**）
- **方法**：两组子代理并行勘查（算层 / 辨层与规则资产）+ 逐项实测验证 + 边审边修
- **环境**：`D:/shuntian/.venv/Scripts/python.exe`
- **本轮 commit**：`3dba5ab3`（代码修复）、`300b2688`（文档校准）

---

## 一、基线核查

### 1.1 千问会话（Z80-B/C/D）改动核查

三个 commit **全部只改 `domain_reading.py`**（+446 行），**无配套单元测试**：

| commit | 内容 | 行数 |
|---|---|---|
| `42f301d9` | Z80-B 语义合成层（`STAR_PAIR_VERDICTS` / `STAR_SOLO_VERDICTS` / `PALACE_EXTRA_SEMANTICS`） | +314 |
| `d8a2d2ce` | Z80-C 跨盘正确性（`OPPOSITE_IMPACT` 写死 → `BORROWED_SEMANTICS` 模板动态填充；`_extra_on_domain` 领域过滤；`_push_extra` 去重） | +89 |
| `ce578022` | Z80-D 冒烟修复（30 盘 fact_mismatch 0 / dup 0） | +43 |

**核查结论**：改动质量良好——`BORROWED_SEMANTICS` 按本盘对宫主星动态生成，逻辑正确；40 盘冒烟 7 项全 0 佐证。**唯一缺口**：无单测（已由本会话 `c3b5e9ac` 落盘的冒烟脚本部分弥补）。

---

## 二、已修缺陷（本轮 7 项）

### P1-1 · `full_chart` 绕过 `_validate_inputs`（fail-closed 失效）
- **位置**：`ziwei_engine.py` `full_chart` 入口
- **证据（实测）**：`full_chart((1983,9,29), 25, 'male')` → **静默出盘**（25→丑时）；`gender='unknown'` → **静默接受**并触发 dependency_adapter 误报「discrepancy detected」；而 `compute()` 对同样输入正确抛 `ZiweiInputError`。
- **修复**：入口处补 `_validate_inputs(lunar_date, hour, gender)`。

### P1-2 · `full_chart` 恒空 `soul_palace_main_star` / `soul_palace_main_stars`
- **证据（实测）**：`full_chart` → `''` / `[]`；`compute` → `'QISHA'` / `['QISHA']`。该二字段被 `signal_engine.py` / `evidence_producer.py` 消费 → **两路径事实不一致**。
- **修复**：按命宫地支取本宫主星，空宫借对宫（新增 `_BRANCH_OPPOSITE` 地支六冲表）。
- **验证**：`full_chart(...).soul_palace_main_star == 'QISHA'`（与 compute 一致）✓

### P1-3 · `rules/decadal.py` `PALACE_ORDER[7]` 用「交友」而盘面为「仆役」
- **证据（实测）**：`PALACE_ORDER[7]='交友'`，`'交友' not in chart.palaces` → 流年/流月应期该宫主星**静默丢弃**。
- **说明**：与 Z80-F 已修的 `qintian/combinations.py` **同类问题**，此处漏改。
- **修复**：统一为「仆役」。

### P2-4 · `compute` 未捕获 `subprocess.TimeoutExpired`
- **证据**：`TimeoutExpired → SubprocessError → Exception`，**不属** `OSError`/`RuntimeError` → 超时会绕过降级契约原样泄漏。
- **修复**：补入 `except` 元组。

### P2-5 · 11 个零引用模块的灰色地带（见第四节）
- **修复**：全部加显式「未接线」标注（含逐项处置建议）。

### P3-6 · 陈旧计数注释（6 处，实测校准）
| 文件 | 原注释 | 实测 |
|---|---|---|
| `qintian/__init__.py:14` | 5 条 production 全部 grade=1 | **60 条**（grade 1×58 / 3×2） |
| `qintian/evidence.py:11` | 8 条 production | 60 条 |
| `qintian/combinations.py:6,92` | 8 条 detect | 60 条 |
| `qintian/judgments.py:27` | 8 条 production | **28 键 / 60 条** |
| `qintian/rule_graph.py:84` | 9 条 production | 60 条 |
| `pattern_rules.py:98,275` | 贵局 26 条 / 失陷破格诀 12 条 | **27 / 9** |

### P3-7 · `ZiweiChart` 恒空字段说明
- `daily_luck_palace`：**恒空死字段**（仅 `to_dict`/`from_dict` 出现，从无赋值）。
- `soul_palace_sihua`：生产路径恒空（`compute`/`full_chart` 均传 `[]`，仅 stub 填），但 `evidence_producer.py:71` **消费它** → 该分支恒无产出。

---

## 三、待裁决项（5 项，未擅改）

| # | 项 | 位置 | 说明 |
|---|---|---|---|
| 1 | **`JUDGMENT_MAPPING` 28/60** | `qintian/judgments.py` | 60 条 production 中 **32 条**无判定强度与 facts，落 neutral。属**内容缺口**，补齐需命理内容 |
| 2 | **`PATTERN_DEFS` 星组重复** | `rule_graph.py:82/117`、`:95/119` | `{紫微,天府}`（天府朝垣/紫府同宫）、`{天同,天梁}`（天同天梁/同梁同宫）→ 同盘双命中。40 条仅 **38 unique 星组** |
| 3 | **`evidence_ref` 悬空** | `method_graphs.py:172/295/447/500/520/554` | `ZW-PATTERN-*` / `ZW-SIHUA-*` / `ZW-PALACE-*` / `ZW-STAR-*` 全项目**无注册表定义**（仅 f-string 模板）→ 证据链无法回查 |
| 4 | **自化事实 `direction` 恒 `"out"`** | `ziwei_engine.py:353-362` | 仅当 `star not in all_stars` 才 append → `direction="self"` 分支不可达。钦天 QTN-004/007/018 依赖自化方向 |
| 5 | **倪海厦断言「六杀」伪星键** | `nihai_assertions.py:386` | `"六杀"` 为聚合伪星键，按星名查永不命中 → 该条断言不可触发。（同文件 `"天空"` **不是**缺陷——实测盘面「天空」「地空」是两颗不同的星） |

### 已澄清（非缺陷）
- **`dependency_adapter` 修的是不存在的 bug**：实测 1950–2000 共 100 盘，iztro 原始大限方向与「年干阴阳」判定**差异为 0**（60 甲子同奇偶，本就等价）。该适配器仅在 `full_chart` 接入，生产 `ZiweiSolarAdapter` 路径未接 → **既未修正也未验证**，属冗余。
- **跨派共识 `_detect_cross_method_consensus`**：取两派 facts 交集输出 `key=value`，与「不融合」铁律有张力，但**未做加权**，判为观测性质（建议改名）。

---

## 四、未接线资产处置（11 模块）

11 个模块在 `src/` + `tests/` + `scripts/` **全部零引用**，已在各模块 docstring 加显式标注：

| 模块 | 处置建议 | 理由 |
|---|---|---|
| `pattern_rules.py` | **应接线** | 富6/贵27/贫8/杂8 + 12宫得地12/失陷9 逐宫诀；生产 `PATTERN_DEFS` 仅星组，无此细目 |
| `temporal_rules.py` | **应接线** | 时间层解释（太岁小限/斗君/流曜），production 无时间层规则 |
| `temporal_facts.py` | **应接线** | 时间层 Fact（大限/小限/童限安法） |
| `child_limit_rules.py` | **应接线** | 童限/小儿命，production 无 |
| `nvming_rules.py` | **应接线** | 女命体系（女命骨髓赋），production 无女命专条 |
| `limit_advanced_rules.py` | **应接线** | 限运进阶（羊陀迭并/七杀重逢），与 QTN-059/060 概念近但规则不同 |
| `palace_relationship.py` | **可删/收敛** | 与 `ZiweiPalaceResolver.resolve_sanfang_sizheng` 及 `combinations._triple_of` 重复 |
| `wuxing_rules.py` | 证据资产 | 星曜五行 + 生克制化原典录入 |
| `palace_general_rules.py` | 证据资产 | 十二宫总论，部分已被 `palace_star_verdicts` 覆盖 |
| `aux_star_verdicts.py` | 证据资产 | 辅煞杂曜断语，与 `palace_star_verdicts`/`nihai` 重叠 |
| `aux_star_ext.py` | 证据资产 | 天伤天使/哭虚/鸾喜补遗，QTN-047~055 部分覆盖 |

**注**：均为 Z77–Z86 期录入的**古籍原文资产**（`school=CLASSICAL_SOURCE`），内容不可再生，**不建议直接删除**（`palace_relationship.py` 除外）。

---

## 五、回归验证

| 项 | 结果 |
|---|---|
| 紫微全量测试 | **552 passed / 0 failed** |
| 健康检查 | **43/43 PASS**（含 H 段随机盘冒烟） |
| 随机盘冒烟（40 盘） | A–G **七项全 0** |
| 文章案例校对 | **21/21** |

**沙箱限制**：`test_body_palace_only_six_homes` 需 480 次 node 子进程被拦（非代码缺陷，已用小样本验证逻辑正确）。

---

## 六、结论

- 三层架构接线完整；辨层**未发现**投票/加权/融合等铁律违反。
- 本轮修复 **7 项**（P1×3 / P2×1 / P3×3 组）。
- **5 项待裁决**（judgment 覆盖、格局星组、证据注册表、自化方向、六杀伪键）—— 均涉命理内容或行为变更，已列证据与建议。
- **11 个未接线模块**已从「灰色地带」转为「显式标注 + 处置建议」。
- 千问 Z80-B/C/D 改动经核查**质量良好**，唯一缺口是无配套单测。

---

## 七、Z80-H 收口（2026-10-15）

本报告 §三「5 项待裁决」与 §四「11 个未接线模块」已于 **Z80-H** 全部处置，
详见 `docs/audit/ZIWEI_ENGINE_Z80H_DELIVERY_20261015.md`。摘要：

| 待裁决项 | 收口结果 |
|---|---|
| `JUDGMENT_MAPPING` 28/60 | **60/60**（32 条按原典语义转写，未新增命理内容；neutral 归零） |
| `PATTERN_DEFS` 星组重复 | **38 条 / 38 unique**（去除 `{紫微,天府}`、`{天同,天梁}` 双命中） |
| `evidence_ref` 悬空 | 建 **74 条**注册表（SIHUA10/STAR14/PATTERN38/PALACE12）+ 加载器回查 |
| 自化 `direction` 恒 `"out"` | 修条件嵌套，`self` 分支可达 |
| 倪海厦「六杀」伪星键 | 移除伪键注册，原文留注 |

11 个未接线模块：新增 `asset_index.py` 显式索引（339 条），`palace_relationship` 已实际收敛，
6 个 `WIRE` 资产提供 `load_asset()` 入口（生产语义接线待专项）。

**回归**：紫微全量 **572 passed / 32 subtests / 0 failed**（基线 552）；健康检查 **43/43 PASS**；
随机盘冒烟 40/40，A–G 七项全 0。

---
*Z80-H 收口 | 2026-10-15*
