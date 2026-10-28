# Human Arbitration Queue — DTS 待裁决队列（2026-09-16）

> **总则（Human 裁决 2026-09-16）**：以下六项全部只登记、不实现、不拍死、不自动 Admission。
> BOT 不得在 Human 裁决前自行处理（拆字段/改 schema/补公式/补精度/统一口径）。
> 解锁条件逐项列明，满足后重新提交 Human。

## PENDING 类型定义（封闭枚举，BOT 不得自创新类型）

| 类型 | 含义 | 对应项 |
|---|---|---|
| `PENDING_SEMANTIC_AUDIT` | 字段语义冲突，需先做语义审计（身份/喜忌/结构关系），审计后由 Human 定拆/改/留 | 01 |
| `PENDING_SCHEMA_REVIEW` | schema 信息损失（数据粒度不足），需 Human 批准 schema 变更 | 02 |
| `PENDING_RULE_FROZEN` | 规则口径冻结——不得凭五行常识自补公式，须走 原文→版本核验→Rule→Evidence→Test→Golden→Admission | 03, 04 |
| `PENDING_TEXT_CRITICISM` | 文本异文裁决——须原文扫描页 + 多版本交叉，Human 文本裁决 | 05 |
| `PENDING_STRENGTH_ITERATION` | 前置引擎精度迭代——不得用数量/权重/分数/阈值补精度 | 06 |

---

## PENDING-01：wuxing_state / jishen_state 字段语义冲突

- **状态**：`PENDING_SEMANTIC_AUDIT`（接受问题发现，暂不拆字段、不改规则）
- **Human 裁决 2026-09-16（字段设计方向，不进入实现）**：
  - **jishen_state → `APPROVED_SPLIT`**（同音异义字段污染——吉神 ji shén / 忌神 jì shén 拼音相同、古典概念不同；不允许依靠拼音字段作为 canonical identifier）。
    - 032/033（吉神显隐）→ 新字段 `auspicious_deity_state`（或 `jishen_good_state`）
    - 041（忌神攻击）→ 新字段 `jishen_attack_state`
    - **迁移方案草案**：见 `docs/字段迁移方案_jishen_state_拆分_草案.md`（含 alias 映射、双写策略、验证点）
  - **wuxing_state → `CONTINUE_PENDING`**（不拆）：057/058「不戾正清和/濁亂偏枯」vs 074「和」——「和」是五行总状态（wuxing_state=和）还是 qing_zhuo_state 的一个结果，维度关系未确认，证据不足。
- **BOT 执行限制（Human 明令）**：✅可做 迁移方案草案 / alias 映射 / 更新仲裁队列；❌不可 删除旧字段 / 修改规则引用 / 修改 evidence 绑定 / 自动迁移生产规则。等待后续 Human 批准。
- **BOT 语义审计（只读，供裁决，非定论）**：
  - **jishen_state 实为拼音缩写撞车**：「吉神」（ji shén）与「忌神」（jì shén）同音。032/033 语境=吉神（喜用神）显隐状态（太露/深藏）；041 语境=忌神攻击状态（展轉攻）。**两个不同概念，非同一实体的两种值域**。
  - **wuxing_state**：057/058 维度=「戾否/清浊/偏枯」；074 维度=「和否」（全者宜全、缺者宜缺、生者宜生、尅者宜尅）。「清和」与「和」概念接近但非全同，是否同一维度待 Human 裁定。
- **禁止**：不得为 Registry 合规强行拆字段/改规则。
- **解锁**：Human 批准迁移方案（字段命名二选一）→ 按草案执行双写迁移。

---

## PENDING-02：007/008 branch 字段粒度不足

- **状态**：`PENDING_SCHEMA_REVIEW`（接受问题发现，暂不改 schema）
- **问题**：DTS-009-003「生方怕動，庫宜開」——规则需回答「谁冲谁/哪一支被冲/冲在哪个位置」，当前 `branch` 单字段无法表达被冲对象，属 schema information loss。
- **禁止**：不得偷偷增加字段。
- **解锁**：Human 批准 schema 变更（如 `chong_source_branch` / `chong_target_branch` 或 `branch_chong_pairs`）后实现。

---

## PENDING-03：010/011 冲旺衰口径

