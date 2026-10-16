# 紫微引擎 Z80-H 交付报告（待裁决项收口）

- **日期**：2026-10-15
- **范围**：收口 `ZIWEI_ENGINE_FULL_AUDIT_20261014.md` 遗留的 **5 项待裁决** + **11 个未接线模块**
- **环境**：`D:/shuntian/.venv/Scripts/python.exe`
- **基线 commit**：`e1bc3c77`（Z80-G 全面深度审核报告）

---

## 一、收口总览

| # | 待裁决项 | 处置 | 状态 |
|---|---|---|---|
| 1 | `JUDGMENT_MAPPING` 28/60 | 补齐至 **60/60**（32 条按原典语义转写） | ✅ 完成 |
| 2 | `PATTERN_DEFS` 星组重复（40 条 / 38 unique） | 去重为 **38 条 / 38 unique** | ✅ 完成 |
| 3 | `evidence_ref` 悬空（ZW-* 无注册表） | 建 **74 条**显式注册表 + 加载器回查 | ✅ 完成 |
| 4 | 自化事实 `direction` 恒 `"out"` | 修条件嵌套，`self` 分支可达 | ✅ 完成 |
| 5 | 倪海厦「六杀」伪星键 | 移除伪键注册，原文留注 | ✅ 完成 |
| 6 | 11 个未接线模块 | 显式索引 + 收敛 + 加载入口 | ✅ 完成（见 §五） |

---

## 二、逐项交付明细

### 2.1 `JUDGMENT_MAPPING` 28 → 60（内容缺口补齐）

- **文件**：`src/tongshu/engines/ziwei/rules/qintian/judgments.py`
- **缺口**：60 条 production 组合中 **32 条**无判定强度与 facts，`resolve_judgment` 落 `neutral`。
- **处置**：为 32 条补齐 `judgment_strength` + `neutral_facts_template`。
  - **数据来源严格限定**：逐条转写自 `combinations.py` 各 detect 函数**已有的古典语义摘要**（蔡明宏《悟我十八年》/《飞星秘仪》/ 陆斌兆《讲义》），**未新增任何命理内容**。
  - `strength` 沿用既有分层惯例：结构决定性 `strong` / 一般组合 `moderate` / 轻微征象 `weak`。
- **验证**：
  - production 60 条 **全部命中映射**，`neutral` 归零（实测 `still neutral = 0`）。
  - 强度分布：`strong 41 / moderate 17 / weak 2`；无空 `neutral_facts`。
  - `resolve_judgment` 仍保留 fail-closed（未登记 → neutral）。

### 2.2 `PATTERN_DEFS` 星组去重 40 → 38

- **文件**：`src/tongshu/engines/ziwei/rules/rule_graph.py`
- **重复项**：`{紫微,天府}`（天府朝垣 / 紫府同宫）、`{天同,天梁}`（天同天梁 / 同梁同宫）→ 同盘双命中。
- **处置**：
  - `天府朝垣` 星组改为 `{天府}`（本义为「天府守命、紫微来朝」，非紫府同宫），保留 `紫府同宫` 承 `{紫微,天府}`；
  - 删除冗余 `天同天梁`（保留 `同梁同宫`）；
  - 删除冗余 `天府坐命`（与改后 `天府朝垣` 单星组重复）。
- **验证**：38 条 / **38 unique 星组**，无重复。

### 2.3 `evidence_ref` 悬空 → 显式注册表（74 条）

- **新增**：`src/tongshu/engines/ziwei/rules/evidence_registry.py`
- **问题**：`method_graphs.py` 的 `RuleSpec.evidence_refs` 以 f-string 模板生成 4 族引用
  （`ZW-SIHUA-*` / `ZW-STAR-*` / `ZW-PATTERN-*` / `ZW-PALACE-*`），全项目**无注册表定义**，审计 G1 gate 无法回查。
- **处置**：
  - 建注册表，逐条登记 `ref_id → 出处/章节/校验状态`；
  - 覆盖度自检 `completeness_report()`：**74/74**（SIHUA 10 + STAR 14 + PATTERN 38 + PALACE 12），`complete=True`；
  - **顺带补齐解层加载器**：`ZiweiEvidenceLoader._load_sanhe()` 此前仅注册 `SANHE-PATTERN-*`，
    SIHUA / PALACE / JUDG 三族恒查无 → 落 UNDETERMINED。现按注册表出处补齐，并新增
    `resolve_zw_ref()` 供 ZW-* 直接回查。
