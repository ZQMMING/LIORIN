# V1.3 A1 — Engine → Component Inventory

**日期**: 2026-08-22
**类型**: READ-ONLY AUDIT
**状态**: FINAL

---

## 原则声明

本文档为只读审计产物，记录 V1.2 中所有 Engine 的 Component 级结构。
禁止修改生产代码、测试代码或任何算法实现。

---

## 一、Bazi Engine 组件清单

| 组件ID | 组件名 | 函数/类 | 来源文件 | 职责描述 |
|--------|--------|---------|---------|---------|
| BAZI-01 | Pillar (年柱) | `class Pillar` | bazi_engine.py | 单个干支柱数据模型 |
| BAZI-02 | 四柱计算 | `BaziEngine.compute()` | bazi_engine.py | 整体四柱计算入口 |
| BAZI-03 | 天干取数 | `stem_element()` | bazi_engine.py | 天干→五行元素映射 |
| BAZI-04 | 地支取数 | `branch_element()` | bazi_engine.py | 地支→五行元素映射 |
| BAZI-05 | 时辰分支 | `hour_branch()` | bazi_engine.py | 小时→地支时辰映射 |
| BAZI-06 | 时辰天干 | `hour_stem_from_day_stem()` | bazi_engine.py | 日干→时干映射规则 |
| BAZI-07 | sxtwl 计算 | `_compute_with_sxtwl()` | bazi_engine.py | 基于寿星天文历的实际计算 |
| BAZI-08 | 简化计算 | `_compute_simple()` | bazi_engine.py | 无sxtwl时的备选计算路径 |
| BAZI-09 | 大运计算 | `_compute_luck_pillars()` | bazi_engine.py | 大运排盘算法 |
| BAZI-10 | 十神映射 | 见 chain/schemas.py | spec/evidence_chain.py | 十神→Ontology 映射 |

---

## 二、Heluo Engine 组件清单

| 组件ID | 组件名 | 函数/类 | 来源文件 | 职责描述 |
|--------|--------|---------|---------|---------|
| HELUO-01 | 天干取数 | `build_stem_number_map()` | heluo/hetu_luoshu.py | 天干→洛书数映射 |
| HELUO-02 | 地支取数 | `build_branch_number_map()` | heluo/hetu_luoshu.py | 地支→洛书数映射 |
| HELUO-03 | 天数计算 | `compute_tian_di_numbers()` | heluo/hetu_luoshu.py | 天干地支→天数计算 |
| HELUO-04 | 地数计算 | `compute_tian_di_numbers()` | heluo/hetu_luoshu.py | 天干地支→地数计算 |
| HELUO-05 | 归一化(天) | `normalize_tian_shu()` | heluo/numbers.py | 天数遇10去十归一 |
| HELUO-06 | 归一化(地) | `normalize_di_shu()` | heluo/numbers.py | 地数遇10去十归一 |
| HELUO-07 | 洛书映射 | `number_to_trigram()` | heluo/numbers.py | 归一化数→八卦 |
| HELUO-08 | 卦名计算 | `get_hexagram_name()` | heluo/numbers.py | 上下卦→六十四卦名 |
| HELUO-09 | 先天卦计算 | `determine_prenatal_hexagram()` | heluo/prenatal.py | 天地数→先天卦 |
| HELUO-10 | 元堂定位 | `find_yuantang()` | heluo/yuan_tang.py | 先天卦→元堂卦 |
| HELUO-11 | 元堂飞支 | `_is_pure_yang()/_is_pure_yin()` | heluo/yuan_tang.py | 纯阳/纯阴元堂处理 |
| HELUO-12 | 后天换卦 | `compute_postnatal()` | heluo/postnatal.py | 先天卦→后天卦(两步变换) |
| HELUO-13 | 流年计算 | `compute_liu_nian()` | heluo/time_sequence.py | 流年卦计算 |
| HELUO-14 | 流月计算 | `compute_liu_yue()` | heluo/time_sequence.py | 流月卦计算 |
| HELUO-15 | 流日计算 | `compute_liu_ri()` | heluo/time_sequence.py | 流日卦计算 |
| HELUO-16 | 节候卦 | `compute_daily_hexagram()` | heluo/temporal.py | 每日节候卦 |
| HELUO-17 | 卦气计算 | `compute_timeline()` | heluo/temporal.py | 卦气时序 |
| HELUO-18 | 天地数归一化 | `_drop_ten()` | heluo/hetu_luoshu.py | 遇10去十算法 |
| HELUO-19 | 天地数求和 | `_sum_with_base()` | heluo/hetu_luoshu.py | 带基准的求和 |
| HELUO-20 | 本命卦验证 | `verify_golden_case()` | heluo/canonical.py | 纪晓岚等黄金案例验证 |
| HELUO-21 | 全案例验证 | `run_all_golden_cases()` | heluo/canonical.py | 批量黄金案例验证 |
| HELUO-22 | 元堂纯阳检测 | `_is_pure_yang()` | heluo/yuan_tang.py | 六爻皆阳判定 |
| HELUO-23 | 元堂纯阴检测 | `_is_pure_yin()` | heluo/yuan_tang.py | 六爻皆阴判定 |
| HELUO-24 | 上下卦提取 | `_lines_to_trigram()` | heluo/postnatal.py | 六爻→上下卦 |
| HELUO-25 | 大運计算 | `is_shun_pai()`等 | heluo/dayu.py | 大運顺逆排法 |
| HELUO-26 | 输入准备 | `prepare_heluo_input()` | heluo/input.py | CalculationContext→HeluoInput |
| HELUO-27 | 解释计算 | `compute()` | heluo/interpretation.py | 最终解释生成 |
| HELUO-28 | 因子权重 | `_compute_factor_weights()` | heluo/interpretation.py | 五行因子权重计算 |
| HELUO-29 | 时间衰减 | `_calculate_time_decay()` | heluo/interpretation.py | 距离当前时间衰减 |
| HELUO-30 | 经典一致性 | `evaluate_classical_consistency()` | heluo/metrics_v2.py | 与经典原文对齐度 |

