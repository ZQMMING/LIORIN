# PATCH-003B：六经典逐章节 Evidence Verification（启动文档）

> 日期：2026-09-16 ｜ Human 批准：APPROVED ｜ 第一准则：V2.22 FINAL + 附录 A–M
> 前置：R1-05 VERIFIED_SCOPE 收官 PASS（commit `da0397da`）

---

## 一、R1-05 冻结边界（Human 2026-09-16 裁决，禁止违反）

```
VERIFIED_SCOPE → 自动生成 RULE        ✗ 禁止
原文 → Scope → Rule Admission → Business Judgment    ✓ 唯一通道
```

### ① 基础五行 / 十神 / 生旺休囚 / 根气 / 党众 —— PASS
- **根气**：`ROOT ≠ DAY_MASTER_ONLY`，对象必须解析：
  `ROOT(object=日主) / ROOT(object=官) / ROOT(object=财) / ROOT(object=杀) / ROOT(object=印)`
- 禁止 `has_root(day_master)` 作为通用强弱开关。

### ② 生扶克泄耗 / 气势 / 调候 / 通关
- **通关**：`DTS_SCOPE_ONLY`。`DTS-019-001` 通关=ORIGINAL/A；其他经典 NOT_FOUND。
  - 禁止：YHZP引化=通关、QTBJ寒暖=通关、SFTK病药=通关。
  - `CONCEPT_SIMILAR ≠ CONCEPT_EQUAL`。
- **调候**：`QTBJ_PRIMARY_SCOPE` + `PZZQ_CONTEXTUAL_SCOPE`（PZZQ-007-003）+ 其他 SOURCE_CHECK_REQUIRED。
  - 禁止生成「统一调候喜忌算法」；必须带 `CLASSICAL_SCOPE=QTBJ`。

### ③ 格局成败 / 相神 / 顺逆
- **相神**：`PZZQ_ONLY`。`PZZQ-007-004`「月令既得用神，則別位亦必有相」；`xiangshen_state` 只能由 PZZQ Rule 注册；禁止「病药救应=相神」。
- **顺逆**：`DTS_PRIMARY`（DTS-025-001 顺其气势）；其他经典引用必须重新验证。

### ④ 干支组合 / 六亲 / 神煞 / 命例
- **神煞**：`EXCLUDED_FROM_RULE`。允许文献检索/参考展示；禁止命局核心裁决、用神判断、吉凶自动输出。
- **命例**：`REFERENCE_ONLY`。允许 Rule 验证/Golden Case/Regression Test；禁止从命例反推规则。

---

## 二、003B 新增两字段（已落库 governance/r1_05_verified_scope.json，25/25 领域）

### classical_usage_type
`FOUNDATIONAL | PRIMARY_RULE | SUPPORTING | CONTEXT_ONLY | REFERENCE_ONLY | EXCLUDED`

关键映射（Human 给定）：
| 概念 | 书 | 类型 |
|---|---|---|
| 用神 | PZZQ | PRIMARY_RULE |
| 病药 | SFTK | PRIMARY_RULE |
| 神煞 | YHZP/SMTH | EXCLUDED |
| 命例 | 六部 | REFERENCE_ONLY |
| 调候 | QTBJ | PRIMARY_RULE |
| 相神 | PZZQ | SUPPORTING（PZZQ_ONLY） |
| 通关 | DTS | SUPPORTING（DTS_SCOPE_ONLY） |

### rule_boundary
```json
{
  "allowed": ["PZZQ用神判断"],
  "forbidden": ["统一八字用神"]
}
```
防止 Agent 扩大解释。

---

## 三、003B 核验流程（目标 = Evidence Verification，不是找关键词）

逐章节检查，每条 source 核验链：

```
Source → Chapter → Text Layer → Attribution → Concept → Scope → Rule Eligibility
```

核验记录 schema（governance/patch_003b_evidence_checklist.json，已生成 130 条）：

```json
{
  "source_id": "DTS-019-001",
  "domains": ["tong_guan"],
  "chapter_verified": null,
  "text_layer_verified": null,
  "attribution_verified": null,
  "evidence_grade_verified": null,
  "usage_type_verified": null,
  "rule_boundary_ok": null,
  "verification_status": "PENDING",
  "note": ""
}
```

### 待核验清单规模（130 条）
| 书 | 条数 |
|---|---|
| YHZP | 24 |
| PZZQ | 17 |
| DTS | 35 |
| QTBJ | 14 |
| SMTH | 15 |
| SFTK | 25 |

> 第一批（f8f85498）9 领域原为早期 dict schema，已统一为 16 字段 cell；缺失字段（text_layer/object_type/semantic_role 等）标 `TO_VERIFY`，全部纳入 003B 核验清单。

---

## 四、执行要求（Human 冻结）

