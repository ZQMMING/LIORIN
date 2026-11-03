# P0-5.6 工作计划：日犯岁君 Local Judgment Replay（CURRENT IMPLEMENTATION）

**目标**: 验证"日犯岁君"的 Local Judgment，但明确标注为 CURRENT IMPLEMENTATION

---

## 一、背景

P0-5.5 语义取证结论：
- "岁君" = "太岁" = 年柱（年干+年支）
- "犯"包含多种关系（日干克年干、日支克年支、运克岁君等）
- 当前只能验证"日干克年干"这一种关系

**关键约束**：
> 不能把"日干克年干"作为永久定义
> 只能称为 CURRENT IMPLEMENTATION
> 不能称为 CLASSICAL COMPLETE DEFINITION

---

## 二、实现计划

### 1. 定义 Canonical Year State
```python
class CanonicalYearState:
    """岁君的 Canonical 表示"""
    year_stem: str  # 年干
    year_branch: str  # 年支
    year_element: str  # 年干五行
    canonical_name: str = "岁君"  # 或 "太岁"
```

### 2. 定义日干/岁君 Relation
```python
class DayMasterVsYearRelation:
    """日干与岁君的关系"""
    relation_type: str  # "克" / "被克" / "生" / "被生" / "同"
    is_fan_sui_jun: bool  # 是否犯岁君
    evidence: str  # 原典证据
```

### 3. 实现 Primitive Condition
```python
primitive_condition = {
    "name": "日犯岁君",
    "feature_name": "day_master_vs_year",
    "operator": "==",
    "threshold": True,
    "status": StateAuthorizationLevel.CLASSICAL_EXPLICIT,
    "source_text": "日犯岁君，灾殃必重；五行有救，其年反必招财",
    "classic": "渊海子平",
    "implementation_note": "CURRENT IMPLEMENTATION: 仅检查日干克年干",
    "missing_relations": ["日支克年支", "运克岁君", "岁运冲刑"],
}
```

### 4. 验证流程
1. 使用 BaziEngine 计算四柱
2. 提取日干和年干
3. 检查日干是否克年干（当前实现）
4. 输出 Local Judgment
5. 明确标注为 CURRENT IMPLEMENTATION

---

## 三、验证用例

使用已知命例验证：
- 甲日见戊年：日干甲木克年干戊土 → 犯岁君 ✅
- 其他命例：日干不克年干 → 不犯岁君 ✅

---

## 四、关键约束

### ✅ 必须遵守
- 明确标注 CURRENT IMPLEMENTATION
- 不声称 CLASSICAL COMPLETE DEFINITION
- 列出缺失的关系类型
- 不接回 strength_engine

### ❌ 禁止
- 不能把"日干克年干"包装成完整定义
- 不能隐藏"岁君=年柱"的复杂性
- 不能引入 strength_engine

---

**请 GPT 裁决是否批准此计划**