---

## 三、Ziwei Engine 组件清单

| 组件ID | 组件名 | 函数/类 | 来源文件 | 职责描述 |
|--------|--------|---------|---------|---------|
| ZW-01 | 时间索引 | `time_index_from_hour()` | ziwei_engine.py | 小时→地支索引 |
| ZW-02 | 命盘模型 | `class ZiweiChart` | ziwei_engine.py | 紫微命盘数据模型 |
| ZW-03 | 主引擎 | `ZiweiEngine.compute()` | ziwei_engine.py | 紫微斗数主计算入口 |
| ZW-04 | iztro 集成 | `_compute_via_iztro()` | ziwei_engine.py | 通过 iztro Python 库计算 |
| ZW-05 | Stub 模式 | `_stub()` | ziwei_engine.py | 无 iztro 时的降级计算 |
| ZW-06 | 信号提取 | `extract_baseline_signal()` | ziwei_engine.py | 从命盘中提取基准信号 |
| ZW-07 | 十四主星映射 | 见 test_ziwei_engine.py | ziwei_engine.py | 主星→符号映射表 |
| ZW-08 | 四化效果 | 见 test_ziwei_engine.py | ziwei_engine.py | 四化(禄权科忌)映射表 |
| ZW-09 | 命宫计算 | 隐含于 _compute_via_iztro() | ziwei_engine.py | 命宫位置计算 |
| ZW-10 | 十二宫排布 | 隐含于 _compute_via_iztro() | ziwei_engine.py | 十二宫位置排布 |

---

## 四、Huangli Engine 组件清单