1. 六部逐章节核验（逐条回查原文，确认 text_layer/attribution/chapter/evidence_grade 与 Scope 一致）
2. 修正 Scope 遗漏（发现新证据 → 补入 r1_05_verified_scope.json 对应 cell）
3. 建立 Rule Admission 边界（每条核验通过的 source 输出 usage_type + rule_boundary）
4. **不开发算法**
5. **不生成业务判断**

## 五、003B 完成后才允许进入

```
旺衰 / 强弱 / 用神 / 格局 算法设计
```
该阶段必须依赖 003B 最终边界，禁止把六部经典"融合成一本书"。

---

## 六、核验顺序（按冻结批序反向核验，从最关键概念开始）

1. 用神（PZZQ-007-004 等）→ 病药（SFTK）→ 调候（QTBJ）→ 通关（DTS）
2. 格局成败 → 相神 → 顺逆
3. 旺强衰 → 令时地根 → 势
4. 其余领域顺序核验

## PATCH-003B 第一轮核验结果（commit 待）

### 状态汇总
- 待核验 130 条（YHZP 24 / PZZQ 17 / DTS 35 / QTBJ 14 / SMTH 15 / SFTK 25）
- **VERIFIED 129 条**（原文库存在，text_layer/evidence_grade/attribution 回查一致）
- **RESOLVED_NOT_FOUND 1 条**（SMTH-030-002）

### 关键修正：SMTH-030-002 引用不实
- 第 5 批落档时引用的 SMTH「地支至切，黨盛為強」**原文库不存在**——003B 核验抓出
- SMTH 实际「黨」命中均为神煞/日时断语语境（財黨煞等），无干支组合 A 级总纲
- 按铁律修正：NOT_FOUND/FAIL_CLOSED，excluded_scope 注明「日时断语为条件变量，不得作干支组合总纲」
- 教训：不得凭印象引用，evidence 必须可回查

### 第一批 schema 统一
- 第一批 9 领域原为早期 dict schema → 已统一为 16 字段 cell（49 cell）
- TO_VERIFY 字段从原文回填：text_layer/evidence_grade/attribution/chapter_id（49/49 清零）

### 层级一致性比对
- 158 条（含多领域重复引用）scope 期望 vs 原文实际 = 一致，0 不一致
- 无 A/B 级错标、无 attribution 错配

### 产物
- governance/r1_05_verified_scope.json：25 领域 16 字段 + classical_usage_type + rule_boundary + 回填完成
- governance/patch_003b_evidence_checklist.json：130 条核验记录（VERIFIED/RESOLVED_NOT_FOUND）

## PATCH-003B-02 概念遗漏检查结果（commit 待）

### 检查范围
11 个现代术语 × 六部原文表达簇：身强/身弱/旺/衰/清/浊/真/假/病/药/喜忌

### 结论：六部原文表达齐备，Scope 覆盖率 25/25 领域

| 现代术语 | 六部同词 | 六部近义表达 | Scope 覆盖 |
|---|---|---|---|
| 身强 | 全六部（SMTH37/SFTK61 最高） | 身健/身旺/日主强 | WANG_QIANG_SHUAI ✓ |
| 身弱 | 全六部（SFTK84 最高） | 身衰/日干无气/身柔 | WANG_QIANG_SHUAI ✓ |
| 旺 | 全六部（SMTH548/SFTK523） | 旺相/当权/司权/帝旺 | ✓（日时断语按 REFERENCE 处理） |
| 衰 | 全六部 | 衰看/休囚/失令 | ✓ |
| 清 | 全六部 | 清奇/清贵/清枯/清气 | QING_ZHUO_ZHEN_JIA ✓ |
| 浊 | **PZZQ 0 命中** | PZZQ 用「雜氣」/混雜 | ⚠️ 已补 PZZQ-007-005 |
| 真/假 | DTS 最集中（真假论） | 真神/假神 | ✓ |
| 病 | SFTK 101 条核心 | DTS「有病方为贵」中和语境 | ⚠️ 已补 DTS-017-002 |
| 药 | 六部同词少（SFTK16） | 救应/去病/解/制（SFTK106） | BING_YAO ✓ |
| 喜忌 | 全六部（SFTK420 最高） | 喜神/忌神/所喜/所忌 | ✓ |

### 抓到的两个 Scope 遗漏（003B-02 修正）
1. **PZZQ-007-005（A）**：PZZQ 原文无「濁」字，用「雜氣/雜而不雜」表达清浊（四墓杂气取清）。补入 QING_ZHUO_ZHEN_JIA 领域，excluded 注明「雜≠濁，与 DTS 清浊体系不同，不得合并」，CONDITIONAL。
2. **DTS-017-002（B1）**：「有病方為貴，無傷不是奇…格中如去病，才祿兩相宜」——DTS 病药表述（中和论注）。补入 BING_YAO 领域，excluded 注明「中和论语境，勿与 SFTK 病药诊断混同」，SUPPORTING_RULE_ONLY。

