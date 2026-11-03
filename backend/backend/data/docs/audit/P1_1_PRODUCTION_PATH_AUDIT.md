# P1.1 — Production Runtime Path Audit

**Date**: 2026-09-01  
**Branch**: main (commit `5bfa656`)  
**Status**: 🔴 Complete — critical gaps found

---

## 1. Executive Summary

The production runtime path has **two parallel signal systems** that are structurally decoupled:

| System | Location | Status | Used By |
|--------|----------|--------|---------|
| Legacy Signal | `reasoning/signal_engine.py` | ✅ Production | Bazi, Ziwei, Huangli engines → ComputeStage |
| New Signal | `signal/canonical_signal.py` | ⚠️ Partial | blind_bazi_engine, yi/adapter (NOT in main pipeline) |
| Temporal Convergence | `temporal/convergence.py` | ⚠️ Narrow | yi/adapter only |
| Signal Convergence | `signal/convergence.py` | 🔴 Dead | No callers |
| Assertion V2 | `assertion_v2/contract.py` | 🔴 Dead | No production callers |
| Judgment Architecture | `judgment_architecture/` | 🔴 Dead | No production callers |

**Critical Gap**: The `signal/` layer (CanonicalSignal, Adapters, Aggregator, ConvergenceArbiter) is **not wired into the production pipeline**. The main pipeline uses the older `reasoning/signal_engine.py` with a locally-defined `Signal` dataclass. Two engines (`blind_bazi_engine`, `yi/adapter`) have migrated to the new system but their output never converges back into the main pipeline's canonical composer.

---

## 2. Production Path Map (Verified)

```
API (/v1/daily-guide)
  └─ TONGSHUPipeline.run()
       └─ ComputeStage.run()
            ├─ BaziEngine → BaziChart (via BaziAdapter)
            ├─ ZiweiEngine → ZiweiChart (via ZiweiAdapter)
            ├─ HuangliEngine → HuangliDay
            ├─ SignalEngine (reasoning/signal_engine.py)
            │    └─ RuleMatcher → Signal[] (local class) × 3 layers
            ├─ CrossAnalyzer → CrossResult (Bazi vs Ziwei)
            ├─ HeluoCanonical → HeluoResult (optional, degrades to None)
            ├─ YiAdapter (spec.canonical_signal.CanonicalSignal) + TemporalConvergence
            │    └─ YiInterpretationEngine → YiInterpretation (optional)
            └─ CanonicalComposer
                 └─ CanonicalContent (SIR) ← Signal[] + CrossResult + Claims
       └─ RenderStage → Renderer → TemplateFallback
       └─ ValidationStage → Validation
       └─ AuditComposer → AuditWriter
```

**Key observation**: `YiAdapter` output (`yi_structure`, `yi_interpretation`) is attached to `ComputeResult` but **not consumed by `CanonicalComposer`**. It appears as metadata on `PipelineResult` only.

---

## 3. Duplicate / Dead Path Audit

### 3.1 Dead Modules (Zero Production Callers)

| Module | Lines | Production Callers | Notes |
|--------|-------|--------------------|-------|
| `assertion_v2/__init__.py` | ~50 | 0 | Only referenced in `scripts/p0_8_assertion_pipeline*.py` (research) |
| `assertion_v2/contract.py` | ~200 | 0 | 5-engine native judgment contract; no pipeline integration |
| `judgment_architecture/*.py` (8 files) | ~2000 | 0 | Only referenced by `tests/test_p6c_*.py` and `scripts/p6c_*.py` |
| `signal/convergence.py` (ConvergenceArbiter) | ~180 | 0 | Self-referenced docstring examples only; no external caller |
| `signal/legacy_adapter.py` | ~100 | 0 | Imported by `signal/__init__.py` but no external consumer |
| `signal/aggregator.py` | ~300 | 0 | Only used in research scripts (`p0_6_aggregation_contract.py`) |

**Total dead code**: ~2,800+ lines in `src/tongshu/` with no production path.

### 3.2 Duplicate Class Definitions

| Class | Location A | Location B | Consumer |
|-------|-----------|-----------|----------|
| `TemporalConvergence` | `spec/temporal_evidence.py` | `temporal/schema.py` | `yi/adapter.py` imports from `spec/`; `temporal/convergence.py` defines its own |

These are structurally identical but independent definitions. If one changes, the other drifts.

### 3.3 Dual Signal Schema

| Schema | File | Used By | Version |
|--------|------|---------|---------|
| Legacy `Signal` (dataclass) | `reasoning/signal_engine.py:63` | ComputeStage → CrossAnalyzer → CanonicalComposer | Current production |
| `CanonicalSignal` (spec) | `spec/canonical_signal.py` | blind_bazi_engine, yi/adapter, signal adapters | New, not in main pipeline |
| `CanonicalSignal` (extended) | `signal/canonical_signal.py` | inherits from spec version | New, orphaned |

The two `CanonicalSignal` definitions create confusion: `spec/canonical_signal.py` defines the base schema, while `signal/canonical_signal.py` extends it with additional fields (confidence, evidence_refs requiring EvidenceChainContext). Only `blind_bazi_engine.py` uses the extended version.