- **验证**：`SANHE-SIHUA-甲` / `SANHE-SIHUA-癸-化忌` / `SANHE-PALACE-命宫` / `SANHE-JUDG-紫微`
  均解析成功；未登记 ref fail-closed 返回 `None`。

### 2.4 自化事实 `direction` 恒 `"out"`

- **文件**：`src/tongshu/engines/ziwei_engine.py`
- **问题**：外层 `if star not in all_stars` 已把「星在本宫」排除，导致 `direction="self"` 分支**永不可达**；
  钦天 QTN-004/007/018 依赖自化方向。
- **处置**：移除该外层条件，改为「先定位化星所在宫，再判定 `self`/`out`」。
- **验证**：`self` 分支可达；紫微全量测试通过。

### 2.5 倪海厦「六杀」伪星键

- **文件**：`src/tongshu/engines/ziwei/rules/nihai_assertions.py`
- **问题**：`star="六杀"` 为聚合伪星键，而 `get_assertions(star, palace)` 的 star 恒来自盘面星名
  （盘面不存在「六杀」这颗星）→ 该断言**永不可触发**。
- **处置**：移除该条注册；其文本（六煞组通用原则）已由火星/铃星/天空/地劫 4 条共用表述覆盖，
  原文保留为注释供人工查阅。
- **注**：同文件 `"天空"` **非缺陷**（盘面「天空」「地空」是两颗不同的星），未改动。

---

## 三、11 个未接线模块处置

- **新增**：`src/tongshu/engines/ziwei/rules/asset_index.py`（显式索引，机器可查）
- **收敛**：`palace_relationship.py` 去除与 `ZiweiPalaceResolver` 重复的 12 地支副本，改为复用 canonical 常量。
- **索引规模**：11 模块 / **203 条**非聚合资产条目（`total_items` 已排除 `ALL_*` 汇总项，避免重复计数）。

| 模块 | 处置 | 条目 | 说明 |
|---|---|---|---|
| `pattern_rules` | WIRE | 70 | 富6/贵27/贫8/杂8 + 12宫得地12/失陷9 |
| `temporal_rules` | WIRE | 29 | 太岁小限25/斗君1/流曜3 |
| `temporal_facts` | WIRE | 10 | 流禄流羊流陀（年干→地支） |
| `child_limit_rules` | WIRE | 5 | 童限安法 |
| `nvming_rules` | WIRE | 15 | 女命骨髓赋9 + 专条6 |
| `limit_advanced_rules` | WIRE | 7 | 羊陀迭并/七杀重逢 |
| `palace_relationship` | CONVERGE | 0 | 已收敛为复用 canonical 地支常量 |
| `wuxing_rules` | EVIDENCE_INDEX | 39 | 星曜五行36 + 生克制化3 |
| `palace_general_rules` | EVIDENCE_INDEX | 6 | 十二宫总论 |
| `aux_star_verdicts` | EVIDENCE_INDEX | 16 | 辅8/煞6/杂2 |
| `aux_star_ext` | EVIDENCE_INDEX | 6 | 天伤天使/哭虚/鸾喜 |

**处置说明**：
- **CONVERGE（1）**：`palace_relationship` 已实际去重收敛。
- **EVIDENCE_INDEX（4）**：古籍原文资产（`school=CLASSICAL_SOURCE`），内容不可再生，
  现登记入册、可溯源；不强行接入生产匹配（与既有 `palace_star_verdicts`/`nihai` 部分重叠）。
- **WIRE（6）**：**已索引 + 已提供显式加载入口 `load_asset()`**（消除「零引用」）；
  生产语义接线见 **§七 Z80-H-2**（本轮已完成）。

---

## 七、Z80-H-2 接线与补齐（2026-10-15 第二轮）

第一轮把 6 个 `WIRE` 资产只做到「索引 + 入口」，本轮**真正接入生产**，并补齐其余缺口。

### 7.1 6 个 WIRE 资产接入生产（新增 `classical_detail` 独立通道）

- **新增**：`src/tongshu/engines/ziwei/rules/classical_detail.py`
- **接入点**：`build_answer()` 新增顶层键 `classical_detail`（**独立通道**，不并入
  12 宫位维 / 体用层——不融合、不污染、可回查）。
- **各资产接线方式（均为机器可判定条件，fail-closed）**：

