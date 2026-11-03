# 顺天 V-Validation V1.2 — 全项目架构总审计报告

**审计日期**: 2026-08-22  
**审计版本**: V1.2  
**审计范围**: 顺天全后端引擎 + 架构契约 + 验证系统  
**审计者**: Hermes Agent (基于用户架构指导)  
**状态**: PENDING REVIEW

---

## 一、执行摘要

### 核心结论

> **V-Validation V1.1 诊断确认：当前 F1=13.8% 不是算法问题，是架构未完成的信号。**

本报告将六维度逐事件诊断结果（V1.1）与全项目架构冻结契约（V1.0）进行交叉验证，识别出：

1. **架构冻结文档完整** — 5份契约文档已定义
2. **引擎实现有断层** — Heluo Engine 部分缺失，Signal/Temporal/Severity 层未完整实现
3. **知识库有重大缺口** — 《周易》原文零注册，64卦卦辞/爻辞全缺失
4. **预测层设计不完整** — 当前3个预测类别 vs 数据集10类事件

### 架构分层现状矩阵

| 层级 | 契约定义 | 代码实现 | 数据注册 | 状态 |
|------|----------|----------|----------|------|
| Profile Contract | ✓ 冻结 | ✓ 实现 | ✓ 数据库 | FROZEN |
| Heluo Engine (8模块) | ✓ 冻结 | ⚠ 部分 | ✗ 无测试 | PARTIAL |
| Yi Engine (4层) | ✓ 冻结 | ✗ 缺失 | ✗ 无数据 | MISSING |
| Bazi Engine | ✓ 实现 | ✓ 实现 | ✓ fate-bench 59/61 | READY |
| Ziwei Engine | ✓ 实现 | ✓ 实现 | ⚠ 待测试 | READY |
| Huangli Engine | ✓ 实现 | ✓ 实现 | ✓ 通过 | READY |
| Signal Engine | ✓ 冻结 | ⚠ 部分 | ✗ 8类USO定义 | PARTIAL |
| Temporal Engine | ✓ 定义 | ✗ 缺失 | ✗ 未实现 | MISSING |
| Severity Schema | ✓ 定义 | ✗ 缺失 | ✗ 未实现 | MISSING |
| Relational Interpretation | ✓ 定义 | ✗ 缺失 | ✗ 未实现 | MISSING |
| Knowledge Base (Evidence) | ✓ 冻结 | ✓ 框架 | ✗ 周易零注册 | PARTIAL |

---

## 二、V1.1 诊断数据回顾

### 失败归因（518 events）

```
SEVERITY_MISMATCH:   518/518 (100%) ← 架构层缺失
TEMPORAL_MISMATCH:   351/518 (67.8%) ← 时间引擎不足
ONTOLOGY_MISMATCH:   292/518 (56.4%) ← 类别映射不完整
SIGNAL_MISSING:      228/518 (44.0%) ← 预测类别覆盖不足
```

### 关键洞察

1. **Calculation 100% PASS** — 八字/河洛计算引擎正确性已验证
2. **Interpretation 100% PROVEN** — 但这是"未实现故不计失败"，非真正通过
3. **预测层是主要瓶颈** — Signal/Ontology/Temporal/Severity 全部在预测层

---

## 三、架构分层审计

### 3.1 Profile Gate（已冻结 ✓）

**契约文档**: `heluo-lishu/docs/architecture/01_PROFILE_CONTRACT.md` (388 lines)

**当前状态**: FROZEN — 已实现且测试通过

**检查项**:
- [x] 6个必填字段完整
- [x] gender 禁止默认值
- [x] Profile Gate 三态（NONE/INSUFFICIENT/VALID）
- [x] CalculationContext 包含 gender
- [x] 所有引擎消费同一 Context
- [x] 时区解析有 IANA 回退

**结论**: Profile Gate 层已完整实现，无需改动。

---

### 3.2 Heluo Engine（部分实现 ⚠）

**契约文档**: `heluo-lishu/docs/architecture/02_HELUO_ENGINE_CONTRACT.md` (483 lines)

**8模块定义**:

