# PATCH-004B Boolean / Enum / State Model Registry（状态模型治理）

- 日期：2026-09-16
- 状态：FROZEN_DRAFT（禁止写任何判断规则，只冻结数据结构与状态类型）
- 依据：Human 裁决「004A-R1 通过，启动 PATCH-004B」
- 契约文件：`governance/patch_004b_state_model_registry.json`

## 目标

防止 Agent 把经典概念压缩成 Boolean，或把证据字段误当裁决字段。

## 1. Boolean 白名单（6 个，仅事实层）

| 字段 | 含义 |
|---|---|
| has_root | 是否存在根气证据 |
| has_hidden_stem | 是否有藏干 |
| has_combination | 是否存在合会刑冲结构 |
| has_transformation_condition | 是否满足某转换条件入口 |
| has_clash | 是否存在冲合刑害关系 |
| has_support_relation | 是否存在生扶关系 |

**禁止输出**：吉/凶、强/弱、喜/忌。

## 2. Boolean 禁止化字段（3 项）

- `{"strong": true}` 禁止——强是关系结果，非事实 → strength_state ENUM
- `{"got_order": true}` 禁止——易被自动转 strong → order_state ENUM
- `{"useful": true}` 禁止——用神必须经经典范围+格局+病药+条件

## 3. 必须 Enum 的状态（7 个）

| 状态 | 值域 | 注 |
|---|---|---|
| strength_state | 见下 | 不得由旺/得令/得根直接产生 |
| wang_state | WANG/PING/SHUAI/UNKNOWN | 时令状态，非力量评分 |
| qiang_state | QIANG/ZHONG/RUO/UNKNOWN | 关系结构 |
| order_state | GET_ORDER/LOSE_ORDER/IRRELEVANT_ORDER/UNKNOWN | 得令/失令/不论令/未知 |
| root_state | HAS_ROOT/NO_ROOT/UNKNOWN | **必须对象化**（日主/官/财/杀/印） |
| support_state | NONE/WEAK/NORMAL/STRONG/EXCESSIVE/UNDETERMINED | 004A 已登记 |
| trend_state | TREND_TO/BURST/GROUP/HOLD/UNDETERMINED | 004A 已登记 |

**strength_state 值域注意**：Human 004B 建议 UNKNOWN/VERY_STRONG/STRONG/BALANCED/WEAK/VERY_WEAK/UNDETERMINED；与 PATCH-001 冻结六级（STRONG/SLIGHTLY_STRONG/NEUTRAL/SLIGHTLY_WEAK/WEAK/UNDETERMINED）存在命名差异，**统一待 Human 拍板（PENDING_UNIFY）**，两套均为工程容器，不影响旺≠强铁律。

## 4. 只能 Evidence 的字段（4 类）

- classical_quote：EVIDENCE_ONLY，原文命中不得进入状态判断
- case_reference：REFERENCE_ONLY，命例不得形成规则
- shen_sha_reference：DISPLAY_ONLY，神煞仅展示
- ruling_schedule：TIME_RECORD_ONLY，禁 15天=50%

## 5. 禁止状态 BLOCKLIST（8 项）

strength_score / wang_score / five_element_score / percentage_strength / favorable_factor_count / **wangqiang_state**（旺≠强禁合并）/ overall_power / luck_level

## 6. 输出 Schema

```
{
  state_id: "",
  state_type: "BOOLEAN | ENUM | EVIDENCE",
  object_type: "",
  source_scope: "",
  value: "",
  execution_mode: "DIRECT_OUTPUT|CONTEXT_ONLY|RULE_REQUIRED|REFERENCE_ONLY",
  can_transition: false,
  forbidden_transition: []
}
```

未登记枚举/字段 FAIL_CLOSED。

## 验收（7 项全过）

Boolean 白名单 / Boolean 禁止业务化 / Enum 经典语义对应 / Evidence 不进入状态 / 禁评分模型 / 禁旺强合并 / Object 维度完整。

## 下一步

PATCH-004C Rule Input Contract → 005 Rule Layer（旺衰/强弱/用神/格局）。

## PATCH-004B-R1：strength_state Enum 裁决（commit 待）

### Human 裁决
采用 PATCH-001 六级值域，废弃 004B 临时七值。原因：①六级是「强弱状态」非「力量幅度」，七值（VERY_STRONG>STRONG>...）易引入现代评分体系隐患；②六级更符合治理模型。

### 冻结值域
STRONG / SLIGHTLY_STRONG / NEUTRAL / SLIGHTLY_WEAK / WEAK / UNDETERMINED

| 值 | 含义 |
|---|---|
| STRONG | 规则层确认后的强状态 |
| SLIGHTLY_STRONG | 偏强状态 |
| NEUTRAL | 中和/难偏状态 |
| SLIGHTLY_WEAK | 偏弱状态 |
| WEAK | 规则层确认后的弱状态 |
| UNDETERMINED | 证据不足或冲突 |

STRONG ≠ 旺 ≠ 得令 ≠ 有根：是未来 Rule Layer 综合判断结果。

### 新增治理字段
- definition_type = "RELATIONAL_RESULT"（禁 POWER_LEVEL——强弱是关系结果，非绝对力量）
- semantic_role = "RELATIONAL_STATE"

### 落库
- governance/patch_004b_state_model_registry.json：strength_state 六级 + definition_type + semantic_role（七值已删）
- governance/enum_registry.json **v1.8.1**：dts_strength_state 补 state_definition（6 值逐义）+ validation_schema（禁 POWER_LEVEL / 禁旺得令得根来源 / 禁 WANG→STRONG、order→STRONG、root→STRONG、factor_count→STRONG）

### 下一步
PATCH-004C Rule Input Contract：只定义 1.Rule 输入允许读取哪些 State 2.禁止读取哪些 Evidence 3.Rule 输出结构 4.Rule 与 Classical Scope 绑定格式；仍不写旺衰/强弱算法。
