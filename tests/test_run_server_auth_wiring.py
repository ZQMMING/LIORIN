"""run_server 的 Auth 装配守卫（无数据库写入）。"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
import run_server


class RunServerAuthWiringTests(unittest.TestCase):
    def test_default_keeps_auth_unavailable(self):
        app = object()
        factory = Mock(return_value=app)
        fake = ModuleType("tongshu.api.app")
        fake.create_app = factory
        with patch.dict(os.environ, {"TONGSHU_AUTH_DB_ENABLED": "0"}), \
             patch.dict(sys.modules, {"tongshu.api.app": fake}):
            self.assertIs(run_server.build_app(), app)
        factory.assert_called_once_with()

    def test_opt_in_requires_explicit_dsn(self):
        with patch.dict(os.environ, {"TONGSHU_AUTH_DB_ENABLED": "1"}):
            old = os.environ.pop("OTC_G_DATABASE_URL", None)
            try:
                with self.assertRaisesRegex(RuntimeError, "OTC_G_DATABASE_URL"):
                    run_server.build_app()
            finally:
                if old is not None:
                    os.environ["OTC_G_DATABASE_URL"] = old

    def test_unreachable_db_fails_closed(self):
        factory = Mock()
        fake_app = ModuleType("tongshu.api.app")
        fake_app.create_app = factory
        fake_db = ModuleType("tongshu.db")
        fake_db.__path__ = []
        fake_config = ModuleType("tongshu.db.config")
        fake_config.db_available = Mock(return_value=(False, "connection refused"))
        with patch.dict(os.environ, {
            "TONGSHU_AUTH_DB_ENABLED": "1",
            "OTC_G_DATABASE_URL": "postgresql://placeholder@127.0.0.1:5432/otcg",
        }), patch.dict(sys.modules, {
            "tongshu.api.app": fake_app,
            "tongshu.db": fake_db,
            "tongshu.db.config": fake_config,
        }):
            with self.assertRaisesRegex(RuntimeError, "不可连接"):
                run_server.build_app()
        factory.assert_not_called()

    def test_profile_store_requires_migrated_table(self):
        dsn = "postgresql://placeholder@127.0.0.1:5432/otcg"
        fake_db = ModuleType("tongshu.db")
        fake_db.__path__ = []
        fake_config = ModuleType("tongshu.db.config")
        fake_config.db_available = Mock(return_value=(True, ""))
        fake_auth_db = ModuleType("tongshu.db.auth_db")
        fake_auth_db.PostgresAuthDB = Mock()
        fake_store = ModuleType("tongshu.db.profile_store")
        store = Mock()
        store.ready.return_value = False
        fake_store.PostgresProfileStore = Mock(return_value=store)
        with patch.dict(os.environ, {
            "TONGSHU_AUTH_DB_ENABLED": "1", "TONGSHU_PROFILE_STORE_ENABLED": "1",
            "OTC_G_DATABASE_URL": dsn,
        }), patch.dict(sys.modules, {
            "tongshu.db": fake_db, "tongshu.db.config": fake_config,
            "tongshu.db.profile_store": fake_store,
            "tongshu.db.auth_db": fake_auth_db,
        }):
            with self.assertRaisesRegex(RuntimeError, "档案表不存在"):
                run_server.build_app()

    def test_opt_in_wires_existing_adapter_without_migration(self):
        dsn = "postgresql://placeholder@127.0.0.1:5432/otcg"
        app = object()
        factory = Mock(return_value=app)
        adapter = object()
        constructor = Mock(return_value=adapter)
        fake_app = ModuleType("tongshu.api.app")
        fake_app.create_app = factory
        fake_db = ModuleType("tongshu.db")
        fake_db.__path__ = []
        fake_config = ModuleType("tongshu.db.config")
        fake_config.db_available = Mock(return_value=(True, ""))
        fake_auth_db = ModuleType("tongshu.db.auth_db")
        fake_auth_db.PostgresAuthDB = constructor
        with patch.dict(os.environ, {
            "TONGSHU_AUTH_DB_ENABLED": "1", "OTC_G_DATABASE_URL": dsn,
        }), patch.dict(sys.modules, {
            "tongshu.api.app": fake_app,
            "tongshu.db": fake_db,
            "tongshu.db.config": fake_config,
            "tongshu.db.auth_db": fake_auth_db,
        }):
            self.assertIs(run_server.build_app(), app)
        constructor.assert_called_once_with(dsn=dsn)
        factory.assert_called_once_with(db_ops=adapter, profile_store=None)


if __name__ == "__main__":
    unittest.main()
