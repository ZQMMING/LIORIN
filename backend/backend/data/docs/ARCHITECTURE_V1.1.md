# SHUNTIAN V-Validation Architecture V1.1

**版本**: V1.1  
**日期**: 2026-08-22  
**状态**: 正式架构文档  
**继承**: ARCHITECTURE_V1.0

---

## 一、架构变更摘要

### V1.0 vs V1.1 核心变化

| 维度 | V1.0 | V1.1 |
|------|------|------|
| 验证层定位 | 测试附属品 | **独立工程层，与算法层并列** |
| 验证体系深度 | 单元测试→Golden Dataset→外部验证 | **六层验证体系（L0-L5）** |
| 基线管理 | 无 | **BASELINE_V1 冻结机制** |
| 失败分析 | 无 | **V1.1 Failure Analysis 六维度诊断** |
| 预测链路 | 计算→预测 | **计算→信号提取→关系解释→事件预测** |

---

## 二、完整架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             SHUNTIAN (顺天)                                  │
│                                                                             │
│  ┌──────────────────────────┐              ┌──────────────────────────────┐ │
│  │     Algorithm Layer      │              │     Validation Layer         │ │
│  │                        │              │                            │ │
│  │  ┌──────────────────┐  │              │  ┌──────────────────────┐  │ │
│  │  │  BaziEngine      │  │              │  │  L0: Calculation     │  │ │
│  │  │  (八字排盘)       │  │              │  │  (算法正确性)        │  │ │
│  │  └──────────────────┘  │              │  └──────────────────────┘  │ │
│  │  ┌──────────────────┐  │              │  ┌──────────────────────┐  │ │
│  │  │  HeluoEngine     │  │              │  │  L1: Golden Dataset  │  │ │
│  │  │  (河洛理数)       │  │              │  │  (历史回测)          │  │ │
│  │  └──────────────────┘  │              │  └──────────────────────┘  │ │
│  │  ┌──────────────────┐  │              │  ┌──────────────────────┐  │ │
│  │  │  ZiweiEngine     │  │              │  │  L2: Blind Test      │  │ │
│  │  │  (紫微斗数)       │  │              │  │  (盲测验证)          │  │ │
│  │  └──────────────────┘  │              │  └──────────────────────┘  │ │
│  │  ┌──────────────────┐  │              │  ┌──────────────────────┐  │ │
│  │  │  YiEngine        │  │              │  │  L3: Ontology        │  │ │
│  │  │  (易经解释)       │  │              │  │  (事件本体论)        │  │ │
│  │  └──────────────────┘  │              │  └──────────────────────┘  │ │
│  │  ┌──────────────────┐  │              │  ┌──────────────────────┐  │ │
│  │  │  CalendarEngine  │  │              │  │  L4: Scoring         │  │ │
│  │  │  (黄历通胜)       │  │              │  │  (评分体系)          │  │ │
│  │  └──────────────────┘  │              │  └──────────────────────┘  │ │
│  └────────────────────────┘              │  ┌──────────────────────┐  │ │
│                                           │  │  L5: Freezing        │  │ │
│  ┌──────────────────────────┐              │  │  (前瞻冻结)        │  │ │
│  │  Signal Extraction       │              │  └──────────────────────┘  │ │
│  │  (信号提取层)            │              │  ┌──────────────────────┐  │ │
│  │  ├─ Bazi Signals        │              │  │  L6: Prospective     │  │ │
│  │  ├─ Heluo Signals       │              │  │  (前瞻预测)          │  │ │
│  │  ├─ Ziwei Signals       │              │  └──────────────────────┘  │ │
│  │  └─ Calendar Signals    │              │  ┌──────────────────────┐  │ │
│  └────────────────────────┘              │  │  L7: Ablation          │  │ │
│                                           │  │  (消融实验)          │  │ │
│  ┌──────────────────────────┐              │  └──────────────────────┘  │ │
│  │  Relational Interpretation│             │  ┌──────────────────────┐  │ │
│  │  (关系解释引擎)          │              │  │  V1.1 Failure Analysis│ │ │
│  │  ├─ State Analysis      │              │  │  (失败诊断)          │  │ │
│  │  ├─ Opportunity/Risk    │              │  └──────────────────────┘  │ │
│  │  └─ Action Guidance     │              │  ┌──────────────────────┐  │ │
│  └────────────────────────┘              │  │  MingLi-Bench        │  │ │
│                                           │  │  (160题盲测)       │  │ │
│  ┌──────────────────────────┐              │  └──────────────────────┘  │ │
│  │  Event Prediction        │              └──────────────────────────────┘ │
│  │  (事件预测层)            │              │                                │
│  │  ├─ Event Candidate     │              │  BASELINE_V1                   │
│  │  ├─ Confidence Scoring  │              │  (50 cases, 518 events)        │
│  │  └─ LLM Language化      │              │  (F1 = 3.15%, 禁止修改)        │
│  └────────────────────────┘              │                                │
└─────────────────────────────────────────┴────────────────────────────────┘
```

---

## 三、分层职责定义

### Algorithm Layer（算法层）

**职责**：独立计算五大传统算法，不混合、不通信。

| 引擎 | 输入 | 输出 | 验证 |
|------|------|------|------|
| BaziEngine | 出生时间+性别 | 四柱干支+十神 | test_p014 (13/13) |
| HeluoEngine | 出生时间+性别 | 先天卦+元堂+后天卦 | test_heluo_full |
| ZiweiEngine | 农历出生时间+性别 | 命盘星曜位置 | test_ziwei_stars |
| YiEngine | 卦象 | 爻辞+象义+解卦 | test_yi_interpret |
| CalendarEngine | 公历日期 | 黄历信息+节气边界 | test_calendar_full |

**约束**：
- 各引擎独立运行，输出结构化结果
- 不允许引擎间直接调用（避免耦合）
- 输出通过 Signal Extraction 层统一提取

---

### Signal Extraction Layer（信号提取层）

**职责**：从各算法输出中提取可操作的命理信号。

```python
class SignalEngine:
    """
    从五大引擎输出中提取信号：
    
    Input:
      - BaziSignals: 日主、十神、大运、流年
      - HeluoSignals: 卦象、爻位、阴阳、承乘比应
      - ZiweiSignals: 命宫主星、十二宫、四化
      - YiSignals: 卦象变化、爻辞吉凶
      - CalendarSignals: 节气边界、黄道黑道
    
    Output:
      - EventSignals: 事业/婚姻/财富/健康/家庭/教育 等类别信号
      - TemporalSignals: 关键时间节点信号
      - SeveritySignals: 事件严重程度信号
    """
    
    def extract_signals(
        self,
        bazi_result: BaziResult,
        heluo_result: HeluoResult,
        ziwei_result: ZiweiResult,
        yi_result: YiResult,
        calendar_result: CalendarResult
    ) -> SignalBundle:
        ...
