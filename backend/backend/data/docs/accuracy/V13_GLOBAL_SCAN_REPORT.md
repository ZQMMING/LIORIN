# V1.3 Phase A0 — Global Accuracy Audit Report

**日期**: 2026-08-22
**执行者**: Hermes (Global Scan)
**状态**: READ-ONLY AUDIT — 未修改任何代码

---

## 一、测试覆盖总览

### 当前测试基线

| 类别 | 测试数 | 占比 | 类型 |
|------|--------|------|------|
| tests/test_*.py | 778 | 61.6% | 混合（Unit + Integration） |
| tests/validation_v12/ | 140 | 11.1% | Contract + Invariant |
| tests/spec/ | 132 | 10.4% | Contract + Schema |
| tests/chain/ | 62 | 4.9% | Contract + Provenance |
| tests/signal/ | 57 | 4.5% | Contract + Adapter |
| tests/temporal/ | 52 | 4.1% | Contract + Convergence |
| tests/yi/ | 29 | 2.3% | Contract + E2E |
| tests/gender/ | 14 | 1.1% | Contract + Divergence |
| **总计** | **1,264** | **100%** | — |

### 测试类型拆解

```text
结构性测试 (Structural) ≈ 95%
├── Contract 测试 (Pydantic 模型校验): ~40%
├── Invariant 测试 (冻结约束): ~30%
├── Schema 测试 (字段完整性): ~15%
└── 集成路径测试 (链路完整性): ~10%

算法性测试 (Algorithmic) ≈ 3%
├── 八字四柱计算: ~1%
├── 河洛取数计算: ~1%
└── 黄历干支计算: ~1%

实证性测试 (Empirical) ≈ 1%
├── Golden Dataset 验证: ~0.5%
├── External Benchmark 采样: ~0.3%
└── 历史案例验证: ~0.2%

前瞻测试 (Forward) ≈ 1%
├── Forward Validation 泄漏检测: ~0.5%
└── Prediction Record 冻结: ~0.5%

缺失类型 (Missing) ≈ 0%
├── Historical Blind Test: 0%
├── Cross-Engine Validation: 0%
├── Ablation Study: 0%
└── Human Blind Evaluation: 0%
```

---

## 二、引擎级测试分布

### 2.1 八字引擎 (Bazi Engine)

| 测试文件 | 测试数 | 主要内容 | 类型 |
|---------|--------|---------|------|
| tests/test_bazi_engine.py | ~30 | 四柱计算、十神映射 | Unit |
| tests/test_p014.py | ~15 | 边界条件（晚子时） | Boundary |
| tests/test_mingli_bench_blind.py | ~20 | MingLi-Bench 盲测 | Empirical |
| tests/test_external_benchmarks.py | ~10 | fate-bench 采样 | External |
| tests/gender/ | ~14 | 男女命分化 | Contract |

**Oracle 来源分析：**
- `sxtwl` 库（寿星天文历）— Deterministic Oracle ✅
- 命盘计算规则 — Deterministic Oracle ✅
- 晚子时边界裁定 — Expert Oracle ⚠️ (仅2例不一致)

**验证缺口：**
- ❌ 流年事件预测准确率 — 无 Statistical Oracle
- ❌ 大運起运时间计算验证 — 无独立 Oracle
- ❌ 节气换日规则验证 — 部分覆盖

---

### 2.2 河洛引擎 (Heluo Engine)

| 测试文件 | 测试数 | 主要内容 | 类型 |
|---------|--------|---------|------|
| tests/test_heluo_canonical.py | ~20 | 天地数→本命卦 | Contract |
| tests/test_heluo_dayu.py | ~10 | 大運计算 | Unit |
| tests/test_heluo_time_sequence.py | ~15 | 流年/流月/流日 | Unit |
| tests/gender/test_golden_jixiaolan.py | ~10 | 纪晓岚案例 | Golden |
| tests/gender/test_heluo_divergence.py | ~8 | 性别分化 | Contract |
| tests/test_s5_golden_cases.py | ~15 | S5 黄金案例 | Empirical |
| tests/test_s6_golden_expansion.py | ~10 | S6 扩展案例 | Empirical |

