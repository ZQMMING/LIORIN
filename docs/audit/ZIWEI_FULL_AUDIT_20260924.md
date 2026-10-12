# 紫微斗数引擎全量审计报告

**审计日期**: 2026-09-24
**代码基线**: commit `e9fa5d74`（2026-09-19 紫微引擎V2全链净物落库）+ 工作区 1 处未提交修改
**审计范围**: `src/tongshu/engines/ziwei_*.py`（5 个）+ `src/tongshu/engines/ziwei/` 子包，共 **59 个 .py / 19,082 行**
**审计方法**: AGENTS.md §2「三重取证纪律」（调用图取证 + 生产入口链取证 + 测试对象核对）
**测试基线**: `pytest -k ziwei` → **476 passed / 1 skipped / 2 errors**（2 errors 属非紫微模块）

---

## 零、审计前提：既有 16 份紫微审计文档已全部过期

`docs/audit/` 下现存 16 份 `ZIWEI_*.md`，文件时间戳均为 **09-14**，内容基线为 **09-04 ~ 09-09**。而当前代码基线是 **09-19** 的 V2 落库。

过期证据（实测）：

| 旧审计（9-04）结论 | 当前实际状态 |
|---|---|
| `ziwei_engine.py` ~800 行 | **1108 行** |
| `ziwei_knowledge.py` 存在，为 dead code | **已删除** |
| `ziwei_pattern.py` 存在，无生产调用 | **已删除** |
| `feature_registry/adapters/zi_wei_adapter.py` 孤立 | **已删除** |
| 生产调 iztro `byLunar()` | 主路径已改 **`bySolar()`**，byLunar 降为 fallback |
| 测试基线 84 passed（5 文件） | **476 passed**（约 28 文件） |

**结论**：本次审计为全量重做，旧文档不可作为基线引用。这与 AGENTS.md §5 红线「禁止引用已被实测推翻的旧审计数字」一致。

---

## 一、核心裁决：生产路径仅占代码量的 10.5%

这是本次审计最重要的发现。

### 1.1 生产入口链（实测取证）

```
api/app.py
  ↓
pipeline.py:24                    from .engines.ziwei_engine import ZiweiEngine
  ↓
pipeline_stages/compute_stage.py
  :33-34   import ZiweiAdapter + ZiweiEngine
  :99      self._ziwei_adapter = ZiweiAdapter(ziwei_engine)
  :137     ziwei_chart = self._ziwei_adapter.compute(...)   ← 主路径
  :147     ziwei_chart = self.ziwei_engine.compute(...)     ← fallback（无 calc_context 时）
  ↓
ZiweiAdapter.compute()  →  compute_via_solar()  →  iztro bySolar()   [ziwei_adapter.py:55-78]
ZiweiEngine.compute()   →  _compute_via_iztro() →  iztro byLunar()   [ziwei_engine.py:265-333]
  ↓
ziwei_engine.py:829-834   ShuntianZiweiDependencyAdapter.adapt_from_chart()  ← 大限方向修正
ziwei_engine.py:849       from ...rules.brightness import get_brightness      ← try/except 可选增强
  ↓
canonical/composer.py:16  → ZiweiChart 写入 SIR
reasoning/signal_engine.py:217-295 → 仅读取 chart 的 soul/body palace 字段合成 ZIWEI BASELINE signal
```

### 1.2 生产可达文件清单（完整，仅 6 个）

| 文件 | 行数 | 生产角色 |
|---|---|---|
| `engines/ziwei_engine.py` | 1108 | 计算核心 |
| `engines/ziwei_adapter.py` | 236 | bySolar 适配 + 时间政策 |
| `engines/ziwei_dependency_adapter.py` | 475 | iztro 2.6.0 大限方向修正 |
| `engines/ziwei/rules/brightness.py` | 56 | 庙旺利陷（唯一被生产引用的 rules 模块） |
| `engines/ziwei/rules/feixing_rule_graph.py` | 130 | 事实层（PalaceStemFact/FlyingTransformFact），Z17 有意保留供钦天共用 |
| `engines/ziwei/__init__.py` | 6 | 包声明 |
| **合计** | **2,011** | **占 19,082 行的 10.5%** |

