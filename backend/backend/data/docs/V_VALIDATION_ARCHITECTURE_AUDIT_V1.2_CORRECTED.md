# 顺天 V-Validation V1.2 — 审计修正版
## 全项目架构总审计报告（用户裁定修正）

**审计日期**: 2026-08-22  
**审计版本**: V1.2-Corrected  
**审计范围**: 顺天全后端引擎 + 架构契约 + 验证系统  
**状态**: **CONDITIONAL APPROVAL** — 允许进入架构整改，禁止直接按原 Phase 1~6 开工  
**前置条件**: 必须完成 Phase 0（审计修正）→ Phase 1（契约冻结）后才能进入工程实施

---

## 一、V1.1 原报告核心问题与修正

### 1.1 已修正的致命错误

#### ❌ 错误1: Interpretation = 100% PROVEN

**原报告**: `Interpretation | 518 | 0 | 100% | PROVEN`

**问题**: "未实现故不计失败"不是PROVEN，这是统计纪律问题。
一个未实现的系统不能说"通过"，只能说是"尚未可评估"。

**修正后**:
```text
INTERPRETATION → STATUS: NOT_IMPLEMENTED / NOT_EVALUABLE
SEVERITY       → STATUS: NOT_IMPLEMENTED / NOT_EVALUABLE
```

---

#### ❌ 错误2: Event Ontology 以数据集倒推

**原报告**: `total_events: 10`（用Golden Dataset数量定义Ontology）

**问题**: Golden Dataset是验证夹具，不是本体权威。不能反过来让数据集绑架产品架构。

**修正原则**:
```text
传统知识体系 → Canonical Ontology → Event Taxonomy → Golden Dataset映射 → Validation
（正确方向）

Golden Dataset → 倒推Ontology → 架构被数据集绑架（错误方向）
```

**正确层级结构**:
```text
Domain（域）          ─── 行业大类
├── Event Type（事件类型）── 具体事件分类
│   ├── Event Subtype（子类型）── 可选细化
│   └── Direction（方向）        ─── 上升/下降/稳定
└── Temporal Granularity ─── 时间粒度（MONTHLY/YEARLY等）
```

示例：
```text
CAREER (Domain)
├── PROMOTION (Type)       → direction: INCREASE, granularity: YEARLY
├── JOB_CHANGE (Type)      → direction: CHANGE,    granularity: YEARLY
├── RESIGNATION (Type)     → direction: DECREASE,  granularity: YEARLY
├── DEMOTION (Type)        → direction: DECREASE,  granularity: YEARLY
└── MAJOR_INCOME (Type)    → direction: INCREASE,  granularity: YEARLY
```

**结论**: Domain有4个，Event Type有15个，不是"10类事件"。

---

#### ❌ 错误3: Severity 乘积公式零门控问题

**原报告**: `Severity = signal_strength × multi_engine_agreement × ...`

**问题**: 若任一因子为0，整个Severity归零。这会把"系统未实现"误判成"事件不存在"。

修正方案 — 分离两个维度：
```text
Evidence Completeness（证据完整度）   = 各来源实际值 × LLM可用性标志
    → 用于判断"我们现在能知道多少"

Event Severity（事件严重度）          = 仅基于已验证证据计算
    → 用于判断"事件本身的性质"

LLM未完成时: Evidence Completeness = 低, 但 Event Severity 仍保持历史/当前证据值
```

---

#### ❌ 错误4: Temporal Engine 职责混淆

**原报告**: 将大运/流年/流月/流日/流时全塞进一个 Temporal Engine

**问题**: Temporal Engine 不应拥有领域算法，它应该是编排层。

**修正架构**:
```text
Temporal Orchestrator（编排层，通用）
    │
    ├── Bazi Time Engine（领域算法）
    │   ├── 大运计算（每10年一变）
    │   ├── 流年计算
    │   └── 流月/流日/流时
    │
    ├── Heluo Time Engine（领域算法）
    │   ├── 本命 → 元堂 → 后天 → 流年/月/日/时
    │   ├── 节候卦计算
    │   └── 卦气时间链
    │
    └── Ziwei Time Engine（领域算法）
        └── 紫微大限/流年/流月周期

    ↓ 统一收敛
Temporal Evidence（多引擎时间信号整合）
    ↓
Temporal Convergence（时间窗口收敛）
```

