# V1.3 A0.7 — Leakage Classification & Prevention Strategy

**日期**: 2026-08-22
**类型**: READ-ONLY AUDIT
**状态**: DRAFT — 待审查确认

---

## 原则声明

本文档定义数据泄漏的分类体系与防护策略。
**禁止修改**: 生产代码、测试代码、Golden Dataset。

---

## 一、泄漏类型定义

### 1.1 时间维度泄漏

```text
TYPE-01: PRE_EVENT_LEAKAGE (预期行为)
├── 定义: 预测在事件发生前生成
├── 合规性: ✅ 允许 (前瞻验证的核心要求)
├── 当前检测: ✅ PredictionRecord.created_at < event.occurred_at
├── 风险等级: NONE
└── 示例: 用户查询2026年运势，系统在2026年前生成预测

TYPE-02: POST_EVENT_LEAKAGE (禁止)
├── 定义: 预测在事件发生后生成，可能利用了事后知识
├── 合规性: ❌ 禁止
├── 当前检测: ⚠️ 未实现自动检测
├── 风险等级: CRITICAL
└── 示例: 系统在2027年生成对2026年的预测，但实际参考了2026年结果

TYPE-03: TOLERANCE_WINDOW_VIOLATION (禁止)
├── 定义: 预测日期在事件日期 ±容忍窗口之外
├── 合规性: ❌ 禁止 (超出合理误差范围)
├── 当前检测: ✅ Severity-dependent tolerance window (已在spec中定义)
├── 风险等级: HIGH
└── 示例: 预测2026-01-01的事件，实际事件发生在2026-06-01
```

### 1.2 数据维度泄漏

```text
TYPE-04: DATA_CONTAMINATION (禁止)
├── 定义: 测试数据进入训练/开发流程
├── 合规性: ❌ 禁止
├── 当前检测: ❌ 未实现
├── 风险等级: CRITICAL
└── 子类型:
    ├── 4a: TEST_IN_TRAINING (训练集包含测试集)
    ├── 4b: TRAINING_IN_TEST (测试集反向污染训练)
    └── 4c: SHARED_DATASET (多个测试共用同一数据集)

TYPE-05: DEMOGRAPHIC_LEAKAGE (禁止)
├── 定义: 案例特征通过训练流程泄漏到测试
├── 合规性: ❌ 禁止
├── 当前检测: ❌ 未实现
├── 风险等级: HIGH
└── 示例: 特定历史人物的八字特征同时出现在训练和测试中

TYPE-06: CROSS_DATASET_CONTAMINATION (禁止)
├── 定义: 不同数据集之间共享案例导致泄漏
├── 合规性: ❌ 禁止
├── 当前检测: ⚠️ 部分检测 (重叠案例已标记)
├── 风险等级: MEDIUM
└── 当前已识别: fate-bench ↔ MingLi-Bench ↔ BaziQA 重叠120题
```

### 1.3 方法论泄漏

```text
TYPE-07: POST_HOC_ADAPTATION (禁止)
├── 定义: 根据测试结果调整算法以"恰好"匹配
├── 合规性: ❌ 禁止
├── 当前检测: ❌ 未实现
├── 风险等级: CRITICAL
└── 示例: 先运行测试看到结果，再调整参数使测试通过

TYPE-08: OVERFITTING_TO_GOLDEN (警告)
├── 定义: 算法过度适配Golden Dataset
├── 合规性: ⚠️ 警告 (非严格禁止，但需监控)
├── 当前检测: ❌ 未实现
├── 风险等级: MEDIUM
└── 示例: Golden Dataset通过率99%，但外部验证通过率<50%

TYPE-09: CHERRY_PICKING (禁止)
├── 定义: 仅报告成功案例，忽略失败案例
├── 合规性: ❌ 禁止
├── 当前检测: ⚠️ 部分检测 (Full Report生成要求)
├── 风险等级: HIGH
└── 示例: 只展示10个成功案例，隐藏90个失败案例

TYPE-10: SELECTIVE_METRIC_REPORTING (禁止)
├── 定义: 仅报告有利指标，忽略不利指标
├── 合规性: ❌ 禁止
├── 当前检测: ❌ 未实现
├── 风险等级: HIGH
└── 示例: 报告Micro-F1=0.85，隐藏Macro-F1=0.42
```

### 1.4 时间隔离泄漏

```text
TYPE-11: PIPELINE_CROSS_CONTAMINATION (禁止)
├── 定义: 验证阶段的结果泄漏到开发阶段
├── 合规性: ❌ 禁止
├── 当前检测: ❌ 未实现
├── 风险等级: CRITICAL
└── 示例: V1.2审计结果被用于调整V1.3算法

TYPE-12: ARCHITECTURE_FROZEN_VIOLATION (禁止)
├── 定义: 修改已冻结的架构/Contract以改善测试分数
├── 合规性: ❌ 禁止
├── 当前检测: ✅ G1-G6 Gate架构保护
├── 风险等级: CRITICAL
└── 示例: 修改Pydantic Schema使验证更容易通过
```