### 1.3 非生产可达：17,071 行（89.5%）

**整个 `rules/` 推理与断言体系不在生产路径上。** 逐项取证：

| 模块 | 行数 | 调用方取证结果 |
|---|---|---|
| `rules/qintian/` 全子包 | ~5,300 | `compute_multi_method_signals()` 仅被 `interpretation.py:2293` 调用 |
| `rules/interpretation.py` | 2339 | `ZiweiInterpreter`/`interpret_signal`/`build_life_reading` **仅 tests 引用**（`test_ziwei_interpretation.py` 8 处） |
| `rules/answer_layer.py` | 907 | `build_answer()` **仅 tests 引用**（`test_ziwei_answer_layer_p12.py` 7 处） |
| `rules/multi_method.py` | 274 | 仅 `interpretation.py:31,2293` 引用（自身也在孤儿链上） |
| `rules/nihai_assertions.py` | 662 | 仅 tests 引用 |
| `rules/palace_star_verdicts.py` | 507 | 零引用 |
| `rules/zhongzhou/` 全子包 | ~1,178 | 零外部引用，仅子包内自引用 |
| `rules/feixing/` 全子包 | ~1,432 | 仅 `test_ziwei_feixing_p05_a.py` 引用 |
| `engines/ziwei_method_profile.py` | 286 | **孤儿**（见下方纠正） |
| `engines/ziwei_palace_resolution.py` | 497 | **孤儿**（见下方纠正） |
| `engines/ziwei/dataset_bridge.py` | 512 | 仅 tests + 脚本引用 |
| `engines/ziwei/evidence_producer.py` | 268 | 仅 tests 引用 |
| `engines/ziwei/z14/evidence_collector.py` | 287 | 仅 tests 引用 |
| 15 个纯孤儿 rules 文件 | 2,151 | 零引用（清单见附录 A） |

### 1.4 纠正：两个被误判为「生产可达」的模块

`ziwei_method_profile.py`(286行) 与 `ziwei_palace_resolution.py`(497行) 常被误认为生产模块。实测取证：

- 全 `src/` 中对 `ziwei_method_profile` 的唯一「引用」是 **`ziwei_engine.py:82` 的一行注释**：
  `# 中州派（王亭之）表见 ziwei_method_profile.SIHUA_TABLE_ZHONGZHOU，`
  —— 是注释文本，不是 import。
- 且该注释指向的 `SIHUA_TABLE_ZHONGZHOU` **变量根本不存在**（全仓库 grep 0 命中），属悬空文档引用。
- `ziwei_palace_resolution.py` 的全部匹配项都在**它自己文件内部**。
- 两者的真实调用方只有测试：`test_ziwei_method_profile.py:20`、`test_ziwei_palace_resolution.py:20,26`、`test_ziwei_rule_graph.py:20,158,178`、`test_ziwei_qintian_p07.py:51`、`test_ziwei_z14_same_chart.py:19`。

**定性：仅测试可达（孤儿），非生产路径。**

### 1.5 False-Green 风险：极高

按 AGENTS.md §2 第 3 条「测试对象核对」，476 个通过的测试中，**绝大多数测的不是生产对象**：

- `test_ziwei_qintian_p07.py` / `p11.py` 测 `qintian/combinations.py`(3609行) → 非生产
- `test_ziwei_interpretation.py` 测 `interpretation.py`(2339行) → 非生产
- `test_ziwei_answer_layer_p12.py` 测 `answer_layer.py`(907行) → 非生产
- `test_ziwei_nihai_assertions.py` 测 `nihai_assertions.py`(662行) → 非生产
- `test_ziwei_feixing_p05_a.py` 测 `feixing/` 子包 → 非生产，且该派已被 Z17 决议废弃

**反向缺口**：唯一真正生产可达的 `rules/brightness.py` **没有专门测试文件**。生产路径上覆盖最薄的恰是最该测的。

---

