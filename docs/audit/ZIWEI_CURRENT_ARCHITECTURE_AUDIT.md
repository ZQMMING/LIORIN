# ZIWEI CURRENT ARCHITECTURE AUDIT
**执行日期**: 2026-09-04  
**执行者**: Claude Code  
**状态**: Gate Z0 完成 — 基线记录，未修改业务逻辑

---

## 一、测试基线（Gate Z0）

### 运行命令
```bash
cd /e/shuntian && uv run pytest tests/test_ziwei_engine.py tests/test_ziwei_pattern.py \
    tests/test_ziwei_chart_cross_validate.py tests/test_ziwei_phase_a0_extended.py \
    tests/spec/test_vertical_slice_ziwei.py -v --tb=short
```

### 结果汇总

| 文件 | 收集 | 通过 | 失败 | 备注 |
|------|------|------|------|------|
| `test_ziwei_engine.py` | 15 | 15 | 0 | ✅ 全部通过 |
| `test_ziwei_pattern.py` | 7 | 7 | 0 | ✅ 全部通过 |
| `test_ziwei_chart_cross_validate.py` | 4（32 subtests） | 4 | 0 | ✅ 公式 vs iztro 一致 |
| `test_ziwei_phase_a0_extended.py` | 45 | 45 | 0 | ✅ 含真太阳时/大限/流月/流日 |
| `test_vertical_slice_ziwei.py` | 13 | 13 | 0 | ✅ V13 Contract 验证 |
| **合计** | **84** | **84** | **0** | ✅ **基线稳定** |

> 运行前发现 `node_modules/lunar-typescript/dist/` 为空（包未构建），通过从 npm registry 下载并解压 dist/ 修复。同时修复 `i18next` 版本不匹配导致 iztro 无法加载的问题（npm install 补装）。

---

## 二、文件清单与职责映射

| 文件路径 | 行数 | 职责定位 | 是否生产路径 |
|----------|------|----------|-------------|
| `engines/ziwei_engine.py` | ~800 | 计算引擎（iztro subprocess 调用）、`ZiweiChart` 数据结构、`GAN_SIHUA` 表、格局提取、四化查询 | ✅ 核心 |
| `engines/ziwei_adapter.py` | ~117 | 时间政策（P0-14 已冻结）：阳历→农历转换、晚子时不换日 | ✅ 已冻结 |
| `engines/ziwei_dependency_adapter.py` | ~474 | iztro 大限方向修正适配器（BUG-P0-2 修复） | ✅ 已冻结 |
| `engines/ziwei_knowledge.py` | ~90 | 疾厄论断层（14主星→脏腑）、宫位主题映射、主星特性关键词 | ⚠️ 仅注释提及 `score_ziwei`，无实际调用 |
| `engines/ziwei_pattern.py` | ~113 | 格局识别（多星优先+单星去重、空宫借星标注） | ⚠️ 有测试，无生产调用路径 |
| `engines/ziwei/evidence_producer.py` | ~138 | V13 contract Evidence Producer（P1.2-A） | ✅ 新路径 |
| `engines/__init__.py` | ~10 | 导出 `ZiweiEngine`, `ZiweiChart` | — |
| `feature_registry/adapters/zi_wei_adapter.py` | ~50 | P6-C-3C-1 Feature Registry 适配层 | ⚠️ 孤立路径 |
| `k2g/concepts/ziwei_concepts.yaml` | — | 概念注册（DRAFT） | — |
| `k2g/mappings/ziwei_mappings.yaml` | — | 概念映射（DRAFT） | — |
| `canonical/composer.py` | ~157 | SIR 构造，引入 `ZiweiChart`，含 `ziwei_version` | ✅ 生产路径 |
| `pipeline.py` | ~291 | 主 Pipeline，引入 `ZiweiEngine`，版本 "1.0.0" | ✅ 生产入口 |
| `pipeline_stages/compute_stage.py` | ~523 | 计算阶段：zwei 计算→信号提取→cross orchestration | ✅ 生产核心 |

