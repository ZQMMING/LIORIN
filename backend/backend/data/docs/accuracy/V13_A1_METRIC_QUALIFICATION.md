# V1.3 A1 — Metric Qualification

**日期**: 2026-08-22
**类型**: READ-ONLY AUDIT
**状态**: FINAL

---

## 原则声明

本文档定义每个 Component 的合格指标，确保指标与 Oracle 类型匹配。
禁止修改任何测试或算法。

---

## 一、指标类型定义

```text
METRIC TYPE DEFINITIONS:

1. EXACT_MATCH (O1 Only)
   ├── 定义: 预测值 == 期望值
   ├── 计算: 1 if pred == expected else 0
   ├── 适用: 干支、卦象、历法计算
   └── 阈值: 100% (不允许误差)

2. ACCURACY (O1+O2)
   ├── 定义: 正确预测比例
   ├── 计算: correct / total
   ├── 适用: 事件预测 (短期窗口)
   └── 阈值: ≥ 0.50 (随机基线 0.33)

3. PRECISION (O2 Only)
   ├── 定义: TP / (TP + FP)
   ├── 适用: 事件类型分类
   └── 阈值: ≥ 0.40

4. RECALL (O2 Only)
   ├── 定义: TP / (TP + FN)
   ├── 适用: 事件检出率
   └── 阈值: ≥ 0.40

5. MICRO-F1 (O2 Primary)
   ├── 定义: 2 * (Precision * Recall) / (Precision + Recall)
   ├── 适用: 多分类事件预测
   └── 阈值: ≥ 0.45 (V1.2 G5 Gate)

6. MACRO-F1 (O2 Secondary)
   ├── 定义: 每类 F1 的平均值
   ├── 适用: 类别不平衡场景
   └── 阈值: ≥ 0.30

7. CLASSICAL_ALIGNMENT (O3 Only)
   ├── 定义: 与经典原文的一致性比率
   ├── 计算: matched_rules / total_rules
   ├── 适用: 河洛/黄历规则验证
   └── 阈值: ≥ 0.80

8. EVIDENCE_CLOSURE_RATE (O3 Only)
   ├── 定义: 有完整证据链的声称比例
   ├── 计算: closed_chains / total_claims
   ├── 适用: 证据链验证
   └── 阈值: ≥ 0.90

9. INTER-RATER_AGREEMENT (O4 Only)
   ├── 定义: 专家间一致性
   ├── 计算: Cohen's Kappa / Fleiss' Kappa
   ├── 适用: Yi 解释质量评级
   └── 阈值: κ ≥ 0.60 (substantial agreement)
```

---

## 二、Component → Metric Mapping

### 2.1 Bazi Engine

| Component | Oracle | 合格指标 | 当前实现 | 状态 |
|-----------|--------|---------|---------|------|
| BAZI-02 四柱计算 | O1+O2 | Exact Match (O1) + Micro-F1 (O2) | fate-bench 96.7% | ✅ |
| BAZI-03~06 映射 | O1 | Exact Match | 100% | ✅ |
| BAZI-09 大运 | O1+O3 | Classical Alignment | 未标准化 | ⚠️ |
| BAZI-10 十神 | O1 | Exact Match | 100% | ✅ |

### 2.2 Heluo Engine

| Component | Oracle | 合格指标 | 当前实现 | 状态 |
|-----------|--------|---------|---------|------|
| HELUO-01~08 取数/归一化 | O1 | Exact Match | 100% | ✅ |
| HELUO-09~11 先天/元堂 | O1+O3 | Exact Match + Classical Alignment | 纪晓岚案例 100% | ✅ |
| HELUO-12 后天换卦 | O1+O3 | Exact Match + Classical Alignment | 两步法已验证 | ✅ |
| HELUO-13~15 流年/月/日 | O1+O2 | Micro-F1 | **未实现** | ❌ |
| HELUO-16~17 节候/卦气 | O1 | Exact Match | 100% | ✅ |
| HELUO-25 大运 | O1+O3 | Classical Alignment | 流派差异 | ⚠️ |
| HELUO-27 解释 | O3+O4 | Inter-Rater Agreement | **未实现** | ❌ |

### 2.3 Ziwei Engine

| Component | Oracle | 合格指标 | 当前实现 | 状态 |
|-----------|--------|---------|---------|------|
| ZW-03~10 排盘 | O1 | Exact Match | Stub 模式 | ⚠️ |
| ZW-03 主引擎 | O2 | Micro-F1 | fate-bench 交叉 | ⚠️ 未直接测试 |

### 2.4 Huangli Engine

| Component | Oracle | 合格指标 | 当前实现 | 状态 |
|-----------|--------|---------|---------|------|
| HL-01~06 历法 | O1 | Exact Match | 继承 sxtwl | ✅ |
| HL-07~10 规则 | O3 | Classical Alignment | **未系统验证** | ❌ |

### 2.5 Yi Engine