---

## 二、当前检测机制

### 2.1 已实现检测

```text
src/tongshu/forward_validation/engine.py
├── prediction_window: 定义预测生成时间范围 ✅
├── evaluation_tolerance: 定义事件评估容差窗口 ✅
├── created_at < occurred_at: 预测必须在事件前 ✅
├── LEAKAGE_STATUS 标记: 标记每次预测的泄漏状态 ✅
└── PredictionRecord 冻结: 不可修改 ✅

src/tongshu/validation/v12/read_only.py
├── Frozen Dataclass 模式: 防止运行时修改 ✅
├── AgreementResult 不可变: 验证结果不可修改 ✅
└── ValidationReport 只读: 报告生成后不可修改 ✅

src/tongshu/audit_validation/gates/
├── G1-G4 运行时守门: 输入/输出约束 ✅
├── L1-L3 三层校验: 结构/语义/法律校验 ✅
└── 冻结Checklist: 架构冻结状态验证 ✅
```

### 2.2 未实现检测

```text
❌ DATA_CONTAMINATION 检测: 无自动化检测
❌ DEMOGRAPHIC_LEAKAGE 检测: 无自动化检测
❌ POST_HOC_ADAPTATION 检测: 无自动化检测
❌ CROSS_DATASET_CONTAMINATION 完整检测: 仅标记重叠
❌ SELECTIVE_METRIC_REPORTING 检测: 无自动化检测
❌ ARCHITECTURE_FROZEN_VIOLATION 动态检测: 仅G1-G6静态检查
```

---

## 三、防护策略

### 3.1 数据隔离策略

```text
STRATEGY-01: Dataset Partitioning
├── 目标: 确保测试集与训练集完全隔离
├── 实施: 
│   ├── 建立 Dataset Registry (dataset_registry.json)
│   ├── 每个案例标记所属数据集
│   ├── 测试前验证无重叠
│   └── 自动生成去重报告
├── 状态: ❌ 未实现
└── 优先级: P0

STRATEGY-02: Data Freeze Timestamp
├── 目标: 记录每个数据集的最后修改时间
├── 实施:
│   ├── 在数据集元数据中添加 frozen_at 字段
│   ├── 验证所有测试在冻结时间后运行
│   └── 拒绝任何修改冻结数据的变更
├── 状态: ❌ 未实现
└── 优先级: P0

STRATEGY-03: Golden Dataset Immutable
├── 目标: 确保Golden Dataset不被修改
├── 实施:
│   ├── Golden Dataset 文件设为只读 (file permissions)
│   ├── 测试前校验文件哈希
│   └── 修改必须走审批流程
├── 状态: ⚠️ 部分实现 (仅文档声明，无技术强制)
└── 优先级: P0
```

### 3.2 方法论防护策略

```text
STRATEGY-04: Blind Test Protocol
├── 目标: 执行者不知道测试答案
├── 实施:
│   ├── 测试答案与测试用例分离存储
│   ├── 测试执行者无答案访问权限
│   ├── 自动生成测试报告 (不显示答案)
│   └── 事后交叉验证
├── 状态: ❌ 未实现
└── 优先级: P0

STRATEGY-05: Pre-registration
├── 目标: 在运行测试前注册测试计划
├── 实施:
│   ├── 测试计划 (包括测试集、评估指标) 预先注册
│   ├── 不得在测试后修改评估标准
│   └── 变更必须记录变更原因
├── 状态: ❌ 未实现
└── 优先级: P1

STRATEGY-06: Full Report Mandate
├── 目标: 要求完整报告所有测试结果
├── 实施:
│   ├── 自动生成完整测试报告 (包括失败案例)
│   ├── 禁止选择性报告
│   └── 报告包含详细失败分析
├── 状态: ⚠️ 部分实现 (V1.2有报告生成，但不强制全量)
└── 优先级: P0
```

### 3.3 架构防护策略

```text
STRATEGY-07: Architecture Freeze Enforcement
├── 目标: 技术上强制执行架构冻结
├── 实施:
│   ├── CI/CD pipeline 检查架构变更
│   ├── 自动检测 Contract Schema 修改
│   └── 拒绝未经批准的架构变更
├── 状态: ❌ 未实现
└── 优先级: P0

STRATEGY-08: Change Audit Trail
├── 目标: 记录所有架构变更
├── 实施:
│   ├── 每个测试变更记录 author/timestamp/reason
│   ├── 生成变更审计报告
│   └── 与 Git commit 关联
├── 状态: ⚠️ 部分实现 (Git记录存在，但无结构化审计)
└── 优先级: P1
```

---

## 四、泄漏风险评估矩阵

### 4.1 风险等级定义

