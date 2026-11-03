# 断言规则进库校验规范（Rule Entry Validation Spec）

> 版本：v1.0 ｜ 状态：**强制（HARD GATE）** ｜ 适用范围：顺天 EXIS 所有断言规则进库
> 关联：`docs/rule.schema.json`（v1.4）、`data/rules/`、`data/evidence/`、`data/knowledge/`
> 原则：**宁缺毋滥、宁断结构不断事件、宁给条件不给结论、证据不足拒断**
> 严禁：不得以"提升准确率"为名使用 bug 撑数、不得未经校验将断言规则标为 verified

---

## 0. 为什么需要这个规范

顺天的排盘层（八字/紫微/河洛）是确定性、可冻结的；真正决定"说得对不对"的是**断言（断事）层**。
一条断言规则一旦进入 `data/rules/` 正式库，就会被引擎引用并参与打分、影响用户结论。
因此**进库本身必须是一道有门槛的闸门**，不是"写了就进"。

本规范定义断言规则从"候选（draft）"到"正式（active）"必须通过的**全部强制校验**。

---

## 1. 状态机（Rule Status Lifecycle）

```
draft（候选草案）
  │  ── 通过 ①来源 ②一致性 ③冲突裁定 ──▶ review（待审）
review
  │  ── 通过 ④字段可计算 ⑤实证验证（Golden/盲测/消融）──▶ validated（已验证）
validated
  │  ── 评审确认无副作用 ──▶ active（正式启用）
  └──────────── 任一环节不通过 ────▶ 回 draft 或 deprecated
```

- **任何规则进 `active` 前必须经过 `review` 与 `validated` 两个中间态**，禁止 draft 直跳 active。
- 未经验证（evidence 不足）的规则**只允许停留在 draft / review**，不得输出给用户作为结论，只能作为 INSUFFICIENT_EVIDENCE 的候选。

---

## 2. 进库强制校验清单（六道闸门，缺一不可）

### ① 来源可追溯
- `source.work` 必须在 rule.schema 允许的古籍枚举内（子平真诠/滴天髓/穷通宝鉴/三命通会/渊海子平等）。
- 必须关联知识库：`book_id` / `passage_id` / `concept_id` / `principle_id` 在 `data/knowledge/` 中真实存在，且 `verify_link_closure() == 0`。
- `evidence_refs` 必须指向 `data/evidence/` 中真实存在的证据文件。
- **来源不实 / 无法定位到原文的规则，一律不进。**

### ② 与古籍原文一致性
- 规则语义必须与古籍原文一致。若规则提炼自**现代讲师解读**（如空空道人视频），必须与对应古籍原文（滴天髓/渊海子平/穷通宝鉴等）**交叉核对**；不一致时以古籍为准，并标注分歧到证据文件。
- 禁止把讲师二手演绎当成古籍原意直接进库。

### ③ 与现有规则冲突裁定
- 新规则与 `data/rules/` 现有规则（MK-101 墓库、HLT 健康、YHZP 渊海子平等）冲突时，必须裁定优先级（用 `precedence` / `specificity_hint` 表达），**禁止并存互相矛盾的结论**。
- 冲突未裁定前，规则不得进入 `review`。
- 已知待裁定项（示例）：调候用神 vs 旺衰喜忌的优先级；身弱不担财的"财重/身弱"量化阈值；合化 vs 合绊判定边界。

### ④ 引擎字段可计算性验证
- `conditions` 中每个 `field` 必须是引擎真实支持、已实现的字段（如 `branch_clash_map`、`month_hidden_main_ten_god`、`day_branch_main_ten_god` 等）。
- 字段不存在 / 引擎未实现，**不得假装可用**；需先由引擎侧补齐字段，或将该规则标记为"待引擎支持"并停留 draft。
- `op` 必须在 rule.schema 允许的运算符枚举内（eq/in/contains/has_any 等）。

### ⑤ 实证验证（最严）
- 可计算的规则，用 Golden Dataset / 盲测 / 消融实验验证**是否有增量信息**（incremental predictive value）。
- 无增量、方向存疑、或与实证相反者，回 draft 标 `INSUFFICIENT_EVIDENCE`，**不得进 active**。
- 禁止"改权重→跑Golden→某类涨→另一类掉→再补规则"的循环掩盖问题；必须定位到具体层（旺衰/喜忌/应期/融合）再修。

### ⑥ 保守进库与字段完整
- 规则必须满足 rule.schema 所有 required 字段（rule_id/title/rule_type/source/conditions/conclusion/applies_to_layers/produces_signal_type/forbidden_inferences/evidence_refs/status/spec_decisions_ref/version）。
- `status` 初始一律 `draft`；通过①②③→`review`；通过④⑤→`validated`；评审后→`active`。
- `spec_decisions_ref` 必须关联对应 DECISION 决策记录，保证决策可追溯。
- 输出字段 `direction`/`polarity`/`strength_modifier` 必须在 schema 枚举内；方向不确定时用 `STABLE`+`neutral`，**禁止强行给方向**。

---

## 3. 输出约束（Output Policy，与底层解耦）

- 底层算法允许完整实现传统语义（判断层不设表达禁区）。
- **用户界面输出**由 Lexicon/Mapping/Output Policy 层负责转译；未经映射的传统断语**不得直接进入用户界面**。
- 不得因输出层限制而删除/弱化底层传统知识或 Signal；反之亦然（四层解耦：计算层→判断层→融合层→表达层）。

---

## 4. 禁止事项（Hard Prohibitions）

1. **不得用 bug 撑准确率**：任何为"涨准确率"而利用缺陷的行为一律禁止。
2. **不得把"测试通过"当"理论正确"**：单一体系测试通过≠跨体系正确；需交叉验证。
3. **不得擅自改排盘口径 / Deterministic Contract**：排盘层冻结，规则只能消费其字段。
4. **不得用一个体系反向修改另一体系原始结果**：子平/盲派/紫微/河洛独立计算，最后才交叉裁定。
5. **不得把未验证规则当作已实现能力对外声称**：准确率指标须区分"单一体系基线"与"多体系收敛"。
6. **不得隐藏矛盾证据**：冲突/否定证据必须保留在证据文件与 review queue 中。

---

## 5. 评审与复核

- 每条进 `active` 的规则需有 `reviewer` 与 `created_at`/`updated_at`。
- 重大规则变更（改变结论方向/强度）需记录到 `data/evidence_meta/evidence_review_queue.json`（含 batch/verdict_basis/reviewer）。
- 支持审计：任意规则可回溯到 证据 → 古籍 passage → 概念/原则 → 决策记录。

---

## 6. 对接与执行

- 本规范为 Hermes 落地断言规则时的**硬性约束**，进库动作必须走本闸门。
- 候选规则来源：`D:\TODAY\docs\五部经典整理\空空道人候选规则清单.md`（32 条候选，标注了可计算性与待裁定项）。
- 待裁定项清单（进库前必须解决）见候选清单"第七节 待验证/待裁定项"。

---

## 附：与 rule.schema.json 的对应

| 校验点 | 对应字段 |
|---|---|
| 来源可追溯 | `source` / `book_id` / `passage_id` / `concept_id` / `principle_id` / `evidence_refs` |
| 冲突裁定 | `precedence` / `specificity_hint` / `scenario` |
| 可计算性 | `conditions[].field` / `conditions[].op` |
| 输出约束 | `conclusion.produces_layer_output_template`（direction/polarity/strength_modifier） |
| 生命周期 | `status`（draft→review→validated→active） |
| 可追溯决策 | `spec_decisions_ref` / `forbidden_inferences` |
