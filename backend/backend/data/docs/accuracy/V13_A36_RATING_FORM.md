# V1.3 A3.6.5 Rating Form — Schema Only

**日期**: 2026-08-22
**状态**: ✅ FROZEN
**版本**: A3.6.5-v1

---

## 一、数据结构定义

### 1.1 rating_schema.json

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Expert Rating Form",
  "description": "Relational Interpretation Evaluation Schema",
  "version": "A3.6.5-v1",

  "type": "object",
  "required": ["rater_id", "sample_id", "timestamp", "scores"],
  
  "properties": {
    "rater_id": {
      "type": "string",
      "pattern": "^RATER_\\d{3}$",
      "description": "Rater 唯一标识"
    },
    "sample_id": {
      "type": "string",
      "pattern": "^SAMPLE_\\d{3}$",
      "description": "样本唯一标识"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "评分时间 (ISO 8601)"
    },
    
    "scores": {
      "type": "object",
      "required": ["state", "opportunity", "risk", "remediation", "action", "temporal", "evidence"],
      "properties": {
        "state": {
          "$ref": "#/definitions/dimension_score"
        },
        "opportunity": {
          "$ref": "#/definitions/dimension_score"
        },
        "risk": {
          "$ref": "#/definitions/dimension_score"
        },
        "remediation": {
          "$ref": "#/definitions/dimension_score"
        },
        "action": {
          "$ref": "#/definitions/dimension_score"
        },
        "temporal": {
          "$ref": "#/definitions/dimension_score"
        },
        "evidence": {
          "$ref": "#/definitions/dimension_score"
        }
      }
    },
    
    "evaluable_dimensions": {
      "type": "integer",
      "minimum": 0,
      "maximum": 7,
      "description": "可评维度数 (7 - NOT_EVALUABLE 数)"
    },
    
    "total_score": {
      "type": "integer",
      "minimum": 0,
      "maximum": 14,
      "description": "总分 (仅可评维度)"
    },
    
    "normalized_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 100,
      "description": "归一化评分 (总分 / (可评维度 × 2) × 100)"
    },
    
    "comments": {
      "type": "string",
      "maxLength": 2000,
      "description": "评分说明"
    }
  },

  "definitions": {
    "dimension_score": {
      "type": "object",
      "required": ["status"],
      "properties": {
        "status": {
          "type": "string",
          "enum": ["SCORED", "NOT_EVALUABLE"]
        },
        "score": {
          "type": "integer",
          "minimum": 0,
          "maximum": 2,
          "description": "评分 (仅当 status=SCORED 时)"
        },
        "not_evaluable_reason": {
          "type": "string",
          "enum": ["INSUFFICIENT_EVIDENCE", "AMBIGUOUS", "NOT_APPLICABLE", "MISSING"],
          "description": "不可评原因 (仅当 status=NOT_EVALUABLE 时)"
        },
        "reason": {
          "type": "string",
          "maxLength": 500,
          "description": "评分理由"
        }
      }
    }
  }
}
```

---

## 二、评分示例

### 2.1 完整评分示例

```json
{
  "rater_id": "RATER_001",
  "sample_id": "SAMPLE_001",
  "timestamp": "2026-08-22T10:00:00Z",
  "scores": {
    "state": {
      "status": "SCORED",
      "score": 2,
      "reason": "准确引用卦名和体用关系"
    },
    "opportunity": {
      "status": "SCORED",
      "score": 1,
      "reason": "识别机会但缺乏经典依据"
    },
    "risk": {
      "status": "SCORED",
      "score": 2,
      "reason": "识别风险，符合体用关系"
    },
    "remediation": {
      "status": "NOT_EVALUABLE",
      "not_evaluable_reason": "MISSING",
      "reason": "系统未输出化解建议"
    },
    "action": {
      "status": "SCORED",
      "score": 1,
      "reason": "建议可操作但与 STATE 关联不强"
    },
    "temporal": {
      "status": "SCORED",
      "score": 2,
      "reason": "正确映射流日状态"
    },
    "evidence": {
      "status": "SCORED",
      "score": 1,
      "reason": "有引用但不够具体"
    }
  },
  "evaluable_dimensions": 6,
  "total_score": 9,
  "normalized_score": 75.0,
  "comments": "整体质量中等，STATE 和 RISK 准确，但 REMEDIATION 缺失。"
}
```

---

## 三、评分约束

### 3.1 合规检查

```text
✅ 所有 7 维度必须评分或标记 NOT_EVALUABLE
✅ SCORED 维度必须提供 score (0-2)
✅ NOT_EVALUABLE 必须提供 reason
✅ 每个维度必须提供 reason (文字说明)
✅ 必须提供 overall comments
```

### 3.2 禁止

```text
❌ 预填评分（当前文件为 schema only）
❌ 使用 AI / LLM 生成评分
❌ 修改已提交评分
❌ 跳过维度（不评分也不标记）
```

---

## 四、当前状态

```text
Rating Form:
  ├── 数据结构: ✅ FROZEN
  ├── 预填评分: ❌ 无 (schema only)
  ├── 生成方式: 需要真实 Rater 手动填写
  └── 文件: dataset/accuracy/expert_pilot/rating_schema.json
```

---

## 五、审计结论

```text
┌─────────────────────────────────────────────────────────────┐
│                  A3.6.5 RATING FORM                            │
├─────────────────────────────────────────────────────────────┤
│  Status:  ✅ FROZEN (Schema Only)                            │
│                                                              │
│  Structure:                                                  │
│    ✅ 7 维度评分 (SCORED / NOT_EVALUABLE)                   │
│    ✅ 评分理由 (文字说明)                                    │
│    ✅ 总分 + 归一化评分                                      │
│    ✅ JSON Schema 验证                                       │
│                                                              │
│  Current Status:                                             │
│    ⏳ NO RATINGS (等待真实独立评价者填写)                    │
│                                                              │
│  Next: A3.6.6 Agreement Analysis                             │
└─────────────────────────────────────────────────────────────┘
```

---

**审计签名**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A3.6.5-v1

**重要声明**: 本文档定义了评分数据结构，但**不包含任何预填评分**。所有评分必须由真实独立 Rater 在盲评协议下填写。