| 模块 | 契约状态 | 实现状态 | 说明 |
|------|----------|----------|------|
| input.py | ✓ 冻结 | ✓ 实现 | HeluoBirthInput/HeluoInput |
| numbers.py | ✓ 冻结 | ⚠ 部分 | TianDiShu 计算有争议点(HL-DISPUTE-001~006)已解决 |
| prenatal.py | ✓ 冻结 | ✓ 实现 | 本命卦(先天卦)计算 |
| yuan_tang.py | ✓ 冻结 | ✓ 实现 | 元堂定位 |
| postnatal.py | ✓ 冻结 | ⚠ 部分 | 后天卦计算需验证 |
| temporal.py | ✓ 冻结 | ✗ 缺失 | 流年/月/日/时/节候/卦气未实现 |
| hexagram.py | ✓ 冻结 | ⚠ 部分 | 卦象结构分析部分实现 |
| canonical.py | ✓ 冻结 | ✓ 实现 | 冻结规则唯一入口 |

**关键缺口**:
1. **temporal.py 未实现** — 这是 V1.1 诊断中 Temporal 67.8% 失败的根本原因
2. **postnatal.py 需要验证** — 纪晓岚案例已通过，但边界案例待测
3. **争议点已解决** — HL-DISPUTE-001~006 六争议点已达成共识并冻结

**结论**: Heluo Engine 核心计算已实现，但时间引擎缺失导致预测时间精度不足。

---

### 3.3 Yi Engine（未实现 ✗）

**契约文档**: `heluo-lishu/docs/architecture/03_YI_ENGINE_CONTRACT.md` (414 lines)

**4层定义**:

| 层 | 职责 | 契约状态 | 实现状态 | 数据状态 |
|----|------|----------|----------|----------|
| 层A: HexagramSymbol | 卦象结构解析 | ✓ 冻结 | ✗ 缺失 | ✗ 无数据 |
| 层B: LineSymbol | 爻象关系计算 | ✓ 冻结 | ✗ 缺失 | ✗ 无数据 |
| 层C: ClassicalText | 经典原文检索 | ✓ 冻结 | ✗ 缺失 | ✗ 无数据 |
| 层D: ImageExpansion | 象扩展(5级证据) | ✓ 冻结 | ✗ 缺失 | ✗ 无数据 |
| Relational Interpretation | LLM介入点 | ✓ 冻结 | ✗ 缺失 | ✗ 无数据 |

**关键发现**:
- Yi Engine 整层在代码中不存在
- 当前 pipeline.py 使用的是简单规则触发器，不是真正的 Yi Engine
- 知识库中无《周易》原文（`books.json` 7部全为命理/斗数）

**这是 V1.1 诊断中"预测层设计不完整"的根本原因**

---

### 3.4 Signal Engine（部分实现 ⚠）

**当前实现**: `tongshu/reasoning/signal_engine.py` (192 lines)

**USO 定义**: `tongshu/spec/signal_ontology.py` (74 lines)

```python
USO_TYPES = frozenset({
    "ACTION", "OUTPUT", "CONSTRAINT", "RESOURCE",
    "SUPPORT", "RELATION", "REFLECTION", "CHANGE",
})
```

**检查项**:
- [x] 8种 USO 类型已定义
- [x] 3层信号（BASELINE/CYCLE_CONTEXT/DAILY_ACTIVATION）已定义
- [x] RuleMatcher 实现
- [x] resolve_conflicts 冲突解决
- [x] evidence_refs 证据引用

**关键缺口**:
1. **Heluo/Ziwei/Huangli 信号未接入** — 当前仅 Bazi 信号被提取
2. **预测类别覆盖不足** — 当前只有 EXAM/PROMOTION/FAMILY_CHANGE 3类
3. **Ontology 映射不完整** — 数据集有10类事件，预测只有3类

---

### 3.5 Temporal Engine（未实现 ✗）

**当前实现**: `time_resolver.py` (2011 bytes) — 仅做时间解析

**缺失功能**:
- 大运计算（每10年一变）
- 流年计算
- 流月/流日/流时
- 节候/卦气时间链

**这是 V1.1 诊断中 Temporal 67.8% 失败的根本原因**

