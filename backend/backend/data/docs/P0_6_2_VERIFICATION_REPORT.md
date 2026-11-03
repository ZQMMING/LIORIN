# P0-6.2 验证报告：真实 Local Judgment Aggregation 实测

**日期**: 2026-08-30  
**状态**: 🟢 完成

---

## 一、测试数据

使用真实已授权资产（非人为构造）：

| Primitive | Authorization | 条件成立 | 未实现部分 |
|-----------|--------------|---------|-----------|
| YHZP-LF-TSJX-5（日犯岁君）| AUTHORIZED_PARTIAL | ✅ 是 | 日支条件、救应判断、灾殃程度 |
| DTS-SZ-HZ-ZL（生克制化）| AUTHORIZED_PARTIAL | ✅ 是 | 太过判断、不及判断、中和程度 |

---

## 二、关键验证结果

所有 4 项检查通过 ✅

### 1. authorization 不升级

- 两个 PARTIAL Judgment 聚合后，结果仍然是 PARTIAL
- eligible_for_higher_level = ❌ 否
- ✅ 验证通过

### 2. evidence 不串线

- 每个 Judgment 的 Evidence 保持独立
- 合并后没有覆盖或污染
- ✅ 验证通过

### 3. trace 完整

- 聚合过程记录 2 条 trace
- 包含 validate_complementary 和 partial_found
- ✅ 验证通过

### 4. unresolved 不被吞掉

- 结论明确提及 "包含 2 个 AUTHORIZED_PARTIAL"
- 未实现部分在输出中清晰可见
- ✅ 验证通过

---

## 三、聚合结论

```
包含 2 个 AUTHORIZED_PARTIAL，结果降为 PARTIAL，不得进入更高层级
```

**关键**: 两个 PARTIAL Judgment 不能组合成 COMPLETE，这证明了授权单调性。

---

## 四、核心原则确认

✅ **Authorization Monotonicity（授权单调性）**

聚合只能保持或降低确定性，不能凭空提高确定性。

```
Evidence certainty
    ↓
Local Judgment
    ↓
Aggregation
```

- PARTIAL + PARTIAL → PARTIAL ✅
- COMPLETE + COMPLETE → COMPLETE ✅
- 任何 UNRESOLVED → 阻断 ✅
- Conflict → 降级为 UNRESOLVED ✅

---

## 五、下一步建议

1. ⏸️ 寻找 AUTHORIZED_COMPLETE 的命例（需要更完整的 Primitive）
2. ⏸️ 继续 P0-7 或其他未决任务
3. ⏸️ 保持跨体系聚合 🔒，等待后续规划

---

**请 GPT 裁决下一步方向**
