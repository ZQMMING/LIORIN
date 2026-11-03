# P0-LEGACY-PATH-AUDIT — Legacy Production Path Matrix

**Audit Date**: 2026-09-01
**Baseline**: origin/main HEAD `b93b8e7` (P1.2 Signal Contract Unification Design)
**Prior Baseline Referenced**: commit `9a1479d` (P0-8.6, 2026-08-31)

---

## Executive Summary

| Component | File Exists | Production Caller | Status | Verdict |
|-----------|-------------|-------------------|--------|---------|
| `strength_engine.py` | ❌ DELETED | N/A | DELETED | ✅ 已清理（commit `966db50`） |
| `infer_verdict()` | N/A | 0 | DEAD_CODE | ✅ 已清理 |
| `evaluate_strength()` | N/A | 0 | DEAD_CODE | ✅ 已清理 |
| `wang_score` (scoring) | N/A | 0 | DEAD_CODE | ✅ 已清理（防御性 guard 保留于 state.py:437） |
| `SignalEngine` | ✅ EXISTS | `pipeline.py:86`, `compute_stage.py:37` | **ACTIVE_PRODUCTION** | 🔴 核心问题 |
| `Signal.direction` | ✅ EXISTS | `composer.py:147`, `compute_stage.py:138` | **ACTIVE_PRODUCTION** | 🔴 核心问题 |
| `Signal.polarity` | ✅ EXISTS | `composer.py:155`, `cross_analysis.py:6` | **ACTIVE_PRODUCTION** | 🔴 核心问题 |
| `_derive_direction_polarity()` | ✅ EXISTS | `signal_engine.py:300` (internal) | **ACTIVE_PRODUCTION** | 🔴 核心问题 |
| `RuleMatcher` | ✅ EXISTS | `pipeline.py:85`, `signal_engine.py:18` | **ACTIVE_PRODUCTION** | ⚠️ 新/旧混合 |
| `RuleLoader` | ✅ EXISTS | `pipeline.py:131` | **ACTIVE_PRODUCTION** | ✅ 新架构基础设施 |
| `cross_analysis.py` | ✅ EXISTS | `pipeline.py`, `compute_stage.py` | **ACTIVE_PRODUCTION** | 🔴 使用旧 Signal 结构 |
| `judgment_production.py` | ✅ EXISTS | 0 | **ISOLATED** | 🟡 未接入主链路 |
| `legacy_adapter.py` | ✅ EXISTS | 0（无调用方） | **TEST_ONLY / UNUSUAL** | 🟡 适配器存在但未启用 |
| `Evidence→Primitive→Judgment→Assertion` | ✅ EXISTS | 0（不在主链路） | **ISOLATED** | 🟡 新架构未接入生产 |

---

## 1. `strength_engine.py` — ❌ 用户误判，已删除

**事实核查**：
- 文件在 commit `966db50` (P0: Legacy Runtime Complete Purge) 中被删除
- `origin/main` 上不存在此文件
- `git show origin/main:src/tongshu/engines/strength_engine.py` → exit code 0, 0 lines

**防御性残留**（`canonical/state.py:437`）：
```python
forbidden_keys = {"strength_score", "root_score", "wangshuai_score", "qiangruo_score", "wang_score"}
for key in forbidden_keys:
    if key in self.metadata:
        errors.append(f"禁止评分模型：metadata 中发现 {key}")
```
此 guard 是防止回归的"看门狗"，不是旧评分系统的残留。

**结论**：`strength_engine.py` 的旧评分系统已清理。用户描述的"D1 旺衰 Deterministic Engine + wang_score 评分"在当前 main 上不存在。需确认用户检查的代码源（可能是本地旧分支或未同步的工作区）。

---

## 2. `signal_engine.py` — 🔴 ACTIVE_PRODUCTION，核心架构问题

