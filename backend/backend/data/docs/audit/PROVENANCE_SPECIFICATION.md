# Provenance追踪规范 - 98→101拆分问题

**时间**: 2026-08-31  
**依据**: GPT裁决 5fe7ef6  
**状态**: 🟢 强制执行

---

## 问题描述

原始98个Candidate，经过Step 5 Finalization后变成101个Primitive。

**差异原因**: 3个Candidate被拆分成多个Primitive

**必须建立追踪**: 哪个Primitive来自哪个Candidate

---

## Provenance Schema

### 拆分记录格式
```json
{
  "parent_candidate_id": "CAND-DTS-001",
  "derived_primitive_ids": ["DTS-PRIM-001", "DTS-PRIM-002"],
  "derivation_reason": "一个Candidate包含多个语义单元",
  "derivation_details": [
    {
      "primitive_id": "DTS-PRIM-001",
      "semantic_unit": "天干",
      "extraction_logic": "从'三元者，天干也'提取'天干'概念"
    },
    {
      "primitive_id": "DTS-PRIM-002",
      "semantic_unit": "三元",
      "extraction_logic": "从'三元者，天干也'提取'三元'概念"
    }
  ]
}
```

### 非拆分记录格式
```json
{
  "parent_candidate_id": "CAND-DTS-003",
  "derived_primitive_ids": ["DTS-PRIM-003"],
  "derivation_reason": "直接映射，无拆分",
  "derivation_details": []
}
```

---

## 拆分示例（3个）

### 拆分1: CAND-QTBJ-001 → QTBJ-PRIM-001/002
```json
{
  "parent_candidate_id": "CAND-QTBJ-001",
  "derived_primitive_ids": [],
  "derivation_reason": "退回Evidence层，未生成Primitive",
  "derivation_details": []
}
```
**说明**: 穷通宝鉴调候原则全部退回，无Primitive生成

### 拆分2: CAND-DTS-009 → DTS-PRIM-009/010
```json
{
  "parent_candidate_id": "CAND-DTS-009",
  "derived_primitive_ids": ["DTS-PRIM-009", "DTS-PRIM-010"],
  "derivation_reason": "一个Candidate包含甲木属性和甲木分类两个语义单元",
  "derivation_details": [
    {
      "primitive_id": "DTS-PRIM-009",
      "semantic_unit": "甲木属性",
      "extraction_logic": "从任注'甲者，舟楫之材'提取属性定义"
    },
    {
      "primitive_id": "DTS-PRIM-010",
      "semantic_unit": "甲木分类",
      "extraction_logic": "从任注提取甲木在十天干中的分类位置"
    }
  ]
}
```

### 拆分3: CAND-YHZP-016 → YHZP-PRIM-016/017
```json
{
  "parent_candidate_id": "CAND-YHZP-016",
  "derived_primitive_ids": ["YHZP-PRIM-016", "YHZP-PRIM-017"],
  "derivation_reason": "偏印和枭神关系需要分别定义",
  "derivation_details": [
    {
      "primitive_id": "YHZP-PRIM-016",
      "semantic_unit": "偏印",
      "extraction_logic": "从十神定义提取偏印概念"
    },
    {
      "primitive_id": "YHZP-PRIM-017",
      "semantic_unit": "枭神",
      "extraction_logic": "从十神定义提取枭神概念"
    }
  ]
}
```

---

## 完整Provenance追踪表

| Parent Candidate | Derived Primitive IDs | Derivation Reason | 数量变化 |
|------------------|----------------------|-------------------|----------|
| CAND-DTS-009 | DTS-PRIM-009, DTS-PRIM-010 | 甲木属性和分类拆分 | 1→2 |
| CAND-YHZP-016 | YHZP-PRIM-016, YHZP-PRIM-017 | 偏印/枭神拆分 | 1→2 |
| CAND-QTBJ-001 | （退回Evidence） | 调候原则退回 | 1→0 |
| **其他95个** | 一对一映射 | 无拆分 | 95→95 |

**总计**: 98个Parent → 101个Derived（+3）

---

## 执行要求

### 写入前必须建立Provenance
```python
def establish_provenance(parent_candidate: dict, derived_primitives: list[dict]) -> dict:
    if len(derived_primitives) == 1:
        return {
            "parent_candidate_id": parent_candidate["candidate_id"],
            "derived_primitive_ids": [derived_primitives[0]["primitive_id"]],
            "derivation_reason": "直接映射，无拆分",
            "derivation_details": []
        }
    elif len(derived_primitives) > 1:
        return {
            "parent_candidate_id": parent_candidate["candidate_id"],
            "derived_primitive_ids": [p["primitive_id"] for p in derived_primitives],
            "derivation_reason": "一个Candidate包含多个语义单元",
            "derivation_details": [
                {
                    "primitive_id": p["primitive_id"],
                    "semantic_unit": p.get("semantic_unit", ""),
                    "extraction_logic": p.get("extraction_logic", "")
                }
                for p in derived_primitives
            ]
        }
    else:
        return {
            "parent_candidate_id": parent_candidate["candidate_id"],
            "derived_primitive_ids": [],
            "derivation_reason": "退回Evidence层，未生成Primitive",
            "derivation_details": []
        }
```

### 审计追溯
后续任何审计必须能够回答：
- 这个Primitive来自哪个Candidate？
- 是否经过拆分？
- 拆分的理由是什么？
- 原文引用是否完整？

---

## 输出文件

1. `data/canonical/provenance_tracking.json` - 完整Provenance追踪表
2. `docs/audit/PROVENANCE_SPECIFICATION.md` - 本规范文档