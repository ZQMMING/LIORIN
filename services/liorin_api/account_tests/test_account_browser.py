"""Real browser against the approved isolated Postgres and local SMTP sink."""
import os
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

from services.liorin_api.account_tests.test_account_real import isolated_dsn, smtp_sink, delivered_code  # noqa: F401
from services.liorin_api.app import create_app
from services.liorin_api.account.api.deps import reset_rate_limit_buckets
from services.liorin_api.account.services import identity_gateway


@pytest.mark.usefixtures('isolated_dsn')
def test_browser_real_login_save_reload_edit_and_logout(smtp_sink, monkeypatch, tmp_path):  # noqa: F811
    dist = Path(__file__).resolve().parents[3] / 'frontend-case' / 'dist'
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
    origin = 'https://127.0.0.1:' + str(server_socket.getsockname()[1])
    monkeypatch.setenv('TONGSHU_BROWSER_SESSION_ORIGIN', origin)
    monkeypatch.setenv('LIORIN_ACCOUNT_MODE', 'isolated-test')
    app = create_app()
    if os.environ.get('VITE_LIORIN_PRODUCT_B_PREVIEW') == '1':
        assert '/v1/personal/heluo-preview' in app.openapi()['paths']
    app.mount('/assets', StaticFiles(directory=dist / 'assets'), name='assets')

    @app.get('/{page:path}')
    def site(page: str):
        return FileResponse(dist / 'index.html')

    server = uvicorn.Server(uvicorn.Config(app, log_level='error', access_log=False, ssl_certfile=str(tmp_path / 'cert.pem'), ssl_keyfile=str(tmp_path / 'key.pem')))
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
            page = browser.new_page(viewport={'width': 390, 'height': 844}, locale='en-US', ignore_https_errors=True)
            try:
                page.goto(origin, wait_until='domcontentloaded')
                product_b = os.environ.get('VITE_LIORIN_PRODUCT_B_PREVIEW') == '1'
                account_tab = 'Me' if product_b else '我的'
                for protected in ('/v1/profile/stored', '/v1/auth/me', '/v1/personal/dna'):
                    unclaimed = page.request.get(origin + protected, params={'uid': 'synthetic-tag'},
                                                 headers={'X-Device-Token': 'synthetic-tag'})
                    assert unclaimed.status == 401
                if os.environ.get('VITE_LIORIN_PRODUCT_B_PREVIEW') == '1':
                    response = page.request.get(origin + '/v1/personal/heluo-preview?target_date=2026-08-17&display_timezone=America%2FNew_York')
                    assert response.status == 401
                    assert response.headers['cache-control'] == 'no-store'
                page.get_by_role('button', name=account_tab).click()
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
                if os.environ.get('VITE_LIORIN_PRODUCT_B_PREVIEW') == '1':
                    page.get_by_role('button', name='查看个人今日').click()
                    page.get_by_label('Target date').fill('2026-08-17')
                    page.get_by_label('Display timezone').fill('America/New_York')
                    with page.expect_response(lambda response: '/v1/personal/heluo-preview?' in response.url) as personal:
                        page.get_by_role('button', name='Calculate preview').click()
                    assert personal.value.status == 200
                    result = personal.value.json()
                    assert result['admission_status'] == 'pending_review'
                    assert result['active_yao_index'] is result['valid_from'] is result['valid_until'] is None
                    assert result['display_timezone'] == 'America/New_York'
                    assert result['birth_timezone'] == 'Asia/Shanghai'
                    assert result['marker_timezone'] == 'Asia/Shanghai'
                    assert result['marker_utc'] == '2026-08-17T20:41:00Z'
                    assert result['provenance']['solar_term_time_basis'] == 'sxtwl_jd2dd_fixed_utc_plus_08'
                    calendar = page.get_by_role('region', name='Daily calendar')
                    expect(calendar.get_by_text('Lunar date', exact=False)).to_be_visible()
                    expect(calendar.get_by_text('Day branch', exact=True)).to_be_visible()
                    expect(calendar.get_by_text('source review pending', exact=False)).to_have_count(3)
                    calendar.get_by_text('Calendar source', exact=True).click()
                    expect(calendar.get_by_text('lunar_python 1.4.8', exact=False)).to_be_visible()
                    expect(page.get_by_role('heading', name=result['hexagram'])).to_be_visible()
                    page.get_by_text('Calculation source', exact=True).click()
                    expect(page.get_by_text('HeluoAdapter.compute_from_chart', exact=False)).to_be_visible()
                    expect(page.get_by_text('Engine marker in UTC', exact=False)).to_contain_text(result['marker_utc'])
                    screenshot_dir = os.environ.get('LIORIN_PREVIEW_SCREENSHOTS')
                    if screenshot_dir:
                        folder = Path(screenshot_dir)
                        folder.mkdir(parents=True, exist_ok=True)
                        for width in (375, 1440):
                            page.set_viewport_size({'width': width, 'height': 900})
                            page.screenshot(path=folder / f'personal-today-{width}.png')
                        page.set_viewport_size({'width': 390, 'height': 844})
                    page.get_by_role('button', name='Pause motion').click()
                    expect(page.get_by_role('button', name='Resume motion')).to_be_visible()
                    page.emulate_media(reduced_motion='reduce')
                    expect(page.get_by_role('button', name='Resume motion')).to_be_hidden()
                    page.get_by_label('Target date').fill('2026-09-06')
                    with page.expect_response(lambda response: '/v1/personal/heluo-preview?' in response.url) as missing:
                        page.get_by_role('button', name='Calculate preview').click()
                    assert missing.value.status == 503
                    expect(page.get_by_role('alert')).to_contain_text('engine preview is unavailable')
                    expect(calendar.get_by_text('Lunar date', exact=False)).to_be_visible()
                    with page.expect_response(lambda response: '/v1/personal/heluo-preview?' in response.url) as handoff:
                        page.get_by_role('button', name='Next day').click()
                    assert handoff.value.status == 200
                    assert handoff.value.json()['requested_local_date'] == '2026-09-07'
                    assert handoff.value.json()['provenance']['engine_day_ordinal'] == 1
                    expect(page.get_by_role('alert')).to_have_count(0)
                    page.get_by_label('Target date').fill('2024-03-01')
                    with page.expect_response(lambda response: '/v1/personal/heluo-preview?' in response.url) as leap:
                        page.get_by_role('button', name='Previous day').click()
                    assert leap.value.status == 200
                    assert leap.value.json()['requested_local_date'] == '2024-02-29'
                    expect(page.get_by_label('Target date')).to_have_value('2024-02-29')
                else:
                    with page.expect_response(lambda response: '/v1/personal/heluo-today' in response.url) as personal:
                        page.get_by_role('button', name='查看个人今日').click()
                    assert personal.value.status == 503
                if product_b:
                    with page.expect_response(lambda response: response.url.endswith('/v1/personal/dna')) as dna:
                        page.get_by_role('button', name='You', exact=True).click()
                    assert dna.value.status == 200
                    expect(page).to_have_url(origin + '/you')
                    expect(page.get_by_role('heading', name='Personal DNA')).to_be_visible()
                    expect(page.get_by_text(dna.value.json()['birth_year_nayin'], exact=True)).to_be_visible()
                    expect(page.get_by_role('table', name='Five-element structure')).to_be_visible()
                    screen_dir = os.environ.get('LIORIN_PREVIEW_SCREENSHOTS')
                    if screen_dir:
                        for width in (320, 1440):
                            page.set_viewport_size({'width': width, 'height': 900})
                            assert page.get_by_role('table').evaluate('(table) => table.scrollWidth <= table.clientWidth')
                            page.screenshot(path=Path(screen_dir) / f'personal-dna-{width}.png')
                        page.set_viewport_size({'width': 390, 'height': 844})
                    page.get_by_label('Language').select_option('zh-Hant')
                    expect(page.get_by_role('heading', name='個人圖譜')).to_be_visible()
                page.reload(wait_until='domcontentloaded')
                if product_b:
                    expect(page.get_by_role('heading', name='Four pillars')).to_be_visible()
                    page.get_by_role('button', name='Insight', exact=True).click()
                    page.get_by_label('Year', exact=True).fill('2026')
                    with page.expect_response(lambda response: '/v1/personal/insight?year=2026' in response.url) as cycle:
                        page.get_by_role('button', name='View cycles').click()
                    assert cycle.value.status == 200
                    expect(page.get_by_role('heading', name='Annual cycle · 2026')).to_be_visible()
                    expect(page.get_by_role('listitem')).to_have_count(12)
                page.get_by_role('button', name=account_tab).click()
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
