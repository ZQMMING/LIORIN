"""邮箱验证登录 API：fake store/mail，不访问外部邮箱或真实 DB。"""
from __future__ import annotations

import os
import unittest
from unittest.mock import patch
import psycopg2

from fastapi.testclient import TestClient

from tongshu.api.app import create_app
from tongshu.api.deps import reset_rate_limit_buckets
from tongshu.services import identity_gateway as gateway_module
from tests.auth.test_b09_route_enforcement import _wire_gateway


class Store:
    def can_send(self, email): return True
    def issue(self, email, code): self.email, self.code = email, code
    def revoke(self, email, code): pass
    def consume(self, email, code): return "u-1" if email == "user@example.com" and code == "123456" else None


class EmailAuthAPITests(unittest.TestCase):
    def setUp(self):
        reset_rate_limit_buckets()
        os.environ.setdefault("TONGSHU_AUTH_SECRET", "test-secret-for-unit-tests")
        _wire_gateway()
        self.store = Store()
        self.client = TestClient(create_app(email_auth_store=self.store))

    def test_bad_code_is_401_and_does_not_issue_tokens(self):
        r = self.client.post("/v1/auth/email/verify", json={"email": "user@example.com", "code": "000000"})
        self.assertEqual(r.status_code, 401)
        self.assertNotIn("access_token", r.text)

    def test_good_code_returns_existing_user_tokens(self):
        r = self.client.post("/v1/auth/email/verify", json={"email": "user@example.com", "code": "123456"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["user_id"], "u-1")
        self.assertTrue(r.json()["access_token"])
        self.assertTrue(r.json()["refresh_token"])
        self.assertEqual(r.json()["expires_in"], gateway_module.ACCESS_TOKEN_TTL)

    def test_missing_email_store_fails_closed(self):
        client = TestClient(create_app())
        r = client.post("/v1/auth/email/request-code", json={"email": "user@example.com"})
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.json()["detail"]["code"], "EMAIL_AUTH_UNAVAILABLE")

    def test_code_request_never_returns_code(self):
        with patch("tongshu.api.email_auth.send_login_code", return_value=None) as send:
            r = self.client.post("/v1/auth/email/request-code", json={"email": "USER@example.com"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"status": "sent_if_available"})
        send.assert_called_once_with(self.store, "user@example.com")

    def test_spoofed_forwarded_addresses_do_not_bypass_send_limit(self):
        with patch("tongshu.api.email_auth.send_login_code", return_value=None):
            for index in range(5):
                r = self.client.post('/v1/auth/email/request-code',
                    headers={'X-Forwarded-For': f'192.0.2.{index}'},
                    json={'email': f'user-{index}@example.test'})
                self.assertEqual(r.status_code, 200)
            r = self.client.post('/v1/auth/email/request-code',
                headers={'X-Forwarded-For': '192.0.2.99'}, json={'email': 'extra@example.test'})
        self.assertEqual(r.status_code, 429)

    def test_database_failure_is_unavailable_without_leaking_details(self):
        with patch.object(self.store, 'consume', side_effect=psycopg2.OperationalError('private-dsn-marker')):
            r = self.client.post('/v1/auth/email/verify', json={'email': 'user@example.test', 'code': '123456'})
        self.assertEqual(r.status_code, 503)
        self.assertNotIn('private-dsn-marker', r.text)
