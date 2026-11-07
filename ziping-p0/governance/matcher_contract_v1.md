# PATCH-132B Assertion Loader / Matcher Contract v1

## 0. 定位
Loader 只做事实匹配，不做命理生产。
```
Assertion + L0 Facts + Subject Resolver Registry
        ↓
   MATCHED / NOT_MATCHED / ABSTAIN
        ↓
   ActivatedAssertion
```
不产 climate_state / strength_state / use_god / 吉凶。

## 1. 输入 Schema
- `assertion`: 单条 SPO Assertion（含 subject/predicate/object/condition）
- `l0_facts`: `{day_stem, month_branch, ...}`，仅 L0 事实，不含 Producer 输出
- `subject_type_registry`: assertion_subject_type_registry_v1.json

## 2. Resolver 调用规则
1. 按 subject_type_registry 路由，只走 READY 的 Resolver
2. NOT_READY / UNKNOWN → 直接 ABSTAIN（reason: resolver_not_ready）
3. Resolver 输出 facts[]（operator: eq/any_of），不输出 state
4. A014 越权扫描：Resolver 输出禁含 state/use_god/strength/fortune/winner/score

## 3. 三态判定规则
| 状态 | 条件 |
|---|---|
| MATCHED | Resolver 输出 facts 全部与 L0 事实一致（eq 相等 / any_of 包含） |
| NOT_MATCHED | facts 中某条件明确与 L0 矛盾（如 eq 不等、any_of 不含） |
| ABSTAIN | L0 缺该事实 / Resolver 未就绪 / subject 无路由 |

**关键**：L0 事实缺失 ≠ NOT_MATCHED，必须 ABSTAIN。

## 4. ActivatedAssertion Schema（仅允许）
```json
{
  "assertion_id": "",
  "source_evidence": [],
  "predicate": "",
  "object": "",
  "matched_facts": []
}
```
**禁止字段**：climate_state / strength_state / use_god / destiny / fortune_level / 任何 state。

## 5. 越权字段黑名单（A014）
state / use_god / strength / fortune / winner / score / climate_use / destiny / 富贵 / 吉凶

## 6. GC-001 验收终点
输入 L0: `{day_stem:乙, month_branch:戌}`
期望输出:
```json
{
  "status": "MATCHED",
  "activated_assertion": {
    "assertion_id": "QTBJ-...",
    "predicate": "requires",
    "object": "癸水润"
  }
}
```
到此停止。**不**输出 climate_use_state=癸（那是 PATCH-133 climate_producer 的事）。

## 7. 本阶段不做
- 不接 climate_producer
- 不跑六库全量
- 不做冲突裁决
- 不做 condition.positive 的古文匹配（本版仅 subject 路由匹配）
