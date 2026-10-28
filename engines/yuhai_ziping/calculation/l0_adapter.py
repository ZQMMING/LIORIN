"""L0 Adapter（Phase 6 §65）· 转发共享实现。

实现已上移 engines/common/l0_adapter.py（引擎族共享）。
此处保留模块名以兼容既有 import 路径。
"""

from __future__ import annotations

from engines.common.l0_adapter import (  # noqa: F401
    build_base_view,
    build_contexts,
    BRANCH_SEASON,
    STEM_ELEMENT,
    STEMS,
    BRANCHES,
)