## 二、P0 级缺陷（3 项）

### P0-1 宫位命名不一致导致钦天门规则静默失效（实测确认）

**缺陷**：`ZW_PALACES_ORDER` 在第 8 宫存在两种写法，与 iztro 实际输出不匹配。

| 位置 | 第 8 宫 |
|---|---|
| `ziwei_engine.py:101` | 仆役 |
| `ziwei_palace_resolution.py:48` | 仆役 |
| `ziwei_dependency_adapter.py:180` | 仆役 |
| **`rules/qintian/combinations.py:54`** | **交友** ← 不一致 |
| **`rules/decadal.py:25`** | **交友** ← 不一致 |

**实测验证**（运行 iztro + 调用 `_palace_index`）：

```
iztro 实际返回的12宫名: ['父母','福德','田宅','官禄','仆役','迁移','疾厄','财帛','子女','夫妻','兄弟','命宫']
其中含'仆役'? True  |  含'交友'? False

combinations.py: _palace_index("仆役") = -1     ← 查不到，返回哨兵值
combinations.py: _palace_index("交友") = 8
```

**影响**：`_palace_index()`（`combinations.py:59-64`）在 `ValueError` 时返回 `-1` 而非抛错。所有涉及仆役宫的钦天门规则会拿到 `-1` 参与后续索引/三方四正运算，产出**静默错误的结果**，不报错、不告警。`decadal.py:25` 同样受影响（大限宫位推算）。

`interpretation.py:1194` 有一行注释显示开发者知道这个问题：`# 注：部分排盘系统用"仆役"代替"交友"，需兼容两种写法` —— 但**只在 interpretation.py 做了兼容，combinations.py 和 decadal.py 没有**。

**修复方向**：统一为 iztro 实际输出的「仆役」；或建立单一权威宫序常量供全仓库 import，消除 4 份重复定义。

### P0-2 9-19 V2 落库违反「紫微 Canonical BLOCKED」冻结约束

AGENTS.md §3 冻结清单明文规定：

> **紫微 Canonical | BLOCKED | 书目/Passage Registry/流派/四化/时间规则无正式冻结记录；iztro stub 仅在 `TONGSHU_ALLOW_ZIWEI_STUB=1` 下可运行；禁止补算法/星曜/四化**

而 commit `e9fa5d74`（9-19）新增了：

- 四化落宫计算 `get_sihua_palaces()`（`ziwei_engine.py:477-504`）
- 宫干自化 `get_zigong_zihua()`（`ziwei_engine.py:571+`）
- 三方四正计算 `get_sanfang_sizheng()`（`ziwei_engine.py:506-563`）
- 流日/流月应期字段（`ziwei_engine.py:135-138`）
- 钦天门完整规则包 `rules/qintian/`（~5,300 行）
- Z46~Z93 释义层（`interpretation.py` 2339 行、`answer_layer.py` 907 行）

这些均属「补算法/星曜/四化」范畴。**在 Canonical 未解冻、Passage Registry 未建立的前提下扩充计算层与断言层，构成对冻结约束的直接违反。**

需要裁决：是**补办解冻手续**（建立 Passage Registry + 冻结记录），还是**回退 V2 落库**。这是治理决策，不是技术问题。

### P0-3 三状态分离与 7 层 Gate 在紫微完全未落地

**三状态分离**（AUDIT_GUIDE §4 核心治理原则）：
实测 grep `EVIDENCE_STATUS|MATCH_STATUS|CONCLUSION_STATUS`（含大小写变体）在整个 `src/tongshu/engines/ziwei/` 下 **0 命中**。

当前实际链路是「匹配即结论」：
```
QintianCombination.detected=True  →  semantic_summary    [combinations.py:42-48]
MethodMatch.judgment_text         ←  辨层直接填充        [multi_method.py:47-54]
interpret_signal()                →  conclusion          [interpretation.py:73]
```
`MethodMatch` 把 match 与 judgment 合为一体，**中间没有独立的「结论授权」判定**。这正是 AUDIT_GUIDE §4.3 明令禁止的「❌ MATCHED → 自动授权结论」。