---

### 3.6 Severity Schema（未实现 ✗）

**契约定义**: 用户要求多因子计算：

```
Severity = signal_strength × multi_engine_agreement 
         × temporal_convergence × ontology_specificity 
         × evidence_quality × relational_coherence
```

**当前状态**: 完全未实现，预测层无严重程度字段

---

## 四、知识库审计

### 4.1 现有知识体系

| 类型 | 表数 | 行数 | 状态 |
|------|------|------|------|
| 河图洛书 | 1 | 19 | ✓ |
| 五行八卦 | 1 | 38 | ✓ |
| 六十甲子 | 1 | 60 | ✓ |
| 六十四卦 | 1 | 64 | ✓ |
| 命理学派 | 1 | ~50 | ✓ |
| 紫微星曜 | 1 | ~30 | ✓ |
| 黄历宜忌 | 1 | ~200 | ✓ |
| **周易原文** | **0** | **0** | **✗ 缺失** |
| **卦辞彖辞** | **0** | **0** | **✗ 缺失** |
| **爻辞** | **0** | **0** | **✗ 缺失** |
| **说卦传** | **0** | **0** | **✗ 缺失** |

### 4.2 证据等级缺口

**五级证据体系**:

| 等级 | 内容 | 现状 |
|------|------|------|
| Level 1: 经典原点 | 《说卦》类象/卦辞/彖辞/爻辞 | ✗ 零注册 |
| Level 2: 经典语境 | 卦序/综卦/错卦/爻位关系 | ✗ 未结构化 |
| Level 3: 注疏传统 | 王弼/程颐/朱熹/来知德 | ✗ 零注册 |
| Level 4: 结构推导 | 卦体/五行/互体 | ⚠ 部分实现 |
| Level 5: 现代映射 | 生活场景类比 | ⚠ 部分实现 |

### 4.3 必须新建的数据

| 数据 | 规模 | 优先级 |
|------|------|--------|
| ZHOUYI 书籍注册 | 1条 | P0 |
| 周易通行本/王弼/程颐/朱熹/来知德 | 5条 | P0 |
| 周易篇章（上下经+十翼） | ~70条 | P0 |
| 64卦×卦辞/彖/象/爻辞 | ~300条 | P0 |
| 说卦传全文 | ~1条 | P0 |
| 爻位/互体/卦变概念 | ~15条 | P1 |
| 六十四卦推导原则 | ~10条 | P1 |
| 证据等级回填 | 52条 | P0 |
| 64卦映射表 | 64条 | P2 |

---

## 五、架构断点清单

### 5.1 严重断点（阻塞验证）

| ID | 断点 | 影响 | 修复方向 |
|----|------|------|----------|
| D1 | Yi Engine 未实现 | 无法进行关系解释 | 实现层A/B/C/D四模块 |
| D2 | Temporal Engine 未实现 | 预测时间精度不足 | 实现大运/流年/流月计算 |
| D3 | 《周易》原文未入库 | Level 1-2证据缺失 | 注册64卦卦辞/爻辞/说卦 |
| D4 | Heluo信号未接入 | Signal覆盖不足 | 扩展SignalEngine |

### 5.2 中等断点（影响诊断精度）

| ID | 断点 | 影响 | 修复方向 |
|----|------|------|----------|
| D5 | Severity Schema 未实现 | 无法评估严重程度 | 实现多因子计算 |
| D6 | Ontology 映射不完整 | 类别不匹配 | 扩展预测类别至10类 |
| D7 | 四家注疏未入库 | Level 3证据缺失 | 注册王弼/程颐/朱熹/来知德 |

### 5.3 轻微断点（可后续优化）

| ID | 断点 | 影响 | 修复方向 |
|----|------|------|----------|
| D8 | 互体算法缺失 | Level 4证据不完整 | 实现互体推导 |
| D9 | 64卦映射未完整 | Level 5证据不完整 | 逐卦映射现代场景 |

---

## 六、V1.2 修复规范草案

### 6.1 八套 Schema 定义

#### Schema 1: Event Ontology V1