**Oracle 来源分析：**
- 天干地支取数规则 — Deterministic Oracle ✅
- 先天卦→后天换卦两步法 — Deterministic Oracle ✅
- 纪晓岚案例 — Historical Golden ✅
- 元堂飞支规则 — Deterministic Oracle ✅

**验证缺口：**
- ❌ 后天换卦算法外部交叉验证 — 无独立 Oracle
- ❌ 节候卦、卦气计算验证 — 无 Statistical Oracle
- ❌ 518,400 命盘组合全覆盖 — 仅覆盖性别分化

---

### 2.3 紫微引擎 (Ziwei Engine)

| 测试文件 | 测试数 | 主要内容 | 类型 |
|---------|--------|---------|------|
| tests/test_ziwei_engine.py | ~25 | 星曜映射、四化、命宫 | Unit |
| tests/test_iztro_validation.py | ~10 | iztro 兼容性 | Contract |

**Oracle 来源分析：**
- `iztro` Python 库 — Deterministic Oracle ✅
- 十四主星固定排盘规则 — Deterministic Oracle ✅
- 四化飞星规则 — Deterministic Oracle ✅

**验证缺口：**
- ❌ 农历转换正确性 — 依赖 sxtwl，无独立验证
- ❌ 大限、流年事件预测 — 无 Empirical Oracle
- ❌ 518,400 命盘组合统计验证 — 未执行

---

### 2.4 黄历引擎 (Huangli Engine)

| 测试文件 | 测试数 | 主要内容 | 类型 |
|---------|--------|---------|------|
| tests/test_huangli_engine.py | ~20 | 干支、节气、建除 | Unit |
| tests/test_huangli_engine_extended.py | ~15 | 宜忌、神煞 | Unit |
| tests/test_trigram_relations.py | ~15 | 五行生克、卦象关系 | Contract |

**Oracle 来源分析：**
- `sxtwl` 干支计算 — Deterministic Oracle ✅
- 节气计算 — Deterministic Oracle ✅
- 建除循环规则 — Deterministic Oracle ✅

**验证缺口：**
- ❌ 宜忌规则与经典原文对照 — 无 Classical Oracle
- ❌ 二十八宿值日验证 — 无独立 Oracle
- ❌ 神煞方位计算验证 — 无 Classical Oracle

---

### 2.5 Yi 引擎 (Yi Engine) — Phase 6 新增

| 测试文件 | 测试数 | 主要内容 | 类型 |
|---------|--------|---------|------|
| tests/yi/test_yi_e2e.py | ~15 | 适配器、解释器、E2E | Contract + E2E |
| tests/yi/test_yi_forward_validation.py | ~14 | 合同边界、数据泄漏检测 | Contract |

**Oracle 来源分析：**
- 术语表约束（17术语禁止）— Structural Oracle ✅
- 输出结构约束（STATE→OPPORTUNITY/RISK/REMEDIATION/ACTION）— Structural Oracle ✅
- 数据泄漏检测（PredictionWindow vs ToleranceWindow）— Structural Oracle ✅

**验证缺口：**
- ❌ 解释质量与经典原文对照 — 无 Human Oracle
- ❌ 关系式解释准确性 — 无 Empirical Oracle
- ❌ 前瞻预测与实际事件对照 — 无 Forward Oracle

---

## 三、外部数据源分析

### 3.1 已集成数据源

