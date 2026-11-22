from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from services.liorin_api.account.services.identity_gateway import AuthError
from services.liorin_api.app import create_app
from services.liorin_api.config import Settings


DATA = Path(__file__).resolve().parents[3] / 'data'
URL = '/v1/personal/dna'
AUTH = {'Authorization': 'Bearer fixture-account'}
BIRTH = {
    'birth_date': '1984-12-07', 'birth_time': {'hour': 16, 'minute': 0},
    'gender': 'male', 'location': 'CN_BEIJING', 'timezone': 'Asia/Shanghai',
}


@pytest.fixture
def isolated_client(monkeypatch):
    profiles = {'account-a': BIRTH.copy()}

    def validate(token):
        if token != 'fixture-account':
            raise AuthError('INVALID_TOKEN')
        return SimpleNamespace(user_id='account-a')

    monkeypatch.setenv('LIORIN_ACCOUNT_MODE', 'isolated-test')
    monkeypatch.setattr('services.liorin_api.account.runtime.attach_test_account',
                        lambda app: SimpleNamespace(get=profiles.get))
    monkeypatch.setattr('services.liorin_api.account.profile.get_gateway_v2_singleton',
                        lambda: SimpleNamespace(validate_access_token=validate))
    return TestClient(create_app(Settings(DATA))), profiles


def test_real_birth_adapter_through_authenticated_dna_route(isolated_client):
    client, _ = isolated_client
    assert client.get(URL, headers={'X-Device-Token': 'tag'}).status_code == 401
    assert client.get(URL, headers={'Authorization': 'Bearer invalid-token'}).status_code == 401
    response = client.get(URL, headers=AUTH)
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    payload = response.json()
    assert payload['birth_year_nayin'] == '海中金'
    assert payload['day_master'] == '乙'
    assert [(p['name'], p['stem_element'], p['branch_element']) for p in payload['pillars']] == [
        ('甲子', 'WOOD', 'WATER'), ('丙子', 'FIRE', 'WATER'),
        ('乙亥', 'WOOD', 'WATER'), ('甲申', 'WOOD', 'METAL'),
    ]
    assert payload['source']['birth_timezone'] == 'Asia/Shanghai'
    assert payload['zodiac_status'] == 'pending_year_boundary_review'
    assert payload['nayin_evidence_id'] == 'E-SMTH-003-001'
    assert payload['useful_elements_status'] == 'pending_rule_admission'
    assert payload['personality_status'] == 'pending_content_admission'
    assert payload['ziwei_status'] == 'pending_domain_admission'
    assert 'zodiac' not in payload


@pytest.mark.parametrize(('birth', 'code'), [
    ({'birth_time': {'hour': 16, 'minute': None}}, 'INCOMPLETE_BIRTH_TIME'),
    ({'birth_date': '2024-11-03', 'birth_time': {'hour': 1, 'minute': 30},
      'timezone': 'America/New_York'}, 'LOCAL_TIME_AMBIGUOUS'),
    ({'birth_date': '2024-03-10', 'birth_time': {'hour': 2, 'minute': 30},
      'timezone': 'America/New_York'}, 'LOCAL_TIME_NONEXISTENT'),
])
def test_uncertain_birth_time_never_returns_a_chart(isolated_client, birth, code):
    client, profiles = isolated_client
    profiles['account-a'] = {**BIRTH, **birth}
    response = client.get(URL, headers=AUTH)
    assert response.status_code == 422
    assert response.json()['detail']['code'] == code


def test_missing_profile_and_production_boundary(isolated_client, monkeypatch):
    client, profiles = isolated_client
    profiles.clear()
    assert client.get(URL, headers=AUTH).status_code == 404
    monkeypatch.delenv('LIORIN_ACCOUNT_MODE')
    assert TestClient(create_app(Settings(DATA))).get(URL, headers=AUTH).status_code == 404


def test_insight_projects_engine_year_and_twelve_solar_months_without_predictions(isolated_client, monkeypatch):
    client, profiles = isolated_client
    route = '/v1/personal/insight?year=2026'
    assert client.get(route, headers={'X-Device-Token': 'tag'}).status_code == 401
    response = client.get(route, headers=AUTH)
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    data = response.json()
    assert data['annual'] == {'ganzhi': '丙午', 'hexagram': '天水讼'}
    assert [month['index'] for month in data['solar_months']] == list(range(1, 13))
    assert data['solar_months'][0]['hexagram'] == '火水未济'
    assert data['source']['reference_date'] == '2026-07-01'
    assert data['source']['month_basis'] == 'solar_term_month_ordinal'
    assert data['decadal_status'] == 'pending_ziping_admission'
    assert data['interpretation_status'] == 'pending_content_admission'
    assert 'interpretation' not in data
    profiles.clear()
    assert client.get(route, headers=AUTH).status_code == 404
    monkeypatch.delenv('LIORIN_ACCOUNT_MODE')
    assert TestClient(create_app(Settings(DATA))).get(route, headers=AUTH).status_code == 404