### 层级一致性
- 重比对：160 条一致、0 不一致（含新增 2 条）
- checklist 更新至 132 条

## PATCH-003B-03 Scope 边界复核结果（commit 待）

### 复核范围
旺强衰 / 令时地根 / 势 / 月令 / 根气 5 领域（用户冻结边界重点）

### 结果：全部通过

1. **对象化审计（OBJECT 维度）**
   - 5 领域 38 cell 全部有 object_type + semantic_role（0 缺失）
   - 根气域：PZZQ-007-021 obj=TEN_GOD（财根深）、QTBJ-011-001 obj=TEN_GOD（庚金无根）、SFTK-020-014 obj=TEN_GOD（弃命从财）——**根对象化已落地**（日主/财/官/杀/印可区分）

2. **RELATION 维度补齐（新增字段 relation_type，38 cell）**
   - 旺强衰：PROSPEROUS_AT / PROSPEROUS_CONTAINED（旺中有衰）/ PROSPEROUS_BLOCKED（失令持势不作旺）
   - 令时地根：GET_ORDER / GET_TIME / RULING_SCHEDULE / SEASONAL_CONDITION / GET_ORDER_BLOCKED
   - 势：TREND_TO / TREND_BURST / TREND_GROUP / TREND_HOLD
   - 月令：RULE_MONTH / RULING_ELEMENT / RULING_SCHEDULE
   - 根气：ROOTED_IN（通根/无根，对象化）
   - **OBJECT + SOURCE + RELATION + CLASSICAL_SCOPE 四维完整，0 缺失**

3. **固化推导模式扫描（169 cell）**
   - 有根→身强：0
   - 得令→身强：0
   - 得令=强：0
   - 旺=强：0
   - **违规 0**（不存在 if daymaster_root: strength="strong" 模式）

4. **rule_boundary 冻结确认**
   - WANG_QIANG_SHUAI forbidden：统一旺衰算法 / WANG→STRONG 自动映射 / 旺=强
   - LING_SHI_DI_GEN forbidden：得令=身强 / 得地=身强 / 时=令=得令 / RULING_SCHEDULE→WEIGHT

### 结论
003B-03 Scope 边界复核 PASS。旺衰/强弱体系保持「对象+关系」结构化，未出现任何 Boolean 固化。

## PATCH-003B-04 Rule Admission 十一门槛检查结果（commit 待）

### 检查范围
Scope 全部 cell 按 CLASSICAL_RULE_ADMISSION 十一门槛核查

### 结果：全部通过

| 门槛 | Scope 层可验证 | 结果 |
|---|---|---|
| 1 六部来源 | ✅ | 全部属于六部 |
| 2 精确章节 | ✅ | chapter_id 全部落档（非占位） |
| 3 原文存在 | ✅ | source_id 可回查原文库 |
| 4 text_layer 确认 | ✅ | 无 TO_VERIFY/占位 |
| 5 evidence_grade 确认 | ✅ | A/B 全部明确 |
| 6 attribution 确认 | ✅ | 32 条回填（ORIGINAL→ORIGINAL_AUTHOR；ANNOTATION→ORIGINAL_ANNOTATION） |
| 7 语境完整 | ✅ | 2 条短定义已补全（十二宫定名） |
| 8 条件完整 | ⏳ PENDING_RULE_LAYER | Scope 层 rule_boundary 已冻结边界；具体条件留 Rule 层逐条写 |
| 9 不跨书融合 | ✅ | rule_boundary forbidden 逐领域冻结 |
| 10 不升级注解 | ✅ | ANNOTATION 层 cell grade 均为 B 系列 |
| 11 Rule-Test-Golden 闭环 | ⏳ PENDING_RULE_LAYER | Rule 层未启动（Human 冻结） |

### 最终状态
- **CORE_RULE_ELIGIBLE：111**（全部 ADMISSIBLE_PENDING_RULE——「准入资格」，非「已准入规则」）
- EXCLUDED_FROM_RULE：7（神煞）
- FAIL_CLOSED：9（NOT_FOUND/引用不实）
- BLOCKED：0

### 关键口径
- ADMISSIBLE_PENDING_RULE = 证据链已钉死、具备申请准入资格；门槛 8/11（条件完整 + RTG 闭环）必须在 Rule 层逐条完成才能转 ADMISSIBLE
- 产物流转：governance/patch_003b_rule_admission.json（111 条逐条十一门槛记录）

### 003B 阶段总结
003B-01 第一轮核验（130 条）→ 003B-02 概念遗漏（补 2 条）→ 003B-03 边界复核（38 cell 四维）→ 003B-04 十一门槛（111 准入资格）
**PATCH-003B 全部完成。按 Human 冻结：接下来才允许旺衰/强弱/用神/格局算法设计（以 ADMISSIBLE_PENDING_RULE 清单为唯一来源）。**
