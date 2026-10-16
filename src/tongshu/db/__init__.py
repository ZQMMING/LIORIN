"""OTC-G DB 运行时 Phase C 平台层 (task #57)落地.

V1 运行时保持内嵌时序DB(锚定懒加载声明 Phase 0 不参与运筹;本包仅提供可选接入
PostgreSQL 的平台层:连接配置、冻结 DDL 幂等迁移、工程数据投喂( seed)、写路径 DAO、
运行时 DAO。

用法见 backend/scripts/db_setup.py。
"""

from __future__ import annotations

from .config import db_available, get_dsn  # noqa: F401
from .migrate import migrate  # noqa: F401
from .seed import seed  # noqa: F401
from .init_auth import init_auth_schema  # noqa: F401

__all__ = ["db_available", "get_dsn", "migrate", "seed", "init_auth_schema"]
