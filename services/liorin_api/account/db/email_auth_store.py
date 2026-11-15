"""邮箱验证码挑战与用户归属，单事务验证；不存明文验证码。"""
from __future__ import annotations

import hashlib
import hmac
import uuid
from contextlib import closing
from datetime import datetime, timedelta, timezone

import psycopg2


class EmailAuthStore:
    def __init__(self, dsn: str, secret: str):
        if not dsn or len(secret.encode("utf-8")) < 32:
            raise ValueError("explicit DSN and a 32-byte email-auth secret required")
        self.dsn = dsn
        self.secret = secret.encode("utf-8")

    def _digest(self, email: str, code: str) -> str:
        return hmac.new(self.secret, f"{email}:{code}".encode("utf-8"), hashlib.sha256).hexdigest()

    def ready(self) -> bool:
        with closing(psycopg2.connect(self.dsn)) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass('public.email_login_challenges')")
                row = cur.fetchone()
                return bool(row and row[0])

    def can_send(self, email: str) -> bool:
        """数据库级发送间隔；失败时不调用邮件网关。"""
        with closing(psycopg2.connect(self.dsn)) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT next_send_at FROM email_login_challenges WHERE email=%s", (email,))
                row = cur.fetchone()
                return not row or row[0] <= datetime.now(timezone.utc)

    def issue(self, email: str, code: str) -> None:
        now = datetime.now(timezone.utc)
        with closing(psycopg2.connect(self.dsn)) as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO email_login_challenges "
                        "(email, code_hash, expires_at, next_send_at, attempts) "
                        "VALUES (%s, %s, %s, %s, 0) "
                        "ON CONFLICT (email) DO UPDATE SET "
                        "code_hash=EXCLUDED.code_hash, expires_at=EXCLUDED.expires_at, "
                        "next_send_at=EXCLUDED.next_send_at, attempts=0 "
                        "WHERE email_login_challenges.next_send_at <= %s",
                        (email, self._digest(email, code), now + timedelta(minutes=10),
                         now + timedelta(seconds=60), now),
                    )
                    if cur.rowcount != 1:
                        raise ValueError("send cooldown")

    def revoke(self, email: str, code: str) -> None:
        """仅删除当前待发送挑战；不误删并发创建的新挑战。"""
        with closing(psycopg2.connect(self.dsn)) as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM email_login_challenges WHERE email=%s AND code_hash=%s",
                                (email, self._digest(email, code)))

    def consume(self, email: str, code: str) -> str | None:
        now = datetime.now(timezone.utc)
        with closing(psycopg2.connect(self.dsn)) as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT code_hash, expires_at, attempts FROM email_login_challenges "
                        "WHERE email=%s FOR UPDATE", (email,),
                    )
                    row = cur.fetchone()
                    if not row or row[1] <= now or row[2] >= 5:
                        return None
                    if not hmac.compare_digest(row[0], self._digest(email, code)):
                        cur.execute("UPDATE email_login_challenges SET attempts=attempts+1 WHERE email=%s", (email,))
                        return None
                    cur.execute("SELECT id FROM users WHERE lower(email)=lower(%s)", (email,))
                    existing = cur.fetchone()
                    if existing:
                        user_id = str(existing[0])
                    else:
                        user_id = str(uuid.uuid4())
                        cur.execute(
                            "INSERT INTO users (id,email,is_new_user,has_birth_info,has_heluo_model,token_version) "
                            "VALUES (%s,%s,true,false,false,1)", (user_id, email),
                        )
                    cur.execute("DELETE FROM email_login_challenges WHERE email=%s", (email,))
                    return user_id
