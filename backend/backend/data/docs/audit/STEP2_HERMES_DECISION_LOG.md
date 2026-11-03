# STEP 2 Hermes裁定 - DECISION_LOG

**时间**: 2026-08-31  
**输入**: Claude独立审计五件套  
**裁定者**: Hermes (总调度) → GPT (最终裁决)

---

## 审计发现汇总

### P0 BLOCKER (8项)

| ID | 发现 | 严重度 | 状态 |
|----|------|--------|------|
| B-01 | wang_score阈值verdict仍生效 | P0 BLOCKER | 🔴 待隔离 |
| B-02 | evaluate_strength仍是唯一生产调用 | P0 BLOCKER | 🔴 待隔离 |
| B-03 | evaluate_strength_features是dead code | P0 BLOCKER | 🔴 待集成 |
| B-04 | P0隔离计划自身存在根本错误 | P0 BLOCKER | 🔴 待重写 |
| B-05 | 双轨系统并存 | P0 BLOCKER | 🔴 待决策 |
| B-06 | DEPRECATED标注不可信 | P0 BLOCKER | 🔴 待治理 |
| B-07 | 23个测试失败未被处理 | P0 BLOCKER | 🔴 待修复 |
| B-08 | return-based测试模式 | P0 BLOCKER | 🔴 待修复 |

### P1 CRITICAL (6项)

| ID | 发现 | 严重度 |
|----|------|--------|
| C-05 | 工程阈值冒充Canonical | P1 CRITICAL |
| C-06 | canonical/禁止wang_score vs engines/强制wang_score | P1 CRITICAL |
| C-07 | wang_score阈值verdict仍生效 | P1 CRITICAL |
| C-08 | ARCHITECTURE文档过期 | P1 CRITICAL |
| C-09 | legacy/assertion_v1仍引用新代码 | P1 CRITICAL |
| C-10 | CanonicalState未被生产路径消费 | P1 CRITICAL |

---

## Hermes裁定

### 裁定1: B-01/B-02/B-03 → 隔离Legacy Strength Engine

**决定**: FIX  
**理由**: Claude审计确认7个调用点，其中5个ORPHAN，1个MAIN() CLI，1个SHADOW(/admin)。用户路径已断，但shadow路径仍存。

**操作**:
1. 切断/admin shadow链路
2. 标记legacy/assertion_v1为DEPRECATED
3. 保留strength_engine.py但移除verdict逻辑

---

### 裁定2: B-04 → 重写P0隔离计划

**决定**: FIX  
**理由**: P0_ISOLATION_PLAN.md路径全部错误，执行将找不到目标文件。

**操作**:
1. 基于Claude审计结果重写隔离计划
2. 明确7个调用点实际位置
3. 制定分阶段隔离方案

---

### 裁定3: B-05 → 双轨系统决策

**决定**: REMOVE Legacy轨  
**理由**: 双轨导致双倍维护成本和bug表面，治理不可信。

**操作**:
1. 确认CanonicalState + Condition Evaluator为唯一生产链
2. Legacy strength_engine移除生产调用
3. 保留代码作为历史研究参考

---

### 裁定4: B-07/B-08 → 测试修复

**决定**: FIX  
**理由**: 23个失败测试阻塞P0验证。

**操作**:
1. 分析失败原因（硬编码dict vs真实Canonical State）
2. 修复测试或代码
3. 统一return→assert模式

---

### 裁定5: C-05/C-06 → 工程阈值清理

**决定**: RESEARCH  
**理由**: 所有weight/threshold值无原典授权，不能进入Production。

**操作**:
1. 标记为RESEARCH/EXPERIMENTAL
2. 不得作为verdict依据
3. 等待五经辨证完成后再评估

---

## 待GPT最终裁决

1. 是否接受Hermes裁定？
2. Legacy Strength Engine隔离方案是否可执行？
3. 是否启动STEP 3派发任务单？
4. 双轨系统REMOVE决策是否正确？

---

**状态**: 等待GPT裁决后进入STEP 3