| 组件ID | 组件名 | 函数/类 | 来源文件 | 职责描述 |
|--------|--------|---------|---------|---------|
| HL-01 | 农历月份标签 | `_lunar_month_label()` | huangli_engine.py | 农历月中文标签 |
| HL-02 | 黄历日数据 | `class HuangliDay` | huangli_engine.py | 单日黄历数据模型 |
| HL-03 | 注册表加载 | `_load_registry()` | huangli_engine.py | 加载宜忌注册表 |
| HL-04 | 单日查询 | `get_day()` | huangli_engine.py | 查询指定日期的黄历信息 |
| HL-05 | 干支计算 | 内置于 sxtwl | huangli_engine.py | 基于 sxtwl 的干支 |
| HL-06 | 节气计算 | 内置于 sxtwl | huangli_engine.py | 基于 sxtwl 的节气 |
| HL-07 | 建除循环 | 内置规则 | huangli_engine.py | 建除十二日循环规则 |
| HL-08 | 宜忌规则 | 注册表驱动 | huangli_engine.py | 宜忌判断规则 |
| HL-09 | 神煞方位 | 注册表驱动 | huangli_engine.py | 神煞计算 |
| HL-10 | 二十八宿 | 注册表驱动 | huangli_engine.py | 二十八宿值日 |

---

## 五、Yi Engine 组件清单

| 组件ID | 组件名 | 函数/类 | 来源文件 | 职责描述 |
|--------|--------|---------|---------|---------|
| YI-01 | 主解释器 | `YiEngine.interpret()` | yi/__init__.py | Yi 关系式解释入口 |
| YI-02 | 经典文本查询 | `get_classical_text()` | yi/classical_text.py | 查询易经经典原文 |
| YI-03 | 爻辞查询 | `get_yao_ci()` | yi/classical_text.py | 查询爻辞 |
| YI-04 | 六十四卦符号 | `get_hexagram_symbol()` | yi/hexagram_symbol.py | 卦名→符号映射 |
| YI-05 | 体用关系 | `get_ti_yong_relation()` | yi/hexagram_symbol.py | 体用生克关系 |
| YI-06 | 错卦计算 | `_get_cuo_gua()` | yi/hexagram_symbol.py | 错卦(对卦) |
| YI-07 | 综卦计算 | `_get_zong_gua()` | yi/hexagram_symbol.py | 综卦(反卦) |
| YI-08 | 互卦计算 | `_get_hu_gua()` | yi/hexagram_symbol.py | 互卦 |
| YI-09 | 象义扩展 | `expand_image()` | yi/image_expansion.py | 象义层级扩展 |
| YI-10 | 象义链验证 | `validate_image_chain()` | yi/image_expansion.py | 验证象义链完整性 |
| YI-11 | 爻位分析 | `analyze_line_symbol()` | yi/line_symbol.py | 爻位当位/中正判断 |
| YI-12 | 承乘比应 | `compute_cheng_cheng_bi_ying()` | yi/line_symbol.py | 爻间关系计算 |
| YI-13 | 关系式解释 | `relational_interpretation()` | yi/relational_interpretation.py | STATE→OPPORTUNITY/RISK/REMEDIATION/ACTION |
| YI-14 | 术语约束检查 | 隐含于 relational_interpretation() | yi/relational_interpretation.py | 17术语禁止列表检查 |

---

## 六、Evidence Chain 组件清单

| 组件ID | 组件名 | 函数/类 | 来源文件 | 职责描述 |
|--------|--------|---------|---------|---------|
| EV-01 | 证据链上下文 | `class EvidenceChainContext` | chain/chain_context.py | 链式证据管理核心 |
| EV-02 | 溯源追踪 | `trace_to_source()` | chain/chain_context.py | SOURCE→PASSAGE→RULE→CLAIM 追踪 |
| EV-03 | 证明验证 | `verify_provenance()` | chain/chain_context.py | 验证引用链完整性 |
| EV-04 | 链验证 | `validate_chain()` | chain/chain_context.py | 整体证据链验证 |
| EV-05 | 源注册 | `add_source()` | chain/chain_context.py | 添加文献来源 |
| EV-06 | 段落注册 | `add_passage()` | chain/chain_context.py | 添加经典段落 |
| EV-07 | 证据注册 | `add_evidence()` | chain/chain_context.py | 添加论证证据 |
| EV-08 | 声称注册 | `add_claim()` | chain/chain_context.py | 添加声称 |
| EV-09 | 草稿晋升 | `promote_draft()` | chain/chain_context.py | Draft→Claim 晋升流程 |
| EV-10 | 来源模型 | `class Source` | spec/evidence_chain.py | 文献来源数据模型 |
| EV-11 | 段落模型 | `class Passage` | spec/evidence_chain.py | 经典段落数据模型 |
| EV-12 | 声称模型 | `class Claim` | spec/evidence_chain.py | 声称数据模型 |
| EV-13 | 证据模型 | `class Evidence` | spec/evidence_chain.py | 证据数据模型 |
| EV-14 | 证据等级 | `class EvidenceLevel` | spec/evidence_chain.py | 5级证据等级枚举 |

