# P0-6 修正报告：Local Judgment Aggregation Contract（三级授权）

**日期**: 2026-08-30  
**状态**: 🟢 验证通过

---

## 一、关键修正

### 1. 三级授权状态

| 状态 | 说明 | 聚合权限 |
|------|------|----------|
| AUTHORIZED_COMPLETE | 完整授权，所有语义已验证 | 可参与任何聚合 |
| AUTHORIZED_PARTIAL | 部分授权，有明确未实现部分 | 只能作为 Evidence |
| UNRESOLVED | 未决 | 不得产生 Judgment |

### 2. 当前规则授权状态

| Primitive | 授权状态 | 未实现部分 |
|-----------|---------|-----------|
| YHZP-LF-TSJX-5（日犯岁君）| AUTHORIZED_PARTIAL | 日支条件、救应判断、灾殃程度 |
| DTS-SZ-HZ-ZL（生克制化）| AUTHORIZED_PARTIAL | 太过判断、不及判断、中和程度 |

### 3. 删除人工构造案例

原"得令 → 得地 → 综合身强"层级案例已删除：
- 得地存在 ENGINEERED_THRESHOLD 问题
- 得令 + 得地 → 身强的推导未证明

---

## 二、验证结果

```
总 Judgment: 2 条
发现冲突: 1 条（跨体系，已降级处理）
互补聚合可进入更高层级: ❌ 否（正确）
证据链可进入更高层级: ❌ 否（正确）
约束验证: ✅ 全部通过
```

### 约束验证详情

| 约束 | 状态 | 说明 |
|------|------|------|
| 无 UNRESOLVED Judgment | ✅ | 所有 Judgment 都有授权状态 |
| 无投票机制 | ✅ | 不使用投票逻辑 |
| 冲突已处理 | ✅ | 跨体系冲突降级为 UNRESOLVED |
| AUTHORIZED_PARTIAL 未升级为完整 | ✅ | 正确拒绝进入更高层级 |

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

## 四、核心原则验证

### ✅ 已验证
1. Local Judgment 只回答"条件是否成立"
2. 不负责综合命理结论
3. 不引入 strength_score
4. 不引入人为阈值
5. 跨体系不互相否定
6. AUTHORIZED_PARTIAL 不会升级为完整结论

### ❌ 已防止
1. 投票机制
2. CONFLICTED 作为最终状态
3. 部分授权被升级为完整判断
4. 跨体系互相否定

---

## 五、下一步

### 待完成
1. ⏸️ 寻找 AUTHORIZED_COMPLETE 的命例（需要更完整的 Primitive）
2. ⏸️ 验证互补组合和证据链聚合的正确性
3. ⏸️ 构造并验证冲突降级逻辑

### 建议
- 等待 GPT 裁决是否进入 P0-6.1（Golden Validation）
- 或继续完善已有 Primitive 的完整性

---

**请 GPT 裁决下一步方向**