**7 层 Gate**：
Gate 实现位于 `src/tongshu/audit_validation/gates/`（g1_evidence ~ g4_output + runner）。实测 grep `gate|admission` 在 `engines/ziwei/` 下 **0 命中** —— 紫微断言**完全绕过 Gate**。

9-19 新增的约 1,000+ 条断言/释义（`interpretation.py` + `answer_layer.py` + `qintian/combinations.py`）**未经任何 Gate 审查**。

> ⚠️ 缓解因素：由于 §1 已证明这些模块**不在生产路径上**，Gate 缺失尚未造成线上影响。但一旦接入生产，即为无条件放行。

---

## 三、P1 级缺陷（6 项）

### P1-1 bySolar 生产主路径无交叉验证防线

`tests/test_ziwei_chart_cross_validate.py`（旧审计称「公式 vs iztro 一致」，4 passed / 32 subtests）实测发现：

- 验证维度：命宫地支、身宫地支、命宫天干、五行局（4 维 × 8 案例）
- **仅走 byLunar 路径**（直接调 `engine.full_chart(lunar, ...)`）
- **生产主路径 bySolar 完全没有交叉验证**
- 边界案例全缺：无晚子时(23h)、无闰月专项、无立春前后、无真太阳时跨时辰

生产走的路径没有独立公式验证，等于计算正确性无防线。考虑到项目历史上出过「88% 案例 Day Master 错误」的同类事故（AUDIT_GUIDE §6.1），这是高风险缺口。

### P1-2 `ZiweiCalculationPolicy.date_source = "lunar"` 是死配置且与事实矛盾

`ziwei_adapter.py:23-24`：
```python
date_source: str = "lunar"
late_zi_handling: str = "same_day"
ratified_policy_version: str = "P0-14-v1"
```
并声明 `is_ratified` 恒为 `True`（已批准冻结）。

实测 grep：`date_source` 仅在 `to_dict()` 序列化时输出，**无任何代码读取它做路径分支**。而实际主路径走的是 **bySolar**（docstring 自己也写「使用 iztro 的 bySolar 函数（阳历输入），而非 byLunar」）。

一份自称「已批准冻结」的政策对象，其核心字段与实际行为相反且从不被读取 —— 属误导性死配置。

### P1-3 未知星名静默丢弃

`ziwei_adapter.py:147`：
```python
[CHINESE_STAR_TO_KEY.get(s, s) for s in major if CHINESE_STAR_TO_KEY.get(s)]
```
`if CHINESE_STAR_TO_KEY.get(s)` 会过滤掉不在表中的星名，导致 `get(s, s)` 的默认值**永远不会生效**。

若 iztro 升级后新增主星或返回变体名称，将**无声丢数据**。

历史先例：代码注释自陈「2026-08-27 修正: 天相(TIANXIANG) 此前缺失导致命宫天相的盘紫微基线失效」—— 这类遗漏已真实造成过 bug。

当前 14 主星覆盖已核查完整（紫微/天机/太阳/武曲/天同/廉贞/天府/太阴/贪狼/巨门/天相/天梁/七杀/破军，`ziwei_engine.py:62-77` 与 `MAIN_STAR_USO:38-53` 均无遗漏）。风险在于未来无告警机制。

### P1-4 MethodProfile 流派隔离形同虚设

`ziwei_method_profile.py` 设计了 `get_sihua_table()` 契约接口，但实测：

- 生产代码 **30+ 处**直接 import 全局硬编码的 `GAN_SIHUA`（`ziwei_engine.py:86-97`）
- `get_sihua_table()` 仅 **2 处**调用（`method_graphs.py:138,398`），而 `method_graphs.py` 本身在孤儿链上

即：**流派隔离机制已设计但生产主路径完全绕过它**。旧审计（9-04）第 10 问就标记过「`GAN_SIHUA` 硬编码，无 MethodProfile 隔离」，**整改至今未执行**。

### P1-5 `extract_baseline_signal()` 事实与解释混淆（旧审计整改未执行）

