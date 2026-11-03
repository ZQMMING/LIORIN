# T2 + T3 裁决文档

**日期**: 2026-08-30  
**裁决者**: Gemini  
**Commit**: 待提交

---

## 一、T2 裁决：🟢 基本通过

### 已通过
- 目标链明确：CanonicalState → Evidence → Primitive → verdict
- wang_score 仅历史记录，不再授权最终判断
- D1FeatureResult 新增，隔离完成

### 后续卡点
⚠️ `derive_verdict_from_evidence()` 不能成为新的隐藏评分器

必须逐条绑定：
```
Evidence → Primitive → Condition → Authorization → Verdict
```

否则只是换名字。

---

## 二、T3 裁决：🔴 HOLD

### 当前状态
- 30 条样本：15/30 VERIFIED，15/30 PENDING
- 50% 的 Condition 无法映射到现有 D1FeatureResult

### 重要发现
这个结果**很有价值**：
- 证明五经辨证不是现有几个得令/得地/得势字段简单组合就能完成
- 发现了 Feature Schema 的边界问题

### 不批准
❌ 不批准直接扩充 D1FeatureResult

不能看到 15 条 PENDING，就反过来为了适配它们，随意增加一堆"命理特征"。

---

## 三、T3 正确下一步

### 步骤 1: 15 条 PENDING 归因分类

| 类别 | 含义 | 处理方式 |
|------|------|----------|
| **A** | 现有 Canonical State 已有，只是映射缺失 | 修 Mapping |
| **B** | 需要新增确定性的 Calculation Feature | 允许扩展 D1FeatureResult |
| **C** | 属于 Primitive/Condition 语义，不应塞进 Feature | 保持分离 |
| **D** | 本身需要综合辨证，不能作为 Feature | 交由辨证层处理 |

**只有 B 才允许扩展 D1FeatureResult。**

### 步骤 2: 先修 Mapping
- 对于 A 类，修复 Feature → Primitive 的映射规则
- 对于 C/D 类，确认语义边界

### 步骤 3: 真正缺计算事实才扩 Feature
- 只对 B 类新增字段
- 每个新增字段必须有明确原典授权

### 步骤 4: 重新跑 30 条
- 不要追求"30/30 强行通过"
- 目标是验证 Schema 边界，不是凑通过率

### 步骤 5: 输出分析报告
- A/B/C/D 分类统计
- 每个类别的样例
- 需要扩展的字段清单（仅 B 类）

---

## 四、当前状态总结

| 任务 | 状态 | 下一步 |
|------|------|--------|
| T2 | 🟢 PASS | 等待 derive_verdict_from_evidence() 合规改造 |
| T3 | 🔴 HOLD | 执行 15 条 PENDING 归因分类 |

---

## 五、数据基础

仓库已有：
- `data/p0_3_3_structured_evidence.json` — 385 条证据
- `data/t3_primitive_validation_result.json` — 30 条样本验证结果
- `docs/P0_3_3_STRUCTURED_EVIDENCE_EXTRACTION_REPORT.md` — P0-3.3 报告

**下一步应该解决 Condition 到 Canonical Feature 的语义边界，不是继续堆字段。**

---

**裁决结论**: T2 🟢 PASS, T3 🔴 HOLD（需归因分类后重新执行）
