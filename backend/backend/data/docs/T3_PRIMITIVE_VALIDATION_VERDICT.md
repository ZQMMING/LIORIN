# T3 裁决文档：Primitive 小闭环验证

**日期**: 2026-08-30  
**状态**: 🟡 PENDING GEMINI VERDICT  
**Commit**: 待提交

---

## 一、验证目标

选取 30 条真实五经证据样本，验证链路：
```
Evidence → Primitive → Condition → Local Judgment → Authorization
```

**约束**：不能直接扩大 `infer_verdict()`，必须证明每条 verdict 的完整授权链条。

---

## 二、样本选取

从 `data/p0_3_3_structured_evidence.json`（385 条）中选取：
- 覆盖 5 大经典（滴天髓/渊海子平/穷通宝鉴/三命通会/子平真诠）
- 覆盖 4 大 domain（wangshuai/pattern/climate/ten_god）
- 混合有条件（83条）和无条件证据
- 覆盖 primitive/composite/local 三种 scope

**最终样本**: 30 条

---

## 三、验证结果

| 指标 | 数值 |
|------|------|
| 总样本 | 30 |
| 通过 (VERIFIED) | 15 (50%) |
| 失败 (INVALID) | 0 |
| 待定 (PENDING) | 15 (50%) |
| 部分通过 (PARTIAL) | 0 |

---

## 四、问题分析

### 4.1 通过原因（VERIFIED）
- 无条件证据：原典授权明确，无需额外验证
- 有条件证据：所有条件可映射到 `D1FeatureResult` 字段

### 4.2 待定原因（PENDING）
- 条件无法映射到现有特征字段
- 需要扩展 `D1FeatureResult` 或定义新的特征提取逻辑

---

## 五、核心卡点

⚠️ **Condition → Feature 映射缺失**

当前验证发现：
- 50% 的证据有条件，但无法直接映射到 `D1FeatureResult`
- 需要定义 `Condition.feature_ref` → `D1FeatureResult` 字段的映射规则
- 或者扩展 `D1FeatureResult` 以支持更细粒度的特征提取

---

## 六、下一步建议

1. **明确映射规则**：定义哪些 Condition 类型可以映射到哪些 Feature 字段
2. **扩展 Feature Schema**：考虑是否需要新增特征字段（如得令权重细节、通根质量分布等）
3. **重新验证待定项**：根据映射规则重新评估 PENDING 项
4. **等待 Gemini 裁决**：确认是否需要调整验证策略

---

## 七、文件清单

- `data/p0_3_3_structured_evidence.json` — 原始 385 条证据
- `data/t3_primitive_validation_result.json` — 30 条样本验证结果
- `scripts/t3_primitive_validation.py` — 验证脚本
- `docs/T3_PLAN.md` — T3 执行计划

---

**裁决结论**: 🟡 PENDING GEMINI VERDICT

请 Gemini 裁决以下问题：
1. 50% 通过率是否可接受？
2. 待定项的处理策略？
3. 是否需要调整验证标准？