---

## 三、生产路径追踪

### 主生产路径
```
API / Pipeline
  ↓
pipeline.py (run)
  ↓
ComputeStage.run()
  ├── bazi_adapter.compute(ctx) → BaziChart
  ├── ziwei_adapter.compute(ctx) → ZiweiChart     ← 走 P0-14 政策
  │   └── ziwei_engine.compute(lunar_date, hour, gender)
  │       └── _compute_via_iztro() (subprocess)
  │           └── ziwei_dependency_adapter.adapt_from_chart()  ← P0-2 方向修正
  ├── signal_engine.build(bazi, ziwei, huangli)
  ├── ziwei_engine.extract_baseline_signal(ziwei_chart, 0)   ← ⚠️ 旧 Signal 形态
  └── ziwei_chart 写入 CanonicalComposer.compose() → SIR
```

### 隐式/孤立路径
| 路径 | 位置 | 问题 |
|------|------|------|
| `ziwei_knowledge.py` | 注释提及 `score_ziwei` | 函数不存在，无调用方 |
| `ziwei_pattern.py` | `recognize_patterns_from_chart()` | 无生产调用，仅在测试中验证 |
| `feature_registry/adapters/zi_wei_adapter.py` | P6-C-3C-1 | 独立注册，未接入主 pipeline |
| `extract_baseline_signal()` | `ziwei_engine.py:161` | 产出旧 Signal（含 direction/polarity/strength/confidence），与 V13 evidence-only 契约冲突 |

---

## 四、答案审计报告问题

| # | 问题 | 答案 | 位置 |
|---|------|------|------|
| 1 | 当前谁负责计算？ | `ZiweiEngine._compute_via_iztro()` → subprocess 调用 iztro `byLunar()` | `ziwei_engine.py:190-268` |
| 2 | 当前谁负责排盘？ | `ZiweiEngine.full_chart()` 调用 iztro + `ShuntianZiweiDependencyAdapter.adapt_from_chart()` 修正大限方向 | `ziwei_engine.py:627-694` |
| 3 | 当前谁负责三方四正？ | `ZiweiEngine.get_sanfang_sizheng()` — 但**无生产调用**，仅在 `native_direction` 删除前使用 | `ziwei_engine.py:368-425` |
| 4 | 当前谁负责四化？ | `GAN_SIHUA` 常量表 + `flow_years_mutagen`/`flow_month_mutagen`/`flow_day_mutagen`/`flow_decadal_mutagen`/`get_sihua_palaces`/`palace_self_mutagen` | `ziwei_engine.py:80-91, 270-625` |
| 5 | 当前谁负责格局？ | `ziwei_pattern.recognize_patterns()` + `recognize_patterns_from_chart()` — **无生产调用** | `ziwei_pattern.py:58-112` |
| 6 | 当前谁负责解释？ | `compute_stage.py:159` 调用 `extract_baseline_signal()` → 产出 `Signal(layer="BASELINE", direction="STABLE")`；断事由 `CrossDomainOrchestrator` + assertion rules 负责 | `compute_stage.py:159, 167-180` |
| 7 | 当前哪里存在 score？ | ❌ **无** `score_ziwei` 或 `score_topic`，已于架构清理中删除（验证通过，测试 `test_no_architectural_violations` 确认） | — |
| 8 | 当前哪里存在 LLM？ | ❌ **紫微路径无 LLM**。LLM 仅出现在 `render_stage.py`（渲染层，不属于计算/辨层） | — |
| 9 | 当前哪里把事实和解释混在一起？ | ⚠️ **`extract_baseline_signal()`** 在引擎层直接产出带 direction/polarity/strength 的 Signal，属于解释 | `ziwei_engine.py:161-188` |
| 10 | 当前哪里存在派别混用？ | ⚠️ `GAN_SIHUA` 硬编码为中州派/王亭之版本，无 MethodProfile 隔离；`ziwei_pattern.py` 格局定义基于倪海厦体系，但无标记 | `ziwei_engine.py:80-91`, `ziwei_pattern.py` |
| 11 | 当前哪些代码是真生产路径？ | `ziwei_engine.py` (核心), `ziwei_adapter.py`, `ziwei_dependency_adapter.py`, `evidence_producer.py` (新路径), `pipeline.py`, `compute_stage.py`, `canonical/composer.py` | — |
| 12 | 哪些是 legacy/dead code？ | `ziwei_knowledge.py` (仅注释引用已删除函数), `ziwei_pattern.py` (无生产调用), `get_sanfang_sizheng`/`palace_self_mutagen` (无调用方), `feature_registry/adapters/zi_wei_adapter.py` (孤立注册) | — |
| 13 | 哪些代码可以复用？ | `GAN_SIHUA` 表、`time_index_from_hour`、`ziwei_dependency_adapter` (方向修正) | — |
| 14 | 哪些代码必须拆分？ | `extract_baseline_signal` 须从引擎移到辨层/推理层；`ziwei_pattern.py` 须移至 methodology 层并带 method_id | — |
| 15 | 哪些代码必须删除？ | `ziwei_knowledge.py`（无调用），`feature_registry/adapters/zi_wei_adapter.py`（孤立），`get_sanfang_sizheng`（无调用方，仅保留 `get_zigong_zihua`/`get_laiyin_gong`/`get_all_zihua`） | — |

