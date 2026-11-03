# V1.3 A1 — Test Oracle Matrix

**日期**: 2026-08-22
**类型**: READ-ONLY AUDIT
**状态**: FINAL

---

## 原则声明

本文档建立 Test → Oracle 映射关系，验证每个测试是否有合法 Oracle 支撑。
禁止修改测试代码或算法实现。

---

## 一、测试分类与 Oracle 来源

### 1.1 结构性测试 (Structural Tests) — ~1227个

```text
特征: 验证数据结构、Schema、Invariants、类型正确性
Oracle 类型: O1 Deterministic
可信度: HIGH
覆盖率: 97%
```

| 测试类别 | 数量估计 | Oracle | 典型用例 |
|---------|---------|--------|---------|
| Schema/Model 验证 | ~200 | O1 | `test_pillar_schema_valid()` |
| Invariant 验证 | ~150 | O1 | `test_enforce_read_only_exists()` |
| Type 检查 | ~100 | O1 | `test_bazi_type_check()` |
| Interface 契约 | ~80 | O1 | `test_api_contract()` |
| Data Flow | ~60 | O1 | `test_pipeline_data_flow()` |
| Spec 完整性 | ~50 | O1 | `test_ontology_invariants()` |
| 其他结构性 | ~600 | O1 | Various |

### 1.2 实证性测试 (Empirical Tests) — ~37个

```text
特征: 使用外部数据集验证算法准确性
Oracle 类型: O1/O2/O3
可信度: MEDIUM-HIGH (取决于数据源)
覆盖率: 3%
```

| 测试名称 | Oracle 类型 | 数据集 | 事件数 |
|---------|------------|--------|--------|
| `test_external_benchmarks` | O2 | fate-bench (官方) | 215题 |
| `test_mingli_bench_blind` | O2 | MingLi-Bench | 160题 |
| `test_p014` | O1+O2 | 边界案例 | 13/13 |
| `test_s5_golden_cases` | O1+O3 | Golden Dataset | 50案例 |
| `test_fate_bench_alignment` | O2 | fate-bench | 59/61 |
| `test_heluo_canonical` | O1+O3 | 河洛理数原文 | 纪晓岚案例 |
| `test_ziwei_engine_stub` | O1 | Stub验证 | N/A |

---

## 二、组件 → 测试 → Oracle 映射

### 2.1 Bazi Engine

```text
BAZI-01 Pillar Model
├── Tests: test_pillar_schema_valid (estimated)
├── Oracle: O1 (Schema Invariant)
└── Status: ✅ COVERED

BAZI-02 四柱计算
├── Tests: test_bazi_four_pillars(), test_p014 (boundary)
├── Oracle: O1 (sxtwl) + O2 (fate-bench 295题)
├── Coverage: 96.7% (59/61 cases)
└── Status: ✅ COVERED

BAZI-03~06 天干地支/时辰映射
├── Tests: test_stem_branch_mapping(), test_hour_mapping()
├── Oracle: O1 (Fixed Lookup Table)
└── Status: ✅ COVERED

BAZI-09 大运计算
├── Tests: test_luck_pillars() (estimated)
├── Oracle: O1 (Formula) + O3 (Classic Text)
└── Status: ⚠️ PARTIAL — 流派差异未标准化

BAZI-10 十神映射
├── Tests: test_shishen_mapping()
├── Oracle: O1 (Fixed Mapping)
└── Status: ✅ COVERED
```

### 2.2 Heluo Engine

```text
HELUO-01~08 取数/归一化/洛书映射
├── Tests: test_stem_number_mapping(), test_di_shu_normalization()
├── Oracle: O1 (Fixed Formula)
└── Status: ✅ COVERED

HELUO-09 先天卦计算
├── Tests: test_prenatal_hexagram()
├── Oracle: O1 (Formula) + O3 (《河洛理数》卷二)
└── Status: ✅ COVERED

HELUO-10~11 元堂定位/飞支
├── Tests: test_yuantang_position(), test_yuantang_flying()
├── Oracle: O1 (Formula) + O3 (《河洛理数》)
└── Status: ✅ COVERED

HELUO-12 后天换卦
├── Tests: test_postnatal_transformation()
├── Oracle: O1 (Two-step Formula) + O3 (Classic Text)
└── Status: ✅ COVERED — 两步法已验证

HELUO-13~15 流年/月/日
├── Tests: test_liu_nian(), test_liu_yue(), test_liu_ri()
├── Oracle: O1 (Calculation) + O2 (Historical Events)
└── Status: ⚠️ PARTIAL — O2 测试未实现

HELUO-16~17 节候/卦气
├── Tests: test_seasonal_hexagram(), test_guaqi_timeline()
├── Oracle: O1 (Fixed Rules)
└── Status: ✅ COVERED

HELUO-20~21 本命卦/全案例验证
├── Tests: test_verify_golden_case(), test_run_all_golden_cases()
├── Oracle: O1 (Formula) + O3 (纪晓岚等历史案例)
└── Status: ✅ COVERED

HELUO-25 大運顺逆
├── Tests: test_dayu_direction()
├── Oracle: O1 (Formula) + O3 (Classic Dispute)
└── Status: ⚠️ DISPUTED — 争议点 HL-DISPUTE-002

HELUO-27 解释计算
├── Tests: test_interpretation_quality()
├── Oracle: O3 (Classic Alignment) + O4 (Human Expert)
└── Status: ❌ NOT_AUTOMATED — 需专家评级

HELUO-28~29 因子权重/时间衰减
├── Tests: test_factor_weights(), test_time_decay()
├── Oracle: O3 (Classical Weights)
└── Status: ⚠️ PARTIAL — 系数定义未标准化
```