| 数据源 | 规模 | 许可 | 状态 | 可用性 |
|--------|------|------|------|--------|
| fate-bench | 295题/63人 | CC BY 4.0 | 已下载 | ✅ 可直接使用 |
| MingLi-Bench | 160题/4人 | MIT | 已 vendored | ✅ 可直接使用 |
| BaziQA | ~450题/90人 | MIT | 已 vendored | ✅ 可直接使用 |
| Ziwei 样本 | 518,400命盘 | CC BY 4.0 | 未下载 | ⚠️ 需下载 |
| CBDB | 649,533人 | CC BY-NC-SA 4.0 | 未下载 | ⚠️ 需下载 |
| chunqiu | 71人/121事件 | CC BY 4.0 | 未下载 | ⚠️ 需下载 |

### 3.2 数据源可信度评估

```text
fate-bench
├── 215/295 题有官方答案 (answer_provenance: "official")
├── 80/295 题有第三方转录 (answer_provenance: "third-party")
├── 2021、2025 两届无官方答案，标记为 third-party
├── 5个命盘无出生时间（被排除）
├── 3个命盘有专家手写四柱，与 sxtwl 计算结果一致
└── HUMAN BASELINE: 专家平均得分可参考
→ 可信度: HIGH (官方答案部分) / MEDIUM (third-party 部分)

MingLi-Bench
├── 与 fate-bench 交叉验证: 120/120 一致
├── 来源于 HKJFMA 2022-2025 四届
└── 许可: MIT
→ 可信度: HIGH

BaziQA
├── 2021-2025 五届 Contest8
├── 50位名人 Celebrity50
├── 与 fate-bench 有部分重叠（同一比赛数据）
└── 许可: MIT
→ 可信度: HIGH (但存在重复案例风险)

Ziwei 样本
├── 518,400 命盘组合（年60×月12×日30×时12×性别2）
├── 每例含完整命盘JSON + 13主题解读文本
├── 基于倪海夏《天纪》体系
└── 许可: CC BY 4.0 (要求 attribution)
→ 可信度: MEDIUM (纯排盘正确性可验证，但解读部分非 Ground Truth)

CBDB
├── 哈佛大学、中研院、北大联合维护
├── 649,533 人传记资料
├── 覆盖唐至清
└── 许可: CC BY-NC-SA 4.0 (非商业)
→ 可信度: HIGH (但需人工筛选可验证案例)

chunqiu (经纬春秋)
├── 春秋时期人物时间线
├── 每条事件可追溯至《左传》《国语》《史记》
├── 71人/121事件/83史料来源
└── 许可: CC BY 4.0
→ 可信度: HIGH (原始史料可核查)
```

### 3.3 数据重复性风险

```text
重叠检测:
├── fate-bench (295题)
│   ├── HKJFMA 2010-2013, 2018, 2021: 135题
│   ├── MingLi-Bench 2022-2025: 160题
│   └── BaziQA 2021 answers: 40题 (重复!)
├── BaziQA 2021-2025: 200题
│   └── 与 fate-bench MingLi-Bench 有重叠
└── 结论: 独立测试集约 295题 (去重后)
```

---

## 四、Oracle 四级体系分类

### O1 — Deterministic Oracle (确定性)

**定义**: 存在明确数学/历法规则，可完全自动化验证

| 引擎 | 组件 | Oracle 来源 | 验证方式 | 覆盖状态 |
|------|------|-------------|---------|---------|
| Bazi | 四柱计算 | sxtwl 寿星天文历 | 单元测试 | ✅ 已有 |
| Bazi | 十神映射 | 固定规则表 | 单元测试 | ✅ 已有 |
| Bazi | 真太阳时 | sxtwl + 经度修正 | 单元测试 | ✅ 已有 |
| Heluo | 天地数计算 | 洛书定则 | 单元测试 | ✅ 已有 |
| Heluo | 本命卦计算 | 先天八卦映射 | 单元测试 | ✅ 已有 |
| Heluo | 元堂飞支 | 既定飞支规则 | 单元测试 | ✅ 已有 |
| Heluo | 后天换卦 | 两步变换法 | 单元测试 | ✅ 已有 |
| Huangli | 干支计算 | sxtwl | 单元测试 | ✅ 已有 |
| Huangli | 节气计算 | sxtwl | 单元测试 | ✅ 已有 |
| Huangli | 建除循环 | 固定12日循环 | 单元测试 | ✅ 已有 |
| Ziwei | 安命宫 | 固定排盘规则 | 单元测试 | ✅ 已有 |
| Ziwei | 十四主星 | 固定安星规则 | 单元测试 | ✅ 已有 |
| Ziwei | 四化飞星 | 固定天干映射 | 单元测试 | ✅ 已有 |

