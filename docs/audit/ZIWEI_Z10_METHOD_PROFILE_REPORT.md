# ZIWEI Z10 METHOD PROFILE REPORT
**日期**: 2026-09-04  
**Gate**: Z10 — ZiweiMethodProfile 方法论契约

---

## 一、交付物

| 文件 | 行数 | 说明 |
|------|------|------|
| `src/tongshu/engines/ziwei_method_profile.py` | ~280 | 方法论契约定义 |
| `tests/test_ziwei_method_profile.py` | ~240 | 24 项测试 |

---

## 二、核心设计

### 数据结构

```
MethodId         → 流派标识 (sanhe/zhongzhou/feixing/qintian)
RuleType         → 规则类型 (pattern/sihua/palace/interaction/cycle)
ConfidenceLevel  → 置信度 (high/medium/low/unknown)
EvidenceRef      → 证据引用 (rule_id, source_work, source_chapter, status)
RuleSpec         → 规则规格 (condition + operation + confidence)
ZiweiMethodProfile → 流派契约基类（抽象）
```

### 流派对比

| 特性 | 三合派 | 中州派 | 飞星派 | 钦天门 |
|------|--------|--------|--------|--------|
| 四化表 | classic | zhongzhou | classic | classic |
| 戊干科星 | 右弼 | **太阳** | 右弼 | 右弼 |
| 自化 | ✗ | ✗ | ✓ | ✓ |
| 立极宫 | ✗ | ✗ | ✗ | ✓ |
| 流昌流曲 | ✗ | ✓ | ✗ | ✗ |
| 小限 | ✓ | ✓ | ✗ | ✓ |
| 空宫策略 | partial | **full** | partial | partial |
| 状态 | 完整 | 完整 | 完整 | DRAFT |

### 关键设计决策

1. **四化表隔离**：`SIHUA_TABLE_CLASSIC` vs `SIHUA_TABLE_ZHONGZHOU`，`sihua_differs()` 函数可检测差异
2. **禁止法投票**：各派独立运行，无 CrossAnalyzer/CONFLICTED/ALIGNED 概念
3. **MethodId 绑定**：所有 RuleSpec 带 method_id，无 method_id=ALL
4. **派别隔离测试**：修改某派特征不影响其他派
5. **钦天门占位**：METHOD_ID=QINTIAN，features 标记 DRAFT，待 Hermes 完成经典资料后充实

---

## 三、测试结果

```
tests/test_ziwei_method_profile.py  →  24 passed
tests/test_ziwei_engine.py          →  15 passed
tests/test_ziwei_chart_cross_validate.py → 4 passed (32 subtests)
tests/test_ziwei_phase_a0_extended.py      → 45 passed
tests/spec/test_vertical_slice_ziwei.py    → 13 passed
────────────────────────────────────────────────
TOTAL                                       →  101 passed, 32 subtests
```

---

## 四、架构位置

```
src/tongshu/engines/
├── ziwei_engine.py              ← Calculation（计算层）
│   └── FrozenZiweiChart         ← Z2 契约
├── ziwei_method_profile.py      ← Z10 方法论层（新增）
│   ├── ZiweiMethodProfile       ← 抽象基类
│   ├── SanheProfile             ← 三合派
│   ├── ZhongzhouProfile         ← 中州派
│   ├── FeixingProfile           ← 飞星派
│   └── QintianProfile           ← 钦天门（DRAFT）
└── ziwei/
    └── evidence_producer.py     ← Evidence 层（消费 FrozenZiweiChart）
```

**计算层不动方法论层**，方法论层不动计算层。
FrozenZiweiChart 是中间契约，两个层次通过它对接。

---

## 五、下一步

- **Z11**：建立 `PalaceResolutionLayer`（取宫/立极/借星/三方四正）
- **Z12**：三合派 RuleGraph 实现（使用 SanheProfile）
- **Z13**：飞星派 RuleGraph 实现（使用 FeixingProfile）
- **Z14**：同盘异法验收（同一 FrozenZiweiChart → 三派独立输出）

---

**状态**: ✅ 完成