```text
CRITICAL: 导致测试结果无效，必须立即修复
├── 数据泄漏 (训练/测试重叠)
├── 方法论泄漏 (Post-hoc适配)
├── 架构泄漏 (修改冻结Contract)
└── 时间泄漏 (Post-event预测)

HIGH: 显著降低结果可信度，需在V1.3中解决
├── 选择性报告 (Cherry-picking)
├──  demographic泄漏
├── 跨数据集污染
└── 指标选择性报告

MEDIUM: 影响结果可解释性，建议解决
├── Golden Dataset过度拟合
├── 部分报告不完整
└── 文档不一致

LOW: 不影响核心结果，可后续处理
├── 元数据不完整
├── 注释不足
└── 命名不一致
```

### 4.2 当前风险状态

| 风险类型 | 等级 | 当前状态 | 风险缓解 |
|---------|------|---------|---------|
| POST_EVENT_LEAKAGE | CRITICAL | ✅ 已防护 | PredictionRecord 冻结 |
| DATA_CONTAMINATION | CRITICAL | ❌ 未防护 | 需实现 Dataset Partitioning |
| ARCHITECTURE_FROZEN_VIOLATION | CRITICAL | ⚠️ 部分防护 | 需CI/CD强制 |
| POST_HOC_ADAPTATION | CRITICAL | ❌ 未防护 | 需实现 Pre-registration |
| DEMOGRAPHIC_LEAKAGE | HIGH | ❌ 未防护 | 需实现 Cross-dataset 检测 |
| CROSS_DATASET_CONTAMINATION | HIGH | ⚠️ 部分检测 | 120题重叠已标记 |
| CHERRY_PICKING | HIGH | ⚠️ 部分防护 | Full Report 部分实现 |
| SELECTIVE_METRIC_REPORTING | HIGH | ❌ 未防护 | 需实现完整报告强制 |
| OVERFITTING_TO_GOLDEN | MEDIUM | ❌ 未防护 | 需实现外部验证对比 |
| PIPELINE_CROSS_CONTAMINATION | CRITICAL | ❌ 未防护 | 需实现阶段隔离 |

---

## 五、V1.3 泄漏防护实施路线图

### Phase 1: 基础隔离 (P0)

```text
任务:
├── 建立 Dataset Registry (dataset_registry.json)
├── 实现数据隔离检测 (cross_dataset_overlap_check.py)
├── Golden Dataset 文件哈希校验
├── 实现 Blind Test Protocol (答案分离)
└── 实现 Pre-registration 机制

交付物:
├── docs/accuracy/dataset_registry.json
├── tests/test_leakage_prevention.py
└── scripts/blind_test_runner.py
```

### Phase 2: 架构防护 (P0)

```text
任务:
├── CI/CD pipeline 集成架构冻结检查
├── 自动检测 Contract Schema 变更
├── 实现 Change Audit Trail (结构化审计)
└── 建立架构冻结审批流程

交付物:
├── .github/workflows/architecture_freeze_check.yaml
├── scripts/schema_diff_checker.py
└── docs/audit/change_audit_log.md
```

### Phase 3: 方法论防护 (P1)

```text
任务:
├── 实现 Full Report 强制生成
├── 实现 Selective Metric 检测
├── 建立测试结果完整性验证
└── 实现外部验证数据集隔离

交付物:
├── tests/test_full_report_compliance.py
├── scripts/result_completeness_checker.py
└── docs/accuracy/external_validation_isolation.md
```

---

## 六、泄漏检测 API 设计

### 6.1 检测函数签名

```python
# 数据泄漏检测
def check_data_contamination(
    test_dataset: Dataset,
    training_datasets: List[Dataset],
    overlap_threshold: float = 0.0
) -> ContaminationReport:
    """检测测试集与训练集的 overlap"""

# 跨数据集检测
def check_cross_dataset_overlap(
    datasets: List[Dataset],
    case_fields: List[str] = ["birth_date", "gender"]
) -> OverlapReport:
    """检测不同数据集之间的案例重叠"""

# 方法论泄漏检测
def check_post_hoc_adaptation(
    algorithm_version: str,
    test_results: List[TestResult],
    last_version: str
) -> AdaptationReport:
    """检测是否在测试后调整算法以匹配结果"""

# 完整性检测
def check_report_completeness(
    report: ValidationReport,
    expected_metrics: List[str]
) -> CompletenessReport:
    """检测报告是否遗漏不利指标"""
```

### 6.2 报告格式

```json
{
  "leakage_type": "DATA_CONTAMINATION",
  "severity": "CRITICAL",
  "details": {
    "test_dataset": "fate-bench-official",
    "training_dataset": "BaziQA-2021",
    "overlapping_cases": 40,
    "overlap_percentage": 13.6
  },
  "recommendation": "Remove BaziQA-2021 cases from training or exclude from test",
  "auto_blocked": true
}
```

---

## 附录：检测工具清单

```
已实现:
├── forward_validation/engine.py (POST_EVENT 检测) ✅
├── audit_validation/gates/* (架构冻结检查) ✅
└── validation/v12/read_only.py (不可变保护) ✅

待实现:
├── leakage_prevention/dataset_registry.py ❌
├── leakage_prevention/cross_check.py ❌
├── leakage_prevention/post_hoc_check.py ❌
└── leakage_prevention/report_completeness.py ❌
```
