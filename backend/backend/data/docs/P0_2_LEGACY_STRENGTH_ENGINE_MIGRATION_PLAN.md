# P0-② 旧评分路径迁移计划

**日期**: 2026-08-30
**目标**: 将 health_signals.py 和 annual_event_evaluator.py 从直接调用 strength_engine 迁移到消费 CanonicalState
**当前状态**: 🟡 核心框架已建立（CanonicalState + Producer），完整迁移待执行

---

## 一、迁移背景

### 1.1 问题

当前生产路径中存在2处直接调用旧评分引擎 strength_engine：

| 文件 | 行号 | 调用 | 用途 |
|---|---|---|---|
| `health_signals.py` | 99 | `evaluate_strength(chart)` | 获取旺衰结果、气候、support_count、drain_count |
| `annual_event_evaluator.py` | 207 | `evaluate_strength(chart)` | 获取旺衰verdict，供十神吉凶动态判断 |

### 1.2 治理原则

- ❌ 禁止五行计分→强弱
- ❌ 禁止 strength_score / root_score
- ✅ 原典授权 ≠ 条件成立 ≠ 断事结论授权
- ✅ 整体旺衰保持 UNRESOLVED，除非有明确原典授权

### 1.3 迁移方向

```
旧路径: BaziChart → evaluate_strength() → D1StrengthResult → 消费方

新路径: BaziChart → CanonicalStateProducer → CanonicalState → 消费方
                                    ↓
                              Facts / Relations
                                    ↓
                          经典辨证（五部经典）
```

---

## 二、已完成的核心框架

### 2.1 CanonicalState 数据结构

**文件**: `src/tongshu/canonical/state.py`

七层结构：
1. `facts` — L1原始事实（天干/地支/藏干/十神/五行/阴阳/十二长生）
2. `relations` — L1关系（生/克/同/通根/刑冲合害）
3. `classical_states` — 经典局部状态
4. `qualifiers` — 限定条件
5. `unresolved_reasons` — 未解决原因
6. `provenance` — 溯源信息
7. `overall_state` — 整体状态（默认 UNRESOLVED）

**治理约束内置**:
- 每个 ClassicalState 必须有 Provenance
- 禁止 strength_score / root_score
- 整体状态默认 UNRESOLVED，禁止自动推导

**测试**: `tests/test_canonical_state.py`，34/34 通过

### 2.2 CanonicalStateProducer

**文件**: `src/tongshu/canonical/producer.py`

从 BaziChart 生产 CanonicalState：
- 四柱 facts（天干、地支、位置）
- 藏干 facts（本气/中气/余气三层）
- 五行阴阳 facts
- 十神 facts
- 通根 relations（藏干与天干同干）
- 生克 relations（五行生克）
- 刑冲合害 relations（从 BaziChart 预计算结果读取）

**验证**: 1990-05-15 12:00 男命 → 29 facts + 1 relations，验证无错误

### 2.3 Signal 适配器

**文件**: `src/tongshu/signal/legacy_adapter.py`

将基础层 Signal 转换为 CanonicalSignal（唯一生产标准）：
- `legacy_signal_to_canonical()` — 单个转换
- `legacy_signals_to_canonical()` — 批量转换
- `add_canonical_conversion_to_signal_engine()` — 给 Signal 类添加 to_canonical() 方法

---

## 三、迁移执行计划

### 阶段1：health_signals.py 迁移（优先级：中）

**目标**: 将 `evaluate_health_signals()` 从直接调用 `evaluate_strength()` 改为消费 CanonicalState

**需要从 CanonicalState 读取的字段**:

| 旧字段（D1StrengthResult） | 新来源（CanonicalState） | 实现方式 |
|---|---|---|
| `climate` | 调候状态 | 需实现 ClimateExtractor（从月令+日干推导寒暖燥湿） |
| `support_count` | 生扶计数 | 需实现 SupportCounter（从facts/relations统计印+比劫） |
| `drain_count` | 泄耗克计数 | 需实现 DrainCounter（从facts/relations统计食伤+财+官杀） |
| `verdict` | 旺衰判断 | ❌ 禁止直接使用，保持 UNRESOLVED |
| `day_master_element` | 日主五行 | 从 facts 读取（FactType.WUXING, subject=日主） |

**执行步骤**:
1. ✅ 建立 CanonicalState + Producer（已完成）
2. ⏳ 实现 ClimateExtractor（从 CanonicalState 推导寒暖燥湿）
3. ⏳ 实现 SupportCounter / DrainCounter（从 CanonicalState 统计计数）
4. ⏳ 新增 `evaluate_health_signals_from_canonical(state)` 函数
5. ⏳ 保留原 `evaluate_health_signals()` 作为 legacy fallback
6. ⏳ 单元测试对比新旧路径输出
7. ⏳ 调用方逐步切换到新路径

