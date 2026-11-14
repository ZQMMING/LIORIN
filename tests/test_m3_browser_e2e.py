"""Real browser against the approved isolated Postgres and local SMTP sink."""
from pathlib import Path
import socket
import threading
import time
import uuid

import pytest
import uvicorn
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from playwright.sync_api import expect, sync_playwright

from tests.test_m3_real_account import isolated_dsn, smtp_sink, delivered_code  # noqa: F401
from tongshu.api.app import create_app
from tongshu.api.deps import reset_rate_limit_buckets
from tongshu.db.auth_db import PostgresAuthDB
from tongshu.db.email_auth_store import EmailAuthStore
from tongshu.db.profile_store import PostgresProfileStore
from tongshu.services import identity_gateway


def test_browser_real_login_save_reload_edit_and_logout(isolated_dsn, smtp_sink, monkeypatch):
    dist = Path(__file__).resolve().parents[1] / 'frontend-case' / 'dist'
    assert (dist / 'index.html').is_file(), 'Run npm run build first'
    reset_rate_limit_buckets()
    identity_gateway._gateway_singleton = None
    monkeypatch.setenv('TONGSHU_AUTH_SECRET', 'test-session-only-' + 'y' * 40)
    monkeypatch.setenv('TONGSHU_SMTP_HOST', '127.0.0.1')
    monkeypatch.setenv('TONGSHU_SMTP_PORT', str(smtp_sink.server_address[1]))
    monkeypatch.setenv('TONGSHU_SMTP_FROM', 'service@example.test')
    monkeypatch.setenv('TONGSHU_EMAIL_AUTH_SECRET', 'test-only-' + 'x' * 40)
    monkeypatch.delenv('TONGSHU_SMTP_USER', raising=False)
    monkeypatch.delenv('TONGSHU_SMTP_PASSWORD', raising=False)
    server_socket = socket.socket()
    server_socket.bind(('127.0.0.1', 0))
    server_socket.listen(128)
    origin = 'http://127.0.0.1:' + str(server_socket.getsockname()[1])
    monkeypatch.setenv('TONGSHU_BROWSER_SESSION_ORIGIN', origin)
    app = create_app(db_ops=PostgresAuthDB(isolated_dsn), profile_store=PostgresProfileStore(isolated_dsn),
                     email_auth_store=EmailAuthStore(isolated_dsn, 'test-only-' + 'x' * 40))
    app.mount('/assets', StaticFiles(directory=dist / 'assets'), name='assets')

    @app.get('/{page:path}')
    def site(page: str):
        return FileResponse(dist / 'index.html')

    server = uvicorn.Server(uvicorn.Config(app, log_level='error', access_log=False))
    thread = threading.Thread(target=lambda: server.run(sockets=[server_socket]), daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.1)
    assert server.started
    try:
        with sync_playwright() as browser_driver:
            browser = browser_driver.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            try:
                page.goto(origin, wait_until='domcontentloaded')
                page.get_by_role('button', name='我的').click()
                email = f'person-{uuid.uuid4().hex}@example.test'
                page.get_by_label('邮箱', exact=True).fill(email)
                page.get_by_role('button', name='发送验证码').click()
                page.get_by_text('如果邮箱可接收邮件，验证码已发送。', exact=False).wait_for()
                code = delivered_code(smtp_sink)
                try:
                    page.get_by_label('邮箱验证码').fill(code)
                except Exception:
                    raise RuntimeError('browser could not enter the captured test code') from None
                page.get_by_role('button', name='验证并登录').click()
                page.get_by_label('出生日期').fill('1980-06-22')
                page.get_by_label('出生时间').fill('12:30')
                page.get_by_label('性别').select_option('male')
                page.get_by_label('出生地').fill('北京')
                page.get_by_role('button', name='北京 · CN').click()
                page.get_by_role('button', name='保存档案').click()
                page.get_by_text('档案已由后端确认保存。').wait_for()
                with page.expect_response(lambda response: '/v1/personal/heluo-today' in response.url) as personal:
                    page.get_by_role('button', name='查看个人今日').click()
                assert personal.value.status == 503
                page.reload(wait_until='domcontentloaded')
                page.get_by_role('button', name='我的').click()
                page.get_by_role('button', name='读取已存档案').click()
                expect(page.get_by_label('出生日期')).to_have_value('1980-06-22')
                page.get_by_label('出生日期').fill('1981-06-22')
                page.get_by_role('button', name='保存档案').click()
                page.get_by_text('档案已由后端确认保存。').wait_for()
                page.get_by_role('button', name='退出').click()
                page.reload(wait_until='domcontentloaded')
                page.get_by_label('邮箱', exact=True).wait_for()
            finally:
                browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=10)
