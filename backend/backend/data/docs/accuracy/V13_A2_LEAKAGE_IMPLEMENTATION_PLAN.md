# V1.3 A2.4 — Leakage Implementation Plan

**日期**: 2026-08-22
**类型**: READ-ONLY AUDIT
**状态**: FINAL

---

## 原则声明

本文档定义 12 种泄漏类型的检测与分类策略。
禁止修改任何代码或数据集。

---

## 一、泄漏类型清单

```text
LEAKAGE TYPE CLASSIFICATION:
├── L01: target-event leakage
├── L02: future-biography leakage
├── L03: source-publication leakage
├── L04: derived-feature leakage
├── L05: duplicate-case leakage
├── L06: cross-dataset leakage
├── L07: oracle contamination
├── L08: manual-label leakage
├── L09: rule-selection leakage
├── L10: temporal-boundary leakage
├── L11: benchmark contamination
└── L12: retrospective wording leakage
```

---

## 二、各类型详细定义与检测

### 2.1 L01: Target-Event Leakage

```text
定义: 预测过程中直接包含目标事件信息
场景: 模型在生成预测时能看到目标事件
检测: 检查 input_context 是否包含 target_event_date 之后的信息
风险等级: CRITICAL
```

**检测规则**:
```python
if input_context.max_date >= target_event_date:
    classify_as("L01", "CONTAMINATED")
else:
    classify_as("L01", "CLEAN")
```

### 2.2 L02: Future-Biography Leakage

```text
定义: 使用事件发生后的传记资料作为输入
场景: 传记在 1900 年撰写，但包含 1950 年的信息
检测: 比较 source_publication_date 与 event_date
风险等级: HIGH
```

**检测规则**:
```python
if source_publication_date > event_date:
    # 传记发布时间晚于事件时间，检查是否包含未来信息
    if contains_future_biography(source_text, event_date):
        classify_as("L02", "CONTAMINATED")
    else:
        classify_as("L02", "REVIEWED")
else:
    classify_as("L02", "CLEAN")
```

### 2.3 L03: Source-Publication Leakage

```text
定义: 数据源发布时已知事件结果，导致模型被动学习
场景: 某命理网站在 2020 年发布"历史人物命运分析"，内含结果
检测: 比较 data_access_date 与 event_date
风险等级: HIGH
```

**检测规则**:
```python
if data_access_date > event_date + threshold_days:
    # 数据访问时事件已发生很久，存在回顾性偏差
    classify_as("L03", "REVIEWED")
else:
    classify_as("L03", "CLEAN")
```

### 2.4 L04: Derived-Feature Leakage

```text
定义: 从目标事件反向推导出的特征泄露到输入
场景: 从"此人中年得志"反推其八字格局
检测: 检查 features 是否与 target_event 强相关
风险等级: MEDIUM
```

**检测规则**:
```python
for feature in input_features:
    if feature_derived_from(target_event, feature_engine):
        classify_as("L04", "CONTAMINATED")
        break
else:
    classify_as("L04", "CLEAN")
```

### 2.5 L05: Duplicate-Case Leakage

```text
定义: 同一案例出现在训练/校准和测试集中
场景: fate-bench 中的案例同时出现在 BLIND 和 CALIBRATION
检测: 计算案例相似度，检查 ID 重叠
风险等级: HIGH
```

**检测规则**:
```python
def check_duplicates(cases_a, cases_b):
    a_ids = {c.person_id for c in cases_a}
    b_ids = {c.person_id for c in cases_b}
    overlap = a_ids & b_ids
    if overlap:
        return "DUPLICATE"
    return "CLEAN"
```

### 2.6 L06: Cross-Dataset Leakage

```text
定义: 不同数据集之间共享敏感信息
场景: fate-bench 和 BaziQA 有大量重叠案例
检测: 跨数据集 ID 比对
风险等级: HIGH
```

**检测规则**:
```python
def check_cross_leakage(dataset_a, dataset_b):
    ids_a = set(dataset_a.person_ids)
    ids_b = set(dataset_b.person_ids)
    return len(ids_a & ids_b) > 0
```

### 2.7 L07: Oracle Contamination

```text
定义: 测试 Oracle 与被测算法同源
场景: 用 sxtwl 验证 BaziEngine (共享依赖)
检测: 检查 Oracle 实现是否依赖被测系统
风险等级: MEDIUM
```

**检测规则**:
```python
def check_oracle_contamination(test_oracle, target_algorithm):
    oracle_impl = get_implementation(test_oracle)
    if shares_dependency(oracle_impl, target_algorithm):
        return "CONTAMINATED"
    return "CLEAN"
```

### 2.8 L08: Manual-Label Leakage