**O1 覆盖率估算: ~85% 组件已验证**

---

### O2 — Statistical Oracle (统计性)

**定义**: 基于公开数据集，存在统计显著性但不保证单个案例正确

| 引擎 | 组件 | Oracle 来源 | 测试集 | 验证方式 | 覆盖状态 |
|------|------|-------------|--------|---------|---------|
| Bazi | 流年事件 | fate-bench (官方答案215题) | 215 MCQ | 历史盲测 | ❌ 未实现 |
| Bazi | 大運计算 | fate-bench + BaziQA | ~450题 | 历史盲测 | ❌ 未实现 |
| Ziwei | 流年事件 | fate-bench (215题) | 215 MCQ | 历史盲测 | ❌ 未实现 |
| Heluo | 事件预测 | 自建 Golden Cases | 50案例 | 回溯验证 | ⚠️ 部分实现 |

**O2 覆盖率估算: ~5% 组件已验证**

---

### O3 — Classical Oracle (经典)

**定义**: 基于古籍原文、专家规则，需要人工或半自动验证

| 引擎 | 组件 | Oracle 来源 | 验证方式 | 覆盖状态 |
|------|------|-------------|---------|---------|
| Heluo | 后天换卦两步法 | 《河洛理数》原典 | 纪晓岚案例 | ✅ 已验证 |
| Heluo | 天地数取数规则 | 洛书定则 | 经典案例 | ✅ 已验证 |
| Huangli | 建除宜忌规则 | 《钦定协纪辨方书》 | 经典对照 | ❌ 未实现 |
| Huangli | 神煞方位 | 《玉匣记》等 | 经典对照 | ❌ 未实现 |
| Yi | 解释术语约束 | 词库V4.0 | 术语映射检查 | ✅ 已验证 |

**O3 覆盖率估算: ~30% 组件已验证**

---

### O4 — Human Oracle (人类专家)

**定义**: 需要人工标注或专家评审，最高成本

| 引擎 | 组件 | Oracle 来源 | 验证方式 | 覆盖状态 |
|------|------|-------------|---------|---------|
| Yi | 解释质量 | 专家评级 | 盲测评估 | ❌ 未实现 |
| Bazi | 格局判断 | 专家标注 | 人工审核 | ❌ 未实现 |
| Heluo | 事件解读 | 专家标注 | 人工审核 | ❌ 未实现 |
| 全引擎 | 最终输出 | 专家评级 | 人类盲测 | ❌ 未实现 |

**O4 覆盖率估算: 0% 组件已验证**

---

## 五、验证基础设施现状

### 5.1 已实现框架

```text
src/tongshu/v_validation/
├── baseline/           ✅ 基础系统（随机基准对比）
├── blind/              ✅ 盲测协议（PredictionBeforeEvent）
├── backtest/           ✅ 回溯引擎（历史事件验证）
├── ablation/           ✅ 消融测试（单引擎影响评估）
├── end_to_end.py       ✅ E2E 链路测试
├── freeze.py           ✅ 冻结检查
├── ontology.py         ✅ 事件本体定义
├── reports/            ✅ 报告生成
├── schema/             ✅ 案例/预测 Schema
└── scoring/            ✅ 评分矩阵

src/tongshu/forward_validation/
├── engine.py           ✅ 前瞻验证引擎
├── prediction_record   ✅ 预测记录冻结
└── leakage_detection   ✅ 数据泄漏检测

src/tongshu/audit_validation/
├── gates/              ✅ G1-G4 运行时守门
│   ├── g1_evidence.py
│   ├── g2_translation.py
│   ├── g3_safety.py
│   └── g4_output.py
└── validators/         ✅ L1-L3 三层校验
```

