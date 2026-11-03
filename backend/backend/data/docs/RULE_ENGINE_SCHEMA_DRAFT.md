# 五经辨证 Rule Engine Schema 设计草案（修正版）

**版本**: v0.2 Corrected  
**日期**: 2026-08-31  
**阶段**: P0-8.10 M3 Phase 2

---

## ⚠️ 关键修正（基于GPT裁决）

### 修正1: Condition Mapper → Condition Evaluator
```
❌ 错误设计:
Condition Mapper → 直接匹配 → 认为条件成立

✅ 正确设计:
Condition Mapper → Condition Evaluator → 输出 TRUE/FALSE/UNRESOLVED
```

**核心原则**:
- Mapper只是映射工具，不产生判断
- Evaluator才是真正执行验证的组件
- 输入：Canonical State（BaziChart）
- 输出：TRUE / FALSE / UNRESOLVED
- 不能因为"匹配到了"就认为条件成立

---

### 修正2: Composition必须原典授权
```
❌ 错误设计:
统计出3条Primitive → 自动OR组合

✅ 正确设计:
每条Composition必须记录:
- composition_source: 原典来源
- composition_evidence: 原典原文定位
- semantic_relation: 关系类型（AND/OR/SEQUENCE）
- authorization: 原典是否明确授权此组合
```

**关键边界**:
- AND/OR/SEQUENCE是原典语义关系，不是工程推断
- 必须逐条回到原典确认组合逻辑
- 没有原典授权的组合 → UNRESOLVED

---

### 修正3: 经验法则优先级禁止进入生产
```
❌ 错误设计:
冲突 → 检查优先级 → 原典明确优先级？经验法则优先级？

✅ 正确设计:
冲突 → 检查优先级
  ├─ 原典明确优先级 → 可执行
  ├─ 原典没有明确优先级 → UNRESOLVED / 并列输出
  └─ 工程经验 → RESEARCH ONLY（禁止进入生产Resolver）
```

**核心原则**:
- 没有证据授权，就不能成为最终判断
- 经验法则只能用于研究参考
- 不能偷偷把"经验"变成"仲裁器"

---

## 完整Schema架构（修正版）

```
┌─────────────────────────────────────────────────────────┐
│                    Evidence Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │Evidence Span│  │Source Verify│  │Type Filter  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                 Semantic Relation Layer                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │Relation Type│  │Direction   │  │Strength    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                 Primitive Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │Primitive ID │  │Stability   │  │EvidenceCount│    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                 Condition Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │Condition    │  │Condition    │  │Evaluator    │    │
│  │Mapper      │  │Standardize │  │(核心组件)   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                 Judgment Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │Local       │  │Composite    │  │Resolver     │    │
│  │Judgment    │  │Judgment     │  │(无经验法则) │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 组件详细说明（修正版）

### 1. Primitive Registry（稳定）
```json
{
  "primitive_id": "PRIM_001",
  "primitive": "印格喜煞",
  "semantic_type": "成格条件",
  "evidence_count": 3,
  "supporting_assertions": ["PZZQ-GEJU-005-A", ...],
  "stability": "HIGH",
  "source": "PZZQ"
}
```

**当前稳定Primitive**:
- 印格相关: 3条（HIGH稳定性）
- 岁君关系: 4条（HIGH稳定性）
- 建禄月劫格: 3条（HIGH稳定性）
- 食神格: 1条（MEDIUM稳定性）

---

### 2. Condition Mapper（修正：仅映射，不判断）
```json
{
  "condition_id": "COND_001",
  "raw_expression": "印轻逢煞",
  "standardized_condition": "印星力量 < 煞星力量",
  "computable": true,
  "mapping_source": "PZZQ-GEJU-005-A"
}
```

**关键边界**:
- Mapper只做映射和标准化
- 不产生TRUE/FALSE判断
- 不定义阈值（阈值由Evaluator处理）

---

### 3. Condition Evaluator（新增：核心组件）
```json
{
  "evaluator_id": "EVAL_001",
  "condition_id": "COND_001",
  "input": {
    "canonical_state": {
      "day_master": "甲",
      "month_branch": "寅",
      "ten_gods_distribution": {...}
    }
  },
  "evaluation_logic": "印星力量 < 煞星力量",
  "output": "TRUE / FALSE / UNRESOLVED",
  "evaluation_detail": "印星力量=2.5, 煞星力量=3.0, 2.5 < 3.0 → TRUE"
}
```

**关键原则**:
- 输入必须是Canonical State（真实BaziChart）
- 输出必须是TRUE/FALSE/UNRESOLVED
- 必须有明确的计算逻辑
- 不能"匹配到了"就认为成立

---

### 4. Judgment Composite（修正：必须原典授权）
```json
{
  "composite_id": "COMP_001",
  "target_pattern": "建禄月劫格成",
  "composition_type": "OR",
  "components": ["PRIM_008", "PRIM_009", "PRIM_010"],
  "composition_source": "PZZQ-论建禄月劫格",
  "composition_evidence": "建禄月劫，透官而逢财印，透财而逢食伤，透煞而遇制伏，建禄月劫之格成也",
  "semantic_relation": "三条独立成格路径",
  "authorization": "原典明确授权OR组合"
}
```

**关键原则**:
- 必须有composition_source和composition_evidence
- 必须明确语义关系（AND/OR/SEQUENCE）
- 必须原典明确授权，不能工程推断
- 没有原典授权的组合 → UNRESOLVED

---

### 5. Resolver（修正：禁止经验法则）
```json
{
  "resolver_id": "RESOLVER_001",
  "conflict_type": "多Primitive冲突",
  "resolution_method": "原典优先级",
  "priority_source": "PZZQ-论用神成败救应",
  "priority_evidence": "原典明确说明XX优先于YY",
  "fallback": "UNRESOLVED / 并列输出",
  "experience_rules": []  // 空列表，禁止经验法则
}
```

**关键原则**:
- 只接受原典明确优先级
- 没有原典优先级 → UNRESOLVED或并列输出
- 经验法则永远在RESEARCH ONLY区域
- 禁止经验法则进入生产Resolver

---

## 执行流程（修正版）

### 流程1: Assertion生产
```
Step 1: Evidence定位
  ↓
