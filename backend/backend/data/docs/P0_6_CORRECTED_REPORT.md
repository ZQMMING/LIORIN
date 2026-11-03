# P0-6 修正报告：Local Judgment Aggregation Contract（三级授权）

**日期**: 2026-08-30  
**状态**: 🟡 修正版验证完成

---

## 一、关键修正

### 1. 三级授权状态

| 状态 | 说明 | 聚合权限 |
|------|------|----------|
| AUTHORIZED_COMPLETE | 完整授权，所有语义已验证 | 可参与任何聚合 |
| AUTHORIZED_PARTIAL | 部分授权，有明确未实现部分 | 只能作为 Evidence，不能进入需要完整语义的聚合 |
| UNRESOLVED | 未决 | 不得产生 Judgment |

### 2. 当前规则授权状态

| Primitive | 授权状态 | 原因 |
|-----------|---------|------|
| YHZP-LF-TSJX-5（日犯岁君）| AUTHORIZED_PARTIAL | 未实现：日支条件、救应判断、灾殃程度 |
| DTS-SZ-HZ-ZL（生克制化）| AUTHORIZED_PARTIAL | 未实现：太过判断、不及判断、中和程度 |

**重要**: 这两个规则都不能作为 AUTHORIZED_COMPLETE 参与完整聚合。

### 3. 删除人工构造的层级案例

原计划中的"得令 → 得地 → 综合身强"层级案例已删除，因为：
- 得地存在 ENGINEERED_THRESHOLD 问题
- 得令 + 得地 → 身强的推导未证明

---

## 二、验证结果

### 测试 Judgment
- 日犯岁君：AUTHORIZED_PARTIAL，judgment=True
- 生克制化：AUTHORIZED_PARTIAL，judgment=True

### 互补组合聚合
- 结论：存在 2 个 AUTHORIZED_PARTIAL Judgment，只能作为 Evidence 输出
- 可进入更高层级：❌ 否

### 证据链聚合
- 结论：证据链包含 0 个 AUTHORIZED_COMPLETE + 2 个 AUTHORIZED_PARTIAL（部分证据）
- 可进入更高层级：❌ 否

### 约束验证
- ✅ 无 UNRESOLVED Judgment
- ✅ 无投票机制
- ✅ 冲突已处理
- ✅ AUTHORIZED_PARTIAL 未升级为完整

---

## 三、冲突处理流程

```
Conflict detected
    ↓
Evidence / scope analysis
    ↓
┌───────────────┬───────────────┐
│  能解决       │  不能解决     │
│    ↓          │    ↓          │
│  RESOLVED     │  DOWNGRADED   │
│               │  → UNRESOLVED │
└───────────────┴───────────────┘
```

**禁止**: 强行裁决、投票解决、停留为 CONFLICTED

---

## 四、下一步

### 需要完成的修正
1. ✅ 增加三级授权状态
2. ✅ 将当前规则标记为 AUTHORIZED_PARTIAL
3. ✅ 删除人工构造的层级案例
4. ✅ 实现冲突降级逻辑
5. ⏸️ 重新做 Golden Validation（需要找到 AUTHORIZED_COMPLETE 的案例）

### Golden Validation 计划
- 寻找或构造满足 AUTHORIZED_COMPLETE 条件的命例
- 验证互补组合和证据链聚合
- 验证冲突降级逻辑

---

**请 GPT 裁决下一步方向**