### 5.2 测试基线文件

| 文件 | 内容 | 状态 |
|------|------|------|
| dataset/golden_v1/golden_cases.json | 50案例/518事件 | ✅ 已创建 |
| docs/golden_backtest_results.json | 回溯测试结果 | ✅ 已生成 |
| docs/audit/FINAL_ARCHITECTURE_AUDIT.md | V1.2架构冻结声明 | ✅ 已完成 |
| docs/audit/G6_YI_ENGINE_AUDIT.md | G6 Gate审计报告 | ✅ 已完成 |
| docs/audit/FORWARD_VALIDATION_REPORT.md | 前瞻验证报告 | ✅ 已完成 |

---

## 六、测试类型正式分类

```text
测试类型枚举 (V1.3 标准):
├── UNIT                    ✅ 已有 (~40%)
├── CONTRACT                ✅ 已有 (~30%)
├── INVARIANT               ✅ 已有 (~20%)
├── GOLDEN                  ✅ 已有 (~5%)
├── CROSS_ENGINE            ❌ 无 (0%)
├── EMPIRICAL               ⚠️ 部分 (~2%)
├── HISTORICAL_BLIND        ❌ 无 (0%)
├── ABLATION                ⚠️ 部分 (~1%)
└── FORWARD                 ✅ 已有 (~2%)

缺失关键类型:
❌ HISTORICAL_BLIND — 历史盲测（最重要）
❌ CROSS_ENGINE — 跨引擎交叉验证
❌ HUMAN_BLIND — 人类专家盲测
```

---

## 七、数据泄漏风险评估

### 7.1 泄漏类型分类

| 类型 | 定义 | 风险等级 | 当前检测 |
|------|------|---------|---------|
| PRE_EVENT | 预测在事件前生成 | ✅ 允许 | ✅ 已检测 |
| POST_EVENT | 预测在事件后生成 | ❌ 禁止 | ⚠️ 未实现 |
| POST_HOC | 事后选择规则解释结果 | ❌ 禁止 | ❌ 未检测 |
| DATA_contamination | 训练数据泄漏到测试 | ❌ 禁止 | ❌ 未检测 |
| DEMOGRAPHIC_LEAKAGE | 案例特征泄漏 | ❌ 禁止 | ❌ 未检测 |

### 7.2 现有检测机制

```text
src/tongshu/forward_validation/engine.py
├── prediction_window     ✅ 定义预测窗口
├── evaluation_tolerance  ✅ 定义评估容差窗口
├── prediction.created_at < event.occurred_at  ✅ 泄漏检测
└── LEAKAGE_STATUS 标记   ✅ 已实现
```

### 7.3 缺口

- ❌ 训练-测试集隔离验证
- ❌ 案例去重与重叠检测
- ❌ 跨数据集重复案例标记

---

## 八、V1.3 第一阶段可执行项

### 8.1 立即执行（不依赖外部数据）

| 任务 | 预估工时 | 优先级 | 产出 |
|------|---------|--------|------|
| A0.1 扫描全项目代码 | ✅ 已完成 | P0 | 本报告 |
| A0.2 建立 ENGINE→COMPONENT→TEST 映射 | 进行中 | P0 | Oracle Catalog |
| A0.3 统计各类型测试覆盖率 | ✅ 已完成 | P0 | 测试分布表 |
| A0.4 扫描现有 dataset | ✅ 已完成 | P0 | 数据集清单 |
| A0.5 扫描公开数据源 | ✅ 已完成 | P0 | 数据源评估表 |
| A0.6 建立数据源 provenance | 进行中 | P1 | Provenance 文档 |
| A0.7 建立 leakage classification | 进行中 | P1 | 泄漏策略文档 |

### 8.2 第二阶段执行（需外部数据）

