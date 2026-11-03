# P0-5.7 工作计划：DTS-SZ-HZ-ZL「生克制化」Primitive 验证

**目标**: 实现"生克制化，须制中有生，生中有制"的 Primitive，只检查关系事实

---

## 一、背景

P0-5.6 完成"日犯岁君"验证，架构闭环跑通：
```
出生四柱 → 流年 → 太岁/岁君 → Canonical Relation → Primitive → Condition → Authorization → Local Judgment
```

下一步：DTS-SZ-HZ-ZL「生克制化」
- 原文："生克制化，须制中有生，生中有制。太过者宜损之，不及者宜益之。"
- **约束**: 只检查关系事实，不碰"太过/不及"（SEMANTIC_ONLY/UNRESOLVED）

---

## 二、语义拆解

### "生克制化"
- 指四柱中存在相生和相克的关系
- 需要检查：
  1. 是否存在相生关系（某五行生另一五行）
  2. 是否存在相克关系（某五行克另一五行）

### "制中有生，生中有制"
- 制 = 相克
- 生 = 相生
- 条件：同时存在相生和相克关系

### "太过者宜损之，不及者宜益之"
- **保持 UNRESOLVED**
- 需要先定义"太过""不及"的确定性标准
- 当前不实现

---

## 三、实现计划

### 1. 定义五行生克关系
```python
GEN_RELATION = {  # 相生
    "WOOD": "FIRE",
    "FIRE": "EARTH",
    "EARTH": "METAL",
    "METAL": "WATER",
    "WATER": "WOOD",
}

KEEPS_RELATION = {  # 相克
    "WOOD": "EARTH",
    "EARTH": "WATER",
    "WATER": "FIRE",
    "FIRE": "METAL",
    "METAL": "WOOD",
}
```

### 2. 检查四柱中的关系
```python
class WuxingRelationChecker:
    @classmethod
    def check_chart(cls, chart) -> dict:
        """检查四柱中的五行生克关系"""
        stems = [chart.year_pillar.heavenly_stem, ...]
        branches = [chart.year_pillar.earthly_branch, ...]
        
        # 提取五行
        elements = [STEM_ELEMENT[s] for s in stems] + [BRANCH_ELEMENT[b] for b in branches]
        
        # 检查相生关系
        has_gen = cls.check_gen_relation(elements)
        
        # 检查相克关系
        has_keeps = cls.check_keeps_relation(elements)
        
        return {
            "has_gen": has_gen,
            "has_keeps": has_keeps,
            "gen_pairs": ...,
            "keeps_pairs": ...,
        }
```

### 3. 定义 Primitive Condition
```python
primitive_condition = {
    "name": "生克制化",
    "feature_name": "wuxing_relations",
    "operator": "all",
    "threshold": {"has_gen": True, "has_keeps": True},
    "status": StateAuthorizationLevel.CLASSICAL_EXPLICIT,
    "source_text": "生克制化，须制中有生，生中有制",
    "classic": "滴天髓",
    "implementation_note": "CURRENT IMPLEMENTATION: 仅检查关系存在性",
    "unresolved_parts": ["太过", "不及", "损之", "益之"],
}
```

### 4. 验证流程
1. 使用 BaziEngine 计算四柱
2. 提取天干地支五行
3. 检查是否存在相生关系
4. 检查是否存在相克关系
5. 输出 Local Judgment

---

## 四、关键约束

### ✅ 必须遵守
- 只检查"关系是否存在"
- 不计算"太过/不及"
- 不引入 strength_score
- 明确标注 CURRENT IMPLEMENTATION

### ❌ 禁止
- 不能包装成完整定义
- 不能引入人为阈值
- 不能接回 strength_engine

---

## 五、验证用例

使用多个命例验证：
- 命例 1: 四柱有相生也有相克 → PASS
- 命例 2: 四柱只有相生没有相克 → FAIL
- 命例 3: 四柱只有相克没有相生 → FAIL

---

**请 GPT 裁决是否批准此计划**