AUDIT_GUIDE §4.3 禁止事实与解释混淆，旧审计（9-04）第 9/14 问明确判定并要求「须从引擎移到辨层/推理层」。

实测：该函数**仍在 `ziwei_engine.py:289-316`**，仍产出带 `direction="STABLE"` / `polarity="neutral"` / `strength="moderate"` 的 Signal。

**整改未执行。**

### P1-6 `FrozenZiweiChart` 是假冻结

- `ziwei_engine.py:117` 标注 `@dataclass(frozen=True)`
- 但含 `list` / `dict` 可变字段（`:120-122, :128`）
- `ziwei_engine.py:1108` 的 `FrozenZiweiChart = ZiweiChart` **仅为类型别名**

`frozen=True` 只阻止重新绑定属性，**不阻止修改 list/dict 内容**。外部可执行 `chart.palaces["命宫"] = ...` 篡改「冻结」盘。

`ziwei_palace_resolution.py` docstring 第 8 行声称「所有输出冻结（Frozen），不修改 FrozenZiweiChart」—— 该声称**无运行时保障**。实测未发现 `object.__setattr__` 之类的主动绕过，但冻结语义本身不成立。

---

## 四、P2 级问题（清理项，7 项）

| # | 问题 | 位置 |
|---|---|---|
| P2-1 | `docs/signal_ontology.md` **不存在**，但 `MAIN_STAR_USO`/`CHINESE_STAR_TO_KEY` 注释声称 source 为该文档 §5.4 → 无源断言 | `ziwei_engine.py:37,59` |
| P2-2 | 注释引用不存在的 `SIHUA_TABLE_ZHONGZHOU` | `ziwei_engine.py:82` |
| P2-3 | `except Exception` 静默降级：`:280` iztro 失败时返回 stub（最危险）；另 `:855/:892/:1051/:1074` 共 4 处宽泛捕获 | `ziwei_engine.py` |
| P2-4 | `interpretation.py:142,151` 有 `except ImportError: pass`，会掩盖断链 | `rules/interpretation.py` |
| P2-5 | `qintian_doujun_data.py:48-53` 的 `get_doujun_weight()` 返回 weight/pct，命名触碰「禁止评分机制」禁区（实际为宫位比重，非评分决策），建议改名 `palace_ratio` | `rules/qintian/qintian_doujun_data.py` |
| P2-6 | `nihai_assertions.py:96` source 字段仅「主星册·紫微」，无页码/章节号，精度不足无法核验 | `rules/nihai_assertions.py` |
| P2-7 | 15 个纯孤儿文件共 2,151 行可安全删除（清单见附录 A） | `rules/` |

---

## 五、通过项（实测确认合规）

审计不只找问题，以下各项**实测通过**：

