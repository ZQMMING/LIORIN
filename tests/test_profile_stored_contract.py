"""个人档案持久化 API 合同（FakeDB/FakeStore，无真实数据库写入）。"""
from __future__ import annotations

import os
import unittest
from unittest.mock import Mock

from fastapi.testclient import TestClient

from tongshu.api.app import create_app
from tongshu.services import identity_gateway as gateway_module
from tests.auth.test_b09_route_enforcement import _wire_gateway


class FakeProfileStore:
    def __init__(self):
        self.rows = {}

    def save(self, user_id, profile):
        self.rows[user_id] = dict(profile)

    def get(self, user_id):
        return self.rows.get(user_id)


class ProfileStoredContractTests(unittest.TestCase):
    def setUp(self):
        os.environ.setdefault("TONGSHU_AUTH_SECRET", "test-secret-for-unit-tests")
        _wire_gateway()
        self.store = FakeProfileStore()
        self.client = TestClient(create_app(profile_store=self.store))

    def _token(self):
        return gateway_module._gateway_singleton.generate_access_token("u-1", "dev-1")

    def test_guest_cannot_read_or_write(self):
        self.assertEqual(self.client.get("/v1/profile/stored").status_code, 401)
        payload = {"birth_date": "1984-12-07", "birth_time": {"hour": 16},
                   "gender": "male", "timezone": "Asia/Shanghai", "location": "Beijing"}
        self.assertEqual(self.client.put("/v1/profile/stored", json=payload).status_code, 401)
        self.assertEqual(self.store.rows, {})

    def test_auth_user_requires_store_to_write(self):
        no_store_client = TestClient(create_app())
        token = self._token()
        r = no_store_client.get("/v1/profile/stored", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(r.status_code, 503)
        self.assertEqual(r.json()["detail"]["code"], "PROFILE_STORE_UNAVAILABLE")

    def test_missing_profile_is_not_fabricated(self):
        token = self._token()
        r = self.client.get("/v1/profile/stored", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json()["detail"]["code"], "PROFILE_NOT_FOUND")

    def test_authenticated_save_then_read_from_store(self):
        token = self._token()
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"birth_date": "1984-12-07", "birth_time": {"hour": 16, "minute": 30},
                   "gender": "male", "timezone": "Asia/Shanghai", "location": "Beijing",
                   "current_location": "Beijing", "calendar_system": "solar"}
        saved = self.client.put("/v1/profile/stored", json=payload, headers=headers)
        self.assertEqual(saved.status_code, 200, saved.text)
        self.assertEqual(saved.json()["stored"], True)
        self.assertIn("u-1", self.store.rows)
        read = self.client.get("/v1/profile/stored", headers=headers)
        self.assertEqual(read.status_code, 200, read.text)
        self.assertEqual(read.json()["birth_date"], payload["birth_date"])
        self.assertEqual(read.json()["birth_time"], payload["birth_time"])
        self.assertEqual(read.json()["location"], payload["location"])

    def test_invalid_profile_never_reaches_store(self):
        token = self._token()
        r = self.client.put("/v1/profile/stored", json={"birth_date": "invalid"},
                            headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.store.rows, {})


if __name__ == "__main__":
    unittest.main()
