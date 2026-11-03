# P0-4.5 工作计划：Condition Graph 验证

**目标**: 验证 Condition Graph 能否忠实表达真实五经复杂条件

---

## 一、背景

P0-4.4 通过，确认了语义类型到可执行规则的边界。

现在需要验证更复杂的条件关系：
```
A成立 → B增强
A成立 → B成立 → C才成立
A成立 但 B出现 → 原结论被制约
A/B/C 不同层级 → 最终语义不同
```

---

## 二、Condition Graph 设计

### 当前简单模型
```
Condition List: [C1, C2, C3]
All Met → Judgment
```

### 目标 Graph 模型
```
Condition Graph: {
  nodes: [C1, C2, C3],
  edges: [
    {from: C1, to: C2, type: "prerequisite"},
    {from: C1, to: C3, type: "blocking"},
    {from: C2, to: C3, type: "enhancement"}
  ]
}
```

### 支持的边类型
| 类型 | 定义 | 示例 |
|------|------|------|
| PREREQUISITE | C1 必须成立，C2 才有意义 | "须从其势" |
| BLOCKING | C1 成立时，C2 被阻断 | "不可犯" |
| ENHANCEMENT | C1 成立时，C2 效果增强 | "得丙癸透，富贵双全" |
| ALTERNATIVE | C1 或 C2 成立均可 | "先丙后癸" |
| PRIORITY | C1 优先级高于 C2 | "丁火为先" |

---

## 三、样本选择

从五经中选择需要多条件的原典：
- 目标: 10-15 条
- 覆盖: PREREQUISITE/BLOCKING/ENHANCEMENT/ALTERNATIVE/PRIORITY
- 禁止: 不为了通过而强行解释

---

## 四、验证方法

对每条原典：
1. 识别所有 Condition
2. 分析 Condition 之间的关系
3. 构建 Condition Graph
4. 判断是否可执行
5. 记录 EXECUTABLE/SEMANTIC_ONLY/UNRESOLVED

---

## 五、输出物

1. `docs/P0_4_5_CONDITION_GRAPH_PLAN.md` - 计划文档
2. `scripts/p0_4_5_condition_graph.py` - 验证脚本
3. `data/p0_4_5_condition_graph_result.json` - 验证结果
4. `docs/P0_4_5_VERIFICATION_REPORT.md` - 验证报告

---

## 六、禁止事项

❌ 不要进入 Composite Judgment  
❌ 不要扩大生产规则数量  
❌ 不要为了通过率而强行解释  
❌ 不要假设原典有 AND/OR 逻辑

---

**开始执行**