| 项 | 判定 | 证据 |
|---|---|---|
| **subprocess 编码规范** | ✅ 通过 | 全部 9 处 `subprocess.run` 均带 `encoding="utf-8"`：`ziwei_engine.py:369,435,467,713,743,770,820,937` + `ziwei_adapter.py:100` + `dataset_bridge.py:248`（本次修复）。无 `open()`/`read_text()` 漏网 |
| **时辰映射 time_index** | ✅ 通过 | 实跑 0~23 全量验证，与 iztro 约定完全一致（h=23→12, h=0→0, 其余 `(h+1)//2`）。两处实现已统一，无第三处独立实现 |
| **四化表流派归属** | ✅ 通过 | `GAN_SIHUA` 与 `SIHUA_TABLE_CLASSIC` **逐天干完全一致**；戊科=右弼、庚科=太阴、壬科=左辅 → **三合派通行本**，与中州派（太阳/天府/天府）明确不同；`ziwei_engine.py:79-85` 注释标注清晰 |
| **14 主星覆盖** | ✅ 通过 | `CHINESE_STAR_TO_KEY` 与 `MAIN_STAR_USO` 均完整覆盖 14 主星 |
| **大限方向修正** | ✅ 通过 | `compute_expected_direction()`（`ziwei_dependency_adapter.py:107-137`）符合「阳男阴女顺、阴男阳女逆」；已被生产调用（`ziwei_engine.py:829-834`）；iztro 仍为 2.6.0，上游未修，不存在二次修正风险 |
| **STUB 环境变量门控** | ✅ 通过 | `ziwei_engine.py:271-286` 双重检查 `TONGSHU_ALLOW_ZIWEI_STUB=="1"`；`test_ziwei_engine.py:118-154` 覆盖默认抛错 + env 允许两条路径 |
| **三方四正偏移** | ✅ 通过 | `ziwei_engine.py:1004-1008`（宫序 ±4/±6/±8）与 `palace_resolution.py:264-266`（地支索引）等价，因十二宫地支连续排列 |
| **宫位解析 9 种类型** | ✅ 通过 | `ziwei_palace_resolution.py` docstring 声明的 A~I 九类解析**均有真实实现**，非虚假文档 |
| **格局判定非关键词触发** | ✅ 通过 | `pattern_rules.py:27-50` 每条格局含 `formation_conditions` + `breaking_conditions` + `verbatim` 结构化条件 |
| **无「放宽标准」痕迹** | ✅ 通过 | 搜索 TODO/FIXME/HACK/临时/硬编码，仅有合理的 stub/fallback 设计标记 |

### 关于「bySolar 闰月参数硬编码 true」的澄清

`ziwei_adapter.py:85` 传 `true` 给第 4 参数，看似可疑（阳历为何需闰月参数）。**实测 iztro 源码后确认这不是 bug**：该参数是 `fixLeap`（非 `isLeapMonth`），语义为「闰月前半月归上月、后半月归下月」，iztro 默认即为 true（`astro.js:138,143`）。传 true 正确。

---

## 六、Z17 架构决策一致性裁决

**Z17**（commit `fa72ff4d`，2026-09-14，docstring 见 `ziwei_method_profile.py:10-12`，标注「用户定稿」）：

> 全系统收敛为两派：SANHE（南派/倪海厦《天纪》）+ QINTIAN（北派/钦天门）
> 已删除：中州派（ZHONGZHOU）、飞星派（FEIXING）及其专属四化表

### 裁决：部分一致

| 核查项 | 结果 |
|---|---|
| `MethodId` 枚举收敛为两派 | ✅ 一致（`ziwei_method_profile.py:36-39` 仅 SANHE/QINTIAN） |
| 生产调度层只出两轨 | ✅ 一致（`multi_method.py:42-43` 只导入 SanheRuleGraph + make_qintian_rule_graph；`compute_multi_method_signals():204-252` 实测只产出 2 轨） |
| 中州专属四化表已删 | ✅ 一致（`SIHUA_TABLE_ZHONGZHOU` 全仓库 0 命中，仅 `:82` 注释残留） |
| **`zhongzhou/` 子包物理删除** | ❌ **不一致**：6 文件 / ~1,178 行完整存在，零生产引用 |
| **`feixing/` 子包物理删除** | ❌ **不一致**：8 文件 / ~1,432 行完整存在，仅 1 个测试引用 |

### 关于 9-19 提交信息「中州三轨」

