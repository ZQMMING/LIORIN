-- 邮箱验证码登录独立迁移；不自动执行，不修改冻结 users 表。
-- users.email 为现有字段；此处只存挑战状态，绝不存验证码明文。
CREATE TABLE IF NOT EXISTS email_login_challenges (
    email TEXT PRIMARY KEY,
    code_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    next_send_at TIMESTAMPTZ NOT NULL,
    attempts SMALLINT NOT NULL DEFAULT 0 CHECK (attempts BETWEEN 0 AND 5),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_email_login_challenges_expiry
    ON email_login_challenges (expires_at);
