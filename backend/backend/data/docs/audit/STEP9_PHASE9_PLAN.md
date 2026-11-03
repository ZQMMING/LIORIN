# Step 9 Phase 9: Golden Path 回归审计

**时间**: 2026-08-31  
**阶段**: Phase 9 Golden Path验证  
**依据**: GPT裁决 9ca275f  
**状态**: 🟢 STARTED

---

## 核心原则

> **不要急着扩充新断言。先把第一批 4 条作为稳定 Golden Path 固化下来。**

---

## 审计目标

### 目标1: Registry → Production Resolver一致性验证
- 验证Registry中的4条APPROVED Judgment与Production Resolver行为完全一致
- 确保Registry修改不会改变已通过的Judgment行为

### 目标2: Golden Path稳定性验证
- 建立4条Judgment的稳定执行路径
- 验证输入→计算的确定性
- 验证输出→溯源的完整性

### 目标3: 基线锁定
- 将当前通过的测试作为Golden Baseline
- 后续任何变更必须通过Golden Path测试

---

## 执行计划

### Phase 9.1: 行为一致性验证
- 对比Registry中4条APPROVED Judgment的字段完整性
- 验证production_resolver.py直接调用Registry的行为
- 验证无Legacy/L4回流

### Phase 9.2: Golden Case测试
- 为每条APPROVED Judgment创建Golden Case（满足/不满足/边界）
- 验证输出的确定性（同一输入→同一输出）
- 验证溯源字段完整性

### Phase 9.3: Baseline锁定
- 创建GOLDEN_BASELINE.md记录当前测试状态
- 记录4条Judgment的Golden Case
- 创建回归测试门禁

---

## 验收标准

```
✅ Registry中4条APPROVED Judgment字段完整且一致
✅ Golden Case输出确定性验证通过
✅ 溯源字段完整性验证通过
✅ 无Legacy/L4回流
✅ 测试1847 passed无回归
```

---

**等待顺天指示开始执行Phase 9.**