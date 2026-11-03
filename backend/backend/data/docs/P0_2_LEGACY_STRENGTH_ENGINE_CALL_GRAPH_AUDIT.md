# P0-② 旧评分路径调用图审计报告

**审计日期**: 2026-08-30
**审计目标**: strength_engine.py（旧评分式强弱计算引擎）
**审计结论**: 🟡 生产路径仍有2处实际调用，需逐步迁移；Legacy路径已隔离

---

## 一、引擎状态

| 项 | 值 |
|---|---|
| 引擎文件 | `src/tongshu/engines/strength_engine.py` |
| 状态标记 | ⚠️ LEGACY / DEPRECATED_IN_PROGRESS |
| 核心问题 | 单一评分式强弱判断，违反"禁止五行计分→强弱"治理原则 |
| 替代方向 | CanonicalState + 五部经典各自辨证（P0-①已建立数据结构） |

---

## 二、生产路径调用（需逐步迁移）

### 2.1 annual_event_evaluator.py

| 项 | 值 |
|---|---|
| 文件 | `src/tongshu/engines/annual_event_evaluator.py` |
| 行号 | 207 |
| 调用位置 | `BaziScorer.compute()` 方法 |
| 调用代码 | `strength = evaluate_strength(chart)` |
| 用途 | 获取旺衰verdict，供十神吉凶动态判断使用 |
| 迁移优先级 | 中（流年事件评估，非核心辨证路径） |

### 2.2 health_signals.py

| 项 | 值 |
|---|---|
| 文件 | `src/tongshu/reasoning/health_signals.py` |
| 行号 | 99 |
| 调用位置 | `evaluate_health_signals()` 函数 |
| 调用代码 | `d1: D1StrengthResult = evaluate_strength(chart)` |
| 用途 | 获取旺衰结果、气候、support_count、drain_count，用于健康信号分析 |
| 附加调用 | 第122行导入 `_hidden_stems`（strength_engine内部函数） |
| 迁移优先级 | 中（健康信号，依赖气候和计数等中间产物） |

### 2.3 judgment_engine.py（类型依赖，非直接调用）

| 项 | 值 |
|---|---|
| 文件 | `src/tongshu/engines/judgment_engine.py` |
| 行号 | 41 |
| 依赖方式 | 导入 `D1StrengthResult` 用于类型注解 |
| 调用位置 | `judgment(chart, d1_result: D1StrengthResult)` 函数参数 |
| 用途 | 接收strength_engine的输出作为输入 |
| 迁移优先级 | 高（P2判定层，核心路径） |

---

## 三、Legacy路径（已隔离）

以下文件位于 `legacy/assertion_v1/` 目录，属于遗留断言系统V1，已与生产路径隔离：

| 文件 | 用途 |
|---|---|
| `legacy/assertion_v1/systems.py` | 旧体系定义 |
| `legacy/assertion_v1/environmental_fit.py` | 旧环境适配 |
| `legacy/assertion_v1/engine_adapters.py` | 旧引擎适配器 |

**状态**: ✅ 已隔离，不影响生产路径

---

## 四、测试文件（直接测试旧引擎）

| 文件 | 用途 |
|---|---|
| `tests/test_strength_engine.py` | strength_engine直接测试 |
| `tests/test_strength_engine_yinyang.py` | 阴阳相关测试 |
| `tests/test_judgment_engine.py` | judgment_engine测试（间接依赖） |
| `tests/test_environmental_fit.py` | legacy环境适配测试 |
| `tests/test_new_engines.py` | 新引擎测试（可能间接依赖） |
| `tests/test_p2_direction_golden.py` | P2方向黄金测试（可能间接依赖） |

**处理建议**: 保留旧引擎测试作为回归参考，迁移完成后标记为legacy测试。

---

## 五、迁移路线图

### 阶段1：数据层建立（✅ 已完成）
- CanonicalState 数据结构（P0-①）
- Facts / Relations / ClassicalStates / Qualifiers / UnresolvedReasons / Provenance

### 阶段2：生产路径标记（✅ 已完成）
- strength_engine.py 添加 LEGACY 标记
- 调用图审计完成（本文档）

### 阶段3：逐步迁移（⏳ 待执行）
1. **health_signals.py**: 从 CanonicalState 读取 climate / support_count / drain_count 等中间产物
2. **annual_event_evaluator.py**: 从 CanonicalState 读取旺衰候选状态，替代 verdict 字符串
3. **judgment_engine.py**: 接收 CanonicalState 替代 D1StrengthResult

### 阶段4：经典辨证替代（⏳ 待执行）
- 五部经典各自 Primitive / Evidence / State 建立后
- 整体旺衰保持 UNRESOLVED，除非有明确原典授权的综合规则

---

## 六、治理原则（持续生效）

1. ❌ 禁止五行计分→强弱
2. ❌ 禁止 strength_score / root_score
3. ❌ 禁止未经授权的组合规则直接推出最终强弱
4. ✅ 原典授权 ≠ 条件成立 ≠ 断事结论授权
5. ✅ 整体旺衰保持 UNRESOLVED，除非有明确原典授权
6. ✅ 每个状态必须可追溯：state → evidence → primitive → canonical facts → 原始命盘

---

## 七、审计结论

| 项 | 裁决 |
|---|---|
| 旧引擎状态标记 | 🟢 PASS（已添加LEGACY标记） |
| 生产路径调用识别 | 🟢 PASS（2处实际调用 + 1处类型依赖） |
| Legacy路径隔离 | 🟢 PASS（已在legacy/目录） |
| 生产路径完全迁移 | 🔴 未完成（需逐步迁移） |
| 经典辨证完全替代 | 🔴 未完成（需五部经典辨证规则建立） |

**最终裁决**: 🟡 CONDITIONAL PASS

旧评分路径已识别并标记，生产路径调用已明确记录。
后续需按迁移路线图逐步将生产路径从 strength_engine 迁移到 CanonicalState + 经典辨证架构。