```

**关键设计**：
- 信号提取使用规则系统（非LLM）
- 信号带置信度和来源标记
- 信号可追溯（traceable）

---

### Relational Interpretation Layer（关系解释层）

**职责**：基于信号进行关系推断，不直接生成预测。

```
State (状态) 
  → Opportunity / Risk (机会/风险) 
  → Action (建议)
```

**六步流程**：
1. **State Analysis** — 当前命局状态评估
2. **Signal Correlation** — 多源信号交叉验证
3. **Causal Chain** — 构建事件因果链
4. **Temporal Mapping** — 映射到时间轴
5. **Severity Assessment** — 评估事件严重程度
6. **Relational Interpretation** — 生成关系解释

**约束**：
- 不使用LLM直接生成预测
- 所有推断必须有证据引用
- 输出结构化为 EventCandidate

---

### Event Prediction Layer（事件预测层）

**职责**：将 EventCandidate 转换为最终预测输出。

```python
class EventPredictor:
    """
    输入: EventCandidate (来自关系解释层)
    输出: PredictedEvent (带时间、类别、置信度)
    """
    
    def predict(
        self,
        candidates: List[EventCandidate],
        threshold: float = 0.6
    ) -> List[PredictedEvent]:
        ...
```

---

### Validation Layer（验证层）

**职责**：建立完整的科学验证链路。

#### L0: Calculation Validation（计算正确性）

```python
class CalculationValidator:
    """验证各引擎计算是否正确"""
    
    def validate_bazi(self, birth_info: BirthInfo) -> ValidationResult:
        # 对比 MySQL/MingLi/fate-bench
        pass
    
    def validate_heluo(self, birth_info: BirthInfo) -> ValidationResult:
        # 对比 iztro/手动计算
        pass