```text
定义: 人工标记过程中引入目标信息
场景: 标注员知道目标事件，在标记时无意中泄露
检测: 检查标注过程是否双盲
风险等级: MEDIUM
```

**检测规则**:
```python
if annotation_process.is_single_blind:
    classify_as("L08", "REVIEWED")
elif annotation_process.is_double_blind:
    classify_as("L08", "CLEAN")
else:
    classify_as("L08", "UNKNOWN")
```

### 2.9 L09: Rule-Selection Leakage

```text
定义: 规则选择过程参考了测试集结果
场景: 根据 BLIND 结果调整规则权重
检测: 检查规则选择日志
风险等级: HIGH
```

**检测规则**:
```python
if rule_selection_timestamp > blind_dataset_lock_timestamp:
    classify_as("L09", "CONTAMINATED")
else:
    classify_as("L09", "CLEAN")
```

### 2.10 L10: Temporal-Boundary Leakage

```text
定义: 预测时间窗口跨越事件边界
场景: 预测 1900 年事件时使用了 1905 年的信息
检测: 检查 prediction_window 与 event_date 关系
风险等级: HIGH
```

**检测规则**:
```python
if prediction_window.end_date > event_date:
    classify_as("L10", "CONTAMINATED")
else:
    classify_as("L10", "CLEAN")
```

### 2.11 L11: Benchmark Contamination

```text
定义: 测试集来自已知 benchmark，模型可能见过
场景: fate-bench 是公开 benchmark，模型训练可能包含
检测: 检查 benchmark 公开时间 vs 模型训练时间
风险等级: MEDIUM
```

**检测规则**:
```python
if benchmark_public_date < model_training_start_date:
    classify_as("L11", "REVIEWED")
else:
    classify_as("L11", "CLEAN")
```

### 2.12 L12: Retrospective Wording Leakage

```text
定义: 数据来源使用回顾性措辞泄露结果
场景: "据说此人命中注定大富大贵" — 事后诸葛亮
检测: 分析 source_text 中的回顾性措辞
风险等级: MEDIUM
```

**检测规则**:
```python
retrospective_markers = ["据说", "注定", "命中", "果然", "果然应验"]
for marker in retrospective_markers:
    if marker in source_text:
        classify_as("L12", "REVIEWED")
        break
else:
    classify_as("L12", "CLEAN")
```

---

## 三、泄漏分类决策矩阵

| L01-L12 | 检测条件 | 分类 | 处理方式 |
|---------|---------|------|---------|
| L01 | input_context 包含 target_event | CONTAMINATED | 禁止使用 |
| L02 | source_pub > event_date + 未来信息 | REVIEWED/CONTAMINATED | 降权或排除 |
| L03 | data_access >> event_date | REVIEWED | 标注风险 |
| L04 | feature 由 target 推导 | CONTAMINATED | 禁止使用 |
| L05 | ID 重叠 | CONTAMINATED | 去重 |
| L06 | 跨数据集共享 | REVIEWED | 标注来源 |
| L07 | Oracle 同源 | REVIEWED | 降低可信度 |
| L08 | 单盲标注 | REVIEWED | 双盲重标 |
| L09 | 规则选择参考测试集 | CONTAMINATED | 禁止使用 |
| L10 | 预测窗口跨越事件 | CONTAMINATED | 禁止使用 |
| L11 | benchmark 早于训练 | REVIEWED | 降权 |
| L12 | 回顾性措辞 | REVIEWED | 标注风险 |

---

## 四、泄漏防护实施步骤

### 4.1 第一阶段: 基础防护

```text
STEP 1: 建立泄漏检测脚本
├── 实现 L01-L12 检测函数
├── 集成到数据预处理管道
└── 输出泄漏分类报告
```

### 4.2 第二阶段: 数据集隔离

```text
STEP 2: 建立分层数据集
├── PRE_EVENT: 仅接受 CLEAN 分类
├── HISTORICAL_BLIND: 接受 CLEAN + REVIEWED
└── POST_HOC: 接受所有分类
```

### 4.3 第三阶段: 持续监控

```text
STEP 3: 建立泄漏审计日志
├── 记录每次数据访问
├── 跟踪泄漏分类变化
└── 定期重新评估
```

---

## 五、泄漏案例处理规则

```text
LEAKAGE HANDLING RULES:
├── CONTAMINATED:
│   ├── 禁止进入任何评估数据集
│   ├── 必须从数据集中移除
│   └── 记录移除原因
│
├── REVIEWED:
│   ├── 可进入 CALIBRATION 数据集
│   ├── 不可进入 BLIND/HOLDOUT 数据集
│   ├── 必须标注风险等级
│   └── 需要额外验证
│
└── CLEAN:
    ├── 可进入所有数据集
    └── 需定期重新审计
```

---

**报告结束**
**下一步**: A2.5 Dataset Construction