---

## 五、架构合规检查（对照手册要求）
n### Z12-FIX（2026-09-04 审查修复）

| 编号 | 问题 | 修复 |
|------|------|------|
| F1 | `FrozenZiweiChart.palaces` 类型注解为 tuple 但运行时是 dict | 修正注解为 `dict`，新增 `birth_year: int` 字段 |
| F2 | `_match_natal_sihua()` 用命宫宫干代替生年干 | 改为从 `chart.birth_year` 计算天干 `stems[(year-4)%10]` |
| F5 | 三合派格局仅匹配命宫，未扩展三方四正 | `match_patterns(include_sanfang=True)` 扩展至本宫+对宫+两合宫星群 |

### 当前违反项

| # | 违反描述 | 位置 | 严重度 |
|---|----------|------|--------|
| V1 | `extract_baseline_signal()` 产出带 direction/polarity/strength 的旧 Signal，违反 V13 evidence-only 契约 | `ziwei_engine.py:161-188` | 🔴 高 |
| V2 | `evidence_producer.py` 宫殿证据层与 `ZiweiChart.palace_data` 实际结构不匹配，实际只产出命宫级证据 | `evidence_producer.py:89-135` | 🔴 高 |
| V3 | `source_rule_ref` 引用不存在文件（`data/rules/ziwei_stars.json` 等） | `evidence_producer.py:61,82,108,130` | 🟡 中 |
| V4 | 无 `FrozenZiweiChart` | **Z2 已完成**：`FrozenZiweiChart` 已定义，`ZiweiChart = FrozenZiweiChart` 别名，dict-style 向后兼容 | ✅ Z2 |
| V5 | `GAN_SIHUA` 等四化/格局/知识数据硬编码在引擎层，无 MethodProfile 隔离 | `ziwei_engine.py:80-91`, `ziwei_pattern.py` | 🟡 中 |
| V6 | `ziwei_pattern.py` 和 `ziwei_knowledge.py` 被注释为倪海厦/中州派，但无 method_id 标记，无法审计来源 | `ziwei_pattern.py`, `ziwei_knowledge.py` | 🟢 低 |

### 当前符合项