```python
# docs/event_ontology_v1.md
EVENT_ONTOLOGY_V1 = {
    "version": "1.0.0",
    "frozen_date": "2026-08-22",
    
    "domains": {
        "EDUCATION": {
            "events": ["EXAM", "ADMISSION", "GRADUATION", "DEGREE"],
            "signal_type": "ACTION",
            "temporal_granularity": "MONTHLY",
        },
        "CAREER": {
            "events": ["PROMOTION", "JOB_CHANGE", "RESIGNATION", "DEMOTION", "MAJOR_INCOME"],
            "signal_type": "OUTPUT",
            "temporal_granularity": "YEARLY",
        },
        "FAMILY": {
            "events": ["NEW_RELATIONSHIP", "MARRIAGE", "CHILD_BIRTH", "FAMILY_CHANGE", "PARENT_DEATH"],
            "signal_type": "RELATION",
            "temporal_granularity": "YEARLY",
        },
        "LIFE_EVENT": {
            "events": ["RELOCATION", "HEALTH_ISSUE", "LEGAL_ISSUE"],
            "signal_type": "CONSTRAINT",
            "temporal_granularity": "YEARLY",
        },
    },
    
    "metadata": {
        "total_events": 10,  # 与Golden Dataset对齐
        "signal_coverage": "每个domain需要至少1个USO信号覆盖",
        "temporal_alignment": "每个event_type定义对应的temporal_granularity"
    }
}
```

#### Schema 2: Canonical Signal Schema

```python
# docs/canonical_signal_schema_v1.md
CANONICAL_SIGNAL = {
    "version": "1.0.0",
    "frozen_date": "2026-08-22",
    
    "signal_schema": {
        "signal_id": "uuid",
        "source_engine": "bazi | heluo | ziwei | huangli | knowledge",
        "ontology_type": "ACTION | OUTPUT | CONSTRAINT | RESOURCE | SUPPORT | RELATION | REFLECTION | CHANGE",
        "direction": "INCREASE | STABLE | DECREASE",
        "polarity": "active | neutral | restricted",
        "strength": "low | moderate | high",
        "layer": "BASELINE | CYCLE_CONTEXT | DAILY_ACTIVATION",
        "confidence": 0.0-1.0,
        "evidence_refs": ["evidence_id_1", "evidence_id_2"],
        "rule_refs": ["rule_id_1", "rule_id_2"],
    },
    
    "multi_engine_aggregation": {
        "method": "weighted_voting",
        "weights": {
            "bazi": 0.3,
            "heluo": 0.3,
            "ziwei": 0.2,
            "huangli": 0.1,
            "knowledge": 0.1,
        },
        "threshold": 0.6,  # 置信度低于此值的信号标记为弱信号
    }
}
```

#### Schema 3: Temporal Evidence Schema

```python
# docs/temporal_evidence_schema_v1.md
TEMPORAL_EVIDENCE = {
    "version": "1.0.0",
    "frozen_date": "2026-08-22",
    
    "time_layers": {
        "BIRTH_TIME": {"granularity": "EXACT", "description": "出生时间（真太阳时）"},
        "LIFE_CYCLE": {"granularity": "10_YEARS", "description": "大运周期"},
        "ANNUAL": {"granularity": "YEARLY", "description": "流年"},
        "MONTHLY": {"granularity": "MONTHLY", "description": "流月"},
        "DAILY": {"granularity": "DAILY", "description": "流日"},
        "HOURLY": {"granularity": "HOURLY", "description": "流时"},
        "HELUA_CHAIN": {"granularity": "CUSTOM", "description": "河洛时间链"},
        "ZIWEI_INDICATORS": {"granularity": "CUSTOM", "description": "紫微时间指标"},
    },
    
    "event_activation": {
        "description": "事件激活窗口",
        "calculation": "基于多引擎时间信号收敛",
        "window_size": "根据event_type.temporal_granularity动态调整",
    }
}
```

#### Schema 4: Severity Schema

