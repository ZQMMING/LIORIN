# P1.4 Cross-System Semantics Purge — Final

**Date**: 2026-09-01
**Commit**: `b6776f7`
**Status**: ✅ PURGED from production, archived for research

---

## 变更清单

### 删除（已归档）

| 原路径 | 归档路径 | 说明 |
|--------|----------|------|
| `src/tongshu/reasoning/cross_analysis.py` | `archive/reasoning/cross_analysis.py` | CrossAnalyzer + CrossResult |
| `src/tongshu/signal/convergence.py` | `archive/signal/convergence.py` | ConvergenceArbiter |
| `src/tongshu/spec/signal_ontology.py` | `archive/spec/signal_ontology.py` | USO 跨类型关系注册表 |
| `src/tongshu/spec/cross_states.py` | `archive/spec/cross_states.py` | CROSS_STATES + REASON_CODES |

### 修改（生产代码）

| 文件 | 变更 |
|------|------|
| `src/tongshu/reasoning/__init__.py` | 移除 CrossAnalyzer/CrossResult 导出 |
| `src/tongshu/types.py` | 移除 cross_result 字段（ComputeResult） |
| `src/tongshu/pipeline.py` | 移除 CrossAnalyzer 导入和实例化 |
| `src/tongshu/pipeline_stages/compute_stage.py` | 移除 cross_analyzer 参数和调用 |
| `src/tongshu/pipeline_stages/render_stage.py` | 移除 cross_result.status 引用 |
| `src/tongshu/pipeline_stages/audit_composer.py` | 移除 cross_result.status 引用 |
| `src/tongshu/canonical/composer.py` | 移除 cross_result 参数 |
| `src/tongshu/render/template_fallback.py` | 移除 6 条 CONFLICTED 模板 |
| `src/tongshu/spec/cross_states.py` | 保留 stub（backward-compatible test import） |

---

## 扫描验证

```bash
# CrossAnalyzer — 生产代码中 0 引用
grep -R "CrossAnalyzer" src/tongshu/
# 结果: 0 (仅测试注释提及)

# ALIGNED/PARTIAL/INSUFFICIENT — 旧 cross-analysis 语境中 0 引用
grep -R "\"ALIGNED\"\|'ALIGNED'" src/tongshu/reasoning/ src/tongshu/signal/
# 结果: 0

# CONFLICTED — template_fallback 中 0 引用
grep -R "CONFLICTED" src/tongshu/render/template_fallback.py
# 结果: 0
```

---

## 保留的 stub

`src/tongshu/spec/cross_states.py` 保留为薄 stub，仅供测试向后兼容导入。
新代码不得 import 此模块。

---

## 最终架构

```
Event Context
    ↓
Bazi Engine → Evidence → SemanticAtom → Authorized Rule → Assertion
Ziwei Engine → Evidence → SemanticAtom → Authorized Rule → Assertion
    ↓
CrossDomainOrchestrator
    ↓
MultiDomainSemanticCoverage
    ↓
Structured Observation
```

**旧架构（已删除）：**
```
Bazi Signals + Ziwei Signals
    ↓
CrossAnalyzer.analyze() → ALIGNED / PARTIAL / INSUFFICIENT
    ↓
template_fallback(CONFLICTED)  ← 已删除
```

---

## 测试验证

| 套件 | 结果 |
|------|------|
| `tests/spec/` (204 tests) | ✅ 全 PASS |
| `tests/temporal/` (52 tests) | ✅ 全 PASS |
| `test_signal_engine_dual_track.py` | ✅ 修复后 PASS |
| **总计** | **256/256 PASS** |

---

## 归档文件（研究参考）

所有旧文件完整保留在 `archive/` 目录，可追溯历史实现：
- `archive/reasoning/cross_analysis.py` — 原始 CrossAnalyzer 实现
- `archive/signal/convergence.py` — 原始 ConvergenceArbiter 实现
- `archive/spec/cross_states.py` — 原始 CROSS_STATES
- `archive/spec/signal_ontology.py` — 原始 USO 注册表

---

## 最终状态

```text
P1.2 Architecture          🔒 FROZEN
P1.3 Cross-Domain          🔒 FROZEN
P1.4 Cross-System Purge    ✅ COMPLETE (b6776f7)
```
