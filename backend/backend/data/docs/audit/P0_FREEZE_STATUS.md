# P0 Freeze Status

**Effective Date:** 2026-09-01
**Commit:** 302b233
**Branch:** main

## Locked (Main — P0 Frozen)

- Legacy assertion / reasoning / guidance / strength production chains: DELETED
- /admin API route: REMOVED
- strength_engine.py, judgment_engine.py, annual_event_evaluator.py: PURGED
- assertion/, legacy/assertion_v1/, guidance/ dirs: DELETED
- Canonical pipeline (pipeline.py) + assertion_v2/: INTACT, READ-ONLY
- Core engines (bazi_engine, blind_bazi_engine, ziwei_engine, etc.): READ-ONLY
- Tests (canonical + core): 201 passing, no changes allowed without approval

## Out of Scope (Deferred)

| Item | Location | Phase |
|------|----------|-------|
| SIGNAL INVENTORY | reasoning/, signal/, temporal/, feature_registry/ | P2 |
| Authority Ledger enforcement | governance/RUNTIME_AUTHORITY_LEDGER.yaml | P2 |
| canonical/state.py God Object split | canonical/state.py (~1900 lines) | P2 |
| 16 test parents[2] path bug | tests/*.py | Separate PR |
| Golden Path re-expression | assertion_v2/contract.py DTS/ZPZQ judgments | New PR |
| reasoning/event_topic.py / rule_resolver.py | reasoning/ | User ruling |

## New Feature Prohibition

No new features enter main during P0 Freeze.
All new work must go through separate PRs approved by user/ruler.