```

#### L1: Golden Dataset（历史回测）

```python
class GoldenBacktester:
    """在已知历史案例上验证预测能力"""
    
    def run_backtest(self, dataset: GoldenDataset) -> BacktestReport:
        # 计算 → 预测 → 匹配 → 评分
        pass
```

#### L2: Blind Test（盲测验证）

```python
class BlindTestRunner:
    """在未知答案的数据集上验证"""
    
    def run_mingli_bench(self, questions: List[MingLiQuestion]) -> BlindReport:
        # 只输入出生信息，不查看答案
        pass
```

#### L3: Event Ontology（事件本体论）

```python
class EventOntology:
    """定义事件类别、严重程度、证据等级"""
    
    categories: Dict[str, Category]
    severities: Dict[int, Severity]
    evidence_grades: Dict[str, EvidenceGrade]
```

#### L4: Scoring（评分体系）

```python
class ValidationScorer:
    """计算 Precision/Recall/F1/类别级指标"""
    
    def score(self, predictions, ground_truth) -> ScoringReport:
        pass
```

#### L5: Freezing（冻结协议）

```python
class FreezeProtocol:
    """建立可复现的基线"""
    
    def freeze(self, commit_hash: str, results: Dict) -> FreezeSnapshot:
        pass
```

#### L6: Prospective Validation（前瞻预测）

```python
class ProspectiveValidator:
    """对冻结后的真实未来事件进行预测"""
    
    def predict_future(self, cases: List[FutureCase]) -> ProspectiveReport:
        pass
```

#### L7: Ablation（消融实验）

```python
class AblationStudy:
    """验证各模块的增量贡献"""
    
    def run_ablation(self) -> AblationReport:
        # Combined vs Bazi-only vs Heluo-only vs Random
        pass
```

---

## 四、V1.1 Failure Analysis 六维度

### 诊断框架

```
F1 = 3.15% 的根因分解：

1. Calculation Failure（计算错误）
   - 八字计算是否正确？
   - 河洛计算是否正确？
   - 紫微计算是否正确？
   - 时柱计算边界？

2. Signal Failure（信号缺失）
   - 是否生成了事业信号？
   - 是否生成了婚姻信号？
   - 是否生成了财富信号？
   - 信号置信度是否足够？

3. Ontology Failure（本体错配）
   - 预测类别 vs 实际类别是否可映射？
   - 时间粒度是否一致？
   - 严重程度是否匹配？

4. Temporal Failure（时间偏差）
   - 预测年份 vs 实际年份偏移？
   - 不同容忍度下的表现？
   - 年/季/月/日精度？

5. Severity Failure（强度误判）
   - 预测严重程度 vs 实际严重程度？
   - 是否区分了 TRIVIAL/MAJOR/CRITICAL？

6. Interpretation Failure（推断错误）
   - 关系解释是否正确？
   - 证据引用是否充分？
   - 因果链是否成立？
```

---

## 五、架构约束（红线）

### 5.1 预测链路约束

```
禁止: 出生信息 → LLM → 预测
禁止: 出生信息 → 单一引擎 → 预测
允许: 出生信息 → 计算层 → 信号提取 → 关系解释 → 事件预测
```

### 5.2 数据管理约束

```
禁止: 修改 Golden Dataset 提高分数
禁止: 修改 Scoring 公式提高分数
禁止: 添加/删除案例适配算法
允许: 添加诊断层分析失败原因
允许: 扩展预测类别（不修改现有案例）
```

### 5.3 算法独立性约束

```
允许: 五大引擎独立计算
禁止: 引擎间直接耦合
允许: 通过 Signal Extraction 层聚合
禁止: 用 LLM 替代命理计算
```

---

## 六、开发路线图

```
V1.0 Baseline (已达成)
  │ 50 cases, 518 events
  │ P=4.23%, R=2.51%, F1=3.15%
  │ BASELINE_V1 冻结
  │
  ▼
