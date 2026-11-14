"""Personal endpoints must pass the validated time facts into the pipeline."""
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from tongshu.api.app import create_app
from tongshu.pipeline import TONGSHUPipeline


@pytest.fixture(scope='module')
def client():
    with patch.dict(os.environ, {'TONGSHU_AUTH_SECRET': 'test-only-m2-context-secret',
                                'TONGSHU_AUTH_ENFORCED': '0'}):
        yield TestClient(create_app(local_qa=True), raise_server_exceptions=False)


@pytest.mark.parametrize('path', ['/v1/calculate', '/v1/daily-guide', '/v1/qa/engine', '/api/reading'])
@pytest.mark.parametrize(('location', 'timezone'), [
    ('AU_SYDNEY', 'Australia/Sydney'),
    ('CN_BEIJING', 'Asia/Shanghai'),
])
@pytest.mark.parametrize('minute', [None, 0, 5])
@pytest.mark.parametrize('explicit_timezone', [False, True])
def test_validated_timezone_and_birth_minute_reach_pipeline(client, path, location, timezone, minute, explicit_timezone):
    payload = {'birth_date': '1984-12-07', 'hour': 0, 'birth_minute': minute,
               'gender': 'male', 'theme': 'WORK', 'analysis_date': '2026-08-17',
               'location': location}
    if explicit_timezone:
        payload['timezone'] = timezone
    with patch.object(TONGSHUPipeline, 'run', side_effect=RuntimeError('capture only')) as run:
        client.post(path, json=payload)
        run.assert_called_once()
        received = run.call_args.kwargs
    assert received['timezone'] == timezone
    assert received['location'] == location
    assert received['birth_minute'] == minute
    assert received['birth_date'] == (1984, 12, 7, 0)


def test_invalid_timezone_does_not_reach_pipeline(client):
    payload = {'birth_date': '1984-12-07', 'hour': 0, 'birth_minute': 5,
               'gender': 'male', 'location': 'AU_SYDNEY', 'timezone': 'Bad/Zone'}
    with patch.object(TONGSHUPipeline, 'run') as run:
        response = client.post('/v1/calculate', json=payload)
    assert response.status_code == 400
    run.assert_not_called()


@pytest.mark.parametrize('birth_date', ['1984-12-07', '1984-07-07'])
def test_real_qa_sydney_omitted_and_explicit_timezone_match(client, birth_date):
    payload = {'birth_date': birth_date, 'hour': 0, 'birth_minute': 5,
               'gender': 'male', 'theme': 'WORK', 'analysis_date': '2026-08-17',
               'location': 'AU_SYDNEY'}
    derived = client.post('/v1/qa/engine', json=payload)
    explicit = client.post('/v1/qa/engine', json={**payload, 'timezone': 'Australia/Sydney'})
    assert derived.status_code == 200, derived.text
    assert explicit.status_code == 200, explicit.text
    assert derived.json()['bazi_pillars'] == explicit.json()['bazi_pillars']
