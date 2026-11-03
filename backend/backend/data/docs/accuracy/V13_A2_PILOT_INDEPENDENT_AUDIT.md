# V1.3 A2 — Pilot Independent Audit Report (Revised v0.2)

**日期**: 2026-08-22
**审计对象**: `64c68ba` + `v2.2` 修复
**审计类型**: READ-ONLY, 人工/规则检查
**状态**: ✅ PASS (P0 已修复)

---

## 一、审计摘要

| 指标 | 原报告 (v0.1) | 修正后 (v0.2) |
|------|--------------|---------------|
| Persons | 30 | 30 |
| Events | 133 | 130 |
| OFFICIAL events | 133 | **90** |
| THIRD_PARTY events | 0 | **40** |
| OX static traits | 0 | **7** |
| BLIND eligible | 30 | **15** |
| HOLDOUT eligible | 0 | 0 |

---

## 二、P0 问题修复确认

### P0-1: Edition 12 Provenance
```text
Before: 38 events labeled OFFICIAL (wrong)
After:  38 events labeled THIRD_PARTY (correct)
Status: ✅ FIXED
```

### P0-2: Missing Birth Data
```text
Excluded: hkjfma_2018_c6 (PB-0019)
Reason: birth_info.missing = true
Status: ✅ FIXED
```

---

## 三、Gate-Level Pass Rate (修正后)

| Gate | Pass Rate | Notes |
|------|-----------|-------|
| G01 Provenance | 30/30 | All persons have source |
| G02 Event Verification | 30/30 | All have events |
| G03 Date Precision | 30/30 | All YEAR precision |
| G04 Ontology Mapping | 26/30 | 4 persons have UNKNOWN (OX events) |
| G05 Source Independence | 30/30 | All independent |
| G06 Leakage | 30/30 | CLEAN or REVIEWED |
| G07 Duplicate | 30/30 | No duplicates |
| G08 Oracle Qualification | 30/30 | All have non-OX events |
| G09 Temporal Eligibility | 30/30 | All have event_year |
| G10 Blind Eligibility | **15/30** | Only OFFICIAL edition persons |
| G11 Holdout Eligibility | 0/30 | Pilot stage, no holdout |
| G12 Reproducibility | 30/30 | All reproducible |

**合格人数**: 30/30 (min 10/12 gates)
**BLIND 可用**: 15/30 persons (90 events)
**THIRD_PARTY**: 15/30 persons (40 events) — 仅用于 O2 验证

---

## 四、数据质量评分

```text
DATA QUALITY SCORE:
├── Provenance 完整性: 90/130 (69%) — 40个THIRD_PARTY
├── Event 可验证性: 123/130 (95%) — 7个静态特征(OX)
├── Temporal 精度: 130/130 (100%) — 全部YEAR
├── Leakage 清洁度: 128/130 (98%) — 2个REVIEWED
├── Ontology 映射: 126/130 (97%) — 4个UNKNOWN(OX)
├── Source 独立性: 130/130 (100%) — 全部fate-bench
└── 总体可用率: 90/130 (69%) — 排除THIRD_PARTY和OX后
```

---

## 五、关键发现

### 5.1 Edition 分布
| Edition | Provenance | Count | BLIND Eligible |
|---------|------------|-------|----------------|
| 1 (2010) | OFFICIAL | 9 | ✅ |
| 2 (2011) | OFFICIAL | 15 | ✅ |
| 3 (2012) | OFFICIAL | 15 | ✅ |
| 4 (2013) | OFFICIAL | 16 | ✅ |
| 9 (2018) | OFFICIAL | 40 | ✅ |
| **12 (2021)** | **THIRD_PARTY** | **38** | ❌ |

### 5.2 Oracle Grade 分布
| Grade | Count | Description |
|-------|-------|-------------|
| O1 | 90 | OFFICIAL answer (A evidence) |
| O2 | 33 | THIRD_PARTY answer (B evidence) |
| OX | 7 | Static trait (not evaluable) |

### 5.3 Event Type 分布
```text
FAMILY.MARRIAGE:      23
CAREER.*:             22
LIFE_EVENT.HEALTH_CRISIS: 16
EDUCATION.GRADUATE:   12
CAREER.WEALTH_CHANGE: 11
FAMILY.CHILD_BIRTH:   10
LIFE_EVENT.SOCIAL_ACHIEVE: 9
CAREER.CHANGE:        4
LIFE_EVENT.LEGAL_ISSUE: 3
LIFE_EVENT.TRAUMA:    2
LIFE_EVENT.UNKNOWN:   2
```

---

## 六、决策记录

### 6.1 数据集分层
```text
BLIND Set (Primary):
├── 15 persons (PB-0001 至 PB-0021, excluding THIRD_PARTY)
├── 90 events (OFFICIAL provenance)
└── Status: Ready for A3 evaluation

THIRD_PARTY Set (Secondary):
├── 15 persons (PB-0022 至 PB-0030)
├── 40 events (THIRD_PARTY provenance)
└── Status: O2 grade, not for primary accuracy claim

Holdout Set:
├── Not available in pilot
└── Status: Will be created from Golden Dataset + new sources
```

### 6.2 统计口径修正
```text
Before (incorrect):
  "Cases passing all gates: 30/30"
  "min 10/12"

After (correct):
  "G01-G12 gate-level pass rate:"
  "G01: 30/30, G02: 30/30, ..., G10: 15/30, G11: 0/30"
  "Qualified persons: 30/30 (all pass min threshold)"
  "BLIND eligible: 15/30"
```

---

## 七、审计结论

```text
┌─────────────────────────────────────────────────────────────┐
│               A2 PILOT INDEPENDENT AUDIT                      │
├─────────────────────────────────────────────────────────────┤
│  Status:  ✅ PASS                                             │
│                                                              │
│  P0 Issues:                                                   │
│    ✅ Edition 12 provenance corrected to THIRD_PARTY         │
│    ✅ hkjfma_2018_c6 excluded (missing birth data)           │
│                                                              │
│  P1 Issues:                                                   │
│    ⚠️ 7 static trait events marked OX                        │
│    ⚠️ prediction_cutoff improved                             │
│    ⚠️ 2 semantic leakage events marked REVIEWED              │
│    ⚠️ Gate-level statistics corrected                        │
│                                                              │
│  Decision:                                                   │
│    Pilot 数据集已通过独立审计。                                │
│    BLIND Set (90 events) 可用于 A3 Accuracy Evaluation。    │
│    THIRD_PARTY Set (40 events) 标记为 O2，用于交叉验证。     │
│                                                              │
│    批准进入 310 扩充阶段。                                     │
└─────────────────────────────────────────────────────────────┘
```

---

**审计签名**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A2-Pilot-Audit-v0.2