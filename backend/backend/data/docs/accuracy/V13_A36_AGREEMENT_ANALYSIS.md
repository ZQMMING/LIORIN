# V1.3 A3.6.6 Agreement Analysis Protocol

**日期**: 2026-08-22
**状态**: ✅ FROZEN
**版本**: A3.6.6-v1

---

## 一、一致性指标定义

### 1.1 主要指标

| 指标 | 公式 | 说明 |
|------|------|------|
| **Cohen's κ** | (p_o - p_e) / (1 - p_e) | 分类一致性，去除随机因素 |
| **Weighted κ** | 1 - (Σ w_ij * x_ij) / (Σ w_ij * m_ij) | 有序评分，考虑距离 |
| **Krippendorff's α** | 1 - (D_o / D_e) | 多位评价者 (≥3) |

### 1.2 解释标准

| κ 值 | 一致性等级 | 说明 |
|------|-----------|------|
| < 0.00 | Poor | 低于随机 |
| 0.00-0.20 | Slight | 极低一致性 |
| 0.21-0.40 | Fair | 低一致性 |
| 0.41-0.60 | Moderate | 中等一致性 |
| **0.61-0.80** | **Substantial** | **Oracle 合格** |
| 0.81-1.00 | Almost Perfect | 几乎完美 |

---

## 二、分析流程

### 2.1 分析步骤

```text
Step 1: 收集评分
  ├── 收集 Rater A 评分
  ├── 收集 Rater B 评分
  └── 验证格式符合 schema

Step 2: 计算总体一致性
  ├── Cohen's κ (整体)
  ├── Weighted κ (整体)
  └── 95% CI (Bootstrap)

Step 3: 计算各维度一致性
  ├── 每个维度 κ
  ├── 识别低一致性维度
  └── 分析分歧原因

Step 4: 分歧分析
  ├── Minor (diff=1): 记录
  ├── Major (diff≥2): Adjudicator
  └── Critical (diff=2): 必须 Adjudicator

Step 5: 生成报告
  ├── 一致性表格
  ├── 分歧矩阵
  └── Oracle 资格判定
```

### 2.2 分析工具

```text
使用 Python scipy.stats 或 sklearn:
  ├── cohen_kappa_score (Cohen's κ)
  ├── cohen_kappa_score with weights (Weighted κ)
  └── 自定义 Bootstrap 函数

注意: 分析工具由 Hermes 编写，但评分数据必须来自真实 Rater。
```

---

## 三、Oracle 资格判定

### 3.1 判定标准

```text
κ ≥ 0.60 → QUALIFIED (Oracle 合格)
  └── 可以进入正式 Relational Interpretation 评估

0.40 ≤ κ < 0.60 → CONDITIONAL
  ├── 需要分歧分析
  ├── 可能需要额外培训
  └── 不能作为正式 Oracle

κ < 0.40 → NOT QUALIFIED
  ├── Oracle 不合格
  ├── 需要重新设计 Rubric
  └── 不能用于正式评估
```

### 3.2 判定流程

```text
┌─────────────────┐
│  κ ≥ 0.60?      │
├───┬─────────────┤
│YES│             │NO
│   ▼             │▼
│ QUALIFIED       │ 分歧分析
│                 │  ├── Rubric 修改？
│                 │  ├── Rater 培训？
│                 │  └── 重试？
│                 │
│                 │  κ ≥ 0.60?
│                 │  ├── YES → QUALIFIED
│                 │  └── NO  → NOT QUALIFIED
└─────────────────┘
```

---

## 四、报告格式

### 4.1 必须报告

```text
1. 样本总数
2. 可评维度数 (去除 NOT_EVALUABLE)
3. Cohen's κ (整体 + 95% CI)
4. Weighted κ (整体)
5. 各维度 κ
6. NOT_EVALUABLE 一致性
7. 分歧数量 (Minor / Major / Critical)
8. 分歧原因分析
9. Adjudication 结果
10. Oracle 资格判定
```

### 4.2 禁止报告

```text
❌ "专家平均评分 78%"
❌ 不报告一致性指标
❌ 不报告分歧分析
❌ 不报告 NOT_EVALUABLE 比例
```

---

## 五、当前状态

```text
Agreement Analysis:
  ├── Protocol: ✅ FROZEN
  ├── 数据: ⏳ NOT_AVAILABLE (等待真实 Rater 评分)
  └── 结果: ⏳ PENDING (需要真实评分数据)
```

---

## 六、审计结论

```text
┌─────────────────────────────────────────────────────────────┐
│              A3.6.6 AGREEMENT ANALYSIS                          │
├─────────────────────────────────────────────────────────────┤
│  Status:  ✅ FROZEN (Protocol)                                │
│                                                              │
│  Metrics:                                                    │
│    ✅ Cohen's κ (primary)                                    │
│    ✅ Weighted κ (ordered)                                   │
│    ✅ Krippendorff's α (≥3 raters)                          │
│                                                              │
│  Oracle Qualification:                                       │
│    ✅ κ ≥ 0.60 → QUALIFIED                                  │
│    ✅ 0.40 ≤ κ < 0.60 → CONDITIONAL                         │
│    ✅ κ < 0.40 → NOT QUALIFIED                               │
│                                                              │
│  Current Status:                                             │
│    ⏳ NOT_AVAILABLE (等待真实 Rater 评分数据)                │
│                                                              │
│  Next: A3.6.7 Gate Audit                                     │
└─────────────────────────────────────────────────────────────┘
```

---

**审计签名**: Hermes (Engineering Auditor)
**日期**: 2026-08-22
**版本**: A3.6.6-v1

**重要声明**: 本文档定义了一致性分析协议，但**未执行实际分析**。真正的分析必须在真实 Rater 评分数据提交后进行。