**契约要求**: `Temporal Orchestrator` 只定义接口，不实现任何具体算法。

---

#### ❌ 错误5: Evidence Cross-Verification 一刀切

**原报告**: "所有证据必须至少2个独立来源"

**问题**: Level 1 经典原点（《周易》原文）本身就是 primary source，不需要第二份来源验证。

**修正**:
```text
evidence_type enum:
  PRIMARY_SOURCE    — 《周易》原文/说卦传（单源可信，不需交叉）
  SECONDARY_SOURCE  — 其他版本通行本（用于交叉验证）
  CROSS_VERIFIED    — 多个独立来源一致
  COMMENTARY        — 王弼/程颐/朱熹/来知德注疏
  DERIVED           — 从卦体/爻位推导出的结论
  MODERN_MAPPING    — 现代生活场景类比（证据等级最低）
```

**验证规则**:
- PRIMARY_SOURCE: 只需来源标注完整（书名/章节/版本）
- COMMENTARY/DERIVED: 需追溯至PRIMARY_SOURCE
- MODERN_MAPPING: 不可用于正式证据链，仅用于LLM补充解释

---

#### ❌ 错误6: Yi Engine 被错误定位为预测核心

**原报告**: "Yi Engine 未实现 → 是预测层主要瓶颈"

**问题**: Yi Engine 是 Interpretation/Evidence 基础设施，不是预测分类器。
当前低F1的直接原因是 Signal/Ontology/Temporal/Severity 缺失，不是 Yi Engine。

**修正优先级**:
```text
P0-A: Canonical Signal        （预测信号接入五大引擎）
P0-B: Event Ontology          （扩展至15个Event Type，非10类）
P0-C: Temporal Evidence       （多引擎时间收敛）
P0-D: Severity Schema         （分离证据完整度与事件严重度）
P0-E: Evidence Chain          （五级证据体系）
P1:   Yi Engine               （六十四卦结构分析）
P1:   Relational Interpretation（LLM关系解释层）
P1:   Cross-Engine Agreement  （多引擎一致性）
```

---

#### ❌ 错误7: F1=30% 作为验收标准

**修正**: 将"验收标准"拆分为两层：

**Architecture Acceptance（架构验收）** — 硬约束:
```text
Contract Compliance = 100%        — 所有Schema完整定义
Reference Integrity = 100%        — 无悬空引用
No Orphan References              — 每条证据可追溯
No Illegal Layer Access           — LLM不进入计算层
No Calculation Regression         — 已有计算正确性不被破坏
```

**Validation Target（验证目标）** — 预期趋势:
```text
Signal Coverage    ↑ (44% → 70%+)
Temporal Miss      ↓ (67.8% → 40%)
Ontology Miss      ↓ (56.4% → 30%)
Evidence Completeness ↑
F1 Score           ↑ (13.8% → baseline+improvement)
```

**F1≥30% 作为 Stretch Goal，不是硬验收门槛。** 如果架构完整但F1未达30%，说明Golden Dataset本身存在问题，需要单独诊断数据集质量。

---

## 二、新增第九套Schema：Validation Status Schema

**原报告遗漏**: V-Validation 没有定义"系统状态"维度。

```python
# docs/validation_status_schema_v1.md
VALIDATION_STATUS_SCHEMA = {
    "version": "1.0.0",
    "frozen_date": "2026-08-22",
    
    "status_enum": {
        "NOT_IMPLEMENTED": "组件尚未实现，不计入诊断",
        "NOT_EVALUABLE": "数据不足，无法评估",
        "BLOCKED": "因上游缺失而无法继续",
        "PASS": "诊断通过",
        "FAIL": "诊断失败",
        "PARTIAL": "部分通过（需标注覆盖比例）",
    },
    
    "dimension_status_matrix": {
        "CALCULATION":    {"status": "PASS",       "score": 1.00, "note": "八字/河洛/紫微计算均正确"},
        "SIGNAL":         {"status": "PARTIAL",    "score": 0.56, "note": "仅Bazi信号接入，Heluo/Ziwei/Huangli未接入"},
        "ONTOLOGY":       {"status": "PARTIAL",    "score": 0.44, "note": "3个预测类别 vs 数据集10类事件"},
        "TEMPORAL":       {"status": "BLOCKED",    "score": None,  "note": "Temporal Engine未实现，依赖上游Signal"},
        "SEVERITY":       {"status": "NOT_IMPLEMENTED", "score": None, "note": "Schema未冻结，未实现"},
        "EVIDENCE":       {"status": "PARTIAL",    "score": 0.20, "note": "缺少Level 1-3证据（周易原文/注疏）"},
        "INTERPRETATION": {"status": "NOT_IMPLEMENTED", "score": None, "note": "Yi Engine + Relational Interpretation均未实现"},
        "CROSS_ENGINE_AGREEMENT": {"status": "NOT_IMPLEMENTED", "score": None, "note": "Multi-Engine Aggregation未实现"},
    },
    
    "diagnostic_rule": "NOT_IMPLEMENTED 和 NOT_EVALUABLE 的维度不参与 Failure Analysis，不计入分母"
}
```

