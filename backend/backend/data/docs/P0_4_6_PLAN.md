# P0-4.6 工作计划：SEMANTIC_ONLY 逐条证据审计

**目标**: 对 6 条 SEMANTIC_ONLY 做逐条原典上下文审计

---

## 一、背景

P0-4.5 结果：
- 11 条 Condition Graph
- 0 条 EXECUTABLE
- 6 条 SEMANTIC_ONLY（需要审计）
- 5 条 UNRESOLVED（优先级/替代关系问题）

核心问题：
1. **生克制化**：存在必要条件链，但 Feature 映射是否正确？
2. **正月甲木**：代码推成 priority(丙) + alternative(癸)，但原典没有明确说明丙、癸的优先级关系

**绝对不能**：
- 为了 Graph "跑起来"自行规定"丙优先于癸"
- 或"癸可以替代丙"
- 这属于新增命理知识

---

## 二、审计框架

对每条 SEMANTIC_ONLY，逐条检查：

### Phase 1: 原典上下文审计
1. 找到完整上下文（±1000字）
2. 确认原典真正表达的意思
3. 检查前后文是否有其他相关论述

### Phase 2: Feature 映射审计
1. 当前 Feature 引用是什么？
2. Feature 是否在原典中有依据？
3. Feature 映射是否准确？

### Phase 3: 关系类型审计
1. 当前边类型是什么？（prerequisite/blocking/enhancement/alternative/priority）
2. 关系类型是否在原典中明确表达？
3. 还是工程师根据语义推断？

### Phase 4: 授权判断
- **明确授权** → 可以 EXECUTABLE
- **不明确授权** → 保持 SEMANTIC_ONLY

---

## 三、区分层级

### ✅ 原典明确表达（可以授权）
```
prerequisite（须...）
blocking（不可...）
enhancement（得...则...）
```

### ⚠️ 工程师推断（不得自动授权）
```
alternative（或...）
priority（优先...）
```

---

## 四、禁止事项

❌ 不得降低 EXECUTABLE 判定标准  
❌ 不得为了提高通过率补充 priority/alternative/prerequisite  
❌ 不得进入 Composite Judgment  
❌ 不得假设原典有明确逻辑关系

---

## 五、输出物

1. `docs/P0_4_6_EVIDENCE_AUDIT.md` - 逐条审计报告
2. `data/p0_4_6_audit_result.json` - 审计结果数据
3. 飞书通知

---

## 六、6 条待审计样本

| ID | 原文 | 当前状态 | 问题 |
|----|------|---------|------|
| graph_001 | 生克制化，须制中有生... | SEMANTIC_ONLY | Feature映射？ |
| graph_002 | 一行得二三人之气... | SEMANTIC_ONLY | Feature映射？ |
| graph_004 | 辛金软弱，温润而清... | SEMANTIC_ONLY | Feature映射？ |
| graph_005 | 戊己愁逢甲乙... | SEMANTIC_ONLY | Feature映射？ |
| graph_008 | 火炽乘龙，水荡骑虎 | SEMANTIC_ONLY | Feature映射？ |
| graph_009 | 戊土固重，既中且正... | SEMANTIC_ONLY | Feature映射？ |

---

**开始执行**
