# P0-6.5 验证报告：多 Primitive 真实生产聚合 Trace

**日期**: 2026-08-31  
**状态**: 🟢 完成

---

## 一、验证目标

验证多个 Primitive 在同一命例上的独立性和聚合正确性。

关键验证点：
1. 两个 Primitive 不串证据
2. 一个 PARTIAL 不会把另一个升级
3. UNRESOLVED 不被吞掉
4. 多 Primitive 聚合仍遵守授权单调性
5. Trace 能明确区分每条 Primitive 的来源

---

## 二、测试配置

**测试案例**: 2018-06-01 12:00（甲日见戊年）  
**Primitive A**: YHZP-LF-TSJX-5（日犯岁君）  
**Primitive B**: DTS-SZ-HZ-ZL（生克制化）

---

## 三、验证结果

总 Trace 记录: 14 条  
ID 唯一性: ✅ (14 total, 14 unique)  
PARTIAL 保留: ✅  
strength_engine 隔离: ✅  
未决事项保留: ✅  
证据隔离: ✅（无串线）  
完整性: ✅（无缺失父节点、无循环引用）

成功率: 100.0%

---

## 四、Trace 层级结构

```
FINAL_VERDICT (FINAL_-007)
  ↓ AGGREGATION (AGGREG-012)
    ↓ LOCAL_JUDGMENT_A (YHZ_LOCA-005)
      ↓ CONDITION_A (YHZ_COND-004)
        ↓ PRIMITIVE_A (YHZ_PRIM-003)
          ↓ CANONICAL_FEATURE_A (YHZ_CANO-002)
            ↓ CALCULATION_A (YHZ_CALC-001)
              ↓ CANONICAL_EVIDENCE_A (YHZ_CANO-000)
    ↓ LOCAL_JUDGMENT_B (DTS_LOCA-011)
      ↓ CONDITION_B (DTS_COND-010)
        ↓ PRIMITIVE_B (DTS_PRIM-009)
          ↓ CANONICAL_FEATURE_B (DTS_CANO-008)
            ↓ CALCULATION_B (DTS_CALC-007)
              ↓ CANONICAL_EVIDENCE_B (DTS_CANO-006)
```

---

## 五、关键验证点

### ✅ 证据隔离验证
- Primitive A 的 Trace 独立于 Primitive B
- Aggregation 层正确引用了两个 Primitive 的 Local Judgment
- 无跨 Primitive 的证据串线

### ✅ 授权单调性验证
- Primitive A: AUTHORIZED_PARTIAL → 保持 PARTIAL
- Primitive B: AUTHORIZED_PARTIAL → 保持 PARTIAL
- Aggregation: 两个 PARTIAL → PARTIAL（未升级）
- Final Verdict: PARTIAL（不得进入更高层级）

### ✅ 未决事项保留验证
- Primitive A 未实现：日支条件、救应判断、灾殃程度
- Primitive B 未实现：太过判断、不及判断、中和程度
- 所有未决事项在 Trace 中清晰可见

### ✅ strength_engine 隔离验证
- Trace 中无 strength_score
- 无 legacy metrics
- 无人为阈值

---

## 六、核心原则确认

✅ **Traceability（可追溯性）**
- 从最终结论可追溯到两个原典 Evidence
- 每条 Trace 都有明确来源标识

✅ **Evidence Isolation（证据隔离）**
- 不同 Primitive 的证据保持独立
- Aggregation 层正确汇聚而非混合

✅ **Authorization Monotonicity（授权单调性）**
- PARTIAL + PARTIAL → PARTIAL
- 不会因聚合而升级

✅ **Unresolved Preservation（未决事项保留）**
- 所有未实现部分在 Trace 中清晰记录
- 未被吞掉或忽略

---

## 七、测试数据

Trace 数据已保存到：
- `data/p0_6_5_multi_primitive.json`

---

## 八、下一步建议

1. ⏸️ P0-6.6：增加更多 Primitive 组合验证
2. ⏸️ P0-7：其他未决任务
3. ⏸️ 保持跨体系聚合 🔒

---

**请 GPT 裁决下一步方向**