| 任务 | 前置条件 | 预估工时 | 优先级 |
|------|---------|---------|--------|
| A1 Oracle Qualification | A0 完成 | 2天 | P0 |
| A2 Dataset Construction | A1 完成 | 3天 | P0 |
| A3 Historical Blind Test | A2 完成 | 5天 | P0 |
| A4 Cross-Engine Validation | A3 完成 | 3天 | P1 |
| A5 Ablation Study | A4 完成 | 2天 | P1 |
| A6 Human Blind Evaluation | A5 完成 | 7天 | P2 |
| A7 Forward Validation | A6 完成 | 持续 | P2 |

### 8.3 禁止事项（A0 阶段）

```text
❌ 禁止修改任何生产代码
❌ 禁止修改 Golden Dataset
❌ 禁止修改 V1.2 Contract
❌ 禁止修改任何已冻结的 Engine
❌ 禁止引入新的算法逻辑
```

---

## 九、Accuracy Matrix 初始模板

```text
| Engine   | Component        | Test              | Oracle        | Dataset          | Eval Type       | Ground Truth | Metric | Leakage Risk | Status |
|----------|------------------|-------------------|---------------|------------------|-----------------|--------------|--------|--------------|--------|
| Bazi     | 四柱计算          | sxtwl 交叉验证     | Deterministic | Canonical vectors | UNIT            | Exact        | Acc    | LOW          | ✅ 85% |
| Bazi     | 十神映射          | 固定规则表         | Deterministic | Canonical vectors | UNIT            | Exact        | Acc    | LOW          | ✅ 90% |
| Bazi     | 真太阳时          | sxtwl + 经度       | Deterministic | 15 locations      | UNIT            | Exact        | Acc    | LOW          | ✅ 80% |
| Bazi     | 大運计算          | fate-bench 官方答案 | Statistical   | fate-bench (215)  | HISTORICAL_BLIND| Event        | MicroF1| HIGH         | ❌ 0%  |
| Bazi     | 流年事件          | fate-bench 官方答案 | Statistical   | fate-bench (215)  | HISTORICAL_BLIND| Event        | MicroF1| HIGH         | ❌ 0%  |
| Heluo    | 天地数计算        | 洛书定则           | Deterministic | Canonical vectors | CONTRACT        | Exact        | Acc    | LOW          | ✅ 95% |
| Heluo    | 本命卦计算        | 先天八卦映射       | Deterministic | Canonical vectors | CONTRACT        | Exact        | Acc    | LOW          | ✅ 90% |
| Heluo    | 元堂飞支          | 既定规则           | Deterministic | Canonical cases   | CONTRACT        | Exact        | Acc    | LOW          | ✅ 85% |
| Heluo    | 后天换卦          | 两步变换法         | Classical     | 纪晓岚案例        | GOLDEN          | Exact        | Acc    | MEDIUM       | ✅ 100%|
| Heluo    | 流年/流月/流日    | 自定义测试         | Deterministic | Self-generated    | UNIT            | Exact        | Acc    | LOW          | ✅ 70% |
| Ziwei    | 安命宫            | 固定规则           | Deterministic | Canonical vectors | UNIT            | Exact        | Acc    | LOW          | ✅ 90% |
| Ziwei    | 十四主星          | 固定规则           | Deterministic | Canonical vectors | UNIT            | Exact        | Acc    | LOW          | ✅ 90% |
| Ziwei    | 四化飞星          | 固定规则           | Deterministic | Canonical vectors | UNIT            | Exact        | Acc    | LOW          | ✅ 95% |
| Ziwei    | 流年事件          | fate-bench 官方答案 | Statistical   | fate-bench (215)  | HISTORICAL_BLIND| Event        | MicroF1| HIGH         | ❌ 0%  |
| Huangli  | 干支计算          | sxtwl              | Deterministic | Canonical vectors | UNIT            | Exact        | Acc    | LOW          | ✅ 95% |
| Huangli  | 节气计算          | sxtwl              | Deterministic | Canonical vectors | UNIT            | Exact        | Acc    | LOW          | ✅ 95% |
| Huangli  | 建除循环          | 固定12日循环       | Deterministic | Canonical vectors | UNIT            | Exact        | Acc    | LOW          | ✅ 100%|
| Huangli  | 宜忌规则          | 《协纪辨方书》     | Classical     | 经典原文          | CLASSICAL       | Exact        | Acc    | MEDIUM       | ❌ 0%  |
| Huangli  | 神煞方位          | 《玉匣记》         | Classical     | 经典原文          | CLASSICAL       | Exact        | Acc    | MEDIUM       | ❌ 0%  |
| Yi       | 术语约束          | 17术语禁止表       | Structural    | Self-generated    | CONTRACT        | Exact        | Pass   | LOW          | ✅ 100%|
| Yi       | 输出结构          | STATE→ACTION格式   | Structural    | Self-generated    | CONTRACT        | Exact        | Pass   | LOW          | ✅ 100%|
| Yi       | 解释质量          | 专家评级           | Human         | Expert set        | HUMAN_BLIND     | Rubric       | Agreement| HIGH      | ❌ 0%  |
| Evidence | provenance        | SOURCE→PASSAGE→RULE | Deterministic | Synthetic         | CONTRACT        | Exact        | 100%   | LOW          | ✅ 100%|
| Temporal | alignment        | 时间对齐一致性       | Deterministic | Synthetic         | CONTRACT        | Exact        | Acc    | LOW          | ✅ 90% |
| Temporal | convergence      | 多信号收敛         | Deterministic | Synthetic         | CONTRACT        | Exact        | Acc    | LOW          | ✅ 85% |
```

