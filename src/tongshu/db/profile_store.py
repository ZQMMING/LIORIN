"""个人出生档案存储；仅在独立迁移 profile_0001.sql 已执行后启用。"""
from __future__ import annotations

from contextlib import closing
from typing import Any

import psycopg2
import psycopg2.extras


class PostgresProfileStore:
    def __init__(self, dsn: str):
        if not dsn:
            raise ValueError("profile store requires explicit DSN")
        self.dsn = dsn

    def ready(self) -> bool:
        """只读检查独立迁移是否已落地；服务启动不自动建表。"""
        with closing(psycopg2.connect(self.dsn)) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass('public.user_birth_profiles')")
                row = cur.fetchone()
                return bool(row and row[0])

    def save(self, user_id: str, profile: dict[str, Any]) -> None:
        if not user_id or user_id == "anonymous":
            raise ValueError("authenticated user_id required")
        with closing(psycopg2.connect(self.dsn)) as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO user_birth_profiles "
                        "(user_id, birth_date, birth_hour, birth_minute, gender, timezone, "
                        " birth_location, current_location, calendar_system) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
                        "ON CONFLICT (user_id) DO UPDATE SET "
                        "birth_date=EXCLUDED.birth_date, birth_hour=EXCLUDED.birth_hour, "
                        "birth_minute=EXCLUDED.birth_minute, gender=EXCLUDED.gender, "
                        "timezone=EXCLUDED.timezone, birth_location=EXCLUDED.birth_location, "
                        "current_location=EXCLUDED.current_location, "
                        "calendar_system=EXCLUDED.calendar_system, updated_at=now()",
                        (user_id, profile["birth_date"], profile["birth_time"]["hour"],
                         profile["birth_time"].get("minute"), profile["gender"],
                         profile["timezone"], profile["location"],
                         profile.get("current_location"), profile["calendar_system"]),
                    )
                    cur.execute("UPDATE users SET has_birth_info = true, updated_at = now() WHERE id = %s", (user_id,))
                    if cur.rowcount != 1:
                        raise ValueError("profile user does not exist")

    def get(self, user_id: str) -> dict[str, Any] | None:
        if not user_id or user_id == "anonymous":
            raise ValueError("authenticated user_id required")
        with closing(psycopg2.connect(self.dsn)) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT birth_date, birth_hour, birth_minute, gender, timezone, "
                    "birth_location, current_location, calendar_system "
                    "FROM user_birth_profiles WHERE user_id = %s",
                    (user_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return {
            "birth_date": row["birth_date"].isoformat(),
            "birth_time": {"hour": row["birth_hour"], "minute": row["birth_minute"]},
            "gender": row["gender"], "timezone": row["timezone"],
            "location": row["birth_location"],
            "current_location": row["current_location"],
            "calendar_system": row["calendar_system"],
        }
