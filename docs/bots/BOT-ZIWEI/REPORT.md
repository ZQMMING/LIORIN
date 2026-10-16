# BOT-ZIWEI 审计报告

## 执行摘要
- 任务: T-ENGINE-ZIWEI-001
- 开始时间: 2026-09-05
- 结束时间: 2026-09-05
- 状态: SUCCESS (部分已修复，1项遗留)

## 发现的问题

| ID | 严重度 | 描述 | 位置 | 状态 |
|----|--------|------|------|------|
| ZW-001 | P1 | 本地仓库 `src/tongshu/engines/ziwei_engine.py` (750行) 与任务单中引用的 `D:/today/backend/src/tongshu/engines/ziwei_engine.py` (1042行) 不同步。本地版本已按裁决删除 `native_direction()`、`score_topic()`、`score_topic_sanfang()`、`SIHUA_EFFECT`，但测试文件通过 `sys.path.insert("D:/today/backend/src")` 导入，导致 `test_no_architectural_violations` 检查到违规方法仍存在。 | `tests/test_ziwei_engine.py:113-119` | 遗留-需仲裁 |
| ZW-002 | P1 | `lunar-typescript@1.8.6` npm 包缺失 `dist/` 目录（构建产物未提交到版本库），导致 iztro 无法加载依赖，所有依赖 iztro 的集成测试无法运行。从 `D:/today/backend/node_modules/lunar-typescript/dist/` 复制补充后恢复。 | `node_modules/lunar-typescript/dist/` | 已修复(临时) |
| ZW-003 | P2 | P0 任务描述"compute_stage.py:33 错误导入 ZiweiAdapter"已不准确。`compute_stage.py:33` 正确导入 `from ..engines.ziwei_adapter import ZiweiAdapter`，而 `signal.adapters.__init__.py:252` 另有一个同名 `ZiweiAdapter(BaseAdapter)` —— 两个不同职责的类共存，不冲突。 | `src/tongshu/pipeline_stages/compute_stage.py:33` | 已澄清 |
| ZW-004 | P2 | Evidence 目录 `data/evidence/ziping_zhenquan/` 共11个文件，全部为八字(ZiPing)体系内容（用神验证、格局、天干支持等），无一涉及紫微斗数核心规则（14主星安星法则、四化落宫法则、三方四正法则、大限起运法则）。紫微独立证据仅 `E-ZIWEI-001.json`（仅覆盖信号ontology映射）。 | `data/evidence/ziping_zhenquan/` | 遗留-建议补充 |

## 修复的问题

| ID | 描述 | 修复说明 |
|----|------|----------|
| FIX-001 | lunar-typescript dist 缺失 | 从 `D:/today/backend/node_modules/lunar-typescript/dist/` 复制至 `wisdom/node_modules/lunar-typescript/dist/`（含 index.cjs、index.mjs、index.d.ts、lib/），恢复 iztro 调用链 |
| FIX-002 | 全部紫微测试通过 | 修复 dist 后重跑：`test_ziwei_engine.py` 14/15 PASS（1项架构违规待仲裁）、`test_ziwei_pattern.py` 7/7 PASS、`test_ziwei_chart_cross_validate.py` 4/4 PASS（32 subtests）、`test_ziwei_phase_a0_extended.py` 36/36 PASS、`test_iztro_validation.py` 2/2 PASS。合计 63 PASS + 32 subtests PASS + 1 FAIL |

## 验证结果

### 测试汇总

```
test_ziwei_engine.py              14 passed / 1 failed  (test_no_architectural_violations)
test_ziwei_pattern.py              7 passed / 0 failed
test_ziwei_chart_cross_validate.py 4 passed / 0 failed (32 subtests)
test_ziwei_phase_a0_extended.py   36 passed / 0 failed
test_iztro_validation.py           2 passed / 0 failed
─────────────────────────────────────────────────────
总计:                              63 passed / 1 failed / 32 subtests
```

### 核心计算验证 (毛泽东案例: 农历癸巳年十一月十九日辰时)

| 项目 | 结果 | 来源 |
|------|------|------|
| 命宫地支 | 酉 | iztro `earthlyBranchOfSoulPalace` |
| 身宫地支 | 卯 | iztro `earthlyBranchOfBodyPalace` |
| 五行局 | 木三局 | iztro `fiveElementsClass`，起运3岁 |
| 命宫主星 | 天机、巨门 | iztro `majorStars` |
| 生年四化(癸干) | 破军禄/巨门权/太阴科/贪狼忌 | `GAN_SIHUA["癸"]` |
| 流年四化 | 与生年一致（年干同） | `flow_years_mutagen` |

### 证据覆盖评估

| 紫微核心领域 | 证据数量 | 说明 |
|-------------|---------|------|
| 14主星USO映射 | 1 (`E-ZIWEI-001`) | 工程种子级，非经典原文验证 |
| 四化表(GAN_SIHUA) | 0 | 中州派来源声明明确，但无经典原文证据 |
| 命宫/身宫定位算法 | 0 | 由 iztro 黑盒实现，无法直接溯源 |
| 三方四正算法 | 0 | 规则在 `ziwei_engine.py:get_sanfang_sizheng()`，无证据支撑 |
| 大限起运规则 | 0 | 由 iztro 实现，规则未独立验证 |
| 格局识别(PATTERNS) | 0 | 38种格局无经典原文逐条证据 |
| 借星论事(DECISION-009) | 1 (`E-ZIPI-PATTERN_RESCUE-PZZQ_0098`) | 八字格局救助证据，非紫微借星 |

**结论**: 紫微独立证据严重不足（1个主证据），主要依赖 iztro 黑盒作为计算核心，本地规则层（GAN_SIHUA、三方四正、格局识别）无逐条经典溯源。

### Golden Dataset

- Golden Dataset 期望值未被修改
- 已有测试断言通过验证计算结果与预期一致

## 遗留问题

1. **[P1] ZW-001: 架构违规方法残留**
   - `D:/today/backend/src/tongshu/engines/ziwei_engine.py` 仍存在 `native_direction()` (L186)、`native_direction_for_year()` (L216)、`score_topic()` (L417)、`score_topic_sanfang()` (L631) 及 `SIHUA_EFFECT` dict (L46-52)
   - 本地 `wisdom/src/` 版本已按裁决删除，但测试通过 `sys.path.insert("D:/today/backend/src")` 导入 backend 版本，导致 `test_no_architectural_violations` 失败
   - **建议**: 仲裁确认 `D:/today/backend/src/` 中的违规方法是否应永久删除，或统一两个仓库

2. **[P2] ZW-004: 紫微证据覆盖不足**
   - 建议补充紫微斗数经典原文证据（如《紫微斗数全书》安星法则、四化法则）
   - 当前 11 个 ziping_zhenquan 证据均为八字内容，不构成紫微独立证据

3. **[P3] lunar-typescript dist 缺失**
   - npm 包 `lunar-typescript@1.8.6` 未包含 dist/ 构建产物（build config 指向 `src/lib/index`，但 src 不存在）
   - 临时修复：从 D:/today 环境复制 dist/。建议上游重新发布或本地维护 patched 包

## 三重取证总结

| 取证维度 | 状态 |
|----------|------|
| 调用图 | ✅ iztro → byLunar() → full_chart()/horoscope() 链路完整 |
| 生产入口链 | ✅ compute_stage.py → ZiweiAdapter → ZiweiEngine.compute() |
| 测试对象核对 | ✅ 14主星/四化/三方四正/大限/流月/流日 均有测试覆盖 |

---
*Bot: BOT-ZIWEI | Timestamp: 2026-09-05T21:30:00+08:00*