**注意**: health_signals.py 中的 `verdict == "身弱"` 判断需要改为基于 CanonicalState 的经典辨证，不能直接使用旧评分结果。

### 阶段2：annual_event_evaluator.py 迁移（优先级：中）

**目标**: 将 `BaziScorer.compute()` 从直接调用 `evaluate_strength()` 改为消费 CanonicalState

**需要从 CanonicalState 读取的字段**:

| 旧字段 | 新来源 | 实现方式 |
|---|---|---|
| `verdict` | 旺衰verdict | ❌ 禁止直接使用，需改为基于经典辨证的候选状态 |
| 十神吉凶动态判断 | 十神facts + 经典规则 | 需实现 TenGodDynamicJudge（基于 CanonicalState + 经典规则） |

**执行步骤**:
1. ✅ 建立 CanonicalState + Producer（已完成）
2. ⏳ 实现 TenGodDynamicJudge（基于 CanonicalState 的十神吉凶判断）
3. ⏳ 新增 `BaziScorer.compute_from_canonical(state)` 方法
4. ⏳ 保留原 `compute()` 作为 legacy fallback
5. ⏳ 单元测试对比新旧路径输出
6. ⏳ 调用方逐步切换到新路径

### 阶段3：judgment_engine.py 类型依赖迁移（优先级：高）

**目标**: 将 `judgment()` 函数的 `d1_result: D1StrengthResult` 参数改为 `state: CanonicalState`

**执行步骤**:
1. ⏳ 修改 `judgment()` 函数签名，接收 CanonicalState
2. ⏳ 实现从 CanonicalState 读取 judgment 需要的字段
3. ⏳ 保留原函数作为 legacy fallback
4. ⏳ 单元测试
5. ⏳ 调用方切换

### 阶段4：清理（优先级：低）

1. ⏳ 所有调用方迁移完成后，将 strength_engine.py 移入 `legacy/` 目录
2. ⏳ 更新文档，标记 strength_engine 为 DEPRECATED
3. ⏳ 移除 legacy fallback 路径

---

## 四、迁移风险与注意事项

### 4.1 风险

| 风险 | 影响 | 缓解措施 |
|---|---|---|
| 新路径输出与旧路径不一致 | 健康信号/流年评估结果变化 | 单元测试对比，逐步切换，保留fallback |
| Climate/Support/Drain 提取器实现不完整 | 新路径缺少字段 | 明确标注 UNRESOLVED，不强行推导 |
| 调用方未及时切换 | 新旧路径并存 | 明确迁移计划，逐步切换 |

### 4.2 注意事项

1. **禁止直接迁移 verdict**: 旧的 `verdict`（身强/身弱）是评分式结果，违反治理原则，不能直接迁移到 CanonicalState
2. **保持 UNRESOLVED**: 整体旺衰在没有明确原典授权的综合规则前，必须保持 UNRESOLVED
3. **逐步迁移**: 不要一次性替换所有调用方，保留 legacy fallback，逐步切换
4. **单元测试**: 每个迁移步骤都需要单元测试对比新旧路径输出
5. **可追溯性**: 新路径的每个结果都必须能追溯到 CanonicalState 的 facts/relations

---

## 五、当前进度

| 阶段 | 任务 | 状态 |
|---|---|---|
| 框架 | CanonicalState 数据结构 | ✅ 完成 |
| 框架 | CanonicalStateProducer | ✅ 完成 |
| 框架 | Signal 适配器 | ✅ 完成 |
| 框架 | 单元测试（34/34） | ✅ 完成 |
| 阶段1 | ClimateExtractor | ⏳ 待实现 |
| 阶段1 | SupportCounter / DrainCounter | ⏳ 待实现 |
| 阶段1 | health_signals.py 新路径 | ⏳ 待实现 |
| 阶段2 | TenGodDynamicJudge | ⏳ 待实现 |
| 阶段2 | annual_event_evaluator.py 新路径 | ⏳ 待实现 |
| 阶段3 | judgment_engine.py 类型迁移 | ⏳ 待实现 |
| 阶段4 | strength_engine.py 移入 legacy | ⏳ 待完成 |

---

## 六、下一步

1. **立即执行**: 实现 ClimateExtractor（从 CanonicalState 推导寒暖燥湿）
2. **然后**: 实现 SupportCounter / DrainCounter（从 CanonicalState 统计计数）
3. **然后**: 新增 health_signals.py 的新路径函数
4. **然后**: 单元测试对比新旧路径
5. **最后**: 调用方逐步切换

**项目总纪律**: 算准→辨准→解准；FROZEN≠PROVEN CORRECT；P6-CALC仍是最高优先级。