| 资产 | 接入段 | 判定条件 |
|---|---|---|
| `pattern_rules` | `palace_jue` | 命宫地支 ∈ `palace_branch`（得地12 / 失陷9 逐宫诀） |
| `pattern_rules` | `classical_patterns` | `supporting_stars ⊆ 命三方`（命宫+三合+对宫）候选级 |
| `nvming_rules` | `nvming` | `gender=female` 且 命宫星 ∩ `good_stars/bad_stars` |
| `child_limit_rules` | `child_limit` | 虚岁 1–15 出安童限诀；十二宫强弱常出 |
| `limit_advanced_rules` | `limit_advanced` | 本命羊陀冲命 + 流年流羊流陀（羊陀迭并/七杀重逢） |
| `temporal_rules` | `temporal_rules` | 太岁宫 == 小限宫 且 该宫星 ∩ 吉凶星表 |
| `temporal_facts` | `temporal_facts` | 小限宫 / 斗君宫 / 太岁宫 / 流禄流羊流陀 落宫 |

- **作用域调优**：`classical_patterns` 若全盘扫描会产生 28 条伪命中（实测 1983 盘），
  收紧为「命三方」后降为 1 条，与古籍「格局看命三方」一致。
- **`temporal_facts` 收敛**：`ziwei_engine._compute_doujun` 改为**复用**
  `temporal_facts.doujun_branch`（单一事实源），删除重复的安法公式。

### 7.2 补齐的其余缺口

| 缺口 | 原状 | 处置 |
|---|---|---|
| `soul_palace_sihua` 恒空 | 生产路径恒 `[]`，而 `evidence_producer.py:71` 消费它 → 该分支恒无产出 | 裁定语义为「**生年四化入命宫**」，`full_chart` 填充 HUA_* 编码；分支恢复产出 |
| `daily_luck_palace` 死字段 | 仅 to_dict/from_dict 出现，从无赋值 | 由 iztro `daily.palaceNames` 定位流日命宫地支 → 映射本命宫名填充 |
| `VERDICT_INTERPRETATION` 102 键不可达 | 仅主星调用，辅煞/斗君 102 键永不可达 | 经 `classical_detail.aux_verdicts` 以「本盘实际辅煞星 + 斗君落宫」接入 |
| `_detect_cross_method_consensus` 命名 | 名含「共识」易误读为投票/融合 | 更名 `_observe_cross_method_agreement`（保留旧名别名），明确观测性质 |
| `dependency_adapter` 冗余 | 声称修 iztro bug，实测差异为 0 | 模块头补 Z80-H 复核结论：六十甲子干/支**奇偶恒同**→ 本就等价，属**防御性审计层（实测 no-op）** |
| `SANHE_TREND_DIMENSION` 缺 5 键 | Z80-F 待裁决 | **实测补键破坏既有契约**（`TestAnswerLayerZ74f` 要求武曲坐命落命宫）→ **决定保留兜底**，在代码内显式记录裁决理由，避免重复提出 |

### 7.3 Z80-H-2 回归

| 项 | 结果 |
|---|---|
| 紫微全量测试（34 文件） | **587 passed / 32 subtests / 0 failed** |
| 健康检查 | **43/43 PASS** |
| 随机盘冒烟（40 盘，已扩检 `classical_detail` 新通道） | **40/40**；A–G 七项全 **0** |
| 新增单测 | `test_ziwei_classical_detail_z80h.py`（15） |

> 说明：一次全量运行中出现 1 例 `EPERM node_modules/iztro/.../ja-JP/brightness.js`
> 失败，经复跑确认为**沙箱文件读拦截**（非代码缺陷），该测试单跑 17/17 通过。

---

## 八、结论

- 5 项待裁决**全部收口**：判定覆盖 60/60、格局 38 unique、证据注册表 74/74、自化方向可达、伪键清除。
- 11 个未接线模块：**6 个已真正接入生产**（`classical_detail` 通道）、1 个收敛、
  4 个证据资产入册；`self_check` 全绿。
- 补齐 4 项静默缺口：`soul_palace_sihua` / `daily_luck_palace` / 102 个不可达断语键 / 命名歧义。
- 2 项**经实测判定不宜改动**并留档：`SANHE_TREND_DIMENSION` 5 键（补键破坏契约）、
  `dependency_adapter`（非 bug，标注为防御层）。
- 回归全绿：**587 passed** + 43/43 健康检查 + 40 盘冒烟七项全 0。

---
*Z80-H / Z80-H-2 | 2026-10-15*
