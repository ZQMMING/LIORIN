# Approved Primitives Schema V5 - 分离语义映射与生产授权

**时间**: 2026-08-31  
**依据**: GPT裁决 5fe7ef6  
**状态**: 🟢 强制执行

---

## 核心修正（GPT裁决明确）

### 问题
```json
{
  "source_authority": "ORIGINAL_COMMENTARY",
  "canonical_mapping": "CANONICAL",
  "finalization_status": "APPROVED"
}
```
**错误**: 任注内容被标记为"APPROVED"，暗示原典授权

### 修正
```json
{
  "source_authority": "COMMENTARY",
  "semantic_mapping": "CANONICAL",
  "production_authorization": "LIMITED",
  "finalization_status": "APPROVED_WITH_LIMITATION"
}
```
**正确**: 明确区分"语义可映射"与"生产授权"

---

## 三层分离定义

### 1. Source Authority（来源权威性）
```
ORIGINAL_TEXT → 原典正文（最高权威）
ORIGINAL_COMMENTARY → 任铁樵注释（次级权威）
LATER_COMMENTARY → 后世解释（最低权威）
```

### 2. Semantic Mapping（语义映射）
```
CANONICAL → Canonical State能准确表达
PARTIAL → 部分可表达
UNRESOLVED → 无法表达
```

### 3. Production Authorization（生产授权）
```
FULL → 完全授权进入Production
LIMITED → 有限授权（仅Evidence层）
PENDING → 待进一步审计
DENIED → 禁止生产
```

---

## 完整Schema V5

```json
{
  "primitive_id": "DTS-PRIM-001",
  "name": "三元",
  "source_book": "滴天髓",
  
  "source_authority": "ORIGINAL_COMMENTARY|ORIGINAL_TEXT|LATER_COMMENTARY",
  "original_text": "",
  "commentary_text": "",
  "later_commentary_text": "",
  "source_location": "通神论·天道篇·任注",
  
  "semantic_mapping": "CANONICAL|PARTIAL|UNRESOLVED",
  "canonical_state_input": ["天干列表"],
  "canonical_state_output": "三元 = 十天干",
  
  "production_authorization": "FULL|LIMITED|PENDING|DENIED",
  "authorization_notes": "任注定义，仅进入Evidence层",
  
  "input_variables": ["天干列表"],
  "output_value": "十天干",
  "relationship_type": "DEFINITION",
  
  "condition_leakage": false,
  "judgment_leakage": false,
  "l4_risk": false,
  "evidence_complete": true,
  
  "finalization_status": "APPROVED|APPROVED_WITH_LIMITATION|REJECTED|BLOCKED",
  "creation_time": "ISO8601",
  "finalized_by": "STEP5_FINALIZATION"
}
```

---

## 强制规则（GPT裁决明确）

### Rule 1: 任注≠原典授权
```
IF source_authority == "ORIGINAL_COMMENTARY":
  → production_authorization 必须为 "LIMITED" 或 "PENDING"
  → 禁止直接标记为 "FULL"
  → authorization_notes 必须说明限制原因
```

### Rule 2: 语义映射≠生产授权
```
IF semantic_mapping == "CANONICAL":
  → 只代表"Canonical State能表达"
  → 不代表"原典授权进入Production"
  → 必须经过production_authorization单独判定
```

### Rule 3: Production边界
```
FULL授权 → 可进入Primitive Production
LIMITED授权 → 仅进入Evidence层
PENDING授权 → 需补充审计
DENIED授权 → 禁止生产
```

---

## 历史数据迁移（58个Approved）

### 迁移规则
```
IF source_authority == "ORIGINAL_COMMENTARY":
  → production_authorization = "LIMITED"
  → finalization_status = "APPROVED_WITH_LIMITATION"
  → authorization_notes = "任注定义，仅进入Evidence层"
  
IF source_authority == "ORIGINAL_TEXT":
  → production_authorization = "FULL"（待定）
  → finalization_status = "APPROVED"
```

### 迁移统计
| 来源权威 | 数量 | 迁移后状态 |
|----------|------|------------|
| **ORIGINAL_TEXT** | 38个 | FULL授权（待定） |
| **ORIGINAL_COMMENTARY** | 20个 | LIMITED授权 |
| **总计** | 58个 | - |

---

## 执行要求

### 所有Worker产出必须遵守V5 Schema
1. 写入前自动校验validate_primitive_v5()
2. 违反规则的Primitive将被拒绝写入
3. 日志记录每次校验结果

### 历史数据迁移
- approved_primitives_v1.json → approved_primitives_v5.json
- 建立parent provenance追踪

---

## 修正历史

### V4 → V5
**修正项**:
- 新增source_authority字段（区分原文/任注/后世）
- 拆分canonical_mapping为semantic_mapping + production_authorization
- 明确任注≠原典授权
- 新增authorization_notes字段
- 强制Rule 1/2/3

**影响**:
- 所有Approved Primitive必须重新评估production_authorization
- 任注内容只能进入Evidence层，不能进入Primitive Production
- 防止Step 6出现"任注→Primitive→Condition→Judgment"的后门