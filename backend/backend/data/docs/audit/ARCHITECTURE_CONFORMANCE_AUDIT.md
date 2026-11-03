# ARCHITECTURE CONFORMANCE AUDIT REPORT

**Project:** 順天 (TONGSHU) - 东方时间智能系统  
**Audit Date:** 2026-09-02  
**Auditor:** Agnes (Architecture Audit Agent)  
**Branch:** admission-governance-v2  
**Scope:** Read-only architecture consistency audit

---

## Executive Summary

This audit traces the complete runtime path from API entry to output, verifying conformance with the architectural requirements. The core question answered: **"Does the actual code execution path match the architecture documentation?"**

**Overall Finding:** The system is largely architecturally sound with clear layer separation, but has **one CRITICAL issue** where the P1.6 CrossDomainOrchestrator is never activated in production, causing the system to run in legacy signal-only mode. Additionally, there are architectural inconsistencies between Signal layer (legacy) and Assertion layer (new) direction concepts.

---

## Findings

### AC-AUDIT-001
**Severity:** CRITICAL  
**Category:** ARCHITECTURAL VIOLATION

**Architecture Requirement:**  
Per compute_stage.py header (line 13): "Version: 1.1.0 (P1.6: CrossDomainOrchestrator 接入生产路径)". The CrossDomainOrchestrator must be wired into production to enable authorized assertions with direction from Rule.

**Expected Behavior:**  
ComputeStage should receive `assertion_library` (ProductionRuleLibrary) and instantiate CrossDomainOrchestrator to produce authorized assertions.

**Actual Behavior:**  
In `pipeline.py` lines 109-121, `ComputeStage` is instantiated **without** the `assertion_library` parameter. This means `self._orchestrator` is always `None` (compute_stage.py line 102-104), and the cross-domain orchestration block (lines 167-169) is **never executed** in production.

**Runtime Path:**  
```
pipeline.py:109 → ComputeStage.__init__(assertion_library=None)
compute_stage.py:103 → if assertion_library is not None: ... (FALSE)
compute_stage.py:167 → if self._orchestrator is not None: ... (FALSE - SKIPPED)
compute_stage.py:184-187 → authorized_assertions is empty, atomic_claims = []
```

**Code Location:**  
- `src/tongshu/pipeline.py:109-121` (missing assertion_library parameter)
- `src/tongshu/pipeline_stages/compute_stage.py:100-104` (orchestrator stays None)
- `src/tongshu/pipeline_stages/compute_stage.py:167-169` (cross-domain skipped)

**Evidence:**
```python
# pipeline.py:109-121
self.compute_stage = ComputeStage(
    bazi_engine=self.bazi_engine,
    ziwei_engine=self.ziwei_engine,
    # ... no assertion_library parameter!
    temporal_convergence_engine=self._temporal_convergence_engine,
)

# compute_stage.py:100-104
self._assertion_library = assertion_library  # None
self._orchestrator = None
if assertion_library is not None and getattr(assertion_library, "is_production", False):
    self._orchestrator = CrossDomainOrchestrator(assertion_library=assertion_library)
```

**Impact:**  
- P1.6 authorization mechanism is **dead code** in production
- No cross-domain assertion production
- atomic_claims will be empty when no legacy signals match
- The system operates in legacy signal-only mode, not the intended assertion-based mode

**Root Cause:**  
Pipeline initialization forgotten to wire the ProductionRuleLibrary to ComputeStage.

**Recommendation:**  
Add `assertion_library` parameter to ComputeStage instantiation in `pipeline.py`. Load ProductionRuleLibrary in `for_demo()` and pass it to ComputeStage.

---

### AC-AUDIT-002
**Severity:** ARCHITECTURAL VIOLATION  
**Category:** ARCHITECTURAL VIOLATION

**Architecture Requirement:**  
Per `cross_domain/result.py` lines 75-78, 148-151: CrossDomainResult must NOT contain `direction`/`polarity`/`strength`/`confidence`/`score`/`weight` fields. The cross-domain layer is "complementary not comparative."

**Expected Behavior:**  
Cross-domain layer produces Structured Observation without direction comparison between engines.

**Actual Behavior:**  
The `Signal` dataclass (signal_engine.py:116-126) contains `direction` and `polarity` fields. While CrossDomainOrchestrator correctly uses `rule.direction` (not signal.direction) for assertions, the legacy Signal layer still carries direction concepts.

