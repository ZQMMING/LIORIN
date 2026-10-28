# P0-b结案报告：化气格合并到专旺五格

## 一、核心结论

### 1.1 架构确立：一格两面

**原文依据：**「天干化合者秀气，地支合局者福德」（《渊海子平·论运化气》第7156行，grade=A）

**架构：**
```
一行成象族 = {曲直, 炎上, 稼穑, 从革, 润下}
├─ 侧面A·福德（支局侧）：
│  ├─ A1: 日主属该行（硬闸）
│  ├─ A2: 或方或局全（硬闸）
│  └─ A3: 不杂官杀（硬闸）
├─ 侧面B·秀气（干合侧）：
│  ├─ B1: 独合/争合（B1a独合/B1b争合降档）
│  ├─ B2: 化神当令（硬闸）
│  ├─ B3: 逢龙引化（增益档，与稼穑去重）
│  └─ B4: 无破（复用现有闸门）
└─ 合并裁决：
   ├─ A+B俱足 → 化气型（争合降MID）
   ├─ A独足 → 专旺型
   ├─ B独足 → CANDIDATE
   └─ 皆空 → REJECT
```

### 1.2 本批用例构成（L1 v1）

#### 按旧引擎输出分档（用于KNOWN_DIFF对齐）
| 档位 | 用例 | 数量 |
|---|---|---|
| CONFIRMED | R1, A1, A5, A7, A9 | 5 |
| CANDIDATE/LOW/[] | li-066, li-071, F1, A2, A4, A6, A8, A10 | 9 |

#### 按新规格期望值分档（L1 v1正式构成）
| 档位 | 用例 | 数量 |
|---|---|---|
| CONFIRMED | R1, A1, A5, A7, A9, li-071 | 6 |
| MID | A3, li-066, F1 | 3 |
| REJECT | A2, A4, A6, A8, A10 | 5 |

**关键战果：** 新规格将li-071从旧引擎REJECT（从旺格/CANDIDATE）挽回为CONFIRMED（一行成象·从革·专旺型）。

### 1.3 三条KNOWN_DIFF（行为变更登记）

| ID | 旧引擎 | 新规格 | 原因 | 处置 |
|---|---|---|---|---|
| li-066 | 从革格/CONFIRMED | 一行成象·从革·化气型/MID | D-争合降档（新增维度，刘注「单透一位」） | 白名单放行，不改期望值 |
| li-071 | 从旺格/CANDIDATE | 一行成象·从革·专旺型/CONFIRMED | D-财星硬闸（行为变更：财星从硬闸降为减项） | 白名单放行；引擎侧待迁族 |
| F1 | []/REJECT | 一行成象·炎上·专旺型/MID | D-财星减项翻转（行为变更：财星仅炎上/稼穑忌） | 白名单放行；证实财星非硬闸 |

### 1.4 两个底层bug修复

1. **合化扣除键名bug**：tian_he返回'stems'，代码写的'gans' → 合化扣除静默失效
2. **score作用域bug**：_gate_debug前score=0初始化覆盖了if块计算的实际score

---

## 二、文件清单

| 文件 | 说明 |
|---|---|
| tests/cases_l1_v1.json | L1用例表（14条：10构造+R1+li-066/li-071+F1） |
| tests/assert_structural.py | structural断言脚本（7项） |
| tests/test_l1_against_engine.py | 引擎对比断言（含EXPECTED_MISMATCH白名单） |
| docs/migrations/pattern_rename_v1.json | 旧名→新名双向映射表 |
| docs/migrations/state_to_confidence_v1.json | state→confidence五档映射 |
| docs/gate_debug_contract.md | gate_debug契约（分数字典≠破格） |
| docs/l2_divergences.md | 分歧记录（5条） |
| docs/s_source_notes.md | S1-S4原文摘录 |

---

## 三、provenance分级规范

| 级别 | 定义 | 示例 |
|---|---|---|
| **A** | 印本对校，纯原著直证 | 卷二外十八格（曲直/炎上/稼穑/从革/润下）、卷三论运化气、PZZQ沈原文 |
| **B** | 校勘复原，现代本交叉验证 | （已全部升A，无B级条目） |
| **C** | 来源不明 / 旧引擎输出 | baseline（provenance=C，单特征分类器） |

**分级原则：** 分级按要件拆分，不按整条用例或整条断言。

---

## 四、后续待办

1. **P0-a-1枚举JSON定死**：枚举域+双向可逆校验脚本
2. **接入新层**：axis_xiuqi/axis_fude/special_merge，跑新旧输出对比
3. **D-透干硬闸实证**：补「支局全+无官杀+本行不透」fixture
4. **从格优先**：一行成象族 ∧ 从格族同时满足时，从格优先
5. **B1完整实现**：B轴完整集成到special_pattern.py

---

**报告生成时间：** 2026-09-22
**报告版本：** v1.1（L1 v1封版）
