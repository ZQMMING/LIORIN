"""档案 SQL/迁移静态合同：模拟连接，绝不访问真实数据库。"""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from tongshu.db.profile_migrate import migrate_profile
from tongshu.db.profile_store import PostgresProfileStore


@pytest.fixture
def db_cursor():
    cursor = MagicMock()
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.cursor.return_value = cursor
    cursor.__enter__.return_value = cursor
    with patch("psycopg2.connect", return_value=conn) as connect:
        yield cursor, conn, connect


def test_migration_requires_explicit_dsn(db_cursor):
    cursor, _, connect = db_cursor
    with pytest.raises(ValueError, match="explicit DSN"):
        migrate_profile("")
    connect.assert_not_called()
    cursor.execute.assert_not_called()


def test_migration_uses_separate_schema_and_transaction(db_cursor):
    cursor, conn, connect = db_cursor
    migrate_profile("postgresql://placeholder@localhost/otcg")
    sql = cursor.execute.call_args.args[0]
    assert "CREATE TABLE IF NOT EXISTS user_birth_profiles" in sql
    assert "birth_date DATE NOT NULL" in sql
    assert "user_id TEXT PRIMARY KEY" in sql
    connect.assert_called_once()
    conn.close.assert_called_once()


def test_store_rejects_anonymous_identity(db_cursor):
    cursor, _, connect = db_cursor
    store = PostgresProfileStore("postgresql://placeholder@localhost/otcg")
    with pytest.raises(ValueError, match="authenticated user_id"):
        store.save("anonymous", {})
    with pytest.raises(ValueError, match="authenticated user_id"):
        store.get("")
    connect.assert_not_called()
    cursor.execute.assert_not_called()


def test_save_is_parameterized_and_user_scoped(db_cursor):
    cursor, _, connect = db_cursor
    store = PostgresProfileStore("postgresql://placeholder@localhost/otcg")
    store.save("user-1", {"birth_date": "1984-12-07", "birth_time": {"hour": 16, "minute": 30},
                          "gender": "male", "timezone": "Asia/Shanghai", "location": "Beijing",
                          "current_location": "Beijing", "calendar_system": "solar"})
    sql, values = cursor.execute.call_args.args
    assert "ON CONFLICT (user_id) DO UPDATE" in sql
    assert "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)" in sql
    assert values[0] == "user-1"
    assert "1984-12-07" not in sql
    connect.assert_called_once()


def test_read_filters_by_user_id(db_cursor):
    cursor, _, _ = db_cursor
    cursor.fetchone.return_value = None
    store = PostgresProfileStore("postgresql://placeholder@localhost/otcg")
    assert store.get("user-2") is None
    sql, values = cursor.execute.call_args.args
    assert "WHERE user_id = %s" in sql
    assert values == ("user-2",)