| Component | Oracle | 合格指标 | 当前实现 | 状态 |
|-----------|--------|---------|---------|------|
| YI-02~03 经典文本 | O3 | Exact Match | 100% | ✅ |
| YI-04~08 卦象规则 | O1 | Exact Match | 100% | ✅ |
| YI-11~12 爻位/承乘 | O1 | Exact Match | 100% | ✅ |
| YI-01/09/13 解释 | O4 | Inter-Rater Agreement | **未实现** | ❌ |

---

## 三、指标覆盖统计

```text
                    EXACT_MATCH | ACCURACY | MICRO-F1 | CLASSICAL_AL | IRR-AGR | 合计
Bazi                3           | 1        | 0        | 1            | 0       | 5
Heluo               6           | 0        | 1        | 3            | 0       | 10
Ziwei               1           | 0        | 0        | 0            | 0       | 1
Huangli             1           | 0        | 0        | 1            | 0       | 2
Yi                  3           | 0        | 0        | 0            | 1       | 4
─────────────────────────────────────────────────────────────────────
Total               14          | 1        | 1        | 5            | 1       | 22
```

### 已实现指标 (Current Implementation)

```text
✅ EXACT_MATCH: 14 components (64%)
✅ MICRO-F1: 1 component (5%) — BAZI-02 via fate-bench
✅ CLASSICAL_ALIGNMENT: 5 components (23%) — HELUO rule validation
⚠️ INTER-RATER_AGREEMENT: 0 components (0%) — Yi 解释层未实现
❌ ACCURACY/PRECISION/RECALL: 0 components — 历史盲测未实现
```

---

## 四、指标阈值达标情况

### 4.1 达标组件 (Pass)

| Component | Metric | 当前值 | 阈值 | 状态 |
|-----------|--------|--------|------|------|
| BAZI-02 四柱 | Micro-F1 | 96.7% | ≥ 50% | ✅ PASS |
| BAZI-03~06 映射 | Exact Match | 100% | 100% | ✅ PASS |
| BAZI-10 十神 | Exact Match | 100% | 100% | ✅ PASS |
| HELUO-01~08 取数/归一化 | Exact Match | 100% | 100% | ✅ PASS |
| HELUO-09~12 卦象 | Exact Match | 100% | 100% | ✅ PASS |
| HELUO-16~17 节候/卦气 | Exact Match | 100% | 100% | ✅ PASS |

### 4.2 未达标组件 (Fail/Not Implemented)

| Component | Metric | 当前值 | 阈值 | 状态 |
|-----------|--------|--------|------|------|
| HELUO-13~15 流年/月/日 | Micro-F1 | N/A | ≥ 50% | ❌ NOT_IMPLEMENTED |
| HELUO-27 解释 | IRR-AGR | N/A | κ ≥ 0.60 | ❌ NOT_IMPLEMENTED |
| YI-01/09/13 解释 | IRR-AGR | N/A | κ ≥ 0.60 | ❌ NOT_IMPLEMENTED |
| HL-07~10 规则 | Classical Alignment | N/A | ≥ 80% | ❌ NOT_IMPLEMENTED |

---

## 五、指标缺口分析

### 5.1 关键缺口 (P0)

| 缺口 | 影响 | 解决方案 | 预估工时 |
|------|------|---------|---------|
| 流年/流月/流日 Micro-F1 | HELUO-13~15 | A2: 建立历史盲测数据集 | 3天 |
| Yi 解释 Inter-Rater Agreement | YI-01/09/13 | A3: 建立专家评级体系 | 1周 |
| 黄历规则 Classical Alignment | HL-07~10 | A4: 经典原文对照 | 2天 |

### 5.2 次要缺口 (P1)

| 缺口 | 影响 | 解决方案 | 预估工时 |
|------|------|---------|---------|
| Ziwei 排盘独立验证 | ZW-03~10 | A2: 引入独立紫微库交叉 | 1天 |
| 大运流派一致性 | BAZI-09, HELUO-25 | A3: 建立流派差异文档 | 1天 |

---

## 六、Metric Qualification 决策

```text
QUALIFICATION CRITERIA:
├── Metric Type 必须与 Oracle 类型匹配
├── 阈值必须基于先验标准 (非测试结果反推)
├── 所有 O1 组件必须达到 100% Exact Match
├── 所有 O2 组件必须达到 Micro-F1 ≥ 0.50
├── 所有 O3 组件必须达到 Classical Alignment ≥ 0.80
└── O4 组件无法自动化，需标注为 NOT_EVALUABLE

CURRENT STATUS:
├── O1 覆盖率: 85% 已通过 (14/14 Exact Match)
├── O2 覆盖率: 5% 已实现 (1/20 Micro-F1)
├── O3 覆盖率: 30% 已实现 (5/20 Classical Alignment)
├── O4 覆盖率: 0% 未实现 (0/3 Inter-Rater Agreement)
└── OX 覆盖率: 6% (8/138 组件不可验证)
```

---

**报告结束**
**下一步**: A1.8 Accuracy Eligibility
