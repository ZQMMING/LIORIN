"""邮箱挑战存储 SQL 边界（假连接，零外部邮件/DB 写入）。"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from tongshu.db.email_auth_store import EmailAuthStore


@pytest.fixture
def fake_db():
    cursor = MagicMock()
    cursor.rowcount = 1
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.cursor.return_value = cursor
    cursor.__enter__.return_value = cursor
    with patch('psycopg2.connect', return_value=conn):
        yield cursor


def store():
    return EmailAuthStore('postgresql://placeholder@localhost/otcg', 'x' * 32)


def test_code_hash_is_domain_bound_and_never_plaintext(fake_db):
    s = store()
    assert s._digest('a@example.com', '123456') != s._digest('b@example.com', '123456')
    s.issue('a@example.com', '123456')
    sql, args = fake_db.execute.call_args.args
    assert 'ON CONFLICT (email)' in sql
    assert '123456' not in sql
    assert '123456' not in repr(args)
    assert len(args[1]) == 64


def test_wrong_code_increments_attempts_without_creating_user(fake_db):
    s = store()
    fake_db.fetchone.return_value = (s._digest('a@example.com', '123456'),
                                     datetime.now(timezone.utc) + timedelta(minutes=5), 0)
    assert s.consume('a@example.com', '000000') is None
    sql_calls = [call.args[0] for call in fake_db.execute.call_args_list]
    assert any('attempts=attempts+1' in sql for sql in sql_calls)
    assert not any('INSERT INTO users' in sql for sql in sql_calls)


def test_five_failed_attempts_lock_challenge(fake_db):
    s = store()
    fake_db.fetchone.return_value = (s._digest('a@example.com', '123456'),
                                     datetime.now(timezone.utc) + timedelta(minutes=5), 5)
    assert s.consume('a@example.com', '123456') is None
    assert len(fake_db.execute.call_args_list) == 1


def test_existing_email_returns_same_user_and_deletes_challenge(fake_db):
    s = store()
    fake_db.fetchone.side_effect = [
        (s._digest('a@example.com', '123456'), datetime.now(timezone.utc) + timedelta(minutes=5), 0),
        ('existing-user',),
    ]
    assert s.consume('a@example.com', '123456') == 'existing-user'
    sql_calls = [call.args[0] for call in fake_db.execute.call_args_list]
    assert not any('INSERT INTO users' in sql for sql in sql_calls)
    assert any('DELETE FROM email_login_challenges' in sql for sql in sql_calls)