- **状态**：`PENDING_RULE_FROZEN`（整组冻结）
- **问题**：DTS-009-009「旺者沖衰衰者拔，衰神沖旺旺者發」——`source_strength`/`target_strength`（冲之双方旺衰）判定口径。
- **禁止**：不得凭五行常识自补公式（如按行计数/得令近似）。
- **解锁**：走 原文→版本核验→Rule→Evidence→Test→Golden→Admission 全链后 Human 裁决。

---

## PENDING-04：062–067 方位/流向/顺逆生

- **状态**：`PENDING_RULE_FROZEN`（整组冻结）
- **问题**：water_flow（西水還南）/fire_flow（東火轉北）/sheng_order（順生逆生）/yangming（陽明遇金）/yinzhuo（陰濁藏火）——判定口径不清。
- **禁止**：不得自行统一口径、不得按方位常识补公式。
- **解锁**：同上，全链验证后 Human 裁决。

---

## PENDING-05：何知章 036–044 版本异文（**优先级最高**）

- **状态**：`PENDING_TEXT_CRITICISM`（明确 PENDING）
- **问题**：DTS-033/035 何知章/小兒論——已发现「濕而不滯 ↔ 濕而滯」反义级异文风险；036-044 不得成为最终 Evidence。
- **异文现状（BOT 已核）**：DTS-033 共 **11 条 source 带 text_variants，30+ 条异文记录**（含已裁决 DTS-033-006 HUMAN_ACCEPTED_BASE）。按风险分级：
  - **反义级（影响规则语义，优先裁决）**：
    - DTS-033-015「濕而不滯，燥而不鬱」vs 通行「湿而滞，燥而郁」——**✅ 已裁决（2026-09-16）采底本**：功能失用型病态（湿失凝蓄→精流/燥失敛藏→氣洩），因果自洽；通行本脱「不」字与精流气泄方向矛盾。见 `docs/PENDING-05_何知章夭段_濕而不滯_审计对照_2026-09-16.md` v3 终审
    - DTS-033-014 寿注「身弱印輕」vs 通行「身弱印旺」（轻/旺反义）——**待裁决**
  - **主客颠倒/结构级**：
    - DTS-033-002 富注「亦有才富而妻傷者」vs「亦有妻伤而财厚者」
    - DTS-033-004 贵注「必主多子」vs「必贵；官星浊而身旺者必多子」（后半句差异大）
    - DTS-033-008 贱注「財輕官重」vs「身轻官重」（财/身）
  - **字差/字序级**：大量（才/财、星/神、旺/强、元气/元神、定性/性定等），影响 Evidence 文本一致性
- **裁决路径（必须交叉，缺一不可）**：
  1. 项目底本扫描页（OCR转录版 + pages）
  2. 《滴天髓》通行本
  3. 《滴天髓阐微》
  4. 《滴天髓辑要》
  → Human 文本裁决
- **禁止**：普通 OCR 修正替代；不得先行进入 Evidence。
- **解锁**：Human 对分级清单逐条裁决（反义级优先）→ text_variant 更新 human_verdict → 036-044 才可进入 Evidence 链。

---

## PENDING-06：阳刃弱 / 客神不可达 / strength 三档精度

- **状态**：`PENDING_STRENGTH_ITERATION`（接受为待迭代问题）
- **问题**：
  - 阳刃弱不可达（刃支=日主帝旺位必帮身得地→恒 WANG）
  - 客神不可达（喜忌三档全覆盖→无闲神）
  - day_strength_state 六档 canonical enum 已冻结，但 SLIGHTLY_STRONG/SLIGHTLY_WEAK 判定规则未完成
- **禁止**：不得用数量/权重/分数/阈值补精度。
- **解锁**：strength 精度迭代（结构条件+Resolution Rules 全链验证）后复查；在此之前阳刃弱/客神保持不可达（代码分支保留+测试锁定）。

---

## 关联现状（BOT 已执行，不受本次裁决影响）

- enum_registry v1.6.0：74 条 = 29 ACTIVE + 45 PENDING（冲突字段均已注册 PENDING，未拆）
- DTS 规则：61 PENDING / 29 CANDIDATE（074/041 等冲突规则已标 PENDING + notes 说明）
- 隔离一致性校验：通过（PENDING 枚举 ↔ PENDING 规则无越权消费）
- 全量测试：247 passed
