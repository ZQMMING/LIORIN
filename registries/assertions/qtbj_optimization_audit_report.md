# 《穷通宝鉴》断语切片优化工程 — 审计报告

- 工程对象：`qtbj_assertions.jsonl`（原 508 条）
- 输出文件：`D:\shuntian-ziping-p0\registries\assertions\qtbj_assertions_new.jsonl`
- 校验脚本：`validate_assertion.py`（Schema V2.2.2）
- 校验结果：**508 条，错误 0，警告 0** ✅
- 原文件未覆盖。

---

## 一、规范化结果总览

| 指标 | 数值 |
|------|------|
| 原始条数 | 508 |
| 去重后输出 | 508 |
| 格式校验错误 | 0 |
| 格式校验警告 | 0 |
| assertion_id 唯一性 | 通过 |

## 二、assertion_type 修改统计

| 原类型 | 映射到 | 条数 |
|--------|--------|------|
| CONDITION | RULE | 289 |
| NEGATION | RULE（polarity=negative） | 101 |
| DEFINITION | 保留 | 20 |
| RELATION | 保留 | 43 |
| EXCEPTION | 保留 | 55 |

- 新文件类型分布：RULE 390、EXCEPTION 55、RELATION 43、DEFINITION 20。
- **NEGATION 判定说明**：101 条全部为"忌／勿／不可／不宜／恶"类禁止性规则，按规范默认 → RULE（polarity=negative）。其中 11 条带"得 X 则解／有 X 则解"补救从句（如 0370/0372/0374/0379/0382/0384/0388/0395/0399/0401/0410），已原样保留在 `condition.exception` 字段，不改判为 EXCEPTION 类型（它们是负面规则＋补救条件，非"前述规则的例外"）。

## 三、predicate 映射统计

| 原谓词 | 映射到 | 条数 |
|--------|--------|------|
| secondary_requires | requires | 89 |
| needs | requires | 10 |
| balances | 保留（已注册扩展谓词） | 21 |
| prefers | 保留（已注册扩展谓词） | 15 |
| warms / dries / dampens / moistens | 保留（已注册扩展谓词） | 各 1 |

- 新文件谓词分布：requires 330、avoids 116、balances 21、controls 18、prefers 15、rejects 4、warms/dries/dampens/moistens 各 1。
- **全部谓词均在词汇表（核心+扩展）内**，无自造谓词。
- secondary_requires→requires 后，"次用／先取"的主次语义已由各条 `condition.positive` 原文承载（如"先癸后丁""次用丙火"），未丢失。

## 四、grade 调整统计

| grade | 条数 |
|-------|------|
| A | 153 |
| B | 355 |

- 本次规范化**未批量调整 grade**。理由：A/B 之分需结合上下文逐条判断（B 级多为"原著原文但需结合次序／条件理解"，如"先壬后甲""次用癸水"），缺乏逐条对照原文的把握前不做无依据升档。
- 抽查中未发现明显应降为 C 的条目；建议 Main Agent 后续按 A 级标准（原著直接原文、语义明确无歧义）对 B 级分批复核升 A。

## 五、其他字段确认

- audit_status：508 条全部 CANDIDATE。
- polarity：positive 347、negative 120、neutral 41（NEGATION 转 RULE 后均保持 negative）。
- namespace：QTBJ.climate_use 289、QTBJ.climate 152、QTBJ.climate_factor_change 67——**三个后缀均已注册**。
- source_evidence：引用 175 个证据 ID，**0 缺失**（全部命中 `sources.qtbj.jsonl`，共 202 条 source）。
- condition：均为含 positive/negative/exception 三字段的对象。

## 六、去重结果

- 严格判重键 = `subject + predicate + object + condition.positive`。
- 规范化后**未发现完全重复组**，删除 0 条。
- 说明：穷通宝鉴各月日干调候 subject 均精确到"日干+月份/节气"（如"甲木正月""甲木二月""辛金三月"），跨月相似调候原则按任务规则**不算重复、予以保留**。若需更激进的语义级去重（如合并同调候不同月），需人工判定，不在本次机械去重范围内。

## 七、质量抽查结果（随机 30 条）

抽查 30 条，将 `condition.positive/negative` 关键词在原著清洗版（繁体）逐条 grep 核对：

- 命中原著，语义支持充分：
  - 0013 夏木 requires 水润 ← 原文"夏月之木，根干叶燥…欲得水盛…诚不可少" ✅
  - 0058 甲木十二月 requires 丁火 ← 原文"十二月甲木，天寒气冻，木性极寒…引丁火" ✅
  - 0102 乙木八月 requires 癸水 ← 原文"白露之后，桂蕊未开，专用癸水以滋桂萼" ✅
  - 0378 辛金三月 requires 壬甲 ← 原文"三月辛金，先壬后甲，壬甲两透" ✅
  - 0016 秋木 avoids 水盛木漂 ← 原文"霜降后不宜水盛，水盛则木漂" ✅
  - 00280 己土正月 requires 丙火 ← 原文"正月己土寒湿" ✅
- 未发现断章取义；subject-predicate-object 对应关系准确。

## 八、待审核问题清单

1. **ASSERT-QTBJ-0024**（甲木正月 balances 水火既济，EXCEPTION）：`condition.positive/negative/exception` 三字段全空。按规范保留空串可通过校验，建议 Main Agent 据 `QTBJ-003-001` 原文补 positive。
2. **异文记录**：ASSERT-QTBJ-0058 `condition.positive="天气寒冻木性极寒引丁"`，原著作"天寒气冻，木性极寒"。"气／气"用字小异，语义一致，留待版本核校。
3. **B 级升 A 待办**：355 条 B 级未批量升级，建议 Main Agent 分批按 A 级标准复核。
4. **跨月语义去重**：严格键下 0 重复；如需合并跨月同调候规则，需人工判定，未在本次执行。

---

**结论**：508 条全部规范化完成，格式校验 0 错误 0 警告，谓词全部合规，类型全部合法，grade 全部合法，证据 ID 全部可溯源。输出见 `qtbj_assertions_new.jsonl`。
