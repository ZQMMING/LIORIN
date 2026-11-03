# Candidate Pool Schema V4.0 - MAPPING_CANDIDATE定义

**时间**: 2026-08-31  
**依据**: GPT裁决 1be4978  
**状态**: 🟢 强制执行

---

## 核心修正：canonical_mapping枚举值

### V3.0（错误）
```json
{
  "canonical_mapping": "CANONICAL"
}
```
**问题**: 暗示"原典授权通过"

### V4.0（正确）
```json
{
  "canonical_mapping": "MAPPING_CANDIDATE"
}
```
**含义**: "目前可以映射到Canonical State的候选，不代表原典授权"

---

## 完整枚举值

```json
{
  "canonical_mapping": "MAPPING_CANDIDATE|PARTIAL_CANDIDATE|UNRESOLVED_CANDIDATE"
}
```

| 值 | 含义 | 生产状态 |
|----|------|----------|
| **MAPPING_CANDIDATE** | 可映射候选 | 待Claude审计 |
| **PARTIAL_CANDIDATE** | 部分可映射 | 需补充定义 |
| **UNRESOLVED_CANDIDATE** | 未解决 | 禁止生产 |

---

## audit_status枚举

```json
{
  "audit_status": "PENDING|APPROVED|DENIED|BLOCKED"
}
```

| 值 | 含义 |
|----|------|
| **PENDING** | 待审查 |
| **APPROVED** | 审计通过 |
| **DENIED** | 审计拒绝 |
| **BLOCKED** | 明确禁止（UNRESOLVED自动BLOCKED）|

---

## 完整Schema V4

```json
{
  "candidate_id": "CAND-{BOOK}-{SEQ}",
  "source_book": "滴天髓|子平真诠|穷通宝鉴|三命通会|渊海子平",
  "text_layer": "ORIGINAL_TEXT|ORIGINAL_COMMENTARY|LATER_COMMENTARY",
  
  "original_text": "",
  "commentary_text": "",
  "later_commentary_text": "",
  
  "source_location": "章节位置",
  "semantic_unit": "提取的语义单元",
  "primitive_candidate": "候选Primitive名称",
  
  "canonical_mapping": "MAPPING_CANDIDATE|PARTIAL_CANDIDATE|UNRESOLVED_CANDIDATE",
  
  "confidence": "HIGH|MEDIUM|LOW",
  "unresolved_questions": [],
  "agent_id": "WORKER-{BOOK}",
  "creation_time": "ISO8601",
  "red_team_flags": [],
  
  "audit_status": "PENDING|APPROVED|DENIED|BLOCKED",
  
  "production_blocked_reason": ""
}
```

---

## 强制规则

### Rule 1: MAPPING_CANDIDATE不等于生产授权
```
IF canonical_mapping == "MAPPING_CANDIDATE":
  → audit_status 必须为 PENDING（等待审计）
  → 禁止直接标记为 APPROVED
  → 必须经过Claude独立审计
```

### Rule 2: UNRESOLVED自动BLOCKED
```
IF canonical_mapping == "UNRESOLVED_CANDIDATE":
  → audit_status 必须为 BLOCKED
  → production_blocked_reason 必须有值
  → 禁止进入Production
```

### Rule 3: 任注≠原典授权
```
IF text_layer == "ORIGINAL_COMMENTARY":
  → 必须明确标注为"任注解释"
  → 不能暗示"原典授权"
  → Claude审计重点验证
```

---

## 验证脚本

```python
def validate_candidate_v4(candidate: dict) -> list[str]:
    errors = []
    
    # Rule 1: MAPPING_CANDIDATE不能自动APPROVED
    if candidate.get("canonical_mapping") == "MAPPING_CANDIDATE":
        if candidate.get("audit_status") == "APPROVED":
            errors.append("MAPPING_CANDIDATE cannot be APPROVED without Claude audit")
    
    # Rule 2: UNRESOLVED必须BLOCKED
    if candidate.get("canonical_mapping") == "UNRESOLVED_CANDIDATE":
        if candidate.get("audit_status") != "BLOCKED":
            errors.append("UNRESOLVED_CANDIDATE must have audit_status=BLOCKED")
        if not candidate.get("production_blocked_reason"):
            errors.append("UNRESOLVED_CANDIDATE must have production_blocked_reason")
    
    # Rule 3: 任注必须明确标注
    if candidate.get("text_layer") == "ORIGINAL_COMMENTARY":
        if "任注" not in candidate.get("source_location", ""):
            errors.append("ORIGINAL_COMMENTARY should have '任注' in source_location")
    
    return errors
```

---

## 执行要求

### 所有Worker产出必须遵守V4 Schema
1. 写入前自动校验validate_candidate_v4()
2. 违反规则的Candidate将被拒绝写入
3. 日志记录每次校验结果

### 历史数据迁移
- CAND-DTS-001~025: MAPPING_CANDIDATE（原CANONICAL）
- CAND-ZPZQ-001~020: MAPPING_CANDIDATE（原CANONICAL）
- 其他同理

---

## 修正历史

### V3.0 → V4.0
**修正项**:
- 新增MAPPING_CANDIDATE枚举值
- 删除CANONICAL（避免误解）
- 明确任注≠原典授权
- 新增validate_candidate_v4()脚本
- 强制Rule 1/2/3

**影响**:
- 所有Worker产出必须使用新Schema
- 历史数据需要迁移（MAPPING_CANDIDATE替代CANONICAL）
- Claude审计必须重点验证任注内容