-- 独立个人档案迁移（不会由现有 migrate() 或 run_server.py 自动执行）。
-- 执行前必须核对目标库、Auth schema 与备份；不修改冻结 11_DATABASE_SCHEMA.sql。
-- 出生资料属于敏感数据：仅存个人计算所需的最小字段；访问由已认证 user_id 约束。
CREATE TABLE IF NOT EXISTS user_birth_profiles (
    user_id TEXT PRIMARY KEY,
    birth_date DATE NOT NULL,
    birth_hour SMALLINT NOT NULL CHECK (birth_hour BETWEEN 0 AND 23),
    birth_minute SMALLINT CHECK (birth_minute BETWEEN 0 AND 59),
    gender TEXT NOT NULL CHECK (gender IN ('male', 'female')),
    timezone TEXT NOT NULL,
    birth_location TEXT NOT NULL,
    current_location TEXT,
    calendar_system TEXT NOT NULL DEFAULT 'solar' CHECK (calendar_system = 'solar'),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
