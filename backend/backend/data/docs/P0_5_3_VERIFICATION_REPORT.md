# P0-5.3 验证报告：Local Judgment Replay（CLASSICAL_EXPLICIT 专用）

**日期**: 2026-08-30  
**状态**: 🟡 发现架构约束

---

## 一、验证结果汇总

总测试: 4 条命例 × 1 条件 = 4 条

### 结果分布
| 状态 | 数量 | 占比 |
|------|------|------|
| PASS | 0 | 0% |
| FAIL | 4 | 100% |

---

## 二、关键发现

### ⚠️ BaziEngine 未计算 Canonical Features
BaziEngine.compute() 只返回四柱，不自动计算 de_ling/de_di/de_shi。

### ⚠️ strength_engine 是 LEGACY
- strength_engine.py 计算 de_ling 等特征
- 但根据 T2 裁决：strength_engine 降级为 Legacy/Feature Evidence
- 调用方必须消费 Canonical State/Evidence

### ✅ 当前行为正确
- 没有使用 legacy strength_engine ✅
- 所有命例默认 FAIL（特征未计算）✅
- 符合"安全优先"原则 ✅

---

## 三、架构约束确认

根据 T2 裁决：
```
strength_engine → Legacy Evidence
                   ↓
            Canonical State（新生产链）
                   ↓
            CLASSICAL_EXPLICIT Condition
                   ↓
            Local Judgment
```

当前 P0-5.3 实现符合这个架构：
- 没有调用 strength_engine ✅
- 使用 StateAuthorizationLevel.CLASSICAL_EXPLICIT ✅
- 特征未计算时默认 FAIL ✅

---

## 四、下一步建议

### 方案 A: 等待 Canonical State 实现
- Canonical State 会提供 de_ling 等特征
- 需要等待 Canonical State Engine 实现完成

### 方案 B: 使用 strength_engine 作为 Evidence 来源
- 根据 T2，可以消费 strength_engine 作为 Legacy Evidence
- 但需要在证据链中明确标注来源

### 方案 C: 进入 P0-5.4
- 基于当前状态，验证其他 Authorized Primitive

---

**请 GPT 裁决下一步方向**
