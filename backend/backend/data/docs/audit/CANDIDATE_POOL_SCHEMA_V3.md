# Candidate Schema V3 - 自动校验规则

**时间**: 2026-08-31  
**依据**: GPT裁决 6fd2910  
**状态**: 🟢 强制执行

---

## 三字段一致性校验

### 规则定义

```
IF text_layer == "ORIGINAL_TEXT":
  → original_text 必须有值
  → commentary_text 必须为空
  → later_commentary_text 必须为空
  → source_location 不能包含"任注"或"注"字样
  
IF text_layer == "ORIGINAL_COMMENTARY":
  → original_text 必须为空
  → commentary_text 必须有值
  → later_commentary_text 必须为空
  → source_location 必须包含"任注"或"注"字样
  
IF text_layer == "LATER_COMMENTARY":
  → original_text 必须为空
  → commentary_text 必须为空
  → later_commentary_text 必须有值
  → source_location 必须包含后世学者姓名或年代
```

### 错误示例（已修正）

❌ **错误1**: CAND-DTS-007（原版本）
```json
{
  "text_layer": "ORIGINAL_TEXT",
  "original_text": "阳干者，甲丙戊庚壬也；阴干者，乙丁己辛癸也。",
  "source_location": "通神论·天干篇·任注"
}
```
**问题**: text_layer=ORIGINAL_TEXT，但source_location包含"任注"，矛盾！

✅ **修正**: CAND-DTS-007（现版本）
```json
{
  "text_layer": "ORIGINAL_TEXT",
  "original_text": "阳干者，甲丙戊庚壬也；阴干者，乙丁己辛癸也。",
  "source_location": "通神论·天干篇"
}
```
**验证**: text_layer=ORIGINAL_TEXT，source_location无"注"字样，一致✅

---

## UNRESOLVED候选处理

### 规则定义

```
IF canonical_mapping == "UNRESOLVED":
  → audit_status 必须为 "BLOCKED" 或 "PENDING"
  → 必须包含 unresolved_questions 数组
  → 必须包含 production_blocked_reason 字段
  → red_team_flags 应包含相关风险标记
```

### 示例（已修正）

✅ **CAND-DTS-005**: "五阳从气不从势"
```json
{
  "canonical_mapping": "UNRESOLVED",
  "audit_status": "BLOCKED",
  "red_team_flags": ["CONDITION_RISK", "L4_RISK", "UNRESOLVED_DEFINITION"],
  "production_blocked_reason": "气/势未定义，涉及L4力量问题，禁止进入Primitive Production",
  "unresolved_questions": ["气的定义不明确", "势的定义不明确", "是否涉及L4力量问题"]
}
```
**验证**: 明确标记BLOCKED，禁止进入生产✅

---

## 自动校验脚本

```python
def validate_candidate(candidate: dict) -> list[str]:
    errors = []
    
    # Rule 1: text_layer与内容字段一致性
    text_layer = candidate.get("text_layer")
    original_text = candidate.get("original_text", "")
    commentary_text = candidate.get("commentary_text", "")
    later_commentary_text = candidate.get("later_commentary_text", "")
    source_location = candidate.get("source_location", "")
    
    if text_layer == "ORIGINAL_TEXT":
        if not original_text:
            errors.append("ORIGINAL_TEXT requires original_text to have value")
        if commentary_text or later_commentary_text:
            errors.append("ORIGINAL_TEXT: other fields must be empty")
        if "注" in source_location:
            errors.append("ORIGINAL_TEXT: source_location should not contain '注'")
    
    elif text_layer == "ORIGINAL_COMMENTARY":
        if not commentary_text:
            errors.append("ORIGINAL_COMMENTARY requires commentary_text to have value")
        if original_text or later_commentary_text:
            errors.append("ORIGINAL_COMMENTARY: other fields must be empty")
        if "注" not in source_location:
            errors.append("ORIGINAL_COMMENTARY: source_location should contain '注'")
    
    elif text_layer == "LATER_COMMENTARY":
        if not later_commentary_text:
            errors.append("LATER_COMMENTARY requires later_commentary_text to have value")
        if original_text or commentary_text:
            errors.append("LATER_COMMENTARY: other fields must be empty")
    
    # Rule 2: UNRESOLVED候选必须标记BLOCKED
    if candidate.get("canonical_mapping") == "UNRESOLVED":
        if candidate.get("audit_status") not in ["BLOCKED", "PENDING"]:
            errors.append("UNRESOLVED candidate must have audit_status=BLOCKED or PENDING")
        if not candidate.get("production_blocked_reason"):
            errors.append("UNRESOLVED candidate must have production_blocked_reason")
    
    return errors
```

---

## 校验结果

### CAND-DTS-001 ~ 008 校验状态

| Candidate | text_layer | 内容字段 | source_location | 一致性 | 状态 |
|-----------|------------|----------|-----------------|--------|------|
| CAND-DTS-001 | ORIGINAL_COMMENTARY | commentary_text ✅ | ...任注 ✅ | ✅ | PASS |
| CAND-DTS-002 | ORIGINAL_COMMENTARY | commentary_text ✅ | ...任注 ✅ | ✅ | PASS |
| CAND-DTS-003 | ORIGINAL_COMMENTARY | commentary_text ✅ | ...任注 ✅ | ✅ | PASS |
| CAND-DTS-004 | ORIGINAL_TEXT | original_text ✅ | 通神论·天干篇 ✅ | ✅ | PASS |
| CAND-DTS-005 | ORIGINAL_TEXT | original_text ✅ | 通神论·天干篇 ✅ | ✅ | BLOCKED |
| CAND-DTS-006 | ORIGINAL_TEXT | original_text ✅ | 通神论·地支篇 ✅ | ✅ | PASS |
| CAND-DTS-007 | ORIGINAL_TEXT | original_text ✅ | 通神论·天干篇 ✅ | ✅ | PASS（已修正）|
| CAND-DTS-008 | ORIGINAL_COMMENTARY | commentary_text ✅ | ...任注 ✅ | ✅ | PASS |

**校验通过率**: 8/8 = 100%

---

## 执行要求

### 后续所有Worker产出必须经过此校验

1. **写入前自动校验**：每个Candidate写入Candidate Pool前必须通过validate_candidate()
2. **失败拦截**：校验失败直接拒绝写入，返回具体错误信息
3. **日志记录**：每次校验结果记录到audit_log
4. **定期审查**：每天运行一次全量校验，确保数据质量

---

## 修正历史

### V2.0 → V3.0
**修正项**：
- 新增三字段一致性校验规则
- 新增UNRESOLVED候选必须标记BLOCKED规则
- 修正CAND-DTS-007 source_location矛盾
- 新增CAND-DTS-005 production_blocked_reason字段
- 新增自动校验脚本

**影响**：
- 所有Worker产出必须遵守此Schema
- 违反规则的Candidate将被拒绝写入