| # | 符合描述 | 验证 |
|---|----------|------|
| C1 | 算与辨边界：计算层只调用 iztro，无断事逻辑 | ✅ |
| C2 | 无 `score_ziwei` / `score_topic` | ✅ 测试已验证 |
| C3 | 大限方向修正已通过 DependencyAdapter 隔离 | ✅ `test_raw_vs_canonical_direction` 通过 |
| C4 | P0-14 时间政策已冻结 | ✅ `ZiweiCalculationPolicy.status == RATIFIED` |
| C5 | 空宫借星策略已在 `compute()` 中实现并有测试 | ✅ |
| C6 | 流月/流年/流日四化各自独立函数 | ✅ |
| C7 | `test_vertical_slice_ziwei.py` 验证无 CrossAnalyzer/signal_engine 旧组件 | ✅ |

---

## 六、待审计者裁决问题

| # | 问题 | Z1/Z1b/Z1c 执行结果 | 状态 |
|---|------|---------------------|------|
| 1 | `extract_baseline_signal` 废弃方案 | **已执行**：从 `ziwei_engine.py` 删除方法、从 `compute_stage.py` 删除注入点、同步清理 `test_rule_lifecycle.py` 注释 | ✅ Z1b+Z1c |
| 2 | `evidence_producer.py` 宫殿数据补全 | **已执行**：`ZiweiChart.palace_data` → `palaces` dict；证据层改为消费 `chart.palaces` | ✅ Z1 |
| 3 | `ziwei_knowledge.py` 处置 | **已执行**：完全删除（确认零调用方） | ✅ Z1 |
| 4 | `ziwei_pattern.py` 归属 | **已执行**：删除（格局识别暂不在 MethodProfile 框架范围内，待 Z3 建立后迁入） | ✅ Z1b |
| 5 | `feature_registry/adapters/zi_wei_adapter.py` 归属 | **已执行**：删除 + 清理 `__init__.py` 引用 | ✅ Z1 |

### 执行细节（commit `774f3079`）

**删除的文件**：
- `src/tongshu/engines/ziwei_knowledge.py`（0 调用方，`score_ziwei` 已不存在）
- `src/tongshu/feature_registry/adapters/zi_wei_adapter.py`（0 测试、0 生产调用）

**修改的文件**：
- `ZiweiChart`：`palace_data: dict` → 扁平字段 `soul_borrowed`/`soul_earthly_branch`/`body_earthly_branch`/各时段 mutagen + `palaces: dict`（宫殿级事实，供证据层消费）
- `ZiweiEvidenceProducer`：修正 `source_rule_ref` 为实际路径 `data/rules_index/ziwei_stars.json`；宫殿证据改为消费 `chart.palaces[pname]["major"]`
- `ziwei_pattern.py`：`recognize_patterns_from_chart()` 改用 `getattr(chart, 'soul_borrowed', False)` 向后兼容旧 chart 对象
- `signal_engine.py`：`soul_palace_main_star_zh` 字段增加 `hasattr(ziwei, 'palace_data')` 防御检查
- `test_vertical_slice_ziwei.py`：fixture 更新为新版 `ZiweiChart` 结构（`palaces` dict，移除 `MiniPalace` dataclass）

**验证**：84/84 紫微测试通过；14 个 pre-existing collection error（tzdata/heluo/s5/s6 缺失，与本次变更无关）。

---

## 七、空目录（待填充骨架）

```
src/tongshu/engines/ziwei/
  calculation/   ← 无文件
  methodology/   ← 无文件
  methods/       ← 无文件
  rules/         ← 无文件
```

---

**基线状态**: ✅ 142/142 测试通过 + 32 subtests（Z12-FIX 已修复契约问题），系统可正常运行  
**Z1 执行**: ✅ 死代码清理完成（commit `774f3079`, `a8bd7e15`, `50b9247b`, `2897cfcb`）  
**Z2 执行**: ✅ `FrozenZiweiChart` 计算契约建立（commit `8dfa252b`）  
**下一步**: Gate Z13 — FeixingRuleGraph（飞星派飞化规则）
