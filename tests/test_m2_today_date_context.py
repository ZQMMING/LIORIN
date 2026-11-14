"""Date provenance does not choose an unapproved user timezone policy."""
from datetime import date
from unittest.mock import patch

import pytest

from tests.test_m2_context_propagation import client  # noqa: F401


@pytest.mark.parametrize('path', ['/v1/today', '/api/today'])
@pytest.mark.parametrize('requested', ['2024-02-29', '2026-03-08', '2026-11-01', '2027-01-01'])
def test_explicit_date_is_preserved_across_dst_and_year_boundaries(client, path, requested):
    class ServerDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 3, 7)

    with patch('tongshu.api.app.date', ServerDate):
        response = client.get(path, params={'date': requested, 'region': 'New York'})
    assert response.status_code == 200, response.text
    assert response.json()['date_context'] == {
        'date': requested, 'source': 'explicit_date', 'timezone': None,
        'timezone_status': 'not_supplied', 'scope': 'public_calendar',
    }
    assert response.json()['day'] == date.fromisoformat(requested).day


@pytest.mark.parametrize('path', ['/v1/today', '/api/today'])
def test_server_local_default_is_identified_not_claimed_as_user_local(client, path):
    class ServerDate(date):
        @classmethod
        def today(cls):
            return cls(2026, 12, 31)

    with patch('tongshu.api.app.date', ServerDate):
        response = client.get(path, params={'region': 'Sydney'})
    assert response.status_code == 200, response.text
    assert response.json()['date_context'] == {
        'date': '2026-12-31', 'source': 'server_local_date', 'timezone': None,
        'timezone_status': 'server_local_unspecified', 'scope': 'public_calendar',
    }