---

## 4. Layer-by-Layer Trace

### Layer 1 — API (`src/tongshu/api/app.py`)
- **Routes**: `/health`, `/v1/auth/*`, `/nfc/*`, `/calculate`
- **Auth gateway** wraps protected routes
- **Comment** references `assertion_v2/judgment_architecture` as future debug surface — confirms they exist but are **not yet integrated**
- ✅ No legacy `/admin` route (P0 purge confirmed)

### Layer 2 — Pipeline (`src/tongshu/pipeline.py`)
- 311 source lines, clean imports
- **No reference to `assertion_v2`, `judgment_architecture`, `signal.convergence`, or `signal.aggregator`**
- `ComputeStage` is the orchestrator; all reasoning happens there

### Layer 3 — Engines (`src/tongshu/engines/`)
| Engine | Signal Output | Production? |
|--------|--------------|-------------|
| `bazi_engine.py` | Legacy `Signal` (via SignalEngine) | ✅ Core |
| `ziwei_engine.py` | Legacy `Signal` (via SignalEngine) | ✅ Core |
| `huangli_engine.py` | Legacy `Signal` (via SignalEngine) | ✅ Support |
| `blind_bazi_engine.py` | `CanonicalSignal` (new) | ⚠️ Present but output unused |
| `heluo/canonical.py` | `HeluoResult` | ✅ Optional path |
| `yi/adapter.py` | `YiStructure` + `TemporalConvergence` | ⚠️ Optional path, output metadata only |

### Layer 4 — Canonical (`src/tongshu/canonical/`)
- `composer.py`: Consumes `Signal` (legacy), `CrossResult`, builds `CanonicalContent` (SIR)
- `state.py`: ~1900 lines — God Object risk (deferred to P2)
- `canonical_validator.py`: JSON Schema validation for SIR output

### Layer 5 — Signal/Reasoning (`src/tongshu/reasoning/` + `src/tongshu/signal/`)
| Module | Role | Production? |
|--------|------|-------------|
| `signal_engine.py` | Rule matching → `Signal[]` × 3 layers | ✅ Main path |
| `cross_analysis.py` | Bazi vs Ziwei conflict resolution | ✅ Main path |
| `theme_engine.py` | Theme-to-modern-label mapping | ✅ Main path |
| `matcher.py` | RuleMatcher + resolve_conflicts | ✅ Main path |
| `rule_loader.py` | Rule loading from JSON | ✅ Main path |
| `knowledge_base.py` | KB link verification | ✅ Main path (verification only) |
| `mapping_registry.py` | Modern语标签映射 | ✅ Main path (optional) |
| `signal/canonical_signal.py` | New signal schema | ⚠️ Partial (blind_bazi, Yi) |
| `signal/adapters/` | Engine→CanonicalSignal adapters | ⚠️ Partial |
| `signal/convergence.py` | ConvergenceArbiter | 🔴 Dead |
| `signal/aggregator.py` | Signal aggregation | 🔴 Dead |
| `signal/legacy_adapter.py` | Legacy→Canonical adapter | 🔴 Dead |
| `signal/normalizer.py` | Signal normalization | ⚠️ Unknown (imported by __init__ only) |

### Layer 6 — Assertion V2 (`src/tongshu/assertion_v2/`)
- `contract.py`: Defines 5-engine native judgment contract (ZiPing, BlindSchool, ZiWei, HeLuo, YiJing)
- **No production import chain** — only referenced in research scripts and a comment in `api/app.py`
- **Verdict**: Dead code in production; valid design artifact but not wired

### Layer 7 — Judgment Architecture (`src/tongshu/judgment_architecture/`)
- 8 files: authenticity_audit, canonical_asset_acquisition, golden_index_coverage, judgment_asset_v2, judgment_index_foundation, source_verification, system_school_contract, vertical_slice_50
- **No production import chain** — only used by `tests/test_p6c_*.py` and `scripts/p6c_*.py`
- **Verdict**: Test/research codebase; not part of runtime

### Layer 8 — Render (`src/tongshu/render/`)
- `renderer.py`: LLM renderer
- `template_fallback.py`: Deterministic fallback (legitimate, not legacy)
- `render_request.py`: Request DTO
- `services/daily_api.py`, `daily_state_service.py`: Service layer

---

## 5. Convergence Gap Analysis

### 5.1 The Missing Link

```
[blind_bazi_engine] --CanonicalSignal--> [signal/adapters/BaziAdapter]
                                             |
                                             X (no connection to main pipeline)
                                             |
[main pipeline] <--Signal[]-------------- [reasoning/signal_engine]
```

`blind_bazi_engine` produces `CanonicalSignal` objects but:
1. `ComputeStage` does NOT call `blind_bazi_engine`
2. Even if it did, `CanonicalComposer` expects `Signal` (legacy), not `CanonicalSignal`
3. There is no `LegacyAdapter` wiring in the production path

### 5.2 Yi Path (Partially Integrated)

```
[YiAdapter] --YiStructure--> [ComputeResult.yi_structure]
                              [CanonicalContent] ✗ (not consumed)
```

