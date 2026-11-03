# Phase A Evidence 原文真实性修复记录（续）

## 修复日期: 2026-09-02

### 问题来源
Commit `211562f` 新增的 10 条 Evidence 存在原文真实性问题，且修改了既有 Evidence。

---

## 修复内容

### 1. 降级处理 (10条)

以下 Evidence 从 `DIRECT/HIGH` 降级为 `PENDING_VERIFICATION/MEDIUM`:

| Evidence ID | Layer | Topic | 原因 |
|-------------|-------|-------|------|
| E-BLIND-WORK_RELATION-004 | B | WORK_RELATION | 原文疑似二次整理，非逐字原文 |
| E-BLIND-WORK_ACTOR-004 | B | WORK_ACTOR | 原文疑似二次整理，非逐字原文 |
| E-BLIND-WORK_TYPE-005 | B | WORK_TYPE | 原文疑似二次整理，非逐字原文 |
| E-BLIND-GUEST_HOST-005 | B | GUEST_HOST | 原文疑似二次整理，非逐字原文 |
| E-BLIND-EMPTY_USELESS-006 | B | EMPTY_USELESS | 原文疑似二次整理，非逐字原文 |
| E-BLIND-IMAGE-006 | B | IMAGE | 原文疑似二次整理，非逐字原文 |
| E-BLIND-C-PARTY_CASE-001 | C | POWER_PARTY | 案例原文待核验 |
| E-BLIND-C-IMAGE_CASE-002 | C | IMAGE | 案例原文待核验 |
| E-BLIND-C-YINGQI_CASE-002 | C | YING_QI | 案例原文待核验 |
| E-BLIND-C-WORK_CASE-001 | C | WORK_RELATION | 案例原文待核验 + 修复记录 |

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

#### E-BLIND-C-WORK_CASE-001

**问题**: 静默覆盖历史版本，source/locator/original_text 全部改变。

**修复措施**:
- 创建修复记录文件 `E-BLIND-C-WORK_CASE-001-fix-record.json`
- 记录原始版本信息（第二章 做功案例 / p.50-55）
- 记录当前版本信息（第五章 做功案例 / p.110-115）
- 降级当前版本为 PENDING_VERIFICATION

**修复记录内容**:
```json
{
  "evidence_id": "E-BLIND-C-WORK_CASE-001",
  "fix_type": "PROVENANCE_REPAIR",
  "fix_date": "2026-09-02T...",
  "previous_version": {
    "source": {...},
    "locator": "p.50-55",
    ...
  },
  "current_version": {...},
  "reason": "source/locator/original_text 同时改变，建立审计轨迹",
  "note": "此次修改不符合 Provenance Monotonicity 原则"
}
```

---

### 3. 当前状态

```
总证据数: 74
├── DIRECT/HIGH: 66条
├── PENDING_VERIFICATION: 18条 (8条旧 + 10条新)
└── CASE_EVIDENCE: 15条 (部分待核验)

Layer分布: A=2, B=57, C=15, D=0
Topic覆盖: 13/13 (100%)
```

---

## 后续要求

1. **所有 PENDING_VERIFICATION 证据** 必须进入 Multi-AI Final Verification 队列
2. **不得**将 PENDING_VERIFICATION 证据提升为 DIRECT/HIGH 除非经过独立文献核验
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

---

## 修复历史

| Commit | 日期 | 修复内容 |
|--------|------|----------|
| 34a7879 | 2026-09-02 | 修复 745dc50 的 8 条可疑 Evidence |
| fc3141a | 2026-09-02 | 同步 manifest 统计 |
| (当前) | 2026-09-02 | 修复 211562f 的 10 条新增 Evidence + WORK_CASE-001 修复 |