V1.1 Failure Analysis (当前)
  │ 六维度逐事件审计
  │ 定位瓶颈层级
  │ 输出诊断报告
  │
  ▼
V1.2 Architecture Refinement
  │ 修复识别的缺陷
  │ SignalEngine 实现
  │ 关系解释引擎
  │
  ▼
V1.3 Backtest Re-run
  │ 重跑 Golden Dataset
  │ 对比 V1.1 vs V1.2
  │
  ▼
V1.4 Ablation Study
  │ 验证各模块增量贡献
  │ Combined vs Bazi-only vs Heluo-only
  │
  ▼
V1.5 MingLi-Bench
  │ 160题完整盲测
  │
  ▼
V2.0 Scale Up
  │ 100 cases → 200 cases
  │ 518 events → 1000+ events
  │
  ▼
V-FROZEN-2026-09-01
  │ 最终基线冻结
  │ 前瞻预测启动
```

---

## 七、文件结构

```
D:/today/backend/
├── src/tongshu/
│   ├── engines/                    # 五大引擎
│   │   ├── bazi_engine.py
│   │   ├── heluo_engine.py
│   │   ├── ziwei_engine.py
│   │   ├── yi_engine.py
│   │   └── calendar_engine.py
│   ├── signal/                     # 信号提取层
│   │   ├── signal_engine.py
│   │   └── signal_bundle.py
│   ├── interpretation/             # 关系解释层
│   │   ├── relational_engine.py
│   │   └── event_candidate.py
│   └── v_validation/               # 验证层
│       ├── l0_calculation/
│       ├── l1_golden/
│       ├── l2_blind/
│       ├── l3_ontology.py
│       ├── l4_scoring.py
│       ├── l5_freeze.py
│       ├── l6_prospective/
│       └── l7_ablation/
├── dataset/
│   └── golden_v1/
│       ├── golden_cases.json       # 50 cases, 518 events (FROZEN)
│       └── README.md
├── docs/
│   ├── BASELINE_V1.md              # 基线冻结记录
│   ├── VALIDATION_FAILURE_ANALYSIS_V1.md  # 失败分析
│   └── ARCHITECTURE_V1.1.md        # 本文档
├── scripts/
│   ├── golden_backtest.py          # 回测脚本
│   └── failure_analysis.py         # 失败分析脚本
└── tests/
    ├── test_calculation.py         # L0 计算验证
    ├── test_golding_backtest.py    # L1 回测
    ├── test_blind.py               # L2 盲测
    ├── test_ontology.py            # L3 本体
    └── test_freeze.py              # L5 冻结
```

---

## 八、关键决策记录

### 决策 1: V-Validation 独立成层
- **理由**: 验证体系复杂度已超过测试附属品的定位
- **影响**: 验证层拥有独立的开发周期、团队分工、质量控制
- **状态**: ✅ 已执行

### 决策 2: BASELINE_V1 冻结
- **理由**: 需要稳定的基准进行比较和复现
- **影响**: Golden Dataset 不可修改，评分标准不可优化
- **状态**: ✅ 已执行

### 决策 3: 六维度诊断框架
- **理由**: 3.15% F1 需要系统性归因
- **影响**: 诊断结果指导后续优化方向
- **状态**: 🔄 进行中

### 决策 4: 预测链路重构
- **理由**: 架构文档要求"计算→信号→解释→预测"
- **影响**: 当前简单规则引擎需要升级为完整链路
- **状态**: 📋 计划中

---

**此文档是顺天项目 V1.1 架构的权威参考，修改需经用户确认。**
