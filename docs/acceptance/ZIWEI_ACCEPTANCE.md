ENGINE: ziwei
VERSION: 1.0.0

# BOT-ZIWEI ACCEPTANCE.md — V2 现状盘点

> 生成: 2026-09-07 | 依据: V2验收和生产准入规范 (E0-E10)
> 说明: 本文件如实标注当前验收状态，不虚标。

## E0 Contract
STATUS: PASS
- Input: Canonical State → ZiWeiAdapter → ZiWei Chart ✅
- 违规方法0残留 (native_direction/score_topic/SIHUA_EFFECT已删) ✅

## E1 Unit
STATUS: PASS
- test_ziwei_engine.py 15 + test_ziwei_method_profile.py + test_ziwei_phase_a0_extended.py 45 = 88 passed + 32 subtests

## E2 Algorithm
STATUS: PASS
- 排盘链: 命宫/身宫/五行局/紫微星/天府/十四主星/十二宫/辅星/煞星/四化 ✅
- 与倪海厦数据集交叉验证 240/240宫位匹配 ✅

## E3 Boundary
STATUS: PARTIAL
- ⚠️ 需补充: 命宫边界/身宫边界/农历月边界/五行局边界/安星边界/四化边界/大限边界

## E4 Negative
STATUS: PARTIAL
- ⚠️ 需补充 fail-closed 负向测试

## E5 Golden
STATUS: PASS
- ✅ cases/golden/ziwei_golden_set.json (80案例, 倪海厦体系)
- ✅ 执行报告: LOAD 80/80 + EXECUTE 80/80 + 12宫主星匹配 80/80 (100%)
- ✅ Skip=0
- 详见 docs/bots/BOT-ZIWEI/GOLDEN_EXECUTION_REPORT.md

## E6 Regression
STATUS: PASS
- ✅ scripts/golden_replay.py — 80/80 案例重放OK, 基线hash稳定(1cf8f6f0)
- ✅ 流程: 算法变更后 `python scripts/golden_replay.py --check`, 差异分类 EXPECTED_CHANGE/REGRESSION (V2 §21)

## E7 Integration
STATUS: PASS
- Canonical State → ZiWeiAdapter → ZiWei 独立验证 ✅

## E8 Production Trace
STATUS: PASS
- ✅ Full Replay抽样100条(5年份×20): 命宫地支/五行局/主星 三项均100%匹配
- 工具: scripts/e8_ziwei_full_replay.py (env var注入, 只读)
- 报告: docs/bots/BOT-ZIWEI/E8_FULL_REPLAY_REPORT.md

## E9 Independent Audit
STATUS: PENDING

## E10 Acceptance
STATUS: CONDITIONAL

## Provenance
STATUS: PASS
- ✅ 证据5条(E-ZIWEI-001~006, 倪海厦《天纪》classical_authority, VERIFIED)
- ZW-004已解决

## Isolation
STATUS: PASS
- ✅ 同盘异法: SanHe/FeiXing/SiHua 派别隔离 ✅ (Chart Hash验证已建 cases/baselines/ziwei_chart_baseline.json)

## 生命周期状态
STATUS: 违规清零，算法就绪
- 不得宣称 Production Ready ⚠️

## 问题清单
| 严重性 | 问题 | 状态 |
|--------|------|------|
| P1 | ZW-004 紫微独立证据不足 | OPEN |
| P1 | Chart Hash验证未建立 | OPEN |
| P1 | E5 Golden执行报告未生成 | OPEN |

## 验收记录
- 最近验收: 2026-09-07 (88 passed + 32 subtests)
- 待办: Golden执行报告 → Chart Hash → 证据补充