```python
# docs/severity_schema_v1.md
SEVERITY_SCHEMA = {
    "version": "1.0.0",
    "frozen_date": "2026-08-22",
    
    "severity_components": {
        "signal_strength": {"range": [0, 1], "description": "信号强度"},
        "multi_engine_agreement": {"range": [0, 1], "description": "多引擎一致性"},
        "temporal_convergence": {"range": [0, 1], "description": "时间收敛度"},
        "ontology_specificity": {"range": [0, 1], "description": "类别特异性"},
        "evidence_quality": {"range": [0, 1], "description": "证据质量"},
        "relational_coherence": {"range": [0, 1], "description": "关系连贯性"},
    },
    
    "severity_classes": {
        "LOW": {"range": [0, 0.3], "description": "低关注度"},
        "MODERATE": {"range": [0.3, 0.6], "description": "中等关注"},
        "HIGH": {"range": [0.6, 0.85], "description": "高度关注"},
        "CRITICAL": {"range": [0.85, 1.0], "description": "临界关注"},
    },
    
    "calculation": {
        "formula": "product_based",  # 乘积加权，非简单平均
        "weight_vector": [0.25, 0.20, 0.15, 0.15, 0.15, 0.10],  # 可配置
    }
}
```

#### Schema 5: Evidence Chain Schema

```python
# docs/evidence_chain_schema_v1.md
EVIDENCE_CHAIN = {
    "version": "1.0.0",
    "frozen_date": "2026-08-22",
    
    "evidence_level": {
        "LEVEL_1": {"name": "经典原点", "source": "周易原文/说卦/注疏", "requirement": "verbatim + cross_verified"},
        "LEVEL_2": {"name": "经典语境", "source": "易经自身结构", "requirement": "structural_mapping"},
        "LEVEL_3": {"name": "注疏传统", "source": "王弼/程颐/朱熹/来知德", "requirement": "commentary_attribution"},
        "LEVEL_4": {"name": "结构推导", "source": "卦体/五行/爻位推导", "requirement": "logical_chain"},
        "LEVEL_5": {"name": "现代映射", "source": "生活场景类比", "requirement": "contextual_mapping"},
    },
    
    "evidence_validation": {
        "cross_verification": "必须至少2个独立来源",
        "source_tracing": "每条证据必须标注来源",
        "level_restrictions": "禁止Level 1直接跳转到Level 5",
    }
}
```

#### Schema 6: Relational Interpretation Schema

```python
# docs/relational_interpretation_schema_v1.md
RELATIONAL_INTERPRETATION = {
    "version": "1.0.0",
    "frozen_date": "2026-08-22",
    
    "pipeline": {
        "step_1": "Signals → Relations (关系推断)",
        "step_2": "Relations → State (状态建模)",
        "step_3": "State → Event_Potential (事件潜力评估)",
        "step_4": "Event_Potential → Temporal_Activation (时间激活)",
        "step_5": "Temporal_Activation → Evidence (证据支撑)",
        "step_6": "Evidence → Final_Output (最终输出)",
    },
    
    "llm_constraints": {
        "input": "只能消费InterpretationInput（不能直接访问CalculationContext）",
        "output": "必须引用来源（source_references）",
        "forbidden": ["玄学术语", "自由联想", "评分式输出"],
        "required": ["证据链追溯", "关系推理过程", "状态描述"],
    }
}
```

#### Schema 7: Validation Dimensions Schema

```python
# docs/validation_dimensions_schema_v1.md
VALIDATION_DIMENSIONS = {
    "version": "1.0.0",
    "frozen_date": "2026-08-22",
    
    "dimensions": {
        "CALCULATION": {"description": "计算正确性", "validation": "external_fate_bench + internal_golden"},
        "SIGNAL": {"description": "信号生成", "validation": "coverage_rate + ontology_alignment"},
        "ONTOLOGY": {"description": "本体映射", "validation": "category_match_rate + direction_accuracy"},
        "TEMPORAL": {"description": "时间精度", "validation": "window_match_rate + granularity_alignment"},
        "SEVERITY": {"description": "严重程度", "validation": "severity_class_accuracy + confidence_calibration"},
        "INTERPRETATION": {"description": "关系解释", "validation": "evidence_chain_completeness + source_attribution"},
        "EVIDENCE": {"description": "证据链", "validation": "cross_verification_rate + level_distribution"},
        "CROSS_ENGINE_AGREEMENT": {"description": "多引擎一致性", "validation": "agreement_rate + weight_sensitivity"},
    }
}
```

