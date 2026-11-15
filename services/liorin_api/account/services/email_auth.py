"""邮箱验证码发行与 SMTP 发送；无配置 fail-closed，绝不记录明文验证码。"""
from __future__ import annotations

import os
import secrets
import smtplib
from email.message import EmailMessage


def normalize_email(value: str) -> str:
    email = value.strip().lower()
    if len(email) > 254 or "@" not in email or any(ch.isspace() for ch in email):
        raise ValueError("invalid email")
    local, domain = email.rsplit("@", 1)
    if not local or not domain or "." not in domain:
        raise ValueError("invalid email")
    # This port is restricted to the isolated test environment.
    if not domain.endswith('.test'):
        raise ValueError("test addresses only")
    return email


def configured() -> bool:
    return bool(os.environ.get("TONGSHU_SMTP_HOST") and
                os.environ.get("TONGSHU_SMTP_FROM") and
                os.environ.get("TONGSHU_EMAIL_AUTH_SECRET"))


def send_login_code(store, email: str) -> None:
    if not configured():
        raise RuntimeError("email service unavailable")
    if not store.can_send(email):
        raise ValueError("send cooldown")
    code = f"{secrets.randbelow(1_000_000):06d}"
    store.issue(email, code)
    message = EmailMessage()
    message["From"] = os.environ["TONGSHU_SMTP_FROM"]
    message["To"] = email
    message["Subject"] = "LIORIN 登录验证码"
    message.set_content(f"验证码：{code}。10 分钟内有效，请勿转发。")
    host = os.environ["TONGSHU_SMTP_HOST"]
    port = int(os.environ.get("TONGSHU_SMTP_PORT", "587"))
    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.starttls()
            user = os.environ.get("TONGSHU_SMTP_USER")
            password = os.environ.get("TONGSHU_SMTP_PASSWORD")
            if user and password:
                smtp.login(user, password)
            smtp.send_message(message)
    except Exception:
        # 发送失败撤销当前挑战；异常可能含 SMTP 凭据/地址，绝不返回原文。
        try:
            store.revoke(email, code)
        except Exception:
            pass  # 服务仍 fail-closed；后续可在过期后重试
        raise RuntimeError("email service unavailable") from None