---

## 七、Signal 组件清单

| 组件ID | 组件名 | 函数/类 | 来源文件 | 职责描述 |
|--------|--------|---------|---------|---------|
| SIG-01 | 信号组 | `class SignalGroup` | signal/aggregator.py | 信号分组容器 |
| SIG-02 | 聚合器 | `class CanonicalSignalAggregator` | signal/aggregator.py | 全局信号聚合 |
| SIG-03 | 信号收集 | `collect()` | signal/aggregator.py | 单个信号收集 |
| SIG-04 | 批量收集 | `collect_batch()` | signal/aggregator.py | 批量信号收集 |
| SIG-05 | 全量验证 | `validate_all()` | signal/aggregator.py | 所有信号验证 |
| SIG-06 | 去重 | `deduplicate()` | signal/aggregator.py | 重复信号去重 |
| SIG-07 | 事件过滤 | `get_by_event()` | signal/aggregator.py | 按事件类型过滤 |
| SIG-08 | 域过滤 | `get_by_domain()` | signal/aggregator.py | 按领域过滤 |
| SIG-09 | 引擎过滤 | `get_by_engine()` | signal/aggregator.py | 按引擎过滤 |
| SIG-10 | 适配器注册 | 见 test_adapters.py | signal/adapters/*.py | 各引擎适配器 |

---

## 八、Temporal 组件清单

| 组件ID | 组件名 | 函数/类 | 来源文件 | 职责描述 |
|--------|--------|---------|---------|---------|
| TP-01 | 时间对齐 | `TemporalAlignmentEngine.compute_overlap()` | temporal/alignment.py | 预测窗口与评估窗口重叠计算 |
| TP-02 | 多信号对齐 | `TemporalAlignmentEngine.align_signals()` | temporal/alignment.py | 多信号时间对齐 |
| TP-03 | 粒度归一化 | `TemporalAlignmentEngine.normalize_to_common_granularity()` | temporal/alignment.py | 年/月/日粒度统一 |
| TP-04 | 收敛引擎 | `TemporalConvergenceEngine.add_signal()` | temporal/convergence.py | 添加时间信号 |
| TP-05 | 收敛计算 | `TemporalConvergenceEngine.compute_convergence()` | temporal/convergence.py | 多信号收敛计算 |
| TP-06 | 收敛结果 | `class TemporalConvergence` | temporal/convergence.py | 收敛结果数据模型 |

---

## 九、Validation V1.2 组件清单

| 组件ID | 组件名 | 函数/类 | 来源文件 | 职责描述 |
|--------|--------|---------|---------|---------|
| VAL-01 | 9维度定义 | `class ValidationDimension` | validation/v12/dimensions.py | 9个验证维度枚举 |
| VAL-02 | 状态机 | `class DimensionStatus` | validation/v12/dimensions.py | 6种验证状态枚举 |
| VAL-03 | 协议一致性 | `test_protocol_consistency` | spec/test_validation_dimensions.py | 9维度+6状态完整性 |
| VAL-04 | 不可变性 | `test_enforce_read_only_exists` | spec/test_validation_dimensions.py | 验证维度只读保护 |
| VAL-05 | 一致性引擎 | `class AgreementEvidenceEngine` | validation/v12/agreement_evidence.py | 多引擎一致性计算 |
| VAL-06 | 一致性结果 | `class AgreementResult` | validation/v12/agreement_evidence.py | 一致性比率计算 |
| VAL-07 | 失败分类 | `class FailureType` | validation/v12/failure_taxonomy.py | 15种失败类型枚举 |
| VAL-08 | 失败记录 | `class FailureRecord` | validation/v12/failure_taxonomy.py | 失败详情记录 |
| VAL-09 | 维度分析 | `class DimensionFailureAnalysis` | validation/v12/failure_taxonomy.py | 维度级失败分析 |
| VAL-10 | 微F1计算 | `TestG5_7_MicroF1` | validation_v12/test_g5_gate.py | 微F1准确率计算 |
| VAL-11 | 宏F1计算 | `TestG5_8_MacroF1` | validation_v12/test_g5_gate.py | 宏F1辅助计算 |
| VAL-12 | 边界条件 | `TestG5_9_BoundaryConditions` | validation_v12/test_g5_gate.py | 空输入/完全匹配/半匹配 |

---

## 十、Forward Validation 组件清单

| 组件ID | 组件名 | 函数/类 | 来源文件 | 职责描述 |
|--------|--------|---------|---------|---------|
| FV-01 | 前瞻引擎 | `class ForwardValidationEngine` | forward_validation/engine.py | 前瞻验证主引擎 |
| FV-02 | 预测创建 | `create_prediction()` | forward_validation/engine.py | 创建预测记录 |
| FV-03 | 事件评估 | `evaluate_event()` | forward_validation/engine.py | 评估预测与实际事件 |
| FV-04 | 泄漏检测 | 隐含于 evaluate_event() | forward_validation/engine.py | 预测时间 vs 事件时间 |
| FV-05 | 预测记录 | `class PredictionRecord` | forward_validation/engine.py | 预测数据模型 |
| FV-06 | 评估记录 | `class EvaluationRecord` | forward_validation/engine.py | 评估数据模型 |
| FV-07 | 窗口定义 | `class PredictionWindow` | v_validation/freeze.py | 预测生成时间窗口 |
| FV-08 | 容差定义 | `get_tolerance()` | v_validation/freeze.py |  severity 依赖的容差 |
| FV-09 | 冻结协议 | `class FreezeProtocol` | v_validation/freeze.py | 完整冻结协议实现 |
| FV-10 | 快照提交 | `commit_hash` | v_validation/freeze.py | 提交时记录commit哈希 |

---

## 十一、Spec 组件清单

| 组件ID | 组件名 | 函数/类 | 来源文件 | 职责描述 |
|--------|--------|---------|---------|---------|
| SP-01 | 信号Schema | `class CanonicalSignal` | spec/canonical_signal.py | 规范信号数据模型 |
| SP-02 | 信号层枚举 | `class SignalLayer` | spec/canonical_signal.py | 5级信号层 |
| SP-03 | 引擎枚举 | `class SourceEngine` | spec/canonical_signal.py | 引擎类型枚举 |
| SP-04 | 时间范围 | `class SignalTemporalScope` | spec/canonical_signal.py | 年/月/日时间范围 |
| SP-05 | 事件本体 | `EventDefinition` | spec/event_ontology_v1.py | 17种事件类型定义 |
| SP-06 | 域枚举 | `class Domain` | spec/event_ontology_v1.py | 4领域枚举 |
| SP-07 | 方向枚举 | `class EventDirection` | spec/event_ontology_v1.py | 5方向枚举 |
| SP-08 | 粒度枚举 | `class TemporalGranularity` | spec/event_ontology_v1.py | 3粒度枚举 |
| SP-09 | 本体不变量 | `validate_ontology_invariants()` | spec/event_ontology_v1.py | 17事件类型完整性校验 |
| SP-10 | 失败分类 | `class FailureType` | spec/failure_taxonomy.py | 15种失败类型 |
| SP-11 | 严重程度 | `class Severity` | spec/severity.py | 严重程度评分逻辑 |
| SP-12 | 验证维度 | `class ValidationDimension` | spec/validation_dimensions.py | 9维度定义 |

---

## 十二、组件总数统计

| 引擎 | 组件数 |
|------|--------|
| Bazi | 10 |
| Heluo | 30 |
| Ziwei | 10 |
| Huangli | 10 |
| Yi | 14 |
| Evidence | 14 |
| Signal | 10 |
| Temporal | 6 |
| Validation V1.2 | 12 |
| Forward Validation | 10 |
| Spec | 12 |
| **总计** | **138** |

---

**报告结束**
**下一步**: A1.2 Component → Test Mapping