#### Schema 8: Fix Priority Schema

```python
# docs/fix_priority_schema_v1.md
FIX_PRIORITY = {
    "version": "1.0.0",
    "frozen_date": "2026-08-22",
    
    "phases": {
        "PHASE_1": {
            "name": "V-Validation 规范冻结",
            "tasks": [
                "定义Validation Dimensions",
                "定义Failure Taxonomy", 
                "定义Event Ontology",
                "定义Signal Schema",
                "定义Temporal Schema",
                "定义Severity Schema",
                "定义Evidence Schema",
                "定义Relational Interpretation Schema",
            ],
            "priority": "P0",
            "timeline": "1周",
        },
        "PHASE_2": {
            "name": "Canonical Signal Engine 实现",
            "tasks": [
                "接入Heluo信号",
                "接入Ziwei信号",
                "接入Huangli信号",
                "接入Knowledge信号",
                "实现Multi-Engine Aggregation",
                "实现Signal Normalization",
            ],
            "priority": "P0",
            "timeline": "2周",
        },
        "PHASE_3": {
            "name": "Event Ontology 规范化",
            "tasks": [
                "扩展预测类别至10类",
                "实现Directionality（方向性）",
                "实现Temporal Granularity映射",
                "实现Ontology-Specificity计算",
            ],
            "priority": "P0",
            "timeline": "1周",
        },
        "PHASE_4": {
            "name": "Relational Interpretation Engine 实现",
            "tasks": [
                "实现HexagramSymbol（层A）",
                "实现LineSymbol（层B）",
                "实现ClassicalText（层C）",
                "实现ImageExpansion（层D）",
                "实现Relational Interpretation（LLM介入）",
                "实现Evidence Chain验证",
            ],
            "priority": "P0",
            "timeline": "3周",
        },
        "PHASE_5": {
            "name": "Temporal Engine 实现",
            "tasks": [
                "实现大运计算",
                "实现流年计算",
                "实现流月/流日/流时",
                "实现节候/卦气时间链",
                "实现Temporal Convergence计算",
            ],
            "priority": "P1",
            "timeline": "2周",
        },
        "PHASE_6": {
            "name": "V-Validation V2 重新运行",
            "tasks": [
                "重新运行六维度诊断",
                "新增Evidence维度诊断",
                "新增Cross-Engine Agreement诊断",
                "新增Temporal Convergence诊断",
                "新增Directionality诊断",
                "输出V1.2 Validation Report",
            ],
            "priority": "P1",
            "timeline": "1周",
        },
    }
}
```

---

## 七、Phase 执行计划

### Phase 1 — 冻结 V-Validation 规范（1周）

**目标**: 定义完整的验证体系

**任务**:
1. 定义 Validation Dimensions（8维度）
2. 定义 Failure Taxonomy（失败分类体系）
3. 定义 Event Ontology V1（10类事件规范）
4. 定义 Canonical Signal Schema
5. 定义 Temporal Evidence Schema
6. 定义 Severity Schema
7. 定义 Evidence Chain Schema
8. 定义 Relational Interpretation Schema

**产出**: `docs/V_VALIDATION_SPEC_V1.2.md`

---

### Phase 2 — 实现 Canonical Signal Engine（2周）

**目标**: 接入五大引擎信号

**任务**:
1. 扩展 SignalEngine 接收 HeluoInput
2. 实现 Heluo Signal 提取（卦象信号）
3. 实现 Ziwei Signal 提取（星曜信号）
4. 实现 Huangli Signal 提取（宜忌信号）
5. 实现 Knowledge Signal 提取（知识库信号）
6. 实现 Multi-Engine Aggregation
7. 实现 Signal Normalization（统一置信度）

**产出**: `tongshu/reasoning/canonical_signal_engine.py`

---

### Phase 3 — 实现 Event Ontology（1周）

**目标**: 扩展预测类别至10类