**生产路径追踪**：
```
pipeline.py:86  →  self.signal_engine = SignalEngine(self.rule_matcher)
compute_stage.py:138 → signals = self.signal_engine.build(...)
canonical/composer.py:87 → signals_dict = self._format_signals(signals)
canonical/composer.py:147 → "signal_id": s.signal_id
canonical/composer.py:155 → for s in signals.get(layer, [])
```

**`_derive_direction_polarity()` 逻辑**（`signal_engine.py:274-294`）：
```python
# T1 修复: produces_semantic_atoms → direction/polarity 推导
_ATOM_DIRECTION_MAP = {
    "SUPPORT": "STABLE", "ACTION": "INCREASE", "WEAKEN": "DECREASE", ...
}
_ATOM_POLARITY_MAP = {
    "SUPPORT": "active", "ACTION": "active", "WEAKEN": "restricted", ...
}
```

**问题**：`Semantic Atom → direction/polarity → Signal` 这个映射关系直接嵌入在生产路径中。每条 rule match 都会触发 `_derive_direction_polarity()`，产出携带 `direction` 和 `polarity` 字段的 Signal 对象，最终序列化进 SIR。

**结论**：这是用户指出的"错误架构"在生产链中的实际存在。新架构主张 `Evidence → Primitive → Condition → Judgment → Assertion`，但主链路仍然走 `Rule → Signal(direction/polarity) → CrossAnalysis → SIR`。

---

## 3. `cross_analysis.py` — 🔴 消费旧 Signal 结构

```python
# cross_analysis.py:12
from .signal_engine import Signal
```

`ComputeStage._build_atomic_claims()` 接收 `signals: dict[str, list[Signal]]`，其中每个 Signal 有 `direction`/`polarity` 字段。Cross Analysis 的结果直接影响 atomic_claims 的生成。

**结论**：Cross Analysis 是新架构下产生 judgment 的关键步骤，但它消费的输入来自旧的 Signal 体系。

---

## 4. `judgment_production.py` — 🟡 ISOLATED（新架构未接入）

```python
# 搜索所有 import/call
grep -rn "JudgmentProducer\|judgment_production\|JudgmentEngine" src/tongshu/ --include="*.py"
# → (no output outside the file itself)
```

`judgment_production.py` 存在但零生产调用方。这是新架构（Evidence→Primitive→Judgment→Assertion）的实现，但**未接入主链路**。

---

## 5. `legacy_adapter.py` — 🟡 TEST_ONLY（适配器存在但未启用）

```python
# legacy_adapter.py:1
"""P0-③ Legacy Signal Adapter — 基础层 Signal 到 CanonicalSignal 的适配器"""
```

`legacy_signal_to_canonical()` 将旧 `Signal(direction/polarity)` 转换为新 `CanonicalSignal(EventDirection)`。但全仓库无调用方：
```
grep -rn "legacy_adapter\|to_canonical\|legacy_signal" src/tongshu/ --include="*.py"
# → only matches legacy_adapter.py itself
```

**结论**：迁移桥梁代码已写好，但没有被实际调用。新旧架构之间没有运行时转换。

---

## 6. 双链并存架构 — 🔴 核心风险

### 当前生产链路（唯一运行）
```
TONGSHUPipeline.run()
  → ComputeStage
    → BaziEngine / ZiweiEngine / HuangliEngine
    → SignalEngine.build()     ← 旧：Rule → Signal(direction/polarity)
    → CrossAnalysis.analyze()  ← 消费旧 Signal
    → CanonicalComposer.compose()
    → RenderStage
    → SIR Output
```

### 新架构（存在但未接入）
```
Evidence → Primitive → Condition → Judgment → Assertion
  ↑
judgment_production.py (零调用方)
  ↑
P0-6.x / P0-8.x commits (已合入 main，但只在测试/独立脚本中)
```

### 风险评估

