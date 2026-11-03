# 盲派辨 Evidence Corpus v1 - Phase A 执行规范

**日期**: 2026-09-02  
**状态**: 🟢 CONDITIONAL PASS  
**仲裁裁决**: B1-B4 四项约束已锁定

---

## 一、执行约束（不可违反）

### B1: Canonical State 共享原则
- 盲派 Signal Namespace 独立
- Canonical Chart State 可以被多体系共享
- 同一事实可同时产生子平 Evidence 和盲派 Evidence
- **禁止**: `Blind PATTERN = 子平 PATTERN`

### B2: BODY_USE_RELATION 命名
- 使用 `BODY_USE_RELATION` 而非 `BODY_USE`
- 明确区分于子平月令用神、调候用神、格局用神
- **禁止**: 产生统一 `yongshen` 字段

### B3: 三层区分
```text
RAW_EVIDENCE       → 原典原文摘录
DERIVED_BLIND_STATE → 结构分析结果
SEMANTIC_INTERPRETATION → 解释推断（不进入 Phase A）
```

### B4: Phase A 范围
- ✅ 只建立 Evidence Corpus
- ❌ 不创建 Signal Schema
- ❌ 不建立 Mapping
- ❌ 不修改 Phase 3
- ❌ 不决定 BLIND_STRUCTURE 等 Signal 命名（仅作为 Candidate Taxonomy）

---

## 二、Evidence Schema（Phase A 专用）

```json
{
  "evidence_id": "E-BLIND-{topic}-XXX",
  "system": "BLIND_SEGMENT",
  "provenance_layer": "A|B|C|D",
  "authority_status": "PRIMARY_TRADITION|SYSTEMATIZED|CASE_EVIDENCE|SECONDARY",

  "source": {
    "title": "...",
    "author": "...",
    "edition": "...",
    "chapter": "...",
    "page": "...",
    "locator": "..."
  },

  "original_text": "...",
  "context": "...",
  "conditions": [],

  "extraction_topic": "GUEST_HOST|BODY_USE_RELATION|WORK_RELATION|WORK_TYPE|WORK_ACTOR|WORK_TARGET|WORK_EFFICIENCY|POWER_PARTY|EMPTY_USELESS|IMAGE|YING_QI",
  "claim_type": "STRUCTURAL|WORK|TEMPORAL",
  "source_fidelity": "DIRECT|PARAPHRASE|SECONDARY",
  "certainty": "HIGH|MEDIUM|LOW",
  "notes": "..."
}
```

---

## 三、分层标准

| Layer | 定义 | Authority Status |
|-------|------|------------------|
| A | 夏仲奇遗例、郝金阳遗例、盲师口诀 | PRIMARY_TRADITION |
| B | 《盲派初级命理学》《段氏理象学》《盲派命理》 | SYSTEMATIZED |
| C | 断例验证材料 | CASE_EVIDENCE |
| D | 网络讲义、教程、后人总结 | 不进入 Evidence Corpus |

---

## 四、执行步骤

### Step 1: 资料确认
- 确认本地文件路径或在线资源 URL
- 建立资料清单

### Step 2: Evidence Extraction
- 从 B 层资料提取 Evidence
- 每条 Evidence 必须包含：original_text、context、conditions、provenance
- 按 extraction_topic 分类存储

### Step 3: Manifest 生成
- 生成 `data/evidence/blind_seg/manifest.json`
- 统计证据数量、分层分布

### Step 4: 报告生成
- 生成 `docs/audit/BLIND_EVIDENCE_CORPUS_V1_REPORT.md`
- 包含：来源分析、证据分布、质量评估

---

## 五、产出要求

```
data/evidence/blind_seg/
├── E-BLIND-GUEST_HOST-001.json
├── E-BLIND-BODY_USE_RELATION-001.json
├── E-BLIND-WORK_RELATION-001.json
├── ...
└── manifest.json

docs/audit/
└── BLIND_EVIDENCE_CORPUS_V1_REPORT.md
```

---

## 六、禁止行为

- ❌ 不创建 `feature_signal_mapping_blind.json`
- ❌ 不修改 `data/feature_signal_mapping.json`
- ❌ 不修改 Phase 3 任何文件
- ❌ 不进入 Production Admission
- ❌ 不使用网络盗版资料

---

*Phase A 执行规范已锁定，等待资料来源确认后开始提取*