---

## 三、V1.2 五道铁律（不可违反）

| # | 铁律 | 违反后果 |
|---|------|----------|
| 1 | V-Validation 的 NOT_IMPLEMENTED / NOT_EVALUABLE / BLOCKED 必须与 FAIL 严格分离 | 数据污染，无法区分"架构未闭合"和"算法错误" |
| 2 | Golden Dataset 是验证夹具，不是 Ontology 的唯一来源 | 数据集绑架产品架构 |
| 3 | Temporal Orchestrator 不得拥有或重写 Bazi/Heluo/Ziwei 的领域算法 | 领域混乱，维护灾难 |
| 4 | Severity 不能把"系统没实现"误判成"事件严重度为0" | 严重误判，漏报真实事件 |
| 5 | Yi Engine 是 Interpretation/Evidence 基础设施，不得被定义为预测分类器 | 架构倒置，开发顺序混乱 |

**附加冻结**:
- 不修改既有计算算法（BaziEngine/ZiweiEngine/HeluoEngine 不动）
- 不修改 Golden Dataset（golden_cases.json 冻结）
- LLM 不得进入计算层（禁止AI在计算层生成原文或推导）

---

## 四、修正后的 Phase 执行计划

### Phase 0 — 审计修正（已完成）

**目标**: 修正V1.1原报告的核心判断错误

**完成项**:
- [x] Interpretation/Severity 状态修正为 NOT_IMPLEMENTED
- [x] Event Ontology 改为 Domain→Type→Subtype 三层结构
- [x] Severity 公式修正（分离证据完整度与事件严重度）
- [x] Temporal Engine 改为编排层，不拥有领域算法
- [x] Evidence Cross-Verification 分级（PRIMARY_SOURCE不需要双源）
- [x] Yi Engine 优先级从P0降至P1
- [x] F1≥30% 降级为 Stretch Goal
- [x] 新增 Validation Status Schema

---

### Phase 1 — V-Validation 契约冻结

**目标**: 定义完整的验证体系规范（只写文档，不写代码）

**产出**: `docs/V_VALIDATION_SPEC_V1.2.md`（9套Schema）

**Schema清单**:
```
1. Validation Status Schema         ← 新增（Phase 0修正）
2. Failure Taxonomy Schema          ← 沿用V1.1
3. Event Ontology Schema            ← 修正：三层结构，15个Event Type
4. Canonical Signal Schema          ← 沿用V1.1
5. Temporal Evidence Schema         ← 修正：编排层不拥有算法
6. Severity Schema                  ← 修正：分离证据完整度与事件严重度
7. Evidence Chain Schema            ← 修正：分级验证规则
8. Relational Interpretation Schema ← 沿用V1.1（定位纠正）
9. Validation Dimensions Schema     ← 沿用V1.1（新增Cross-Engine维度）
```

**冻结原则**: 所有Schema必须通过人工审查后才能开始工程实施。

---

### Phase 2 — 证据/知识基座建设

**目标**: 建立完整的经典证据基础

**产出**: 知识库数据 + 文档

**任务**:
```
1. 注册《周易》通行本（Wang Bi / Cheng Yi / Zhu Xi / Lai Zhide 四版本）
   - 每卦: 卦辞 + 彖传 + 象传 + 六爻爻辞
   - 来源: 纸质书扫描/权威数据库，禁止LLM生成
   - 标注: source / edition / chapter / passage / evidence

2. 注册《说卦传》全文
   - 30条卦象类象原文
   - 结构: 八卦×三方卦象 × 万物类象

3. 注册5级证据概念
   - Level 1: 经典原点（卦辞/爻辞/说卦）
   - Level 2: 经典语境（卦序/综卦/错卦/爻位）
   - Level 3: 注疏传统（王弼/程颐/朱熹/来知德）
   - Level 4: 结构推导（卦体/五行/互体）
   - Level 5: 现代映射（生活场景类比）

4. 实现 Evidence Registry
   - 支持 source_tracing（溯源）
   - 支持 level_classification（分级）
   - 支持 cross_verification（交叉验证标记）
```

