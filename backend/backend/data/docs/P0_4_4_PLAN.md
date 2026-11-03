# P0-4.4 工作计划：Semantic Type → Executable Rule 映射验证

**目标**: 验证语义类型到可执行规则的映射边界

---

## 一、背景

P0-4.3 通过，建立了 9 种语义类型体系。

但语义分类 ≠ 可执行规则。

需要验证：
- 哪些能算（可执行）
- 哪些只能辨（停留在 Evidence/Semantic 层）
- 哪些必须保持 UNRESOLVED

---

## 二、验证框架

对每条原典，逐条判断：

| 验证项 | 问题 |
|--------|------|
| 语义类型 | FACT/CONDITION/SUFFICIENT/NECESSARY/PREFERENCE/BLOCKING/INFERENCE/COMPOUND/UNKNOWN |
| 结构化表达 | 能否用 Feature/Condition/Judgment 表达 |
| 可执行性 | 能否直接映射到引擎逻辑 |
| 是否需要 Condition | 是否有明确的条件关系 |
| 是否需要 Composite | 是否有多个条件组合 |
| 最终状态 | EXECUTABLE/SEMANTIC_ONLY/UNRESOLVED |

---

## 三、样本选择

目标: 20-30 条真实五经原典

分布（参考 P0-4.3 统计）:
- FACT: ~5 条
- NECESSARY: ~8 条
- BLOCKING: ~5 条
- INFERENCE: ~4 条
- COMPOUND: ~4 条
- PREFERENCE: ~2 条
- UNKNOWN: ~3 条

---

## 四、禁止事项

❌ 不要为了通过率而强行解释  
❌ 不要假设原典有 AND/OR 逻辑  
❌ 不要把倾向/宜忌当作确定性规则  
❌ 不要进入 Composite Judgment

---

## 五、成功标准

✅ 每条原典都有明确的语义类型  
✅ 每条原典都有可执行性判断  
✅ 区分出 EXECUTABLE/SEMANTIC_ONLY/UNRESOLVED  
✅ 验证结果有原文依据  
✅ UNKNOWN 类型保持保守

---

## 六、输出物

1. `docs/P0_4_4_MAPPING_VERIFICATION.md` - 验证报告
2. `data/p0_4_4_mapping_samples.json` - 样本数据
3. 飞书通知

---

**开始执行**