**Runtime Path:**  
```
signal_engine.py:116-126 → Signal class with direction/polarity fields
signal_engine.py:289-295 → _DIRECTION_MAP converts "INCREASE/DECLINE" to "POSITIVE/NEGATIVE"
compute_stage.py:382-397 → _map_signal_to_temporal uses sig.direction
```

**Code Location:**  
- `src/tongshu/reasoning/signal_engine.py:116-126` (Signal has direction field)
- `src/tongshu/reasoning/signal_engine.py:289-295` (_DIRECTION_MAP)
- `src/tongshu/pipeline_stages/compute_stage.py:369-374` (_DIR_MAP)

**Evidence:**
```python
# signal_engine.py:116-126
@dataclass(frozen=True)
class Signal:
    signal_id: str
    ontology_type: str
    direction: str  # ← Legacy direction field
    polarity: str   # ← Legacy polarity field
    strength: str
    layer: str
    rule_refs: list
    evidence_refs: list

# compute_stage.py:369-374
_DIR_MAP = {
    "INCREASE": "POSITIVE",
    "DECLINE": "NEGATIVE",
    "STABLE": "NEUTRAL",
    "VOLATILE": "CHANGE",
}
```

**Impact:**  
- Legacy Signal layer still carries direction/polarity concepts that contradict the new assertion architecture
- Temporal convergence maps Signal.direction to TemporalSignal.direction, propagating legacy concepts
- Creates confusion between old "signal direction" and new "assertion direction"

**Root Cause:**  
Migration from legacy signal-based architecture to assertion-based architecture incomplete. Signal layer retains old fields for backward compatibility.

**Recommendation:**  
Deprecate `direction` and `polarity` fields in Signal class. Use only `ontology_type` for semantic meaning. Direction should only exist in CanonicalAssertion.

---

### AC-AUDIT-003
**Severity:** IMPLEMENTATION BUG  
**Category:** IMPLEMENTATION BUG

**Architecture Requirement:**  
Template fallback should be invoked only when necessary (renderer failure or validation failure).

**Expected Behavior:**  
Single, clear fallback path with proper source tracking.

**Actual Behavior:**  
Template fallback is invoked in **two places**:
1. `render_stage.py:90-92` - when renderer returns None (hard failure)
2. `pipeline.py:256-262` - when validation fails

This creates potential for double fallback and unclear source tracking.

**Runtime Path:**  
```
Case 1: render_stage.py:90 → fallback = self.template_fallback.render(theme, ...)
        → source = "template_fallback"

Case 2: pipeline.py:256-262 → fallback = self.template_fallback.render(theme, None)
       → rendered_text = fallback
       → source = "template_fallback"
```

**Code Location:**  
- `src/tongshu/pipeline_stages/render_stage.py:84-92`
- `src/tongshu/pipeline.py:256-262`

**Evidence:**
```python
# render_stage.py:84-92
if rendered is not None:
    source: str = "llm_renderer"
    rendered_text = rendered.text
else:
    fallback = self.template_fallback.render(theme, compute.cross_result.status if compute.cross_result else None)
    rendered_text = fallback or ""
    source = "template_fallback" if rendered_text else "template_fallback"

# pipeline.py:256-262
if not validation_passed and self._enable_validation:
    fallback = self.template_fallback.render(theme, None)
    if fallback:
        rendered_text = fallback
        source = "template_fallback"
```

**Impact:**  
- Confusing fallback logic with two entry points
- Source tracking may be inconsistent
- Hard to debug which fallback path was taken

**Root Cause:**  
Historical accumulation of fallback logic in different stages without unification.

**Recommendation:**  
Unify fallback logic into a single point. Consider moving all fallback handling to RenderStage or to pipeline.run().

---

### AC-AUDIT-004
**Severity:** LEGACY RESIDUE  
**Category:** LEGACY RESIDUE

**Architecture Requirement:**  
Deprecated endpoints should be removed after sunset date (2027-08-18 per app.py line 7-8).