**数据来源原则**: 纸质书扫描/OCR → 人工核验 → 入库。禁止LLM生成经典原文。

---

### Phase 3 — Canonical Signal + Event Ontology

**目标**: 打通五大引擎信号 + 建立完整事件本体

**产出**: `tongshu/reasoning/canonical_signal_engine.py` + `tongshu/spec/event_ontology_v1.py`

**Signal Engine 任务**:
```
1. 扩展 SignalEngine 接口，支持 HeluoInput/ZiweiInput/HuangliInput/KnowledgeInput
2. 实现 Heluo Signal 提取（卦象→USO映射）
3. 实现 Ziwei Signal 提取（星曜→USO映射）
4. 实现 Huangli Signal 提取（宜忌→USO映射）
5. 实现 Knowledge Signal 提取（知识库→USO映射）
6. 实现 Multi-Engine Aggregation（加权投票，权重可配置）
7. 实现 Signal Normalization（统一置信度）
```

**Event Ontology 任务**:
```
1. 定义 Domain（4个）: EDUCATION / CAREER / FAMILY / LIFE_EVENT
2. 定义 Event Type（15个，含directionality）:
   - EDUCATION: EXAM↑, ADMISSION↑, GRADUATION↑, DEGREE↑
   - CAREER: PROMOTION↑, JOB_CHANGE(中立), RESIGNATION↓, DEMOTION↓, MAJOR_INCOME↑
   - FAMILY: NEW_RELATIONSHIP↑, MARRIAGE↑, CHILD_BIRTH↑, FAMILY_CHANGE(?), PARENT_DEATH↓
   - LIFE_EVENT: RELOCATION(?), HEALTH_ISSUE↓, LEGAL_ISSUE↓
3. 实现 Ontology Mapper（预测→实际类别映射）
4. 实现 Directionality 检查（PROMOTION≠RESIGNATION）
5. 实现 Temporal Granularity 映射
6. 实现 Ontology-Specificity 计算
```

---

### Phase 4 — Temporal Engine

**目标**: 实现多引擎时间收敛

**产出**: `tongshu/engines/temporal_orchestrator.py` + 各领域时间引擎

**架构**:
```text
Temporal Orchestrator（编排层，无领域知识）
    ├── BaziTimeEngine（领域算法：大运/流年/流月）
    ├── HeluoTimeEngine（领域算法：节候/卦气/流年/月/日/时）
    └── ZiweiTimeEngine（领域算法：大限/流年/流月）
        ↓
Temporal Evidence（多引擎时间信号整合）
    ↓
Temporal Convergence（时间窗口收敛）
```

**约束**: 各领域时间引擎的算法实现不得修改（Bazi/Heluo/Ziwei 已有引擎保留）。
Temporal Engine 只做"时间信号的包装和整合"。

---

### Phase 5 — Severity + Cross-Engine Agreement

**目标**: 实现严重程度评估 + 多引擎一致性

**产出**: `tongshu/reasoning/severity_engine.py` + `tongshu/reasoning/agreement_engine.py`

**Severity Schema（修正版）**:
```python
# 分离两个概念
Evidence_Completeness = sum(
    signal_confidence × signal_weight,
    evidence_quality_score,
    llm_availability_flag
)
# llm_availability_flag = 1 if LLM层可用, 0 if LLM层未实现
# 未实现时，Evidence_Completeness 标记为 partial，但不影响 Event_Severity

Event_Severity = signal_strength × multi_engine_agreement 
               × temporal_convergence × ontology_specificity 
               × evidence_quality × relational_coherence
# 仅基于已验证证据计算，不考虑LLM可用性
```

**Cross-Engine Agreement**:
```text
agreement_rate = |BaziSignal ∩ HeluoSignal ∩ ZiweiSignal| / total_signals
weight_vector = [Bazi:0.3, Heluo:0.3, Ziwei:0.2, Huangli:0.1, Knowledge:0.1]
```

