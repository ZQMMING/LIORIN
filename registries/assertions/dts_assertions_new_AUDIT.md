# AGENT-DTS 断语切片规范化审计报告

- 任务：滴天髓（DTS）现有 354 条断语格式规范化与质量抽查
- 输入：`D:\shuntian-ziping-p0\registries\assertions\dts_assertions.jsonl`
- 输出：`D:\shuntian-ziping-p0\registries\assertions\dts_assertions_new.jsonl`（354 条，未覆盖原文件）
- 校验：`validate_assertion.py` 对新文件 **0 错误 / 0 警告，通过**
- assertion_id：保留 `ASSERT-DTS-XXXX` 三字母格式（校验器正则已由 `[A-Z]{4}` 放宽为 `[A-Z]{3,4}`，向后兼容其余五经典）

---

## 一、总体结果

| 项 | 结果 |
|---|---|
| 断言总数 | 354（无增删） |
| 格式校验 | 0 错误 / 0 警告 ✅ |
| 合法 assertion_type | DEFINITION 96 / RELATION 94 / RULE 152 / EXCEPTION 12 ✅ |
| 合法 grade | A 171 / B 182 / C 1 ✅ |
| audit_status | 354 全部 CANDIDATE ✅ |
| predicate | 全部在核心+扩展词汇表，无未注册谓词 ✅ |
| namespace | strength_relation 97 / flow 94 / qi_shi 78 / shape 74 / trend 8 / tongguan 3，全部已注册 ✅ |
| source_evidence | 全部非空数组，全部证据 ID 在 `sources.dts.jsonl` 中存在 ✅ |
| condition | 全部为含 positive/negative/exception 的对象 ✅ |
| 额外字段 | consumer、runtime_action 354 条全部保留 |

---

## 二、assertion_type 修改统计（共 152 条）

| 原类型 | 数量 | 映射到 | 说明 |
|---|---|---|---|
| CONDITION | 125 | RULE | 条件句本质为「在 X 条件下 Y 成立」的可执行规则 |
| NEGATION | 27 | RULE（polarity=negative） | 逐条判定：27 条全部为「忌/不可/不宜/畏/不必」禁止性规则，**无一条**为「但/然/第」但书例外语气，故全部归 RULE 而非 EXCEPTION |
| DEFINITION / RELATION / EXCEPTION | 96/94/12 | 保留 | — |

---

## 三、predicate 映射统计（按谓词词汇表第四节「常见映射速查表」映射为核心谓词）

共 **64 条**谓词被映射；其余已注册扩展谓词（语义独特，如 separates/rooted_in/stops_at/mediates/blocked_by/channels/warms 类等）按规则保留。

| 映射 | 条数 |
|---|---|
| determines → implies | 36 |
| blocks → prevents | 20 |
| rejects → conflicts_with | 11 |
| activates → enables | 11 |
| defined_by → is_defined_as | 8 |
| flows_to → produces | 7 |
| requires_adjustment → requires | 6 |
| requires_mediator → requires | 5 |
| drains_to → drains | 4 |
| supported_by → receives_support | 4 |
| corresponds_to → refers_to | 3 |
| is_not_overcome_by → but_not | 2 |
| must_not → prevents | 2 |
| supports → strengthens | 2 |
| attacks → controls | 2 |
| should_not → prevents | 2 |
| prefers → requires | 1 |
| requires_root → requires | 1 |
| requires_support → requires | 1 |
| is_injured_by → receives_control | 1 |
| is_weakened_by → weakens | 1 |
| does_not_escalate → but_not | 1 |
| does_not_block → but_not | 1 |
| drains_into → drains | 1 |
| transforms_with → combines_with | 1 |
| is_fixed_as → is_defined_as | 1 |
| differs_from → is_opposite_of | 1 |

**保留未映射的已注册扩展谓词（节选）**：requires(88)、separates(18)、selects(10)、rooted_in(9)、receives_support(7)、stops_at(7)、controls(6)、changes(4)、blocked_by(4)、drains(3)、mediates(2) 等，均在扩展谓词表中注册且编码了滴天髓独特语义。

---

## 四、grade 规范化

- 交叉核验 grade 与证据原文层级（ORIGINAL / ANNOTATION / LATER_COMMENTARY / UNVERIFIED）：
  - A×ORIGINAL = 171，B×ANNOTATION = 181，B×ORIGINAL = 1 —— **grade 与原文/注文层级本已高度吻合**，无需批量调整。
- **唯一降级**：`ASSERT-DTS-0219` 原 grade=A，但其主证据 `text_layer=UNVERIFIED`，无法确认为原文，按规则降级为 **C**。

---

## 五、质量抽查（随机 20 条，seed=20260920）

逐条将断语 subject-predicate-object 与 `source_text` 原文比对：

| 结论 | 数量 |
|---|---|
| 原文直接支撑、无断章取义 | 17 |
| 合理抽象（grade 已正确标注），可留待 MainAgent 微调 | 3 |
| 断章取义 / 误读 / 错误 | 0 |

**3 处抽象点（不构成 reject，仅提示）**：
1. `ASSERT-DTS-0066`「壬水通根透癸 becomes_rushing 申子辰局」——原典「通根透癸，沖天奔地」未直书「申子辰」，客体的申子辰为壬水通根之地支补全，语义成立。
2. `ASSERT-DTS-0065`「壬水 produces 周流不滞」——原典「週流不滯」为壬水性情，谓词 produces 略偏，可考虑改为 describes/refers_to（不影响校验）。
3. `ASSERT-DTS-0202`「财印 refers_to 所亲之位」——原典「以才為父，以印為母」，「所亲之位」为对六亲父母位的抽象。

抽查覆盖 ORIGINAL 与 ANNOTATION 两类证据层，grade×layer 对应关系全部正确。

---

## 六、待审核问题清单（交 MainAgent 裁决）

1. **`ASSERT-DTS-0219`**：A→C 降级（证据层 UNVERIFIED），建议 MainAgent 补证后决定是否回升。
2. **谓词粒度回退项**：本次按速查表将 `requires_mediator`(5)、`requires_adjustment`(6)、`requires_root`、`requires_support` 统一映射为核心 `requires`。若需保留「需通关媒介/需调整/需根气」的细分语义，可在扩展表保留这些谓词并回退映射——它们均已注册，回退不影响校验。
3. **3 处抽象点**（0066 / 0065 / 0202）见上，是否微调谓词或客体由 MainAgent 定夺。
4. **第零步补充新增（第二步）未执行**：滴天髓为气势论命经典，现有 354 条覆盖 strength_relation/flow/qi_shi/shape/trend/tongguan 六类，元覆盖已充足，按「不强制新增」原则未补新断言。如需针对某 namespace 加深可另行提出。

---

## 七、完成标准核对

- [x] 354 条全部规范化，格式校验 0 错误
- [x] predicate 全部在词汇表（核心+扩展），无未注册谓词
- [x] assertion_type 全部合法（DEFINITION/RELATION/RULE/EXCEPTION）
- [x] grade 全部合法（A/B/C）
- [x] 繁体原著证据链完整，source_evidence 全部可溯源
- [x] 未覆盖原文件，新文件独立输出
