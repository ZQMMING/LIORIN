import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from services.liorin_api.app import create_app
from services.liorin_api.config import Settings


DATA = Path(__file__).resolve().parents[3] / 'data'


@pytest.fixture
def client():
    return TestClient(create_app(Settings(DATA)))


def test_catalogue_uses_existing_data_and_excludes_colliding_ids(client):
    response = client.get('/v1/locations')
    assert response.status_code == 200
    entries = response.json()['locations']
    assert any(item['id'] == 'CN_BEIJING' and item['timezone'] == 'Asia/Shanghai' for item in entries)
    assert not any(item['id'].casefold() == 'au_perth' for item in entries)
    assert len({item['id'].casefold() for item in entries}) == len(entries)
    assert client.get('/health').json()['components']['locations'] == 'ready'


@pytest.mark.parametrize('value', ['Beijing', ' beijing ', 'CN_BEIJING', 'cn_beijing'])
def test_unique_name_or_id_resolves_to_canonical_id(client, value):
    result = client.get('/v1/locations/resolve', params={'value': value})
    assert result.status_code == 200
    assert result.json()['id'] == 'CN_BEIJING'


@pytest.mark.parametrize('value', ['Hamilton', '聖地牙哥', 'AU_PERTH', 'AU_PERTh'])
def test_ambiguous_names_and_colliding_ids_are_not_guessed(client, value):
    result = client.get('/v1/locations/resolve', params={'value': value})
    assert result.status_code == 422
    assert result.json()['detail']['code'] == 'PROFILE_LOCATION_AMBIGUOUS'


def test_missing_or_malformed_catalogue_fails_closed(tmp_path):
    client = TestClient(create_app(Settings(tmp_path)))
    assert client.get('/v1/locations').status_code == 503
    assert client.get('/v1/locations/resolve', params={'value': 'Beijing'}).status_code == 503
    (tmp_path / 'locations.json').write_text(json.dumps({'locations': [{'id': 'incomplete'}]}), encoding='utf-8')
    assert client.get('/v1/locations').status_code == 503


def test_unknown_city_is_not_assigned_a_default(client):
    result = client.get('/v1/locations/resolve', params={'value': 'not-a-real-city-8472'})
    assert result.status_code == 400
    assert result.json()['detail']['code'] == 'LOCATION_UNKNOWN'
