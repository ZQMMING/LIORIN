# PATCH-003A-R1：DTS Evidence Layer Reclassification（滴天髓证据层重分类）

> 日期：2026-09-16 ｜ Human 拍板：暂停 28×6，先完成 DTS 证据层标死
> 状态：R1 完成 → 才可继续 28×6 VERIFIED_SCOPE

## 一、DTS 分层现状确认（全量 258 条盘点）

| text_layer | 条数 | evidence_grade | 说明 |
|---|---|---|---|
| ORIGINAL | 132 | A | 正文诗/正文断语 |
| ANNOTATION | 124 | B | 注层（含原注/注释） |
| LATER_COMMENTARY | 1 | C | 滴天髓序（后人序文） |
| UNVERIFIED | 1 | D | 何知章待核条目 |

**结论**：每章「正文 ORIGINAL + 注 ANNOTATION」体例转录正确，分层无错标需修正；本 R1 聚焦「标死关键句 + 证据用途政策」。

## 二、五簇关键句逐条标死（EVIDENCE LAYER LOCKED）

| 关键句 | source_id | TEXT_LAYER | TEXT_ROLE | EVIDENCE | 用途 |
|---|---|---|---|---|---|
| 「月令提綱之府，譬之宅也。人元用事之神，宅之定向也」 | DTS-015-003 | ORIGINAL | 正文 | A | CORE_RULE_ELIGIBLE |
| 「生時歸宿之地，譬之墓也。人元用事之神，墓之穴方也」 | DTS-015-005 | ORIGINAL | 正文 | A | CORE_RULE_ELIGIBLE |
| 「能知衰旺之真機，其於三命之奧思過半矣」 | DTS-016-001 | ORIGINAL | 正文 | A | CORE_RULE_ELIGIBLE |
| 「令上尋真聚得真，假神休要亂真神」 | DTS-023-001 | ORIGINAL | 正文 | A | CORE_RULE_ELIGIBLE |
| 「真假參差難辨論…提綱不與真神照」 | DTS-023-003 | ORIGINAL | 正文 | A | CORE_RULE_ELIGIBLE |
| 「令星乃三命之至要，氣象得令者吉，喜神得令者吉」「寅月立春後七日戊土用事，八日後十四日前丙火用事，十五日後甲木用事」 | DTS-015-004 | **ANNOTATION** | **原注** | **B** | SUPPORTING_RULE_ONLY / CANDIDATE_RULE / **NO_ORIGINAL_UPGRADE** |
| 「子時生人，前三刻三分壬水用事，後三刻七分癸水用事…當究其時之先後」 | DTS-015-006 | **ANNOTATION** | **原注** | **B** | SUPPORTING_RULE_ONLY / CANDIDATE_RULE |
| 「旺中有衰者存，不可損也；衰中有旺者存，不可益也。旺之極者不可損…」 | DTS-016-002 | **ANNOTATION** | **原注** | **B** | SUPPORTING_RULE_ONLY / CANDIDATE_RULE / **NO_ORIGINAL_UPGRADE** |
| 「真神得令，假神得局而黨多；假神得令，真神得局而黨多」 | DTS-023-004 | **ANNOTATION** | **原注** | **B** | SUPPORTING_RULE_ONLY / CANDIDATE_RULE |
| 清濁論正文「一清到底有精神…」「滿盤濁氣令人苦…」 | DTS-022-001/003 | ORIGINAL | 正文 | A | CORE_RULE_ELIGIBLE |
| 順逆正文「順逆不齊也…順其氣勢而已矣」 | DTS-025-001 | ORIGINAL | 正文 | A | CORE_RULE_ELIGIBLE |
| 寒溫濕燥正文「天道有寒煖…」「地道有濕燥…」 | DTS-026-001/003 | ORIGINAL | 正文 | A | CORE_RULE_ELIGIBLE |
| 從象正文「從得真者只論從…」/化象「化得真者只論化…」 | DTS-040-001/041-001 | ORIGINAL | 正文 | A | CORE_RULE_ELIGIBLE |
| 從象注「日主孤弱無氣…才官強甚，乃為真從也」 | DTS-040-002 | **ANNOTATION** | **原注** | **B** | SUPPORTING_RULE_ONLY / CANDIDATE_RULE |