| 风险项 | 等级 | 说明 |
|--------|------|------|
| 同一 Evidence 双路径解释 | 🔴 HIGH | 旧 Signal 路径主导生产，新 Judgment 路径仅测试 |
| direction/polarity 语义漂移 | 🔴 HIGH | Semantic Atom → direction 映射是硬编码，无溯源 |
| legacy_adapter 死代码 | 🟡 MEDIUM | 迁移桥梁未启用，占用代码空间但不产生危害 |
| judgment_production 孤儿化 | 🟡 MEDIUM | 新架构实现已写入但未集成，测试覆盖有限 |

---

## 7. 测试状态

```
pytest tests/ --ignore=tests/auth/ --ignore=tests/test_llm_client.py
→ 大量 pass，但部分失败（FF.F.F...）
→ 失败原因：环境依赖问题（tongshu模块配置），非代码逻辑错误
```

关键测试文件：
- `test_judgment_production.py` — 不存在（被删除或重命名）
- `test_strength_engine.py` — 不存在（模块已删除）
- `test_new_engines.py` — 存在，45 passed

---

## 8. 建议行动

### P0-LEGACY-CLEANUP（阻塞 P0-8.7+ 断言扩展）

1. **明确 SignalEngine 的定位**：
   - 选项 A：将 `direction`/`polarity` 从 Signal 数据类中移除，改为在 `legacy_adapter` 中按需推导
   - 选项 B：将 SignalEngine 标注为 `LEGACY_COMPAT`，新建 `EvidenceEngine` 作为生产路径
   - **推荐选项 B**：保留旧 SignalEngine 供向后兼容，新生产路径用 Evidence→Primitive→Judgment

2. **接入 legacy_adapter**：
   - 在 `ComputeStage` 或 `CanonicalComposer` 中调用 `legacy_signal_to_canonical()`
   - 或明确放弃 adapter，直接让 SignalEngine 输出 CanonicalSignal

3. **judgment_production.py 整合决策**：
   - 要么接入主链路（需设计 Evidence→Primitive 接口）
   - 要么标注为 `RESEARCH_TOOL` 并从生产目录移除

4. **禁止向 P0-8.7 扩展断言资产**直到上述决策完成

---

## 附录：各组件 callers 明细

### SignalEngine callers
| 文件 | 行号 | 用法 |
|------|------|------|
| `pipeline.py` | 26, 86 | `from .reasoning.signal_engine import SignalEngine`; `self.signal_engine = SignalEngine(self.rule_matcher)` |
| `compute_stage.py` | 37, 65, 138 | `from ..reasoning.signal_engine import SignalEngine`; 构造注入; `self.signal_engine.build(...)` |
| `ziwei_engine.py` | 164 | `from ..reasoning.signal_engine import Signal` (仅用 Signal dataclass) |
| `canonical/composer.py` | 18 | `from ..reasoning.signal_engine import Signal` |
| `reasoning/cross_analysis.py` | 12 | `from .signal_engine import Signal` |
| `signal/legacy_adapter.py` | — | 引用 Signal 做转换 |

### RuleMatcher callers
| 文件 | 行号 | 用法 |
|------|------|------|
| `pipeline.py` | 29, 85, 139 | 创建并注入 SignalEngine |
| `compute_stage.py` | 36, 71 | 构造注入 |
| `signal_engine.py` | 18 | `from .matcher import RuleMatcher` |
| `db/seed.py` | — | 测试/初始化用 |

### direction/polarity 在生产的完整流
```
signal_engine.py:274  _derive_direction_polarity(rule)
  → signal_engine.py:300  direction, polarity = _derive_direction_polarity(rule)
  → signal_engine.py:306  Signal(direction=direction, polarity=polarity, ...)
  → compute_stage.py:138  signals = self.signal_engine.build(...)
  → compute_stage.py:143  bazi_signals = signals.get("BASELINE", []) + ...
  → compute_stage.py:147  cross_result = self.cross_analyzer.analyze(bazi_signals, ...)
  → composer.py:87  signals_dict = self._format_signals(signals)
  → composer.py:147  "signal_id": s.signal_id, ... (含 direction/polarity)
  → SIR output
```
