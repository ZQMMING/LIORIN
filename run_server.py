"""TONGSHU API dev server.

Usage (from backend/):
    PYTHONPATH=src python run_server.py
    # -> http://127.0.0.1:8000/docs

Env:
    TONGSHU_HOST      (default 0.0.0.0)
    TONGSHU_PORT      (default 8000)
    TONGSHU_CORS_ORIGINS  comma-separated (default *)
    DEEPSEEK_API_KEY  set → real LLM renderer; unset → deterministic Stub
"""

from __future__ import annotations
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

def build_app():
    """构建开发服务。Auth DB 必须显式 opt-in；默认仍为 503。

    不执行 migration/seed，也不使用 config.py 的默认本地库口令。
    缺少显式 DSN 或连接失败时直接报错，避免向用户呈现假登录入口。
    """
    enabled = os.environ.get("TONGSHU_AUTH_DB_ENABLED") == "1"
    dsn = os.environ.get("OTC_G_DATABASE_URL")
    if not enabled:
        if os.environ.get("TONGSHU_EMAIL_AUTH_ENABLED") == "1":
            raise RuntimeError("Email auth requires an explicitly enabled auth database")
        from tongshu.api.app import create_app
        return create_app()

    if not dsn:
        raise RuntimeError("Auth DB 已启用，但未设置 OTC_G_DATABASE_URL")

    from tongshu.db.config import db_available
    ok, _ = db_available(dsn)
    if not ok:
        raise RuntimeError("Auth DB 不可连接；未启动服务，也未执行迁移")

    from tongshu.db.auth_db import PostgresAuthDB
    from tongshu.api.app import create_app
    # 个人档案表独立迁移，绝不在启动时自动建表。
    # 只有显式二级开关才装配存储层；未完成迁移时由独立验收发现并阻止上线。
    profile_store = None
    if os.environ.get("TONGSHU_PROFILE_STORE_ENABLED") == "1":
        from tongshu.db.profile_store import PostgresProfileStore
        profile_store = PostgresProfileStore(dsn=dsn)
        if not profile_store.ready():
            raise RuntimeError("个人档案表不存在；需单独验收并执行 profile_0001.sql，服务未启动")
    email_store = None
    if os.environ.get("TONGSHU_EMAIL_AUTH_ENABLED") == "1":
        from tongshu.db.email_auth_store import EmailAuthStore
        from tongshu.services.email_auth import configured
        if not configured():
            raise RuntimeError("Email auth configuration is incomplete")
        email_store = EmailAuthStore(dsn=dsn, secret=os.environ.get("TONGSHU_EMAIL_AUTH_SECRET", ""))
        if not email_store.ready():
            raise RuntimeError("Email auth schema is unavailable; no migration was run")
    auth_db = PostgresAuthDB(dsn=dsn)
    if email_store is not None:
        return create_app(db_ops=auth_db, profile_store=profile_store, email_auth_store=email_store)
    return create_app(db_ops=auth_db, profile_store=profile_store)


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("TONGSHU_HOST", "127.0.0.1")  # B3: 仅本地，禁止公网
    port = int(os.environ.get("TONGSHU_PORT", "8000"))
    uvicorn.run(build_app(), host=host, port=port, log_level="info")