Step 2: Semantic Relation判定
  ↓
Step 3: Primitive提取
  ↓
Step 4: Condition标准化（Mapper，仅映射）
  ↓
Step 5: 执行验证（Evaluator，输出TRUE/FALSE/UNRESOLVED）
  ↓
Step 6: Local Judgment生成
  ↓
Step 7: 四问裁决
  ↓
Step 8: 最终裁决（COMPLETE/REJECT）
```

### 流程2: Canonical State执行
```
Input: BaziChart（Canonical State）
  ↓
Step 1: 提取十神分布
  ↓
Step 2: 匹配Condition Mapper（仅映射，不判断）
  ↓
Step 3: Condition Evaluator执行
  - 输入：Canonical State
  - 输出：TRUE/FALSE/UNRESOLVED
  ↓
Step 4: 触发Primitive逻辑
  - TRUE → 执行Primitive
  - FALSE → 跳过
  - UNRESOLVED → 标记等待人工裁决
  ↓
Step 5: 生成Local Judgment
  ↓
Step 6: Composite Judgment处理（如需）
  - 检查composition_source和authorization
  - 只有原典明确授权的组合才执行
  ↓
Step 7: Resolver处理冲突（如无经验法则）
  ↓
Output: 最终Judgment + 置信度
```

---

## 当前资产验证状态

### 需要验证的条件组合
```
【印格】
- 印轻逢煞 → 印格成
  - 原典: PZZQ-论印绶格
  - 组合类型: 单条Primitive
  - 授权状态: ✅ 已授权

- 官印双全 → 印格成
  - 原典: PZZQ-论印绶格
  - 组合类型: 单条Primitive
  - 授权状态: ✅ 已授权

- 身印两旺而用食伤泄气 → 印格成
  - 原典: PZZQ-论印绶格
  - 组合类型: 单条Primitive
  - 授权状态: ✅ 已授权

【印格整体】
- 三条路径组合类型: 待确认（OR？）
- 需要回到原典确认：是三条独立路径还是单一复合条件？
- 授权状态: ⚠️ 待验证
```

### 不可计算的Condition
```
【需定义阈值】
- "伤官旺" → 需定义力量标准
- "印有根" → 需定义根气标准
- "身强" → 需定义力量阈值（不能复用wang_score）

【处理策略】
- 暂时标记为ENGINEERED_THRESHOLD
- 进入HOLD/RESEARCH队列
- 不进入生产Evalutor
```

---

## 风险与缓解（修正版）

### 风险1: 误把Mapper当Evaluator
- **表现**: 匹配到Condition就认为成立
- **缓解**: 强制要求Evaluator输出TRUE/FALSE/UNRESOLVED
- **检测**: 审计日志中所有Condition必须有Evaluator执行记录

### 风险2: 误把统计当成原典授权
- **表现**: 看到3条Primitive就自动OR组合
- **缓解**: 每条Composition必须有composition_source和authorization
- **检测**: 审计所有Composite Judgment的授权链

### 风险3: 经验法则偷偷进入Resolver
- **表现**: "按照经验，XX应该优先于YY"
- **缓解**: Resolver只接受原典明确优先级，其他全部UNRESOLVED
- **检测**: 审查Resolver的priority_source字段，必须有原典引用

---

## 下一步行动

### 立即执行
1. 更新M2资产，补充每条Assertion的Evaluator实现
2. 对Composite Judgment进行原典授权核查
3. 建立审计日志，追踪所有Condition的Evaluator执行

### 等待裁决
- 是否批准修正后的Schema设计？
- 是否开始实现Condition Evaluator核心组件？
- 是否优先处理不可计算的Condition阈值定义？

---

**状态**: Schema设计v0.2已修正，等待GPT确认后开始实现
