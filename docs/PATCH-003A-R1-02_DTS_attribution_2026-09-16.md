# PATCH-003A-R1-02：DTS attribution 细分（原注 / 任氏注 / 后世注定层）

> 日期：2026-09-16 ｜ 执行：R1-01 attribution 细分 → R1-02 逐条定层（本报告）
> 前置：R1-01 已确认 DTS 分层（132A/124B/1C/1D，见 R1 报告）

## 一、attribution 判定方法

1. **维基文库《滴天髓阐微》对照**：该版明确分三层「正文 / 〈原註〉/ 〈任氏曰〉」，全文 67,981 token 已抓取前 12,000 建立文本特征库
2. **本地注文特征扫描**：124 条注中「任氏/任铁樵/任曰」0 命中；任氏命例特征词（此造/余曰/某造/命書/余觀/余詳/推過/以餘論之等）0 命中——**本地底本无任氏曰内容**
3. **抽样逐字对照**（本地 ↔ 阐微〈原註〉）：天道、天干（丁/辛/壬/癸）、地支、月令、生時、衰旺、真假 8 组注文与阐微〈原註〉同源一致
4. **结论**：本地民国本底本 = 「正文 + 原注」结构（阐微体系之〈原註〉层），**不含任氏曰**

## 二、attribution 定层结果（258 条全量）

| attribution | 条数 | 对应阐微层 | evidence_use_policy |
|---|---|---|---|
| ORIGINAL_AUTHOR | 132 | 正文 | CORE_RULE_ELIGIBLE |
| **ORIGINAL_ANNOTATION** | 124 | 〈原註〉 | SUPPORTING_RULE_ONLY + CANDIDATE_RULE + NO_ORIGINAL_UPGRADE |
| LATER_COMMENTARY | 1 | 序 | SUPPORTING_ONLY |
| UNKNOWN | 1 | 何知章待核 | FAIL_CLOSED |
| REN_TIEQIAO | 0 | （本地未转录任氏曰） | — |

**字段已写入 sources.dts.jsonl**：`attribution` / `evidence_use_policy` / `attribution_basis`

## 三、关键句 attribution 定死（五簇相关）

| source_id | 内容 | attribution | 用途 |
|---|---|---|---|
| DTS-015-003 | 月令提綱之府譬之宅也 | ORIGINAL_AUTHOR | CORE_RULE_ELIGIBLE |
| DTS-015-005 | 生時歸宿之地譬之墓也 | ORIGINAL_AUTHOR | CORE_RULE_ELIGIBLE |
| DTS-016-001 | 能知衰旺之真機 | ORIGINAL_AUTHOR | CORE_RULE_ELIGIBLE |
| DTS-023-001/003 | 真假正文 | ORIGINAL_AUTHOR | CORE_RULE_ELIGIBLE |
| DTS-015-004 | 令星乃三命之至要 + 寅月戊丙甲用事 | **ORIGINAL_ANNOTATION** | SUPPORTING_RULE_ONLY / CANDIDATE_RULE / NO_ORIGINAL_UPGRADE |
| DTS-015-006 | 子時前三刻三分壬水/後三刻七分癸水用事 | **ORIGINAL_ANNOTATION** | SUPPORTING_RULE_ONLY / CANDIDATE_RULE |
| DTS-016-002 | 旺中有衰者存 | **ORIGINAL_ANNOTATION** | SUPPORTING_RULE_ONLY / CANDIDATE_RULE / NO_ORIGINAL_UPGRADE |
| DTS-023-004 | 真神得令假神得局而黨多 | **ORIGINAL_ANNOTATION** | SUPPORTING_RULE_ONLY / CANDIDATE_RULE |

## 四、B 级证据细分规则（Human 拍板锁定）

```
A  ORIGINAL          → CORE_RULE_ELIGIBLE
B1 ORIGINAL_ANNOTATION → SUPPORTING / CANDIDATE（原注，传统传承注释层）
B2 REN_TIEQIAO      → SUPPORTING / CANDIDATE（任氏注，本地暂缺）
B3 LATER_COMMENTARY → SUPPORTING ONLY（后世注释，序言类）
D  QUOTED_SOURCE    → SOURCE_TRACE_REQUIRED
U  UNVERIFIED       → FAIL_CLOSED
```

**禁止**：`if text_layer == "ANNOTATION": evidence_grade = "B"`——必须先判 attribution。
**禁止**：`if evidence_grade in ["A","B"]: admit_rule()`——B 级不得自动升级 A。

## 五、重要语义拆分（用户锁定）

| 概念 | 层 | 说明 |
|---|---|---|
| 「人元用事」概念本身 | **ORIGINAL/A** | DTS-015-003/005 正文有「人元用事之神」 |
| 「寅月戊7/丙7/甲15」「子时壬3/癸7」具体时间表 | **ANNOTATION/B1** | 原注层，须六部交叉验证后才能进执行层 |

## 六、R1 执行状态

```
R1-01  DTS attribution 细分               ✅ PASS（本报告）
R1-02  原注/任氏曰/后世材料逐条定层         ✅ PASS（258 条全量，attribution 已写入）
R1-03  人元用事时间表六部交叉验证           ⏳ 下一步
R1-04  SOURCE_ALIGNMENT                   ⏳
R1-05  28×6 VERIFIED_SCOPE                ⏳（R1-03/04 完成后）
PATCH-003B                                ⏳
```

## 七、待 Human 确认

1. attribution 定层结论（本地 = 正文 + 原注，无任氏曰）是否认可？
2. 若后续需要任氏注（B2），是否要转录《滴天髓阐微》任氏曰层？还是保持本地底本（原注层）为准？
3. R1-03 六部交叉验证范围：12 月用事 + 12 时用事，在 YHZP/PZZQ/QTBJ/SMTH/SFTK 逐部检索「用事/司令/司權/人元/支藏」原文