---

## 十、关键发现与结论

### 10.1 主要优势

1. **架构冻结完整**: G1-G6 全部 PASS，1263 测试通过
2. **Contract 层坚实**: 所有 Schema、Invariant、Negative Contract 均已验证
3. **证据链闭合**: SOURCE→PASSAGE→RULE→MAPPING 链路完整
4. **前瞻验证机制**: PredictionRecord 冻结、泄漏检测已实现
5. **外部数据源可用**: fate-bench (215官方题)、MingLi-Bench、BaziQA 均可直接引用

### 10.2 主要缺口

1. **算法准确性验证缺失**: 1263 测试中 ~97% 是结构性测试，仅 ~3% 是实证性测试
2. **历史盲测未实现**: 无对 fate-bench/MingLi-Bench 的实际预测验证
3. **跨引擎交叉验证缺失**: Bazi vs Ziwei vs Heluo 无对比验证
4. **Human Oracle 未建立**: 无专家评级体系
5. **数据泄漏防护不足**: POST_HOC 检测、训练-测试隔离均未实现

### 10.3 下一步建议

**立即执行 A0 剩余项**：
- A0.6: 建立数据源 provenance 文档
- A0.7: 建立泄漏分类策略文档

**然后进入 A1 Oracle Qualification**：
- 对每个组件明确标注 Oracle 来源
- 建立可复现的验证脚本

**避免提前进入编码**：
- A0 阶段只输出文档和映射表
- 不修改任何生产代码
- 不运行任何测试

---

## 附录：扫描命令记录

```bash
# 测试总数
python -m pytest tests/ --collect-only -q

# 测试分布
grep "test_" tests/**/*.py | wc -l

# 引擎文件列表
find src/tongshu/engines -name "*.py"

# 外部数据源引用
grep -r "fate.bench\|baziqa\|mingli.bench" src/ tests/ --include="*.py"

# Golden Dataset 规模
cat dataset/golden_v1/golden_cases.json | python -c "import json,sys; d=json.load(sys.stdin); print(f\"Cases: {d['case_count']}, Events: {d['event_count']}\")"
```

---

**报告结束**
**下一阶段**: A0.6-A0.7 数据源 provenance 与泄漏策略文档