commit `e9fa5d74` 的信息写「南派/钦天/**中州三轨**」，与 Z17 决策矛盾。**实测裁决：提交信息有误**。`compute_multi_method_signals()` 代码中无任何中州分支，实际产出严格为 2 轨。属提交信息笔误，非代码三轨。

---

## 七、证据溯源（Provenance）审计

### 7.1 覆盖率：约 31%，且两极分化

统计约 1,080 条规则，其中约 336 条有结构化 provenance（`source_section` + `verbatim`）：

**有完整溯源（~336 条）**：
`qintian/evidence.py`(60条，含 verbatim_quote + source_url)、`pattern_rules.py`(70)、`nihai_assertions.py`(89，但仅「主星册·X」无页码)、`sanhe_pattern_judgments.py`(38)、`temporal_rules.py`(29)、`nvming_rules.py`(15)、`sanhe_judgments.py`(14)、`limit_advanced_rules.py`(7)、`palace_general_rules.py`(7)、`child_limit_rules.py`(5)

**零溯源（~744 条，68%）**：
| 文件 | 规则数 | 溯源 |
|---|---|---|
| `palace_star_verdicts.py` | ~376 | **0**（仅文件头笼统声明《全书》） |
| `qintian/combinations.py` | 62 | **0** |
| `shengong_wuxing_data.py` | ~300行数据 | **0** |
| `aux_star_verdicts.py` | ~21 | **0** |
| `answer_layer.py` | ~6 | **0**（source 字段填的是派别名，非原典） |
| `decadal.py` | 7 | **0** |
| `brightness.py` | 1 表 | **0** |

**关键**：零溯源的恰是**体量最大**的文件。规则量增长与治理覆盖率呈反比。

### 7.2 `EvidenceRef` 字段名与文档不符

`ziwei_method_profile.py:71-77` 定义的 `EvidenceRef` 字段为 `rule_id / source_work / source_chapter / verification_status`（Literal["canonical","candidate","unverified"]）。

但 `rules/interpretation.py:39` 另有一个**同名不同构**的 `EvidenceRef`，字段为 `classic / source / text_preview`，且全仓库仅被构造 **2 次**。两个同名 dataclass 并存是维护隐患。

### 7.3 Passage Registry 仍不存在

- `data/classics/ziwei/index.json`、`raw_manifest.json` —— 实测**不存在**
- 全紫微代码 grep `Passage` / `passage_registry` / `EVIDENCE_STATUS` —— **0 命中**
- `src/tongshu/classic_evidence/` 下只有五部**八字**经典的 agent（dts/pzzq/qtbj/smth/yhzp），**无紫微对应 agent**
- 紫微未接入 `governance/evidence_index.py`、`provenance_resolver.py`

**AGENTS.md「书目/Passage Registry 无正式冻结记录」的 BLOCKED 判定，至今仍然成立。**

### 7.4 既有溯源矩阵完全失效

`docs/audit/ZIWEI_RULE_PROVENANCE_MATRIX_REPORT.md`（2026-09-02）仅覆盖 **18 条排盘算法级规则**（iztro 对照表：命宫定位/身宫/五行局/安星法/四化表），属**计算层**而非断言层。

- 9-19 新增的约 1,000+ 条断言/释义规则**无一被纳入**
- 该报告结论「IZTRO_DEFAULT + ZHONGZHOU_SIHUA_ADAPTER」已被 Z17 两派收敛决议推翻

**裁决：完全失效，不可作为当前 provenance 基线。**

---

## 八、风险汇总与处置建议

### P0（阻塞级，需裁决后处置）

| # | 问题 | 建议 |
|---|---|---|
| P0-1 | 宫名「交友」vs「仆役」不一致，钦天门仆役宫规则静默失效 | **可立即修**：统一为「仆役」，并合并 4 份重复宫序定义为单一权威常量 |
| P0-2 | 9-19 V2 落库违反「紫微 Canonical BLOCKED / 禁止补算法星曜四化」 | **需你裁决**：补办解冻手续（建 Passage Registry + 冻结记录）或回退 V2 |
| P0-3 | 三状态分离未实现 + 7 层 Gate 未接入，1000+ 断言未审查 | **需架构决策**：补建机制，或在接入生产前明确阻断 |

### P1（重要缺陷）

| # | 问题 | 建议 |
|---|---|---|
| P1-1 | bySolar 生产主路径无交叉验证；晚子时/闰月/立春边界零覆盖 | 补 `test_ziwei_chart_cross_validate.py` 的 bySolar 分支 + 边界案例 |
| P1-2 | `date_source="lunar"` 死配置且与 bySolar 事实矛盾 | 改为 `"solar"` 或删除该 policy 对象 |
| P1-3 | 未知星名静默丢弃，无告警 | 改为显式抛错或记 warning |
| P1-4 | MethodProfile 流派隔离被 30+ 处硬编码 `GAN_SIHUA` 绕过 | 统一走 `get_sihua_table()`（9-04 旧审计已提，未执行） |
| P1-5 | `extract_baseline_signal()` 仍在引擎层产出解释性 Signal | 移到辨层/推理层（9-04 旧审计已提，未执行） |
| P1-6 | `FrozenZiweiChart` 含可变字段，是类型别名而非真冻结 | 改用 `tuple` / `MappingProxyType`，或加 `__post_init__` 校验 |

### P2（清理项）

见 §4 表格，7 项。其中 P2-7（15 个纯孤儿文件 2,151 行）可安全删除。

### 架构级建议

**89.5% 的代码不在生产路径上**，这是本次审计最根本的发现。它同时解释了多个表面问题：
- 为什么 Gate 缺失尚未造成线上事故（断言层根本没接入）
- 为什么 476 个测试通过却仍有 P0 缺陷（测的多是孤儿）
- 为什么旧审计的整改项（P1-4/P1-5）长期未执行（不在生产路径，无人被迫面对）

建议优先决策：**这批规则资产是要接入生产，还是确认为研究性储备？**
- 若接入生产 → 必须先补 P0-3（三状态 + Gate），否则等于无条件放行 1000+ 未审断言
- 若为储备 → 应在目录结构与文档上明确标注「非生产 / research」，避免后续误判，并考虑迁出 `src/`

---

## 附录 A：15 个纯孤儿文件清单（零生产 + 零测试引用，2,151 行）

```
rules/pattern_rules.py              317
rules/shengong_wuxing_data.py       300
rules/decadal.py                    267
rules/sanhe_pattern_judgments.py    242
rules/temporal_rules.py             230
rules/sanhe_judgments.py            135
rules/nvming_rules.py               107
rules/wuxing_rules.py                98
rules/temporal_facts.py              85
rules/limit_advanced_rules.py        85
rules/palace_general_rules.py        70
rules/child_limit_rules.py           63
rules/palace_relationship.py         61
rules/aux_star_verdicts.py           48
rules/aux_star_ext.py                43
```

> 注：`sanhe_judgments.py` / `sanhe_pattern_judgments.py` 被 `method_graphs.py:178-179` 引用，但 `method_graphs.py` 自身仅通过孤儿链（`multi_method.py` → `interpretation.py`）可达，故整链归为非生产。

## 附录 B：本次审计的工作区改动

审计为只读，未修改任何代码。工作区现存改动来自审计前的独立任务，与本报告结论无关：

```
 M src/tongshu/engines/ziwei/dataset_bridge.py   (+1 行 encoding="utf-8"，修复 GBK 解码缺陷)
 D tests/test_ziwei_feixing_production.py        (Z17 残留测试，已送回收站)
 D tests/test_ziwei_feixing_rule_graph.py        (同上)
 D tests/test_ziwei_zhongzhou_p04_a.py           (同上)
```

## 附录 C：审计方法与取证标准

本报告严格遵循 `AGENTS.md §2` 三重取证纪律：

1. **调用图取证**：对每个模块 grep 全仓库符号引用，零调用方即判孤儿，不假定生产路径
2. **生产入口链取证**：从 `api/app.py` → `pipeline.run()` → `compute_stage` → 引擎逐层追踪，确认运行时绑定实现
3. **测试对象核对**：核对测试断言作用对象与生产路径是否同一实体，识别 false-green

标注约定：
- **「实测」** = 运行代码/iztro 得到的结果（如 §2 P0-1 的 `_palace_index` 返回值、§5 的时辰映射表）
- **「实读」** = 直接读取文件内容确认
- **「推断」** = 基于代码结构的推理，已显式标注

审计过程中对子代理结论做了独立复核，纠正了 2 处误判：
- `ziwei_method_profile.py` / `ziwei_palace_resolution.py` 被误判为「生产可达」→ 实测为孤儿（唯一「引用」是 `ziwei_engine.py:82` 的注释文本）
- 「bySolar 闰月参数硬编码 true 是 bug」→ 实读 iztro 源码确认为 `fixLeap` 参数，传 true 正确
