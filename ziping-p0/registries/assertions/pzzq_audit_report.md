# 《子平真诠》断语切片优化工程 — 审计报告

- 工程代号：AGENT-PZZQ
- 输出文件：`D:\shuntian-ziping-p0\registries\assertions\pzzq_assertions_new.jsonl`
- 源文件（未改动）：`pzzq_assertions.jsonl`（83条）
- 证据库：`sources.pzzq.jsonl`（49条 source_id，PZZQ-001-001 ~ PZZQ-007-035）
- 校验脚本：`validate_assertion.py`（Schema v2.2.2）
- 完成日期：2026-09-20

---

## 一、总量与完成度

| 指标 | 数值 |
|------|------|
| 规范化现有断言 | 83 条（ASSERT-PZZQ-0001 ~ 0083） |
| 新增原子断言 | 133 条（ASSERT-PZZQ-0084 ~ 0216） |
| **总断言数** | **216 条**（≥200，达标） |
| 格式校验错误 | **0** |
| 格式校验警告 | 29（全部为 use_god namespace，见决策记录 D1） |
| source_evidence 不存在 | 0（全部命中 sources 库 49 个 ID） |
| assertion_id 重复 | 0 |

> 校验结论：`✅ 格式校验通过（原典依据和语义准确性需人工审核）`

---

## 二、第零步：现有 83 条规范化映射明细

| 规范化项 | 原值→新值 | 条数 | 说明 |
|----------|-----------|------|------|
| assertion_id 格式 | 带字母后缀（0006a 等）→ 连续纯数字 0001~0083 | 全部 83 | 旧 ID 不合 `^ASSERT-[A-Z]{4}-\d{4}$`，按文件顺序重编号；旧语义分组已保留在 human_text/condition 中 |
| grade | ORIGINAL → A | 10 | 对应原 0050a/b/c、0051a/b、0060a/b/c、0061a/b |
| audit_status | 缺失 → CANDIDATE | 10 | 同上 10 条补齐 |
| human_text | 缺失 → 按 source 原文补人话 | 10 | 同上 10 条补齐（如"财喜根深不宜太露""官格忌刑冲破害"） |
| condition | 空 `{}` → `{positive,negative,exception}` 空串对象 | 10 | 同上 10 条补齐 |
| assertion_type | CONDITION → RULE | 62（合并计） | 条件断言本质为可执行判断规则 |
| assertion_type | NEGATION → RULE（polarity=negative） | 17 | 均为"忌/不可/勿"禁止性规则，非例外语气，故不入 EXCEPTION |
| assertion_type | EXCEPTION / DEFINITION / RELATION | 保留 | 1 / 12 / 8 |
| predicate | determines → implies | 6 | 决定=蕴含 |
| predicate | rejects → conflicts_with | 6 | 排斥=冲突 |
| predicate | supports → strengthens | 10 | 支持=增强 |
| predicate | changes / distinguishes / blocks / requires / activates / selects / separates | 保留 | 均在 V2.1 扩展谓词表内 |

规范化后字段分布：grade 全部 A；assertion_type = RULE 154 / DEFINITION 44 / RELATION 8 / EXCEPTION 10。

---

## 三、第一步：缺口分析与新增覆盖

现有 83 条偏"合并命题"（单条塞入多个成格条件）。新增 133 条按**原子粒度**切片，覆盖子平真诠格局体系核心命题：

| namespace | 现有 | 新增 | 合计 | 覆盖命题 |
|-----------|------|------|------|----------|
| PZZQ.pattern | 61 | 56 | 117 | 八格成格/败格、顺用逆用、杂气取用、墓库刑冲、四吉四凶神破格成格、生克先后、星辰无关、外格用舍、八格细分 |
| PZZQ.use_god | 5 | 24 | 29 | 用神专求月令、八格顺逆配合、妄取用神、月令无用神另取、用神变化（善/不善/不失本格）、纯杂 |
| PZZQ.pattern_success | 6 | 22 | 28 | 八格成象败象逐条原子化、带忌、救应、因成得败因败得成 |
| PZZQ.pattern_level | 10 | 9 | 19 | 有情无情有力无力、格之最高/高而次/低而无力 |
| PZZQ.xiangshen | 1 | 5 | 6 | 相神定义、赖一字成格、伤相甚于伤用、相神无破/有伤 |
| PZZQ.diaohou | 0 | 6 | 6 | 配气候互参、金寒水冷、金水伤官喜见官、木火通明、金水相涵 |
| PZZQ.yingqi | 0 | 11 | 11 | 取运配八字喜忌、美运败运、似喜实忌似忌实喜、冲缓急轻重、会局解冲、成格变格、透清 |

极性分布：neutral 92 / positive 72 / negative 52。

---

## 四、核心铁律执行记录

1. **原著优先**：全部 216 条 source_evidence 命中 `sources.pzzq.jsonl` 既有 49 个 ID，无凭空创造。
2. **格局成立 ≠ 命贵**：成格/败格断言 object 一律用"成格/格成/格破"等结构词，polarity 标 positive/negative 仅指结构成败，不升级为"命贵/贫贱"命运吉凶。原文"贵格"仅作为结构上的成格结构保留（如"贵格已成"标注为"结构成"）。
3. **禁止结构候选升级为命题成立**：候选项一律 RULE 待审（audit_status=CANDIDATE），未自行 APPROVE。
4. **禁止合并多命题**：新增 133 条全部单命题原子切片。
5. **不覆盖现有文件**：输出独立 `_new.jsonl`，原 `pzzq_assertions.jsonl` 保持原样。

---

## 五、关键决策记录

- **D1（namespace use_god）**：任务指令声明 use_god 已注册。校验脚本 V2.2.2 的 `VALID_NAMESPACE_SUFFIXES` 暂未列入 use_god（仅 yongshen），故产生 29 条 warning（非 error，不影响"0 错误"）。**保留 use_god** 以与现有 83 条及下游引用一致；若后续注册表更新为仅认 yongshen，可一次性 `use_god→yongshen` 映射消除 warning。
- **D2（assertion_id 重编号）**：旧 ID 大量带字母后缀（0006a/b 等），不合校验正则。按文件顺序重编为连续纯数字 0001~0083，新增自 0084 起，无冲突。
- **D3（异文采信）**：印格成格条件"印轻逢煞"一句，sources 库 `PZZQ-005-008` 已记录人裁（2026-09-16 采信通行本"印輕逢煞"，弃底本"財輕逢煞"），新增对应断言按人裁后文本表述，并在 exception 字段标注。
- **D4（NEGATION 归并）**：17 条 NEGATION 均为禁止性规则（忌/不可/勿），语义非"但书例外"，故全部 → RULE(polarity=negative)，未入 EXCEPTION；原 1 条例外语气断言（0012b 会合解冲）保留 EXCEPTION。

---

## 六、待人工复核项

1. 29 条 use_god warning：确认下游注册表口径后决定是否映射 yongshen。
2. 全部 216 条 grade=A、audit_status=CANDIDATE，语义准确性（吉凶措辞、格局归类）需 MainAgent 终审后批量 APPROVE。
3. `PZZQ-007-015`（变格）原文"壬生戌下闕"有阙文，对应断言 exception 已标注"原文下阙"。
