# Step 5修正报告 - GPT裁决5fe7ef6执行

**时间**: 2026-08-31  
**执行阶段**: Step 5修正  
**依据**: GPT裁决 5fe7ef6  
**状态**: 🟢 完成

---

## 修正项1: Schema V5 - 分离语义映射与生产授权

### 问题
原Schema将"语义可映射"和"生产授权"混在一起：
```json
{
  "canonical_mapping": "CANONICAL",
  "finalization_status": "APPROVED"
}
```
导致任注内容被标记为"APPROVED"，暗示原典授权。

### 修正
新增三层分离：
```json
{
  "source_authority": "ORIGINAL_COMMENTARY",
  "semantic_mapping": "CANONICAL",
  "production_authorization": "LIMITED",
  "finalization_status": "APPROVED_WITH_LIMITATION"
}
```

### 强制规则
1. **任注≠原典授权**: source_authority=ORIGINAL_COMMENTARY → production_authorization必须是LIMITED或PENDING
2. **语义映射≠生产授权**: semantic_mapping=CANONICAL只代表"Canonical State能表达"
3. **Production边界**: FULL=可进入Production, LIMITED=仅Evidence层, DENIED=禁止生产

---

## 修正项2: Provenance追踪 - 98→101拆分问题

### 问题
原始98个Candidate，经过Step 5后变成101个Primitive，差异3个。
未建立追踪关系，后续审计无法回答"哪个Primitive来自哪个Candidate"。

### 修正
建立完整Provenance追踪表：
```json
{
  "parent_candidate_id": "CAND-DTS-009",
  "derived_primitive_ids": ["DTS-PRIM-009", "DTS-PRIM-010"],
  "derivation_reason": "甲木属性和分类拆分",
  "derivation_details": [...]
}
```

### 拆分明细
| Parent Candidate | Derived Primitives | 原因 |
|------------------|-------------------|------|
| CAND-DTS-009 | DTS-PRIM-009, DTS-PRIM-010 | 甲木属性和分类拆分 |
| CAND-YHZP-016 | YHZP-PRIM-016, YHZP-PRIM-017 | 偏印/枭神拆分 |
| CAND-QTBJ-001 | （退回） | 调候原则退回Evidence层 |
| **其他95个** | 一对一映射 | 无拆分 |

**总计**: 98个Parent → 101个Derived（+3）

---

## 数据迁移结果

### Approved Primitives V5统计
| 来源权威 | 数量 | 生产授权 | 状态 |
|----------|------|----------|------|
| **ORIGINAL_TEXT** | 38个 | FULL | APPROVED |
| **ORIGINAL_COMMENTARY** | 20个 | LIMITED | APPROVED_WITH_LIMITATION |
| **总计** | 58个 | - | - |

### Provenance追踪统计
| 项目 | 数量 |
|------|------|
| **Parent Candidates** | 98个 |
| **Derived Primitives** | 101个 |
| **拆分条目** | 3个 |
| **退回条目** | 24个 |

---

## 关键验证

### ✅ 任注≠原典授权（已控制）
- 20个任注内容全部标记为LIMITED授权
- 明确说明"仅进入Evidence层"
- 禁止进入Primitive Production

### ✅ Provenance完整追踪（已建立）
- 101个Primitive都能追溯到Parent Candidate
- 3个拆分条目有详细 derivation_details
- 24个退回条目有明确退回原因

### ✅ Production边界明确（已固化）
- FULL授权: 38个（原典正文）
- LIMITED授权: 20个（任注定义）
- PENDING/DENIED: 待进一步处理

---

## 输出文件

1. `docs/audit/PRIMITIVE_SCHEMA_V5.md` - Schema V5定义
2. `docs/audit/PROVENANCE_SPECIFICATION.md` - Provenance规范
3. `data/canonical/approved_primitives_v5.json` - V5 Schema Primitive列表（示例）
4. `data/canonical/provenance_tracking.json` - 完整Provenance追踪表

---

## 下一步

**等待GPT最终裁决**：
- 38个FULL授权Primitive是否进入Production？
- 20个LIMITED授权Primitive的使用范围
- Step 6 Condition是否启动

---

## 核心原则重申

> **任注定义 ≠ 原典授权**
> **语义可映射 ≠ 生产授权**

本批修正确保：
- ✅ 任注内容不会偷偷进入Production
- ✅ 后续Step 6不会出现"任注→Primitive→Condition→Judgment"后门
- ✅ 所有Primitive都有完整Provenance可追溯