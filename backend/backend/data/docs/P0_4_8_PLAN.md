# P0-4.8 工作计划：Semantic Feature → Primitive 映射验证

**目标**: 验证三类 Feature 如何安全进入 Primitive，特别保证 SEMANTIC_ONLY 不伪装成确定性计算

---

## 一、背景

P0-4.7 通过，建立了 Semantic Feature Ontology：
- CANONICAL_FEATURE: 已有确定性计算
- DERIVABLE_FEATURE: 需增加计算，但定义可证明
- SEMANTIC_ONLY: 只能保留经典语义，不能硬算

**核心原则**：
> SEMANTIC_ONLY 永远不能伪装成确定性计算事实

---

## 二、验证框架

### A. CANONICAL_FEATURE → Primitive
- 验证现有确定性计算能否直接支持 Primitive
- 示例: de_ling（得令）→ de_ling=True 的 Primitive

### B. DERIVABLE_FEATURE → Primitive
- 验证是否需要增加确定性计算
- 示例: 二三人之气 → 可能需要新的 support_ratio 计算

### C. SEMANTIC_ONLY → Primitive
- 验证是否保持 SEMANTIC_ONLY 状态
- 禁止伪装成确定性计算
- 示例: 畏土之埋 → 保持 SEMANTIC_ONLY，不能写成 wu_element_wang < threshold

---

## 三、测试矩阵

选择真实 Primitive 作为测试样本：

| ID | 原典 | Feature 类型 | 预期状态 |
|----|------|-------------|---------|
| test_001 | 滴天髓_生克制化 | SEMANTIC_ONLY | 禁止伪装 |
| test_002 | 滴天髓_气势 | SEMANTIC_ONLY | 禁止伪装 |
| test_003 | 渊海子平_太岁 | SEMANTIC_ONLY | 禁止伪装 |
| test_004 | （待确认） | CANONICAL_FEATURE | 应可执行 |
| test_005 | （待确认） | DERIVABLE_FEATURE | 需验证定义 |

---

## 四、验证方法

### Phase 1: Feature 类型确认
1. 确认每条 Primitive 的 Feature 类型
2. 检查 Feature 定义是否明确

### Phase 2: Primitive 映射验证
1. CANONICAL_FEATURE → 是否可以直接映射？
2. DERIVABLE_FEATURE → 是否需要新计算？
3. SEMANTIC_ONLY → 是否保持 SEMANTIC_ONLY？

### Phase 3: 安全边界检查
1. SEMANTIC_ONLY 是否被错误地当作确定性计算？
2. 是否有 Feature 定义不明确的情况？
3. 是否有"伪确定性"的判断？

---

## 五、输出物

1. `docs/P0_4_8_MAPPING_VERIFICATION.md` - 验证报告
2. `data/p0_4_8_mapping_result.json` - 验证结果
3. 飞书通知

---

## 六、禁止事项

❌ 不得继续扩大 Feature 数量  
❌ 不得将 SEMANTIC_ONLY 伪装成确定性计算  
❌ 不得为了通过而强行映射  
❌ 不得进入 Composite Judgment

---

## 七、成功标准

✅ CANONICAL_FEATURE 正确映射  
✅ DERIVABLE_FEATURE 明确定义  
✅ SEMANTIC_ONLY 保持保守  
✅ 无"伪确定性"判断

---

**开始执行**