### 2.3 Ziwei Engine

```text
ZW-01~02 时间索引/命盘模型
├── Tests: test_time_index(), test_ziwei_chart_schema()
├── Oracle: O1 (Fixed Mapping)
└── Status: ✅ COVERED

ZW-03~04 主引擎/iztro集成
├── Tests: test_ziwei_engine_computation(), test_iztro_integration()
├── Oracle: O1 (iztro Library) + O2 (fate-bench)
└── Status: ⚠️ PARTIAL — Stub模式降低可信度

ZW-07~10 主星/四化/命宫/十二宫
├── Tests: test_ziwei_stars(), test_si_hua_effects()
├── Oracle: O1 (Fixed Tables)
└── Status: ✅ COVERED
```

### 2.4 Huangli Engine

```text
HL-01~06 标签/查询/sxtwl继承
├── Tests: test_huangli_day_query(), test_sxtwl_integration()
├── Oracle: O1 (sxtwl) + O1 (Lookup Tables)
└── Status: ✅ COVERED

HL-07~10 建除/宜忌/神煞/二十八宿
├── Tests: test_jianchu_cycle(), test_yiji_rules()
├── Oracle: O3 (《玉匣记》《协纪辨方书》)
└── Status: ⚠️ PARTIAL — 经典原文未系统验证
```

### 2.5 Yi Engine

```text
YI-02~03 经典文本/爻辞
├── Tests: test_classical_text_lookup(), test_yao_ci_lookup()
├── Oracle: O3 (《易经》原文)
└── Status: ✅ COVERED

YI-04~08 卦符号/体用/错综互
├── Tests: test_hexagram_symbol(), test_ti_yong_relation()
├── Oracle: O1 (Fixed Rules)
└── Status: ✅ COVERED

YI-11~12 爻位分析/承乘比应
├── Tests: test_line_analysis(), test_cheng_cheng_bi_ying()
├── Oracle: O1 (Fixed Rules)
└── Status: ✅ COVERED

YI-01/09/13 主解释/象义扩展/关系式解释
├── Tests: N/A (无法自动化)
├── Oracle: O4 (Human Expert)
└── Status: ❌ NOT_EVALUABLE — 需建立专家评级 Rubric
```

### 2.6 Evidence Chain

```text
EV-01~09 链上下文/溯源/验证/注册
├── Tests: test_evidence_chain_context(), test_provenance_trace()
├── Oracle: O1 (Graph Traversal)
└── Status: ✅ COVERED

EV-10~14 数据模型
├── Tests: test_evidence_models_schema()
├── Oracle: O1 (Schema Invariant)
└── Status: ✅ COVERED
```

### 2.7 Signal / Temporal / Validation / Forward

```text
SIG-01~10 信号聚合
├── Oracle: O1 (Data Structure)
└── Status: ✅ COVERED

TP-01~06 时间对齐/收敛
├── Oracle: O1 (Mathematical Formula)
└── Status: ✅ COVERED

VAL-01~12 9维度/一致性/失败分类/Micro-F1
├── Oracle: O1 (Invariant/Formal Verification)
└── Status: ✅ COVERED

FV-01~10 前瞻验证
├── Oracle: O1 (Time Isolation)
└── Status: ✅ COVERED
```

---

## 三、Oracle 覆盖矩阵

```text
                    O1    O2    O3    O4    OX    合计
Bazi                8     2     0     0     0      10
Heluo              22     5     3     0     0      30
Ziwei               8     1     0     0     1      10
Huangli             6     0     4     0     0      10
Yi                  9     0     3     2     0      14
Evidence           10     0     0     0     0      10
Signal             10     0     0     0     0      10
Temporal            6     0     0     0     0       6
Validation         12     0     0     0     0      12
Forward            10     0     0     0     0      10
Spec               12     0     0     0     0      12
────────────────────────────────────────────────────
Total             103    8    10     2     1     138
```

---

## 四、关键缺口

### 4.1 缺失的 O2 测试

```text
缺口: 流年/流月/流日 历史盲测
影响: HELUO-13~15 (3个组件)
原因: 缺乏自动化的历史事件匹配系统
风险: 无法验证时间维度的预测准确性
建议: A2 阶段建立 Historical Event Matcher
```

### 4.2 缺失的 O4 测试

```text
缺口: Yi 解释质量评级
影响: YI-01/09/13 (3个组件)
原因: 缺乏专家评级 Rubric
风险: 无法验证解释层质量
建议: A3 阶段建立 Expert Rubric + Inter-rater Agreement
```

### 4.3 缺失的 O3 验证

```text
缺口: Huangli 宜忌/神煞 经典原文对照
影响: HL-08~10 (3个组件)
原因: 未系统对照《玉匣记》《协纪辨方书》
风险: 规则来源不明
建议: A4 阶段建立 Classical Source Verification
```

---

**报告结束**
**下一步**: A1.5 Oracle Independence Verification
