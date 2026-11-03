# Primitive Registry - 35个Approved Primitive正式注册

**时间**: 2026-08-31  
**阶段**: Step 5完成 → Step 6准备  
**依据**: GPT裁决 e93f74d  
**状态**: 🟢 APPROVED注册

---

## Registry定义

### 什么是Primitive Registry？
> 35个Approved Primitive的正式注册表，作为Condition Extraction的基础。

### Registry结构
```json
{
  "primitive_id": "DTS-PRIM-004",
  "name": "天干阴阳属性",
  "source_book": "滴天髓",
  "source_authority": "ORIGINAL_TEXT",
  "semantic_mapping": "CANONICAL",
  "production_authorization": "FULL",
  "canonical_state_input": ["天干"],
  "canonical_state_output": "阴阳属性",
  "input_variables": ["天干"],
  "output_value": "阴阳分类",
  "relationship_type": "PROPERTY",
  "registry_status": "ACTIVE",
  "registry_time": "ISO8601",
  "provenance": {
    "parent_candidate_id": "CAND-DTS-004",
    "derivation_reason": "直接映射，无拆分"
  }
}
```

---

## 35个Approved Primitive清单

### 滴天髓（12个）
| # | Primitive ID | 名称 | 输入变量 | 输出值 | 关系类型 |
|---|--------------|------|----------|--------|----------|
| 1 | DTS-PRIM-004 | 天干阴阳属性 | 天干 | 阴阳分类 | PROPERTY |
| 2 | DTS-PRIM-006 | 地支动静属性 | 地支 | 动静分类 | PROPERTY |
| 3 | DTS-PRIM-007 | 天干阴阳分类 | 天干 | 阴阳分类 | DEFINITION |
| 4 | DTS-PRIM-008 | 五阳 | 天干列表 | 甲丙戊庚壬 | DEFINITION |
| 5 | DTS-PRIM-009 | 五阴 | 天干列表 | 乙丁己辛癸 | DEFINITION |
| 6 | DTS-PRIM-010 | 丙 | 天干 | 最阳天干 | PROPERTY |
| 7 | DTS-PRIM-011 | 癸 | 天干 | 最阴天干 | PROPERTY |
| 8 | DTS-PRIM-014 | 地支阴阳属性 | 地支 | 阴阳分类 | PROPERTY |
| 9 | DTS-PRIM-015 | 阳支 | 地支列表 | 子寅辰午申戌 | DEFINITION |
| 10 | DTS-PRIM-016 | 阴支 | 地支列表 | 丑卯巳未酉亥 | DEFINITION |
| 11 | DTS-PRIM-017 | 阳支定义 | 地支 | 阳性质地支 | DEFINITION |
| 12 | DTS-PRIM-018 | 阴支定义 | 地支 | 阴性质地支 | DEFINITION |

### 子平真诠（4个）
| # | Primitive ID | 名称 | 输入变量 | 输出值 | 关系类型 |
|---|--------------|------|----------|--------|----------|
| 13 | ZPZQ-PRIM-001 | 月令格 | 月令地支 | 格局类型 | DEFINITION |
| 14 | ZPZQ-PRIM-002 | 月令透干 | 月令+天干 | 透干状态 | PROPERTY |
| 15 | ZPZQ-PRIM-003 | 辅佐用神 | 用神 | 辅佐神 | RELATIONSHIP |
| 16 | ZPZQ-PRIM-007 | 财官印食 | 十神 | 四吉神 | DEFINITION |

**注意**: ZPZQ-PRIM-008（护用之神）、ZPZQ-PRIM-009（八格）未在Claude复核列表中，可能未通过或不在35个范围内。

### 三命通会（20个）
| # | Primitive ID | 名称 | 输入变量 | 输出值 | 关系类型 |
|---|--------------|------|----------|--------|----------|
| 17-36 | SMTH-PRIM-001~020 | 天干地支总论 | 天干/地支 | 属性描述 | DEFINITION |

---

## Registry状态机

### 状态定义
```
INACTIVE → PENDING → ACTIVE → REVOKED
```

### 状态转换规则
1. **INACTIVE → PENDING**: 通过Claude复核，等待GPT裁决
2. **PENDING → ACTIVE**: GPT裁决批准，注册到Registry
3. **ACTIVE → REVOKED**: 发现新证据，撤销授权

---

## 强制规则（GPT裁决明确）

### Rule 1: 禁止直接写进Condition Engine
```
❌ 35 Approved Primitive → Condition Engine
✅ 35 Approved Primitive → Registry → Canonical State Mapping → Condition Extraction
```

### Rule 2: Primitive ≠ Condition
```
Primitive: 天干有阴阳属性（事实描述）
Condition: 若天干为阳 + 月令为春 → 用丙火（条件判断）

禁止从Primitive自动推导Condition
```

### Rule 3: 每个Primitive必须有Provenance
```
每个Primitive必须能追溯到：
- Parent Candidate ID
- Original Text引用
- Claude复核结果
- GPT裁决记录
```

---

## 输出文件

### 1. Primitive Registry数据
```
data/canonical/primitive_registry.json
```

### 2. Registry文档
```
docs/audit/PRIMITIVE_REGISTRY.md
```

### 3. Step 6准备文档
```
docs/audit/STEP6_CONDITION_EXTRACTION_PLAN.md
```

---

## 下一步

### Phase 1: 建立Registry（当前）
- 注册35个Approved Primitive
- 建立Provenance追踪
- 设置ACTIVE状态

### Phase 2: Canonical State Mapping
- 验证每个Primitive能否被Canonical State准确表示
- 验证输入/输出变量是否明确
- 验证无隐含Condition/Judgment

### Phase 3: Schema/Provenance Validation
- 验证Registry Schema完整性
- 验证Provenance链路完整
- 验证无缺失字段

### Phase 4: Condition Extraction（待GPT裁决）
- 基于Registry中的Primitive
- 提取Condition（严格限制）
- 等待GPT裁决批准

---

## 核心原则重申

> **Primitive → Condition 是"辨规律"的开始**
> 
> 从这里开始比Primitive层更严格
> 
> 因为要回答："原典说的这个事实，在什么条件下成立？"

**当前状态**:
- ✅ 35个Primitive注册完成
- ⏳ Canonical State Mapping待验证
- 🔴 Condition Extraction禁止（等Registry稳定后）