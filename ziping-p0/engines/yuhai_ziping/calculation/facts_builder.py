"""YHZP Facts Builder（Phase 6 §65/§B-3）· 转发共享实现。

实现已上移 engines/common/facts_builder.py（引擎族共享，engine 参数化）。
此处保留 FactsBuilder 类名以兼容既有 import 路径；默认 engine="yhzp"。
"""

from __future__ import annotations

from engines.common.facts_builder import (  # noqa: F401
    FactsBuilder,
    ENGINE_ID_MAP,
    TEN_GOD_FIELDS,
    SIX_RELATIVE_FIELDS,
    PALACE_FIELDS,
    RELATION_FIELDS,
    GEJU_CANDIDATE_FIELDS,
)