Yi output is attached to `ComputeResult` and `PipelineResult` but **never fed into `CanonicalComposer`**. It exists as metadata only.

### 5.3 Temporal Convergence Duplication

`TemporalConvergence` class exists in two places:
- `spec/temporal_evidence.py` — imported by `yi/adapter.py`
- `temporal/schema.py` — imported by `temporal/convergence.py`

Both define the same class. `yi/adapter.py` uses the `spec/` version. `temporal/convergence.py`'s `TemporalConvergenceEngine` returns the `temporal/schema` version. These are **independent copies** that can diverge.

---

## 6. Recommendations (P1 Priority)

### P1.1-A: Decide on Signal Schema Unification [HIGH]
**Problem**: Two signal schemas (`Signal` vs `CanonicalSignal`) coexist with no migration path.
**Options**:
- **Option A**: Migrate `CanonicalComposer` to accept `CanonicalSignal` (requires SignalEngine rewrite)
- **Option B**: Add `LegacyAdapter` in `signal/` to convert legacy `Signal` → `CanonicalSignal` for unified downstream processing
- **Option C**: Keep both but add explicit routing in `ComputeStage` with clear deprecation timeline

**Recommended**: Option B (add adapter) — lowest risk, preserves existing tests.

### P1.1-B: Wire blind_bazi_engine into ComputeStage [HIGH]
**Problem**: `blind_bazi_engine` is present but never called from the production pipeline.
**Action**: Add optional blind_bazi step to `ComputeStage` with graceful degradation (same pattern as heluo/yi).

### P1.1-C: Eliminate Dead Code [MEDIUM]
**Action**: Move or delete:
- `signal/convergence.py` (ConvergenceArbiter) — if no planned use, defer to P2 cleanup
- `signal/legacy_adapter.py` — if no planned use, defer
- `assertion_v2/` — if not in current P1 scope, mark as research artifact
- `judgment_architecture/` — if not in current P1 scope, mark as research artifact

### P1.1-D: Deduplicate TemporalConvergence [MEDIUM]
**Action**: Pick one canonical location (`spec/` or `temporal/`) and remove the duplicate. All consumers must import from the same location.

### P1.1-E: Clarify Yi Output Consumption [LOW]
**Problem**: `yi_structure` and `yi_interpretation` are attached to `PipelineResult` but never used by render or validation stages.
**Action**: Either wire into `CanonicalComposer` or document as observability-only metadata.

---

## 7. Files Requiring Immediate Review

| File | Issue | Priority |
|------|-------|----------|
| `src/tongshu/reasoning/signal_engine.py` | Legacy Signal schema — may need adapter bridge | P1.1-A |
| `src/tongshu/canonical/composer.py` | Accepts legacy Signal, not CanonicalSignal | P1.1-A |
| `src/tongshu/engines/blind_bazi_engine.py` | Outputs CanonicalSignal but not called from pipeline | P1.1-B |
| `src/tongshu/yi/adapter.py` | Uses spec.canonical_signal; output not consumed | P1.1-E |
| `src/tongshu/spec/temporal_evidence.py` | Duplicate TemporalConvergence | P1.1-D |
| `src/tongshu/temporal/schema.py` | Duplicate TemporalConvergence | P1.1-D |
| `src/tongshu/signal/convergence.py` | Dead code (ConvergenceArbiter) | P1.1-C |
| `src/tongshu/signal/aggregator.py` | Dead code (no callers) | P1.1-C |
| `src/tongshu/assertion_v2/contract.py` | Dead code (no production callers) | P1.1-C |
| `src/tongshu/judgment_architecture/*.py` (8 files) | Dead code (test/research only) | P1.1-C |

---

## 8. Confidence Assessment

| Finding | Confidence | Basis |
|---------|-----------|-------|
| assertion_v2 has zero production callers | **High** | `git grep` across all src/ files |
| judgment_architecture has zero production callers | **High** | `git grep` across all src/ files |
| signal/convergence.py (ConvergenceArbiter) is dead | **High** | Self-referenced only |
| signal/aggregator.py is dead | **High** | Only used in research scripts |
| Dual signal schema exists | **High** | Direct file inspection |
| TemporalConvergence duplicated | **High** | Both class definitions inspected |
| blind_bazi_engine not called from pipeline | **High** | Not in ComputeStage imports |
| Yi output is metadata-only | **High** | ComputeStage attaches but Composer ignores |

---

## 9. Next Steps

1. **P1.1-D (TemporalConvergence dedup)**: Can be done immediately — lowest risk, clear win.
2. **P1.1-C (Dead code removal)**: Safe to remove `signal/convergence.py`, `signal/legacy_adapter.py`, and mark `assertion_v2`/`judgment_architecture` as research artifacts.
3. **P1.1-A (Signal schema unification)**: Requires design decision — consult with architecture owner.
4. **P1.1-B (blind_bazi integration)**: Requires understanding blind_bazi's role in the overall system.
5. **P1.1-E (Yi output consumption)**: Low priority — document current behavior as-is until unification decision.