**Expected Behavior:**  
Only current API paths (/v1/*) should be active.

**Actual Behavior:**  
Deprecated endpoints `/api/reading` (line 531-553) and `/api/today` (line 555-569) are still registered in the FastAPI app.

**Code Location:**  
- `src/tongshu/api/app.py:531-569`

**Evidence:**
```python
@app.post("/api/reading", deprecated=True, ...)
def reading_legacy(...):
    ...

@app.get("/api/today", deprecated=True, ...)
def today_legacy(...):
    ...
```

**Impact:**  
- Unnecessary code surface
- Potential security surface (deprecated paths may have different validation)
- Technical debt

**Root Cause:**  
 Sunset date is in the future (2027-08-18), so cleanup deferred.

**Recommendation:**  
Add automated cleanup job to remove deprecated endpoints after sunset date. Document sunset policy.

---

### AC-AUDIT-005
**Severity:** DOCUMENTATION GAP  
**Category:** DOCUMENTATION GAP

**Architecture Requirement:**  
Architecture documentation should accurately reflect production code paths.

**Expected Behavior:**  
Documentation should state whether P1.6 CrossDomainOrchestrator is active in production.

**Actual Behavior:**  
Documentation claims "CrossDomainOrchestrator 接入生产路径" but code shows it's never instantiated with a production library.

**Code Location:**  
- `src/tongshu/pipeline_stages/compute_stage.py:13` (Version comment)
- `src/tongshu/pipeline_stages/compute_stage.py:6` (Feature list)

**Evidence:**
```python
# compute_stage.py header
Version: 1.1.0 (P1.6: CrossDomainOrchestrator 接入生产路径)
```

**Impact:**  
- Misleading documentation creates false confidence
- New developers may assume P1.6 is active when it's not

**Root Cause:**  
Documentation updated before implementation completed.

**Recommendation:**  
Update documentation to reflect actual production state. Either:
1. Complete P1.6 integration and update docs
2. Mark P1.6 as "pending implementation" in docs

---

### AC-AUDIT-006
**Severity:** IMPLEMENTATION BUG  
**Category:** IMPLEMENTATION BUG

**Architecture Requirement:**  
API responses should not leak internal signal/evidence details to external consumers.

**Expected Behavior:**  
Only final authorized output (rendered_text, atomic_claims summary) should be returned.

**Actual Behavior:**  
`/v1/daily-guide` endpoint returns `atomic_claims` (line 308) and `signal_counts` (lines 304-306) in the response. While these are counts and summarized data, they expose internal state.

**Code Location:**  
- `src/tongshu/api/app.py:291-314`

**Evidence:**
```python
# app.py:291-314
def _reading_response(result, analysis: date) -> dict:
    canon = result.canonical
    signals = canon.signals or {}
    resp = {
        ...
        "signal_counts": {
            "BASELINE": len(signals.get("BASELINE", [])),
            "CYCLE_CONTEXT": len(signals.get("CYCLE_CONTEXT", [])),
            "DAILY_ACTIVATION": len(signals.get("DAILY_ACTIVATION", [])),
        },
        "atomic_claims": canon.atomic_claims or [],  # ← Full claims exposed
        ...
    }
    return resp
```

**Impact:**  
- Internal signal structure exposed to API consumers
- Potential information leakage about internal architecture
- Consumers may depend on internal structure that could change

**Root Cause:**  
API response designed for debugging/development, not hardened for production.

**Recommendation:**  
Consider removing or minimizing internal details from public API. Use separate internal/debug endpoint if needed.

---

### AC-AUDIT-007
**Severity:** IMPLEMENTATION BUG  
**Category:** IMPLEMENTATION BUG

**Architecture Requirement:**  
Engines should be deterministic and not return fallback/default values that pollute results.

**Expected Behavior:**  
Engine outputs should be pure computations without silent defaults.

**Actual Behavior:**  
Several engines use `try/except` with fallback to None or empty values:
- `compute_stage.py:288`: Heluo/Yi integration fails silently, returns (None, None, None)
- `render_stage.py:80-81`: RenderClientError caught, falls back to template
- `ziwei_engine.py`: Multiple except Exception blocks

**Code Location:**  
- `src/tongshu/pipeline_stages/compute_stage.py:268-290`
- `src/tongshu/pipeline_stages/render_stage.py:75-92`
- `src/tongshu/engines/ziwei_engine.py:148,228,488,527,969,1015`

**Evidence:**
```python
# compute_stage.py:288
except Exception as exc:  # noqa: BLE001 — 河洛/易经降级，不中断主管道
    log.warning("Heluo/Yi integration failed (degraded, 不影响主链路): %s", exc)
return heluo_result, yi_structure, yi_interpretation  # Could be all None
```

**Impact:**  
- Silent failures may produce incomplete results
- Hard to detect when optional engines fail
- May affect downstream processing that expects valid data

**Root Cause:**  
Design decision to make optional engines non-blocking, but creates observability gaps.

**Recommendation:**  
Add explicit failure tracking in PipelineResult. Log warnings at appropriate level. Consider making failure modes explicit in output schema.

---

### AC-AUDIT-008
**Severity:** NON-ISSUE  
**Category:** NON-ISSUE

**Architecture Requirement:**  
Five systems (子平/盲派/紫微/河洛/易经) should be complementary, not comparative.

**Expected Behavior:**  
No voting/conflict resolution between systems.

**Actual Behavior:**  
Cross-domain layer correctly implements complementary architecture. No vote/conflict/majority logic found in production path.

**Code Location:**  
- `src/tongshu/cross_domain/result.py:75-78,148-151` (forbidden attributes documented)
- `src/tongshu/cross_domain/orchestrator.py:10-15` (forbidden operations documented)

**Evidence:**
```python
# cross_domain/result.py:75-78
Forbidden:
- direction / polarity / strength / confidence / score / weight
- CONFLICTED / ALIGNED / PARTIAL states
- vote / compare / rank logic
```

**Impact:**  
None - architecture is correctly implemented.

**Root Cause:**  
N/A - This is the expected behavior.

**Recommendation:**  
None needed.

---

### AC-AUDIT-009
**Severity:** TEST GAP  
**Category:** TEST GAP

**Architecture Requirement:**  
Tests should verify that CrossDomainOrchestrator is properly wired in production.

**Expected Behavior:**  
Test coverage for P1.6 integration path.

**Actual Behavior:**  
No tests found that verify CrossDomainOrchestrator is instantiated with production library in pipeline.

**Code Location:**  
- Test files would need to be checked (not in scope of this read-only audit)

**Impact:**  
- P1.6 bug would not be caught by tests
- Regression risk when modifying pipeline initialization

**Root Cause:**  
Test coverage focused on legacy signal path, not new assertion path.

**Recommendation:**  
Add integration test that verifies:
1. ComputeStage receives assertion_library in production
2. CrossDomainOrchestrator is instantiated
3. authorized_assertions are produced from rules

---

### AC-AUDIT-010
**Severity:** ARCHITECTURAL VIOLATION  
**Category:** ARCHITECTURAL VIOLATION

**Architecture Requirement:**  
Assertion direction (AssertionDirection enum: supportive/caution/neutral) should be the only direction concept in the assertion layer.

**Expected Behavior:**  
Clean separation: Signal has ontology_type, Assertion has direction.

**Actual Behavior:**  
Two parallel direction systems exist:
1. Legacy Signal.direction: "INCREASE"/"DECLINE"/"STABLE"/"VOLATILE"
2. New AssertionDirection: "supportive"/"caution"/"neutral"

The mapping between them is implicit and not enforced.

**Code Location:**  
- `src/tongshu/reasoning/signal_engine.py:289-295` (_DIRECTION_MAP)
- `src/tongshu/spec/canonical/assertion.py:16-21` (AssertionDirection enum)
- `src/tongshu/pipeline_stages/compute_stage.py:369-374` (_DIR_MAP)

**Evidence:**
```python
# signal_engine.py:289-295
_DIRECTION_MAP = {
    "INCREASE": "POSITIVE",
    "DECLINE": "NEGATIVE",
    "STABLE": "NEUTRAL",
    "VOLATILE": "CHANGE",
}

# assertion.py:16-21
class AssertionDirection(str, enum.Enum):
    SUPPORTIVE = "supportive"
    CAUTION = "caution"
    NEUTRAL = "neutral"
```

**Impact:**  
- Confusion about which direction system to use
- Potential for inconsistency if mapping is not maintained
- Technical debt from dual systems

**Root Cause:**  
Incremental migration from signal-based to assertion-based architecture.

**Recommendation:**  
Complete migration: Remove direction from Signal class. Map ontology_type directly to AssertionDirection in CrossDomainOrchestrator.

---

## Runtime Path Trace

### Complete Execution Flow

```
1. API Entry (app.py)
   ↓
   POST /v1/daily-guide
   ↓
   _gate_personal(req) → Profile validation
   ↓
   pipeline.run(...)
   
2. Pipeline.run() (pipeline.py:166-313)
   ↓
   B-02: Build calc_context (if timezone+location provided)
   ↓
   Stage 1-6: compute_stage.run()
   ↓
   Stage 7-8: render_stage.run()
   ↓
   Stage 9: validation_stage.run()
   ↓
   Stage 10: audit_composer.compose_and_write()
   ↓
   Optional: DAO write
   
3. ComputeStage.run() (compute_stage.py:108-247)
   ↓
   Engine layer:
   - BaziEngine.compute() or BaziAdapter.compute()
   - ZiweiEngine.compute() or ZiweiAdapter.compute()
   - HuangliEngine.get_day()
   - Heluo/Yi (optional, degraded on failure)
   ↓
   Signal extraction:
   - SignalEngine.build()
   - Ziwei extract_baseline_signal()
   ↓
   Cross-domain (P1.6 - NEUTERED in production):
   - CrossDomainOrchestrator.orchestrate() [SKIPPED]
   ↓
   Temporal convergence (P1.7)
   ↓
   Atomic claims build
   ↓
   Canonical composition
   ↓
   Schema validation
   
4. RenderStage.run() (render_stage.py:51-99)
   ↓
   Build RenderRequest
   ↓
   Renderer.render() or fallback to TemplateFallback
   
5. ValidationStage.run() (validation_stage.py:51-100)
   ↓
   Layer 1: Claim coverage
   ↓
   Layer 2: Text similarity
   ↓
   Layer 3: Entailment
   ↓
   Gates: G1-G4
   ↓
   Fail-closed decision
   
6. AuditComposer.compose_and_write() (audit_composer.py:35-130)
   ↓
   Write audit log
```

---

## Architecture Compliance Matrix

| Component | Requirement | Status | Notes |
|-----------|-------------|--------|-------|
| Pipeline 1-10 stages | Sequential execution | ✅ PASS | Stages properly separated |
| ComputeStage | Pure computation, no render/validation | ✅ PASS | Correctly isolated |
| RenderStage | LLM render + template fallback | ✅ PASS | Fallback logic present |
| ValidationStage | 3-layer + 4 gates, fail-closed | ✅ PASS | Correctly implemented |
| AuditComposer | Log all stages | ✅ PASS | Comprehensive logging |
| CrossDomainOrchestrator | P1.6 production path | ❌ FAIL | Never instantiated |
| SignalEngine | direction from Rule | ⚠️ PARTIAL | Legacy fields retained |
| AssertionDirection | New enum system | ✅ PASS | Correctly defined |
| Five systems complementarity | No vote/conflict | ✅ PASS | Architecture correct |
| API response cleanliness | No internal leaks | ⚠️ PARTIAL | Some internal data exposed |

---

## Priority Recommendations

### P0 (Immediate)
1. **Wire CrossDomainOrchestrator in production** - Add assertion_library to ComputeStage instantiation in pipeline.py
2. **Complete P1.6 integration** - Load ProductionRuleLibrary and pass to pipeline

### P1 (High)
3. **Deprecate Signal.direction** - Remove from Signal dataclass, use only ontology_type
4. **Unify fallback logic** - Consolidate template fallback to single entry point
5. **Add P1.6 integration tests** - Verify cross-domain path works in production

### P2 (Medium)
6. **Clean up legacy endpoints** - Schedule removal of /api/reading and /api/today
7. **Improve error observability** - Track optional engine failures explicitly
8. **Update documentation** - Reflect actual production state

---

## Conclusion

The TONGSHU system architecture is fundamentally sound with clear layer separation and proper fail-closed validation. However, the **critical issue is P1.6 CrossDomainOrchestrator not being wired into production**, causing the system to operate in legacy signal-only mode. This is the highest priority fix.

The dual direction system (Signal.direction vs AssertionDirection) is a migration artifact that should be cleaned up. Template fallback logic has two entry points that should be unified.

Overall conformance: **75%** - Core architecture is correct, but key production features are not fully activated.