**任务**:
1. 定义 EVENT_ONTOLOGY_V1（含domain/type/subtype/direction/granularity）
2. 实现 Ontology Mapper（预测→实际类别映射）
3. 实现 Directionality（方向性检查：晋升vs离职）
4. 实现 Temporal Granularity 映射
5. 实现 Ontology-Specificity 计算

**产出**: `tongshu/spec/event_ontology_v1.py`

---

### Phase 4 — 实现 Relational Interpretation Engine（3周）

**目标**: 实现真正的关系解释链路

**任务**:
1. 实现 HexagramSymbol（层A：纯数据查询）
2. 实现 LineSymbol（层B：纯逻辑计算）
3. 实现 ClassicalText（层C：知识库检索）
4. 实现 ImageExpansion（层D：5级证据扩展）
5. 实现 Relational Interpretation（LLM介入点）
6. 实现 Evidence Chain 验证
7. 注册《周易》原文数据（P0）

**产出**: `tongshu/reasoning/yi_engine.py` + 知识库数据

---

### Phase 5 — 实现 Temporal Engine（2周）

**目标**: 实现动态时间计算

**任务**:
1. 实现 Life Cycle 计算（大运）
2. 实现 Annual 计算（流年）
3. 实现 Monthly/Daily/Hourly 计算
4. 实现 Temporal Convergence（多引擎时间收敛）
5. 实现 Event Activation Window 计算

**产出**: `tongshu/engines/temporal_engine.py`

---

### Phase 6 — V-Validation V2 重新运行（1周）

**目标**: 验证修复效果

**任务**:
1. 运行完整六维度诊断（新增Evidence维度）
2. 计算 Cross-Engine Agreement
3. 计算 Temporal Convergence
4. 计算 Directionality Accuracy
5. 输出 V1.2 Validation Report

**产出**: `docs/V_VALIDATION_REPORT_V1.2.md`

---

## 八、风险清单

| 风险 | 级别 | 缓解措施 |
|------|------|----------|
| 《周易》原文获取困难 | 中 | 优先注册通行本，次优先王弼注 |
| LLM Prompt工程复杂 | 中 | 分阶段实现，先基础再高级 |
| 多引擎信号冲突 | 低 | 实现Conflict Resolution规则 |
| 时间精度提高但预测仍错 | 中 | 保持11%基线，允许迭代优化 |
| 知识库注册工作量大 | 高 | Phase 4分批执行，先10卦再扩展 |

---

## 九、验收标准

### Phase 1 验收
- [ ] 8套Schema文档完整
- [ ] 无遗漏的维度定义
- [ ] 所有Schema可被代码引用

### Phase 2 验收
- [ ] SignalEngine 接收5引擎输入
- [ ] 至少1个Golden Case的Signal覆盖从44%→70%
- [ ] 多引擎Aggregation有明确权重

### Phase 3 验收
- [ ] 预测类别从3类→10类
- [ ] Directionality检查通过（PROMOTION≠RESIGNATION）
- [ ] Ontology Mismatch 从56.4%→30%

### Phase 4 验收
- [ ] Yi Engine四层全部实现
- [ ] Evidence Chain完整性≥80%
- [ ] LLM不直接访问CalculationContext
- [ ] 禁止跨级证据输出

### Phase 5 验收
- [ ] 时间预测窗口从±2年→±0.5年（或更精确）
- [ ] Temporal Miss 从67.8%→40%

### Phase 6 验收
- [ ] F1从13.8%→30%+
- [ ] 所有维度诊断通过
- [ ] 无新的架构断点

---

## 十、关键原则

1. **不修改算法，只实现架构** — BaziEngine/ZiweiEngine/HeluoEngine 不动
2. **不修改数据集** — golden_cases.json 冻结
3. **不修改评分公式** — F1计算规则冻结
4. **先定义Schema，再实现代码** — 所有Schema必须冻结后才能开始实现
5. **证据链必须完整** — 每条预测必须有可追溯的证据
6. **LLM只在最后介入** — 禁止AI在计算层生成原文或推导

---

**此报告基于V1.1诊断数据 + 全项目架构契约交叉验证生成。未经用户确认，不执行任何修复。**