---

### Phase 6 — Yi Engine + Relational Interpretation

**目标**: 实现六十四卦结构分析 + LLM关系解释

**产出**: `tongshu/reasoning/yi_engine.py` + LLM Prompt

**Yi Engine 四层**:
```
层A: HexagramSymbol  — 纯数据查询（64卦卦象结构）
层B: LineSymbol      — 纯逻辑计算（爻位关系：当位/中正/应/承/乘）
层C: ClassicalText   — 知识库检索（卦辞/爻辞/彖传/说卦）
层D: ImageExpansion  — 5级证据扩展
```

**Relational Interpretation（LLM介入点）**:
```
Input:  EvidenceChain + SignalContext + TemporalWindow
Output: RelationalState（非分类！）
        - STATE: 当前整体态势
        - OPPORTUNITY: 机会方向
        - RISK: 风险点
        - ACTION: 建议行动
        - REMEDIATION: 补救措施

约束:
- 禁止输出玄学术语（"官鬼"、"忌神"等）
- 禁止自由联想
- 禁止评分式输出
- 必须引用来源（source_references）
- 禁止直接访问 CalculationContext
```

---

### Phase 7 — V-Validation V2 重新运行

**目标**: 验证修复效果，输出最终报告

**产出**: `docs/V_VALIDATION_REPORT_V1.2.md`

**诊断维度（9维度）**:
```
1. CALCULATION          — PASS (100%)
2. SIGNAL               — 预期 PARTIAL (44%→70%+)
3. ONTOLOGY             — 预期 PARTIAL (44%→70%+)
4. TEMPORAL             — 预期 BLOCKED→PARTIAL
5. SEVERITY             — 预期 NOT_IMPLEMENTED→PARTIAL
6. EVIDENCE             — 预期 PARTIAL (20%→60%+)
7. INTERPRETATION       — 预期 NOT_IMPLEMENTED→PARTIAL
8. CROSS_ENGINE_AGREEMENT — 预期 NOT_IMPLEMENTED→PARTIAL
9. DIRECTIONALITY       — 预期 NEW: PROMOTION≠RESIGNATION
```

**验收标准**:
```
Architecture Acceptance (硬约束):
- Contract Compliance = 100%
- Reference Integrity = 100%
- No Orphan References
- No Illegal Layer Access
- No Calculation Regression

Validation Target (预期趋势):
- Signal Coverage ↑ (44%→70%+)
- Temporal Miss ↓ (67.8%→40%)
- Ontology Miss ↓ (56.4%→30%)
- Evidence Completeness ↑
- F1 Score ↑ (13.8%→baseline+)

Stretch Goal (非硬门槛):
- F1 ≥ 30%
```

---

## 五、关键决策记录

| 决策点 | 原报告 | 修正后 | 理由 |
|--------|--------|--------|------|
| Interpretation状态 | 100% PROVEN | NOT_IMPLEMENTED | 统计纪律：未实现≠通过 |
| Severity状态 | 0% FAIL | NOT_IMPLEMENTED | 未实现≠算法错误 |
| Event Ontology | 10类事件 | 4域15类型 | 数据集是夹具，不是本体权威 |
| Severity公式 | 纯乘积 | 证据完整度+事件严重度分离 | 避免zero-gating |
| Temporal Engine | 单一引擎 | 编排层+领域引擎 | 不重写领域算法 |
| Evidence验证 | 所有证据需双源 | PRIMARY_SOURCE单源即可 | 经典原文不需要交叉验证 |
| Yi Engine优先级 | P0（预测核心） | P1（Interpretation基础设施） | 不是预测分类器 |
| F1≥30% | 验收标准 | Stretch Goal | 架构正确≠F1一定达标 |

---

## 六、下一步指令

**当前状态**: V1.2 审计修正版已完成（本文件）

**下一步**: 等待用户确认后，进入 Phase 1（V-Validation 契约冻结）。

**Phase 1 只允许做的事**:
- 编写9套Schema文档（`docs/V_VALIDATION_SPEC_V1.2.md`）
- 获取用户批准冻结

**Phase 1 不允许做的事**:
- 写任何Python代码
- 修改任何现有引擎
- 修改Golden Dataset

---

**此修正版报告基于用户18条裁决生成。未经用户确认，不进入工程实施阶段。**
