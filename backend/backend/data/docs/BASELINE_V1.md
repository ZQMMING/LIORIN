# BASELINE_V1 — 冻结验证基线

**冻结日期**: 2026-08-22  
**commit**: 034d0b2 (V-FROZEN-2026-09-01)  
**状态**: **FROZEN** — 禁止修改

---

## 数据集规格

```
dataset: golden_v1
cases: 50
events: 518
source_types: historical (30), modern (15), mingli-bench (5)
evidence_grades: A (84), B (434)
year_range: 155-2074
severity_distribution: {3: 224, 4: 237, 5: 57}
category_distribution: {EXAM: 125, CHILD_BIRTH: 80, PARENT_DEATH: 80, JOB_CHANGE: 76, PROMOTION: 76, FAMILY_CHANGE: 39, NEW_RELATIONSHIP: 30, MAJOR_INCOME: 5, RELOCATION: 5, RESIGNATION: 2}
```

## 验证结果（禁止修改以提高分数）

```
prediction_engine: SimpleBaziRuleEngine (EXAM/PROMOTION/FAMILY_CHANGE only)
time_tolerance: ±2 years
matching_method: exact_category + year_window

Precision:    4.23%
Recall:       2.51%
F1:           3.15%
Predictions:  307
Actual:       518
Matched:      13
```

## 测试覆盖

```
total_tests: 791
passed: 791
skipped: 1
status: ALL_GREEN
```

---

## 冻结约束

1. **禁止修改 golden_cases.json** — 数据集是基准
2. **禁止修改 scoring 函数** — 评分标准是基准
3. **禁止修改 Golden Dataset 添加/删除案例** — 保持50 cases, 518 events
4. **禁止为提升分数而调整时间窗口** — ±2年固定
5. **只允许修改预测引擎和诊断层** — 用于分析问题

---

## 基准用途

BASELINE_V1 用于：
1. 诊断算法缺陷（V1.1 Failure Analysis）
2. 比较不同预测引擎的增量贡献（消融实验）
3. 验证架构改进是否带来真实提升
4. 建立可复现的科学验证链路

---

**此文件是项目里程碑，修改需经过用户确认。**
