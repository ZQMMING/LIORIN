# Phase A Evidence 原文真实性修复记录

## 修复日期: 2026-09-02

### 问题来源
Commit `745dc50` 新增的 12 条 Evidence 存在原文真实性问题。

---

## 修复内容

### 1. 降级处理 (8条)

以下 Evidence 从 `DIRECT/HIGH` 降级为 `PENDING_VERIFICATION/MEDIUM`:

| Evidence ID | Layer | Topic | 原因 |
|-------------|-------|-------|------|
| E-BLIND-BODY_USE_RELATION-007 | B | BODY_USE_RELATION | 原文疑似二次整理，非逐字原文 |
| E-BLIND-WORK_EFFICIENCY-005 | B | WORK_EFFICIENCY | 原文疑似二次整理，非逐字原文 |
| E-BLIND-POWER_PARTY-005 | B | POWER_PARTY | 原文疑似二次整理，非逐字原文 |
| E-BLIND-WORK_TARGET-005 | B | WORK_TARGET | 原文疑似二次整理，非逐字原文 |
| E-BLIND-IMAGE-005 | B | IMAGE | 原文疑似二次整理，非逐字原文 |
| E-BLIND-YING_QI-005 | B | YING_QI | 原文疑似二次整理，非逐字原文 |
| E-BLIND-EMPTY_USELESS-005 | B | EMPTY_USELESS | 原文疑似二次整理，非逐字原文 |
| E-BLIND-WORK_METHOD-004 | B | WORK_METHOD | 原文疑似二次整理，非逐字原文 |

**降级后状态**:
```json
{
  "source_fidelity": "PENDING_VERIFICATION",
  "certainty": "MEDIUM",
  "verification_status": "SOURCE_VERIFICATION_REQUIRED",
  "notes": "... | ⚠️ 原文真实性待最终文献核验"
}
```

---

### 2. PROVENANCE REPAIR (1条)

#### E-BLIND-COMPLEX_WORK-002

**问题**: 静默覆盖历史版本，locator 和 original_text 同时改变。

**修复措施**:
- 创建修复记录文件 `E-BLIND-COMPLEX_WORK-002-fix-record.json`
- 记录原定位: `第二章 复合做功进阶 / p.45-50`
- 记录新定位: `第三章 做功详解 第九节 复杂做功的综合分析 / p.68-75`
- 保留完整修复轨迹

**修复记录内容**:
```json
{
  "evidence_id": "E-BLIND-COMPLEX_WORK-002",
  "fix_type": "PROVENANCE_REPAIR",
  "fix_date": "2026-09-02T...",
  "original_locator": "第二章 复合做功进阶 / p.45-50",
  "corrected_locator": "第三章 做功详解 第九节 复杂做功的综合分析 / p.68-75",
  "reason": "原文定位信息更正，建立审计轨迹",
  "current_data": {...}
}
```

---

### 3. 保留不处理 (4条)

以下 Evidence 保持原状态:

| Evidence ID | Layer | Topic | 原因 |
|-------------|-------|-------|------|
| E-BLIND-GUEST_HOST-004 | B | GUEST_HOST | 待后续核验 |
| E-BLIND-C-GUESTHOST_CASE-001 | C | GUEST_HOST | C层案例，结构正确 |
| E-BLIND-C-EFFICIENCY_CASE-001 | C | WORK_EFFICIENCY | C层案例，结构正确 |
| E-BLIND-COMPLEX_WORK-002 | B | COMPLEX_WORK | 已建立修复记录 |

---

## 当前状态

```
总证据数: 65
├── DIRECT/HIGH: 57条 (已验证)
├── PENDING_VERIFICATION: 8条 (待核验)
└── CASE_EVIDENCE: 12条 (C层案例)

Layer分布: A=2, B=51, C=12, D=0
Topic覆盖: 13/13 (100%)
```

---

## 后续要求

1. **所有 PENDING_VERIFICATION 证据** 必须进入 Multi-AI Final Verification 队列
2. **不得**将 PENDING_VERIFICATION 证据提升为 DIRECT/HIGH
3. **provenance 修复** 必须建立记录，不得静默覆盖
4. **Phase A 继续扩充** 时，确保 original_text 为真实原文，不将二次整理文本标为 DIRECT

---

## 仲裁原则重申

```text
Evidence Collection
       ↓
Source Verification (Multi-AI Final)
       ↓
Authority Assignment (DIRECT/HIGH)
       ↓
Production Admission
```

**不在 Source Verification 阶段完成的 Evidence，不得标记为 DIRECT/HIGH。**
