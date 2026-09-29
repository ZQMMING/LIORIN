# 黄历 (Huangli) Engine — standalone slice

Extracted from the shuntian monorepo as a self-contained, testable
engine branch. See feature/huangli-engine on ZQMMING/LIORIN.

## Contents
- src/tongshu/engines/huangli_engine.py  (core)
- src/tongshu/engines/yi/               (hexagram_symbol dep: core/models/hexagram_symbol)
- src/tongshu/facts/                    (shared fact tables, no bazi-specific logic)
- tests/test_huangli_engine*.py         (52 tests)
- backend/data/calendar_sources.json    (calendar source registry, degrades to empty if absent)

## Run
    .venv/Scripts/python.exe -m pytest tests/test_huangli_engine*.py -q

## Dependencies (declared in pyproject.toml)
lunar_python / pytest

## Note
The huangli engine is intentionally NOT a dependency of any other engine;
it is a leaf. It imports only from engines.yi.hexagram_symbol and
lunar_python, plus an optional calendar_sources.json registry.
