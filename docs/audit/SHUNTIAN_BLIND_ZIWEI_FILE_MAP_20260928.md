# Shuntian blind/ziwei migration map

## Decision
No E-side ordinary source file is approved for direct overwrite at this stage.

## Excluded artifacts
- `E:\迁移合并\ziwei_engine\node_modules\**`
- `E:\迁移合并\ziwei_engine\src\tongshu.egg-info\**`
- all `__pycache__` and `*.pyc`
- test caches and generated reports
- external original texts
- Golden/accuracy datasets

## Structural conflicts
| E path | D path | Decision | Reason |
|---|---|---|---|
| `ziwei_engine/src/tongshu/engines/blind/` | `src/tongshu/engines/blind/` | exclude from direct overwrite | E is newer BlindEngine layered API; D path is existing evidence/rules package; APIs are not drop-in compatible |
| `ziwei_engine/src/tongshu/engines/ziwei/engine.py` | `src/tongshu/engines/ziwei/engine.py` | exclude from direct overwrite | E is a facade/interpretation pipeline; D production imports top-level `ziwei_engine.py` |
| `engines/ziwei_engine.py` | `src/tongshu/engines/ziwei_engine.py` | exclude from overwrite | E file is older/different and lacks D's current chart contract fixes |
| `engines/ziwei_adapter.py` | `src/tongshu/engines/ziwei_adapter.py` | exclude from overwrite | E version uses raw hour for bySolar and lacks current time-index/field fixes |
| `engines/blind_bazi_engine.py` | `src/tongshu/engines/blind_bazi_engine.py` | exclude from overwrite | E version is older/different and removes current D-side boundary logic |
| `engines/blind_yingqi.py` | `src/tongshu/engines/blind_yingqi.py` | exclude from overwrite | E version has different API and older behavior |

## Same-content mirrors
- E/D top-level `blind/` and `blind_engine/blind/` ordinary files are SHA-256 identical in the baseline comparison.
- E/D `blind_seg/` and `blind_evidence/blind_seg/` are duplicate evidence mirror trees; no production overwrite is justified.

## Approved action for this turn
- Preserve D's already-tested production code.
- Do not copy E source trees.
- Record the comparison and run D-side regression tests.
- Any future E feature adoption requires a separate file-level plan and compatibility tests.
