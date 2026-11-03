# P0-6.4 验证报告：Trace Integration（真实生产路径）

**日期**: 2026-08-31  
**状态**: 🟢 完成

---

## 一、验证方法

使用真实 BaziEngine.compute() 从真实出生输入计算四柱，然后生成完整 Trace。

测试用例：
- 2018-06-01 12:00（甲日见戊年）→ 条件成立 ✅
- 1990-05-15 10:00（庚日见庚年）→ 条件不成立 ✅
- 1985-12-03 14:00（丙日见乙年）→ 条件不成立 ✅

---

## 二、验证结果

总 Trace 记录: 24 条（3 案例 × 8 层）  
ID 唯一性: ✅ (24 total, 24 unique)  
PARTIAL 保留: ✅  
strength_engine 隔离: ✅  
未决事项保留: ✅  
所有案例无问题: ✅  
成功率: 100.0%

---

## 三、Trace 层级结构（每个案例）

```
FINAL_VERDICT (FINAL_-007)
  ↓ AGGREGATION (AGGREG-006)
    ↓ LOCAL_JUDGMENT (LOCAL_-005)
      ↓ CONDITION (CONDIT-004)
        ↓ PRIMITIVE (PRIMIT-003)
          ↓ CANONICAL_FEATURE (CANONI-002)
            ↓ CALCULATION (CALCUL-001)
              ↓ CANONICAL_EVIDENCE (CANONI-000)
```

---

## 四、关键验证点

### ✅ 真实性验证
- 使用真实 BaziEngine.compute() 计算四柱
- 不是手动构造 BaziChart
- 真实输入 → 真实输出 → 真实 Trace

### ✅ 完整性验证
- 每个生产结论都有完整 Trace
- 无孤儿记录
- 无缺失父节点

### ✅ ID 稳定性验证
- 所有记录都有全局唯一 ID
- ID 格式规范（LEVEL-NNN）
- 无重复 ID

### ✅ PARTIAL 保留验证
- 最终 Verdict 保持 PARTIAL
- 未被升级为 COMPLETE
- 不得进入更高层级

### ✅ strength_engine 隔离验证
- Trace 中无 strength_score
- 无 legacy metrics
- 无人为阈值

### ✅ 未决事项保留验证
- 原典未实现部分（日支条件、救应判断、灾殃程度）在 Trace 中清晰可见
- 未被吞掉或忽略

---

## 五、核心原则确认

✅ **Traceability（可追溯性）**
- 从最终结论可追溯到原典 Evidence
- 每一层都有稳定 ID

✅ **Semantic Integrity（语义完整性）**
- 原典语义不被替换
- Evidence 保持一致

✅ **Authorization Monotonicity（授权单调性）**
- PARTIAL 不会升级为 COMPLETE
- 授权等级只能保持或降低

✅ **Production Integrity（生产真实性）**
- 使用真实 BaziEngine 计算
- 不是人工构造 fixture
- 可重复验证

---

## 六、测试数据

三个真实命例的 Trace 数据已保存到：
- `data/p0_6_4_integration.json`

---

## 七、下一步建议

1. ⏸️ P0-6.5：多 Primitive 聚合 Trace 验证
2. ⏸️ P0-7：其他未决任务
3. ⏸️ 保持跨体系聚合 🔒

---

**请 GPT 裁决下一步方向**
