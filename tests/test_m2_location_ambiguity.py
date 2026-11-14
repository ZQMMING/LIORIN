"""Ambiguous location aliases must not select a city silently."""
import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from tongshu.api.app import create_app
from tongshu.pipeline import TONGSHUPipeline


@pytest.fixture(scope='module')
def client():
    with patch.dict(os.environ, {'TONGSHU_AUTH_SECRET': 'test-only-m2-location-secret',
                                'TONGSHU_AUTH_ENFORCED': '0'}):
        yield TestClient(create_app(local_qa=True), raise_server_exceptions=False)


@pytest.mark.parametrize('path', ['/v1/calculate', '/v1/daily-guide', '/v1/qa/engine', '/api/reading'])
@pytest.mark.parametrize('location', ['Hamilton', '聖地牙哥'])
def test_ambiguous_alias_rejected_before_calculation(client, path, location):
    payload = {'birth_date': '1984-12-07', 'hour': 0, 'birth_minute': 5,
               'gender': 'male', 'theme': 'WORK', 'location': location}
    with patch.object(TONGSHUPipeline, 'run') as run:
        response = client.post(path, json=payload)
    assert response.status_code == 422
    assert response.json()['error']['code'] == 'PROFILE_LOCATION_AMBIGUOUS'
    run.assert_not_called()


@pytest.mark.parametrize(('location', 'timezone'), [
    ('BM_HAMILTON', 'Atlantic/Bermuda'), ('NZ_HAMILTON', 'Pacific/Auckland'),
    ('US_SAN_DIEGO', 'America/Los_Angeles'),
    ('DO_SANTIAGO_DE_LOS_CABALLEROS', 'America/Santo_Domingo'),
])
def test_explicit_city_ids_remain_unambiguous(client, location, timezone):
    payload = {'birth_date': '1984-12-07', 'hour': 0, 'birth_minute': 5,
               'gender': 'male', 'location': location}
    with patch.object(TONGSHUPipeline, 'run', side_effect=RuntimeError('capture only')) as run:
        client.post('/v1/calculate', json=payload)
    run.assert_called_once()
    assert run.call_args.kwargs['timezone'] == timezone


def test_unique_alias_is_normalized_to_city_id(client):
    payload = {'birth_date': '1984-12-07', 'hour': 0, 'birth_minute': 5,
               'gender': 'male', 'location': 'Beijing'}
    with patch.object(TONGSHUPipeline, 'run', side_effect=RuntimeError('capture only')) as run:
        client.post('/v1/calculate', json=payload)
    assert run.call_args.kwargs['location'] == 'CN_BEIJING'


def test_profile_rejects_ambiguous_alias(client):
    response = client.post('/v1/profile', json={
        'birth_date': '1984-12-07', 'birth_time': {'hour': 0, 'minute': 5},
        'gender': 'male', 'location': 'Hamilton',
    })
    assert response.status_code == 422
    assert response.json()['error']['code'] == 'PROFILE_LOCATION_AMBIGUOUS'


def test_stored_profile_rejects_ambiguous_and_normalizes_unique_id():
    from tongshu.api.deps import get_current_user_or_device

    class Store:
        rows = {}

        def save(self, user_id, profile):
            self.rows[user_id] = profile

    with patch.dict(os.environ, {'TONGSHU_AUTH_SECRET': 'test-only-m2-location-secret'}):
        store = Store()
        app = create_app(profile_store=store)
        app.dependency_overrides[get_current_user_or_device] = lambda: SimpleNamespace(user=SimpleNamespace(user_id='test-user'))
        client = TestClient(app, raise_server_exceptions=False)
        payload = {'birth_date': '1984-12-07', 'birth_time': {'hour': 0, 'minute': 5},
                   'gender': 'male', 'location': 'Hamilton'}
        ambiguous = client.put('/v1/profile/stored', json=payload)
        assert ambiguous.status_code == 422
        assert store.rows == {}
        saved = client.put('/v1/profile/stored', json={**payload, 'location': 'Beijing'})
        assert saved.status_code == 200, saved.text
        assert store.rows['test-user']['location'] == 'CN_BEIJING'
