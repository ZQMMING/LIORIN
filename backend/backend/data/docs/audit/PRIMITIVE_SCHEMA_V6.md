# Approved Primitives Schema V6 - PENDING状态修正

**时间**: 2026-08-31  
**依据**: GPT裁决 9521999  
**状态**: 🟢 强制执行

---

## 核心修正（GPT裁决明确）

### 问题
原Schema存在逻辑冲突：
```json
{
  "source_authority": "ORIGINAL_TEXT",
  "production_authorization": "FULL",
  "finalization_status": "APPROVED"
}
```
**错误**: FULL还"待定"，但finalization_status已经是"APPROVED"

### 修正
```json
{
  "source_authority": "ORIGINAL_TEXT",
  "production_authorization": "PENDING",
  "finalization_status": "PENDING_AUDIT"
}
```
**正确**: 等待GPT最终裁决后才变成FULL+APPROVED

---

## 完整状态机定义

### production_authorization枚举
```
PENDING → 等待GPT裁决
FULL → GPT裁决批准后
LIMITED → 任注内容，仅Evidence层
DENIED → 禁止生产
```

### finalization_status枚举
```
PENDING_AUDIT → 等待Claude复核（ORIGINAL_TEXT）
APPROVED_WITH_LIMITATION → 任注内容，Evidence层
APPROVED → GPT裁决批准（FULL授权）
REJECTED → 退回Evidence层
BLOCKED → L4风险，禁止生产
```

---

## 三层状态对应关系

| source_authority | production_authorization | finalization_status | 说明 |
|------------------|-------------------------|---------------------|------|
| **ORIGINAL_TEXT** | PENDING | PENDING_AUDIT | 等待GPT裁决 |
| **ORIGINAL_TEXT** | FULL | APPROVED | GPT裁决批准 |
| **ORIGINAL_COMMENTARY** | LIMITED | APPROVED_WITH_LIMITATION | Evidence层 |
| **LATER_COMMENTARY** | DENIED | REJECTED | 禁止生产 |
| **任意** | DENIED | BLOCKED | L4风险 |

---

## 强制规则（GPT裁决明确）

### Rule 1: ORIGINAL_TEXT不能直接APPROVED
```
IF source_authority == "ORIGINAL_TEXT":
  → production_authorization 必须先为 "PENDING"
  → finalization_status 必须先为 "PENDING_AUDIT"
  → 禁止直接标记为 "FULL" + "APPROVED"
```

### Rule 2: GPT裁决后才升级状态
```
IF GPT裁决批准:
  → production_authorization: PENDING → FULL
  → finalization_status: PENDING_AUDIT → APPROVED
  
IF GPT裁决拒绝:
  → production_authorization: PENDING → DENIED
  → finalization_status: PENDING_AUDIT → REJECTED
```

### Rule 3: 任注保持LIMITED
```
IF source_authority == "ORIGINAL_COMMENTARY":
  → production_authorization 必须为 "LIMITED"
  → finalization_status 必须为 "APPROVED_WITH_LIMITATION"
  → 禁止升级为 "FULL"
```

---

## 数据迁移（38个ORIGINAL_TEXT）

### 迁移规则
```
IF source_authority == "ORIGINAL_TEXT":
  → production_authorization = "PENDING"（原FULL）
  → finalization_status = "PENDING_AUDIT"（原APPROVED）
  → authorization_notes = "等待GPT最终裁决"
```

### 迁移统计
| 原状态 | 新状态 | 数量 |
|--------|--------|------|
| FULL + APPROVED | PENDING + PENDING_AUDIT | 38个 |
| LIMITED + APPROVED_WITH_LIMITATION | 不变 | 20个 |
| **总计** | - | **58个** |

---

## 修正后的状态命名

### ❌ 错误命名（误导）
```
"58 Approved Primitives"
```
**问题**: 暗示58个都已授权生产

### ✅ 正确命名（准确）
```
"38 PENDING Audit + 20 LIMITED Evidence"
```
**说明**: 
- 38个ORIGINAL_TEXT等待GPT裁决
- 20个ORIGINAL_COMMENTARY仅Evidence层
- 真正FULL Production = 0个

---

## 完整Schema V6

```json
{
  "primitive_id": "DTS-PRIM-001",
  "name": "三元",
  "source_book": "滴天髓",
  
  "source_authority": "ORIGINAL_TEXT|ORIGINAL_COMMENTARY|LATER_COMMENTARY",
  "original_text": "",
  "commentary_text": "",
  "later_commentary_text": "",
  "source_location": "...",
  
  "semantic_mapping": "CANONICAL|PARTIAL|UNRESOLVED",
  "canonical_state_input": [],
  "canonical_state_output": "",
  
  "production_authorization": "PENDING|FULL|LIMITED|DENIED",
  "authorization_notes": "...",
  
  "input_variables": [],
  "output_value": "",
  "relationship_type": "DEFINITION|PROPERTY|RELATIONSHIP",
  
  "condition_leakage": false,
  "judgment_leakage": false,
  "l4_risk": false,
  "evidence_complete": true,
  
  "finalization_status": "PENDING_AUDIT|APPROVED|APPROVED_WITH_LIMITATION|REJECTED|BLOCKED",
  "creation_time": "ISO8601",
  "finalized_by": "STEP5_FINALIZATION",
  
  "parent_candidate_id": "CAND-XXX",
  "derivation_reason": "..."
}
```

---

## 执行要求

### 所有Worker产出必须遵守V6 Schema
1. 写入前自动校验validate_primitive_v6()
2. 违反规则的Primitive将被拒绝写入
3. 日志记录每次校验结果

### 历史数据迁移
- approved_primitives_v5.json → approved_primitives_v6.json
- 38个ORIGINAL_TEXT状态降级为PENDING

---

## 修正历史

### V5 → V6
**修正项**:
- 修正ORIGINAL_TEXT的production_authorization从FULL改为PENDING
- 修正finalization_status从APPROVED改为PENDING_AUDIT
- 明确GPT裁决后才升级状态
- 纠正"58 Approved Primitives"的错误命名

**影响**:
- 38个ORIGINAL_TEXT条目状态降级
- 防止Step 6误用未授权Primitive
- 明确Production边界

---

## 下一步

### Claude独立复核（38个ORIGINAL_TEXT）
- 逐条验证原典是否真正授权
- 验证Semantic Mapping是否正确
- 验证无Condition/Judgment泄露

### Claude通过后
- 提交GPT裁决
- GPT批准后升级为FULL+APPROVED
- 才能进入Step 6 Condition

### 当前状态
- **38个PENDING**: 等待Claude复核 + GPT裁决
- **20个LIMITED**: Evidence层，禁止进入Production
- **真正FULL Production**: 0个