**铁律（写入 Evidence Policy）**：
1. 不得再写「《滴天髓》原文曰：旺中有衰者存…」——必须标注 TEXT_LAYER=ANNOTATION/B, TEXT_ROLE=原注
2. B 级可解释正文/补充语义/提供候选算法/提供条件细化/与其他经典交叉验证；**不得升级 ORIGINAL/A**
3. 人元用事时间表（寅月戊→丙→甲、子时壬→癸）为 B 级候选规则，须经六部交叉验证 + Rule Admission 后才可进执行层

## 三、EVIDENCE_USE_POLICY（Human 拍板，Registry/Evidence 层执行）

```
A_ORIGINAL        → CORE_RULE_ELIGIBLE（可直接进 CLASSICAL_RULE_ADMISSION）
B_ANNOTATION      → SUPPORTING_RULE_ONLY
                  → CANDIDATE_RULE
                  → NO_ORIGINAL_UPGRADE（不得冒充原典正文、不得单独创建 A 级核心规则）
D_QUOTED_SOURCE   → SOURCE_TRACE_REQUIRED（未验证不得作当前经典 ORIGINAL）
U_UNVERIFIED      → FAIL_CLOSED
```

**禁止**：
```python
if evidence_grade in ["A", "B"]:
    admit_rule()      # ❌ 错误
```
**正确**：
```python
A + 完整条件 + 原文 + 章节 + 语义一致 → 可申请 Rule Admission
B → 仅 B 级支持/候选规则，不自动升级 A
D → 追溯来源
U → FAIL_CLOSED
```

## 四、SCHEDULE ≠ WEIGHT（硬规则落档）

- 人元用事时段（戊土 7 日 / 丙火 7 日 / 甲木 15 日）= 原典时间节点序列，**不是**五行力量百分比
- 禁止工程转换：`戊土力量 = 7/30`（数学转换，非经典规则）
- RULING_ELEMENT_SCHEDULE 字段：source_id / chapter_id / branch / start_boundary / end_boundary / ruling_element / text_layer / evidence_grade / verification_status——**无 weight 字段**
- 六部原文未提供量化权重语义前，一律 FAIL_CLOSED

## 五、「旺 ≠ 强」证据链重新分级（结论保留，证据链修正）

| 链 | 证据 | 层 | 作用 |
|---|---|---|---|
| A 级正文链 | 「全象喜行財地，而財神要旺」（财神对象）；「旺木得火而愈敷榮」（木对象）；「身旺遇印」（身对象）；「能知衰旺之真機」（体系纲领） | ORIGINAL/A | 证明旺的对象多样（木/身/财/五行），非固定 DAYMASTER_STRENGTH |
| B 级注解链 | 「旺中有衰者存，衰中有旺者存…」 | ANNOTATION/B | 展开旺衰内部结构，辅助证明 WANG≠STRONG |

**结论**：WANG ≠ STRONG 工程禁映射**保留**；但不得声称由 DTS-016-002 ORIGINAL 得出（其为 B 级）。

## 六、五簇 Object/Relation 初判 → semantic_status=PRELIMINARY

- 「官得令」→ object=OFFICIAL, relation=GET_ORDER
- 「強殺無根」→ object=OFFICIAL(殺), relation=ROOTED_IN（**Golden Case：验证 OBJECT 隔离**）
- 「黨盛為強」→ object=BRANCH_GROUP, relation=GROUP_FORCE（**Golden Case：验证 RELATION_TYPE 隔离**，该「強」≠DAYMASTER_STRONG）

全部标 `semantic_status = PRELIMINARY`（未达 VERIFIED）。

## 七、R1 完成清单

- [x] DTS 全量 258 条分层盘点（132A/124B/1C/1D，无错标）
- [x] 五簇关键句逐条标死（正文 A 6 组 / 原注 B 5 组）
- [x] EVIDENCE_USE_POLICY 落档（A/B/D/U 用途 + 禁 admit_rule）
- [x] SCHEDULE ≠ WEIGHT 硬规则
- [x] 旺≠强证据链重新分级
- [x] 初判标 PRELIMINARY + 2 个 Golden Case
- [ ] attribution 细分（原注 vs 任铁樵注）——待下一轮（对照阐微版）
- [ ] 六部交叉验证人元用事时间表（寅月/子时用事在 YHZP/SFTK/QTBJ 的佐证）——PATCH-003B 前置

## 八、裁决状态（Human 冻结）

```
PATCH-003A-R1  DTS Evidence Layer Reclassification：PASS（本报告）
28×6 VERIFIED_SCOPE：HOLD（R1 后继续）
PATCH-003B：HOLD
```
